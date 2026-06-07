"""Phase 15j: PendingAssisted action route idempotency integration tests."""

from __future__ import annotations

import importlib
import os
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from product_persistence import flags
from product_persistence.db_manager import ProductDbManager, reset_product_db_manager
from product_persistence.pending_assisted_action_routes import (
    handle_approve_pending_assisted,
    handle_reject_pending_assisted,
)
from product_persistence.repositories.sqlite_action_idempotency_repository import (
    ActionIdempotencyRepositorySQLite,
)
from product_persistence.services.assisted_outbound_port import DryRunAssistedOutboundPort
from product_persistence.services.assisted_reply_service import (
    AssistedReplyService,
    AssistedServiceResult,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ROUTE_SOURCE = _REPO_ROOT / "product_persistence" / "pending_assisted_action_routes.py"
_APP_SOURCE = _REPO_ROOT / "app.py"
_NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
_FUTURE = (
    datetime.now(timezone.utc) + timedelta(days=7)
).replace(microsecond=0).isoformat()
_SHOP_ID = "shop-j-route-1"


def _approve_body(**overrides) -> dict:
    base = dict(
        workspace_id="ws-j-route-1",
        shop_id=_SHOP_ID,
        actor_user_id="op-j-route-1",
        actor_role="operator",
        client_request_id="req-j-route-approve-1",
        expected_pending_status="pending",
        dry_run_expected=True,
        csrf_token="csrf-token-j-1",
        confirm_checkbox=True,
        final_reply_override="您好，该商品目前有货，欢迎下单。",
    )
    base.update(overrides)
    return base


def _reject_body(**overrides) -> dict:
    base = dict(
        workspace_id="ws-j-route-1",
        shop_id=_SHOP_ID,
        actor_user_id="op-j-route-1",
        actor_role="operator",
        client_request_id="req-j-route-reject-1",
        expected_pending_status="pending",
        reject_reason="not suitable",
        csrf_token="csrf-token-j-1",
        confirm_checkbox=True,
    )
    base.update(overrides)
    return base


def _create_kwargs(**overrides) -> dict:
    base = dict(
        reply_log_id="rl-j-route-1",
        workspace_id="ws-j-route-1",
        shop_id=_SHOP_ID,
        account_id="acc-j-route-1",
        platform_id="pinduoduo",
        buyer_id="buyer-j-route-1",
        buyer_message="这款商品还有库存吗",
        ai_suggested_reply="您好，该商品目前有货，欢迎下单。",
        intent="inventory_question",
        intent_bucket="allowed",
        risk_level="low",
        expires_at=_FUTURE,
        inbound_created_at=_NOW,
    )
    base.update(overrides)
    return base


class TestPendingAssistedActionRoutesIdempotency(unittest.TestCase):
    _db_manager: ProductDbManager | None = None

    def setUp(self) -> None:
        self._db_manager = None
        reset_product_db_manager()
        self._tmpdir = _REPO_ROOT / "temp" / "phase15j_route_tests"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._tmpdir / "product_gate_action_route_idempotency.db"
        if self._db_path.exists():
            self._db_path.unlink()
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_PERSISTENCE_ENABLED",
            "PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED",
            "PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG",
            "PRODUCT_PERSISTENCE_WRITE_SEND_DECISION",
            "PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY",
            "PRODUCT_PERSISTENCE_WRITE_ACTION_IDEMPOTENCY",
            "PRODUCT_ASSISTED_SERVICE_ENABLED",
            "PRODUCT_ASSISTED_SEND_ENABLED",
            "PRODUCT_ASSISTED_SEND_DRY_RUN",
            "PRODUCT_ASSISTED_SEND_TEST_SHOP_ID",
            "PRODUCT_DB_URL",
        ):
            os.environ.pop(key, None)
        importlib.reload(flags)

    def tearDown(self) -> None:
        if self._db_manager is not None:
            self._db_manager.close_product_db()
        reset_product_db_manager()
        if self._db_path.exists():
            self._db_path.unlink(missing_ok=True)
        self._env_patch.stop()

    def _enable_assisted_flags(self) -> ProductDbManager:
        os.environ["PRODUCT_PERSISTENCE_ENABLED"] = "true"
        os.environ["PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED"] = "true"
        os.environ["PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG"] = "true"
        os.environ["PRODUCT_ASSISTED_SERVICE_ENABLED"] = "true"
        os.environ["PRODUCT_DB_URL"] = f"sqlite:///{self._db_path.as_posix()}"
        importlib.reload(flags)
        reset_product_db_manager()
        self._db_manager = ProductDbManager(db_url=os.environ["PRODUCT_DB_URL"])
        self._db_manager.init_product_db()
        return self._db_manager

    def _enable_dry_run_and_idempotency_flags(self) -> ProductDbManager:
        db = self._enable_assisted_flags()
        os.environ["PRODUCT_ASSISTED_SEND_ENABLED"] = "true"
        os.environ["PRODUCT_ASSISTED_SEND_DRY_RUN"] = "true"
        os.environ["PRODUCT_ASSISTED_SEND_TEST_SHOP_ID"] = _SHOP_ID
        os.environ["PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY"] = "true"
        os.environ["PRODUCT_PERSISTENCE_WRITE_SEND_DECISION"] = "true"
        os.environ["PRODUCT_PERSISTENCE_WRITE_ACTION_IDEMPOTENCY"] = "true"
        importlib.reload(flags)
        return db

    def _service(self) -> AssistedReplyService:
        assert self._db_manager is not None
        return AssistedReplyService(
            db_manager=self._db_manager,
            outbound_port=DryRunAssistedOutboundPort(),
        )

    def _idempotency_repo(self) -> ActionIdempotencyRepositorySQLite:
        assert self._db_manager is not None
        return ActionIdempotencyRepositorySQLite(db_manager=self._db_manager)

    def _create_pending(self, service: AssistedReplyService, **overrides) -> str:
        result = service.create_pending_from_preview(**_create_kwargs(**overrides))
        self.assertTrue(result.success, msg=result.error or result.reason)
        assert result.pending_assisted_id is not None
        return result.pending_assisted_id

    def test_missing_client_request_id_invalid(self) -> None:
        status, body = handle_approve_pending_assisted(
            "pending-j-1",
            _approve_body(client_request_id=""),
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["reason"], "client_request_id_required")

    def test_flag_off_preserves_existing_15i_behavior(self) -> None:
        self._enable_dry_run_and_idempotency_flags()
        os.environ.pop("PRODUCT_PERSISTENCE_WRITE_ACTION_IDEMPOTENCY", None)
        importlib.reload(flags)
        service = self._service()
        pending_id = self._create_pending(service)
        status, body = handle_approve_pending_assisted(
            pending_id,
            _approve_body(),
            service=service,
            idempotency_repo=self._idempotency_repo(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "dry_run_would_send")
        record = self._idempotency_repo().get("req-j-route-approve-1")
        self.assertIsNone(record)

    def test_approve_acquires_idempotency_before_service_call(self) -> None:
        self._enable_dry_run_and_idempotency_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        repo = self._idempotency_repo()
        with patch.object(
            service,
            "approve_pending",
            wraps=service.approve_pending,
        ) as approve_mock:
            handle_approve_pending_assisted(
                pending_id,
                _approve_body(),
                service=service,
                idempotency_repo=repo,
            )
            approve_mock.assert_called_once()
        record = repo.get("req-j-route-approve-1")
        assert record is not None
        self.assertEqual(record.status, "completed")

    def test_approve_replay_completed_returns_previous_response_without_service_call(
        self,
    ) -> None:
        self._enable_dry_run_and_idempotency_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        repo = self._idempotency_repo()
        first_status, first_body = handle_approve_pending_assisted(
            pending_id,
            _approve_body(),
            service=service,
            idempotency_repo=repo,
        )
        with patch.object(service, "approve_pending") as approve_mock:
            second_status, second_body = handle_approve_pending_assisted(
                pending_id,
                _approve_body(),
                service=service,
                idempotency_repo=repo,
            )
            approve_mock.assert_not_called()
        self.assertEqual(second_status, first_status)
        self.assertEqual(second_body, first_body)

    def test_approve_same_request_in_progress_returns_conflict_without_service_call(
        self,
    ) -> None:
        self._enable_dry_run_and_idempotency_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        repo = self._idempotency_repo()
        payload = {
            "action": "approve",
            "pending_assisted_id": pending_id,
            "workspace_id": "ws-j-route-1",
            "shop_id": _SHOP_ID,
            "actor_user_id": "op-j-route-1",
            "actor_role": "operator",
            "expected_pending_status": "pending",
            "dry_run_expected": True,
            "final_reply_override": "您好，该商品目前有货，欢迎下单。",
        }
        repo.acquire(
            "req-j-route-approve-1",
            workspace_id="ws-j-route-1",
            shop_id=_SHOP_ID,
            actor_user_id="op-j-route-1",
            actor_role="operator",
            pending_assisted_id=pending_id,
            action="approve",
            payload=payload,
        )
        with patch.object(service, "approve_pending") as approve_mock:
            status, body = handle_approve_pending_assisted(
                pending_id,
                _approve_body(),
                service=service,
                idempotency_repo=repo,
            )
            approve_mock.assert_not_called()
        self.assertEqual(status, 409)
        self.assertEqual(body["reason"], "already_in_progress")

    def test_approve_different_payload_conflict_without_service_call(self) -> None:
        self._enable_dry_run_and_idempotency_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        repo = self._idempotency_repo()
        handle_approve_pending_assisted(
            pending_id,
            _approve_body(),
            service=service,
            idempotency_repo=repo,
        )
        with patch.object(service, "approve_pending") as approve_mock:
            status, body = handle_approve_pending_assisted(
                pending_id,
                _approve_body(final_reply_override="different reply text"),
                service=service,
                idempotency_repo=repo,
            )
            approve_mock.assert_not_called()
        self.assertEqual(status, 409)
        self.assertEqual(body["reason"], "client_request_conflict")

    def test_approve_service_success_completes_idempotency(self) -> None:
        self._enable_dry_run_and_idempotency_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        repo = self._idempotency_repo()
        status, body = handle_approve_pending_assisted(
            pending_id,
            _approve_body(),
            service=service,
            idempotency_repo=repo,
        )
        self.assertEqual(status, 200)
        record = repo.get("req-j-route-approve-1")
        assert record is not None
        self.assertEqual(record.status, "completed")
        assert record.response is not None
        self.assertEqual(record.response["http_status"], 200)
        self.assertEqual(record.response["body"], body)

    def test_approve_service_exception_marks_failed_no_send(self) -> None:
        self._enable_dry_run_and_idempotency_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        repo = self._idempotency_repo()
        with patch.object(
            service,
            "approve_pending",
            side_effect=RuntimeError("service boom"),
        ):
            status, body = handle_approve_pending_assisted(
                pending_id,
                _approve_body(),
                service=service,
                idempotency_repo=repo,
            )
        self.assertEqual(status, 500)
        self.assertEqual(body["status"], "internal_error")
        record = repo.get("req-j-route-approve-1")
        assert record is not None
        self.assertEqual(record.status, "failed")

    def test_reject_acquires_idempotency_before_service_call(self) -> None:
        self._enable_dry_run_and_idempotency_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        repo = self._idempotency_repo()
        with patch.object(
            service,
            "reject_pending",
            wraps=service.reject_pending,
        ) as reject_mock:
            handle_reject_pending_assisted(
                pending_id,
                _reject_body(),
                service=service,
                idempotency_repo=repo,
            )
            reject_mock.assert_called_once()
        record = repo.get("req-j-route-reject-1")
        assert record is not None
        self.assertEqual(record.status, "completed")

    def test_reject_replay_completed_returns_previous_response(self) -> None:
        self._enable_dry_run_and_idempotency_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        repo = self._idempotency_repo()
        first_status, first_body = handle_reject_pending_assisted(
            pending_id,
            _reject_body(),
            service=service,
            idempotency_repo=repo,
        )
        with patch.object(service, "reject_pending") as reject_mock:
            second_status, second_body = handle_reject_pending_assisted(
                pending_id,
                _reject_body(),
                service=service,
                idempotency_repo=repo,
            )
            reject_mock.assert_not_called()
        self.assertEqual(second_status, first_status)
        self.assertEqual(second_body, first_body)

    def test_reject_different_payload_conflict(self) -> None:
        self._enable_dry_run_and_idempotency_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        repo = self._idempotency_repo()
        handle_reject_pending_assisted(
            pending_id,
            _reject_body(),
            service=service,
            idempotency_repo=repo,
        )
        with patch.object(service, "reject_pending") as reject_mock:
            status, body = handle_reject_pending_assisted(
                pending_id,
                _reject_body(reject_reason="changed reason"),
                service=service,
                idempotency_repo=repo,
            )
            reject_mock.assert_not_called()
        self.assertEqual(status, 409)
        self.assertEqual(body["reason"], "client_request_conflict")

    def test_route_still_not_registered_in_app(self) -> None:
        app_source = _APP_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("pending_assisted_action_routes", app_source)
        self.assertNotIn("register_pending_assisted_action_routes", app_source)

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    @patch(
        "Message.handlers.ai_handler.AIReplyHandler._send_reply",
        new_callable=AsyncMock,
    )
    def test_no_sendmessage_outbound_pdd_doudian_called(
        self,
        send_reply_mock: AsyncMock,
        send_text_mock: MagicMock,
    ) -> None:
        self._enable_dry_run_and_idempotency_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        handle_approve_pending_assisted(
            pending_id,
            _approve_body(),
            service=service,
            idempotency_repo=self._idempotency_repo(),
        )
        handle_reject_pending_assisted(
            pending_id,
            _reject_body(client_request_id="req-j-route-reject-2"),
            service=service,
            idempotency_repo=self._idempotency_repo(),
        )
        send_reply_mock.assert_not_awaited()
        send_text_mock.assert_not_called()
        route_source = _ROUTE_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("doudian", route_source.lower())


if __name__ == "__main__":
    unittest.main()

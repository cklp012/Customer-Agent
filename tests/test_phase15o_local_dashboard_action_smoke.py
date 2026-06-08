"""Phase 15o: Local dashboard action route smoke tests (lightweight · no real PDD)."""

from __future__ import annotations

import importlib
import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from product_persistence import flags
from product_persistence.db_manager import ProductDbManager, reset_product_db_manager
from product_persistence.pending_assisted_action_routes import (
    apply_dashboard_action_route_bootstrap,
    handle_approve_pending_assisted,
    handle_reject_pending_assisted,
    reset_action_route_registration_state_for_tests,
)
from product_persistence.repositories.sqlite_action_idempotency_repository import (
    ActionIdempotencyRepositorySQLite,
)
from product_persistence.services.assisted_outbound_port import DryRunAssistedOutboundPort
from product_persistence.services.assisted_reply_service import AssistedReplyService

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ROUTE_SOURCE = _REPO_ROOT / "product_persistence" / "pending_assisted_action_routes.py"
_BOOTSTRAP_SOURCE = _ROUTE_SOURCE
_SHOP_ID = "shop-local-smoke-1"
_NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
_FUTURE = (
    datetime.now(timezone.utc) + timedelta(days=7)
).replace(microsecond=0).isoformat()
_FORBIDDEN_RESPONSE_TOKENS = frozenset(
    {"cookie", "token", "credential", "password", "secret", "api_key", "session"}
)


def _approve_body(**overrides) -> dict:
    base = dict(
        workspace_id="ws-local-smoke-1",
        shop_id=_SHOP_ID,
        actor_user_id="op-smoke-1",
        actor_role="operator",
        client_request_id="req-smoke-approve-1",
        expected_pending_status="pending",
        dry_run_expected=True,
        csrf_token="csrf-smoke-1",
        confirm_checkbox=True,
        final_reply_override="您好，该商品目前有货，欢迎下单。",
    )
    base.update(overrides)
    return base


def _reject_body(**overrides) -> dict:
    base = dict(
        workspace_id="ws-local-smoke-1",
        shop_id=_SHOP_ID,
        actor_user_id="op-smoke-1",
        actor_role="operator",
        client_request_id="req-smoke-reject-1",
        expected_pending_status="pending",
        reject_reason="not suitable",
        csrf_token="csrf-smoke-1",
        confirm_checkbox=True,
    )
    base.update(overrides)
    return base


def _create_kwargs(**overrides) -> dict:
    base = dict(
        reply_log_id="rl-smoke-1",
        workspace_id="ws-local-smoke-1",
        shop_id=_SHOP_ID,
        account_id="acc-smoke-1",
        platform_id="pinduoduo",
        buyer_id="buyer-smoke-1",
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


class _MockFlaskApp:
    def __init__(self) -> None:
        self.routes: list[tuple] = []

    def add_url_rule(self, rule, endpoint=None, view_func=None, methods=None) -> None:
        self.routes.append((rule, endpoint, view_func, methods))


def _set_local_dry_run_smoke_env(db_path: Path) -> None:
    os.environ["PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED"] = "true"
    os.environ["PRODUCT_PERSISTENCE_ENABLED"] = "true"
    os.environ["PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED"] = "true"
    os.environ["PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG"] = "true"
    os.environ["PRODUCT_PERSISTENCE_WRITE_SEND_DECISION"] = "true"
    os.environ["PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY"] = "true"
    os.environ["PRODUCT_PERSISTENCE_WRITE_ACTION_IDEMPOTENCY"] = "true"
    os.environ["PRODUCT_ASSISTED_SERVICE_ENABLED"] = "true"
    os.environ["PRODUCT_ASSISTED_SEND_ENABLED"] = "true"
    os.environ["PRODUCT_ASSISTED_SEND_DRY_RUN"] = "true"
    os.environ["PRODUCT_ASSISTED_SEND_TEST_SHOP_ID"] = _SHOP_ID
    os.environ["PRODUCT_DB_URL"] = f"sqlite:///{db_path.as_posix()}"
    importlib.reload(flags)


class TestPhase15oDefaultSafeState(unittest.TestCase):
    def setUp(self) -> None:
        reset_action_route_registration_state_for_tests()
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED",
            "PRODUCT_PERSISTENCE_ENABLED",
            "PRODUCT_ASSISTED_SERVICE_ENABLED",
            "PRODUCT_ASSISTED_SEND_ENABLED",
            "PRODUCT_ASSISTED_SEND_DRY_RUN",
            "PRODUCT_ASSISTED_SEND_TEST_SHOP_ID",
        ):
            os.environ.pop(key, None)
        importlib.reload(flags)

    def tearDown(self) -> None:
        reset_action_route_registration_state_for_tests()
        self._env_patch.stop()

    def test_o1_default_flags_routes_off(self) -> None:
        self.assertFalse(flags.is_dashboard_action_routes_enabled())
        mock_app = _MockFlaskApp()
        self.assertFalse(apply_dashboard_action_route_bootstrap(mock_app))
        self.assertEqual(len(mock_app.routes), 0)

    def test_o16_rollback_flags_disable_routes(self) -> None:
        os.environ["PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED"] = "true"
        importlib.reload(flags)
        mock_app = _MockFlaskApp()
        self.assertTrue(apply_dashboard_action_route_bootstrap(mock_app))
        os.environ.pop("PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED", None)
        importlib.reload(flags)
        reset_action_route_registration_state_for_tests()
        mock_app2 = _MockFlaskApp()
        self.assertFalse(apply_dashboard_action_route_bootstrap(mock_app2))
        self.assertEqual(len(mock_app2.routes), 0)


class TestPhase15oLocalDashboardActionSmoke(unittest.TestCase):
    _db_manager: ProductDbManager | None = None

    def setUp(self) -> None:
        reset_product_db_manager()
        reset_action_route_registration_state_for_tests()
        self._tmpdir = _REPO_ROOT / "temp" / "phase15o_smoke_tests"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._tmpdir / "product_smoke_local.db"
        if self._db_path.exists():
            self._db_path.unlink()
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED",
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
        reset_action_route_registration_state_for_tests()
        if self._db_path.exists():
            self._db_path.unlink(missing_ok=True)
        self._env_patch.stop()

    def _boot_smoke(self) -> ProductDbManager:
        _set_local_dry_run_smoke_env(self._db_path)
        reset_product_db_manager()
        self._db_manager = ProductDbManager(db_url=os.environ["PRODUCT_DB_URL"])
        self._db_manager.init_product_db()
        return self._db_manager

    def _service(self) -> AssistedReplyService:
        assert self._db_manager is not None
        return AssistedReplyService(
            db_manager=self._db_manager,
            outbound_port=DryRunAssistedOutboundPort(),
        )

    def _idempotency_repo(self) -> ActionIdempotencyRepositorySQLite:
        assert self._db_manager is not None
        return ActionIdempotencyRepositorySQLite(db_manager=self._db_manager)

    def _create_pending(self, service: AssistedReplyService) -> str:
        result = service.create_pending_from_preview(**_create_kwargs())
        self.assertTrue(result.success, msg=result.error or result.reason)
        assert result.pending_assisted_id is not None
        return result.pending_assisted_id

    def test_o2_local_dry_run_flags_routes_on(self) -> None:
        self._boot_smoke()
        self.assertTrue(flags.is_dashboard_action_routes_enabled())
        self.assertTrue(flags.is_assisted_send_dry_run())
        self.assertFalse(flags.would_assisted_send_live())
        mock_app = _MockFlaskApp()
        self.assertTrue(apply_dashboard_action_route_bootstrap(mock_app))
        self.assertEqual(len(mock_app.routes), 2)

    def test_o3_approve_requires_csrf(self) -> None:
        status, body = handle_approve_pending_assisted(
            "pending-smoke-1",
            _approve_body(csrf_token=""),
        )
        self.assertEqual(status, 403)
        self.assertEqual(body["status"], "csrf_failed")

    def test_o4_approve_requires_confirm_checkbox(self) -> None:
        status, body = handle_approve_pending_assisted(
            "pending-smoke-1",
            _approve_body(confirm_checkbox=False),
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["reason"], "confirm_checkbox_required")

    def test_o5_approve_requires_client_request_id(self) -> None:
        status, body = handle_approve_pending_assisted(
            "pending-smoke-1",
            _approve_body(client_request_id=""),
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["reason"], "client_request_id_required")

    def test_o6_approve_dry_run_expected_true_required(self) -> None:
        status, body = handle_approve_pending_assisted(
            "pending-smoke-1",
            _approve_body(dry_run_expected=False),
        )
        self.assertEqual(status, 422)
        self.assertEqual(body["status"], "dry_run_required")
        self.assertEqual(body["reason"], "live_send_not_implemented")

    def test_o7_approve_dry_run_response_no_live_send(self) -> None:
        self._boot_smoke()
        service = self._service()
        pending_id = self._create_pending(service)
        status, body = handle_approve_pending_assisted(
            pending_id,
            _approve_body(),
            service=service,
            idempotency_repo=self._idempotency_repo(),
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["success"])
        self.assertTrue(body["dry_run"])
        self.assertTrue(body["would_send"])
        self.assertFalse(body["live_send_attempted"])
        self.assertEqual(body["status"], "dry_run_would_send")
        self.assertIsNone(body.get("provider_message_id"))
        self.assertNotIn("sent_at", body)

    def test_o8_approve_replay_same_client_request_id(self) -> None:
        self._boot_smoke()
        service = self._service()
        pending_id = self._create_pending(service)
        repo = self._idempotency_repo()
        body_in = _approve_body()
        status1, body1 = handle_approve_pending_assisted(
            pending_id,
            body_in,
            service=service,
            idempotency_repo=repo,
        )
        status2, body2 = handle_approve_pending_assisted(
            pending_id,
            body_in,
            service=service,
            idempotency_repo=repo,
        )
        self.assertEqual(status1, status2)
        self.assertEqual(body1, body2)

    def test_o9_approve_conflict_different_payload(self) -> None:
        self._boot_smoke()
        service = self._service()
        pending_id = self._create_pending(service)
        repo = self._idempotency_repo()
        handle_approve_pending_assisted(
            pending_id,
            _approve_body(),
            service=service,
            idempotency_repo=repo,
        )
        status, body = handle_approve_pending_assisted(
            pending_id,
            _approve_body(final_reply_override="DIFFERENT TEXT"),
            service=service,
            idempotency_repo=repo,
        )
        self.assertEqual(status, 409)
        self.assertEqual(body["status"], "conflict")
        self.assertEqual(body["reason"], "client_request_conflict")

    def test_o10_reject_no_send(self) -> None:
        self._boot_smoke()
        service = self._service()
        pending_id = self._create_pending(service)
        status, body = handle_reject_pending_assisted(
            pending_id,
            _reject_body(),
            service=service,
            idempotency_repo=self._idempotency_repo(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["action"], "reject")
        self.assertFalse(body.get("live_send_attempted", False))

    def test_o11_reject_replay_same_client_request_id(self) -> None:
        self._boot_smoke()
        service = self._service()
        pending_id = self._create_pending(service)
        repo = self._idempotency_repo()
        body_in = _reject_body()
        status1, body1 = handle_reject_pending_assisted(
            pending_id,
            body_in,
            service=service,
            idempotency_repo=repo,
        )
        status2, body2 = handle_reject_pending_assisted(
            pending_id,
            body_in,
            service=service,
            idempotency_repo=repo,
        )
        self.assertEqual(status1, status2)
        self.assertEqual(body1, body2)

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    @patch(
        "Message.handlers.ai_handler.AIReplyHandler._send_reply",
        new_callable=AsyncMock,
    )
    def test_o12_no_sendmessage_called(
        self,
        send_reply_mock: AsyncMock,
        send_text_mock: MagicMock,
    ) -> None:
        self._boot_smoke()
        service = self._service()
        pending_id = self._create_pending(service)
        handle_approve_pending_assisted(
            pending_id,
            _approve_body(),
            service=service,
            idempotency_repo=self._idempotency_repo(),
        )
        send_reply_mock.assert_not_awaited()
        send_text_mock.assert_not_called()

    def test_o13_no_pdd_outbound_import_static(self) -> None:
        import_lines = [
            line
            for line in _ROUTE_SOURCE.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        block = "\n".join(import_lines)
        self.assertNotIn("Channel.pinduoduo", block)
        self.assertNotIn("SendMessage", block)

    def test_o14_no_doudian_import_static(self) -> None:
        import_lines = [
            line
            for line in _ROUTE_SOURCE.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        self.assertNotIn("Channel.doudian", "\n".join(import_lines))

    def test_o15_pdd_queue_name_unchanged(self) -> None:
        from Message.queue_naming import pdd_queue_name

        self.assertEqual(pdd_queue_name("shop123"), "pdd_shop123")

    def test_o17_logs_no_secret_leak(self) -> None:
        self._boot_smoke()
        service = self._service()
        pending_id = self._create_pending(service)
        status, body = handle_approve_pending_assisted(
            pending_id,
            _approve_body(),
            service=service,
            idempotency_repo=self._idempotency_repo(),
        )
        self.assertEqual(status, 200)
        blob = json.dumps(body, ensure_ascii=False).lower()
        for token in _FORBIDDEN_RESPONSE_TOKENS:
            self.assertNotIn(token, blob)

    def test_o18_read_dashboard_unchanged(self) -> None:
        source = _BOOTSTRAP_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("register_dashboard_read_routes", source)
        self.assertNotIn("register_pending_assisted_read_routes", source)
        self.assertFalse(flags.should_read_dashboard_from_product_db())


if __name__ == "__main__":
    unittest.main()

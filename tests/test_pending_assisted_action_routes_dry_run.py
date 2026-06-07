"""Phase 15i: PendingAssisted dashboard action route dry-run skeleton tests."""

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
    REGISTERED_POST_ROUTES,
    _FORBIDDEN_EXTRA_ROUTES,
    dispatch_pending_assisted_action_route,
    handle_approve_pending_assisted,
    handle_reject_pending_assisted,
    pending_assisted_action_route_names,
    register_pending_assisted_action_routes,
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
_SHOP_ID = "shop-i-1"


def _approve_body(**overrides) -> dict:
    base = dict(
        workspace_id="ws-i-1",
        shop_id=_SHOP_ID,
        actor_user_id="op-i-1",
        actor_role="operator",
        client_request_id="req-i-approve-1",
        expected_pending_status="pending",
        dry_run_expected=True,
        csrf_token="csrf-token-i-1",
        confirm_checkbox=True,
    )
    base.update(overrides)
    return base


def _reject_body(**overrides) -> dict:
    base = dict(
        workspace_id="ws-i-1",
        shop_id=_SHOP_ID,
        actor_user_id="op-i-1",
        actor_role="operator",
        client_request_id="req-i-reject-1",
        expected_pending_status="pending",
        reject_reason="not suitable",
        csrf_token="csrf-token-i-1",
        confirm_checkbox=True,
    )
    base.update(overrides)
    return base


def _create_kwargs(**overrides) -> dict:
    base = dict(
        reply_log_id="rl-i-1",
        workspace_id="ws-i-1",
        shop_id=_SHOP_ID,
        account_id="acc-i-1",
        platform_id="pinduoduo",
        buyer_id="buyer-i-1",
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


def _approve_kwargs(**overrides) -> dict:
    base = dict(
        actor_user_id="op-i-1",
        actor_role="operator",
        final_reply="您好，该商品目前有货，欢迎下单。",
        effective_mode="assisted_only",
        inbound_created_at=_NOW,
        now=_NOW,
    )
    base.update(overrides)
    return base


class _MockFlaskApp:
    def __init__(self) -> None:
        self.routes: list[tuple] = []

    def add_url_rule(self, rule, endpoint=None, view_func=None, methods=None) -> None:
        self.routes.append((rule, endpoint, view_func, methods))


class TestPendingAssistedActionRoutesDryRun(unittest.TestCase):
    _db_manager: ProductDbManager | None = None

    def setUp(self) -> None:
        self._db_manager = None
        reset_product_db_manager()
        self._tmpdir = _REPO_ROOT / "temp" / "phase15i_action_tests"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._tmpdir / "product_gate_action_test.db"
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

    def _enable_dry_run_flags(self) -> ProductDbManager:
        db = self._enable_assisted_flags()
        os.environ["PRODUCT_ASSISTED_SEND_ENABLED"] = "true"
        os.environ["PRODUCT_ASSISTED_SEND_DRY_RUN"] = "true"
        os.environ["PRODUCT_ASSISTED_SEND_TEST_SHOP_ID"] = _SHOP_ID
        os.environ["PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY"] = "true"
        os.environ["PRODUCT_PERSISTENCE_WRITE_SEND_DECISION"] = "true"
        importlib.reload(flags)
        return db

    def _service(self) -> AssistedReplyService:
        assert self._db_manager is not None
        return AssistedReplyService(
            db_manager=self._db_manager,
            outbound_port=DryRunAssistedOutboundPort(),
        )

    def _create_pending(self, service: AssistedReplyService, **overrides) -> str:
        result = service.create_pending_from_preview(**_create_kwargs(**overrides))
        self.assertTrue(result.success, msg=result.error or result.reason)
        assert result.pending_assisted_id is not None
        return result.pending_assisted_id

    def test_i1_approve_route_requires_csrf(self) -> None:
        status, body = handle_approve_pending_assisted(
            "pending-i-1",
            _approve_body(csrf_token=""),
        )
        self.assertEqual(status, 403)
        self.assertEqual(body["status"], "csrf_failed")
        self.assertFalse(body["success"])

    def test_i2_approve_route_requires_confirm_checkbox(self) -> None:
        status, body = handle_approve_pending_assisted(
            "pending-i-1",
            _approve_body(confirm_checkbox=False),
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["status"], "invalid_request")
        self.assertEqual(body["reason"], "confirm_checkbox_required")

    def test_i3_viewer_cannot_approve(self) -> None:
        status, body = handle_approve_pending_assisted(
            "pending-i-1",
            _approve_body(actor_role="viewer"),
        )
        self.assertEqual(status, 403)
        self.assertEqual(body["status"], "forbidden")
        self.assertEqual(body["reason"], "viewer_cannot_action")

    def test_i4_approve_route_calls_assisted_service_only(self) -> None:
        mock_service = MagicMock(spec=AssistedReplyService)
        mock_service._pending_repository.return_value.get_pending.return_value = MagicMock(
            workspace_id="ws-i-1",
            shop_id=_SHOP_ID,
            status="pending",
        )
        mock_service.approve_pending.return_value = AssistedServiceResult(
            success=True,
            action="approve_pending",
            status="dry_run_would_send",
            pending_assisted_id="pending-i-1",
            reply_log_id="rl-i-1",
            audit_log_id="audit-i-1",
            final_guard_allowed=True,
            reason="dry_run_would_send",
        )
        status, body = handle_approve_pending_assisted(
            "pending-i-1",
            _approve_body(),
            service=mock_service,
        )
        self.assertEqual(status, 200)
        mock_service.approve_pending.assert_called_once()
        self.assertEqual(body["action"], "approve")
        self.assertFalse(body["live_send_attempted"])

    def test_i5_approve_dry_run_expected_false_live_not_implemented(self) -> None:
        status, body = handle_approve_pending_assisted(
            "pending-i-1",
            _approve_body(dry_run_expected=False),
        )
        self.assertEqual(status, 422)
        self.assertEqual(body["status"], "dry_run_required")
        self.assertEqual(body["reason"], "live_send_not_implemented")

    def test_i6_approve_dry_run_would_send_response_shape(self) -> None:
        self._enable_dry_run_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        status, body = handle_approve_pending_assisted(
            pending_id,
            _approve_body(
                final_reply_override="您好，该商品目前有货，欢迎下单。",
            ),
            service=service,
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["success"])
        self.assertEqual(body["action"], "approve")
        self.assertEqual(body["status"], "dry_run_would_send")
        self.assertTrue(body["dry_run"])
        self.assertTrue(body["would_send"])
        self.assertFalse(body["live_send_attempted"])
        self.assertEqual(body["idempotency_key"], f"assisted_send:{pending_id}")
        self.assertEqual(body["pending_assisted_id"], pending_id)

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    @patch(
        "Message.handlers.ai_handler.AIReplyHandler._send_reply",
        new_callable=AsyncMock,
    )
    def test_i7_approve_route_does_not_sendmessage(
        self,
        send_reply_mock: AsyncMock,
        send_text_mock: MagicMock,
    ) -> None:
        self._enable_dry_run_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        handle_approve_pending_assisted(
            pending_id,
            _approve_body(),
            service=service,
        )
        send_reply_mock.assert_not_awaited()
        send_text_mock.assert_not_called()

    def test_i8_approve_route_does_not_import_handler_or_outbound(self) -> None:
        import_lines = [
            line
            for line in _ROUTE_SOURCE.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        block = "\n".join(import_lines)
        for token in (
            "SendMessage",
            "Message.handlers",
            "outbound_resolver",
            "Channel.pinduoduo",
            "Channel.doudian",
            "database.models",
            "database.db_manager",
            "evaluate_final_guard",
            "DryRunAssistedOutboundPort",
        ):
            self.assertNotIn(token, block, msg=token)

    def test_i9_reject_route_requires_csrf(self) -> None:
        status, body = handle_reject_pending_assisted(
            "pending-i-1",
            _reject_body(csrf_token=""),
        )
        self.assertEqual(status, 403)
        self.assertEqual(body["status"], "csrf_failed")

    def test_i10_reject_route_requires_confirm_checkbox(self) -> None:
        status, body = handle_reject_pending_assisted(
            "pending-i-1",
            _reject_body(confirm_checkbox=False),
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["reason"], "confirm_checkbox_required")

    def test_i11_viewer_cannot_reject(self) -> None:
        status, body = handle_reject_pending_assisted(
            "pending-i-1",
            _reject_body(actor_role="viewer"),
        )
        self.assertEqual(status, 403)
        self.assertEqual(body["reason"], "viewer_cannot_action")

    def test_i12_reject_route_calls_assisted_service_only(self) -> None:
        mock_service = MagicMock(spec=AssistedReplyService)
        mock_service._pending_repository.return_value.get_pending.return_value = MagicMock(
            workspace_id="ws-i-1",
            shop_id=_SHOP_ID,
            status="pending",
        )
        mock_service.reject_pending.return_value = AssistedServiceResult(
            success=True,
            action="reject_pending",
            status="rejected",
            pending_assisted_id="pending-i-1",
            reply_log_id="rl-i-1",
            audit_log_id="audit-i-1",
            reason="not suitable",
        )
        status, body = handle_reject_pending_assisted(
            "pending-i-1",
            _reject_body(),
            service=mock_service,
        )
        self.assertEqual(status, 200)
        mock_service.reject_pending.assert_called_once()
        self.assertEqual(body["action"], "reject")

    def test_i13_reject_response_shape(self) -> None:
        self._enable_assisted_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        status, body = handle_reject_pending_assisted(
            pending_id,
            _reject_body(),
            service=service,
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["success"])
        self.assertEqual(body["action"], "reject")
        self.assertEqual(body["status"], "rejected")
        self.assertEqual(body["pending_assisted_id"], pending_id)
        self.assertIsNotNone(body["audit_log_id"])

    def test_i14_reject_route_does_not_final_guard_or_outbound(self) -> None:
        source = _ROUTE_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("evaluate_final_guard", source)
        self.assertNotIn("DryRunAssistedOutboundPort", source)
        self.assertNotIn("AssistedOutboundPort", source)

    def test_i15_no_post_patch_delete_extra_routes(self) -> None:
        methods = {method for method, _path in REGISTERED_POST_ROUTES}
        self.assertEqual(methods, {"POST"})
        self.assertEqual(
            set(pending_assisted_action_route_names()),
            {"approve_pending_assisted", "reject_pending_assisted"},
        )
        self.assertTrue(_FORBIDDEN_EXTRA_ROUTES)
        for mutation in ("GET", "PATCH", "DELETE", "PUT"):
            status, body = dispatch_pending_assisted_action_route(
                mutation,
                f"/api/product/pending-assisted/pending-i-1/approve",
            )
            self.assertEqual(status, 405, msg=mutation)
            self.assertEqual(body["error"], "method_not_allowed")

    def test_i16_route_not_registered_in_app(self) -> None:
        app_source = _APP_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("pending_assisted_action_routes", app_source)
        self.assertNotIn("register_pending_assisted_action_routes", app_source)

    def test_i17_pdd_queue_name_unchanged(self) -> None:
        from Message.queue_naming import pdd_queue_name

        self.assertEqual(pdd_queue_name("shop123"), "pdd_shop123")

    def test_i18_doudian_not_enabled(self) -> None:
        source = _ROUTE_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("doudian", source.lower())
        self.assertNotIn("USE_DOUDIAN", source)

    @patch(
        "product_persistence.services.assisted_outbound_port.DryRunAssistedOutboundPort.send"
    )
    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    def test_route_does_not_call_port_directly(
        self,
        send_text_mock: MagicMock,
        port_send_mock: MagicMock,
    ) -> None:
        mock_service = MagicMock(spec=AssistedReplyService)
        mock_service._pending_repository.return_value.get_pending.return_value = MagicMock(
            workspace_id="ws-i-1",
            shop_id=_SHOP_ID,
            status="pending",
        )
        mock_service.approve_pending.return_value = AssistedServiceResult(
            success=True,
            action="approve_pending",
            status="dry_run_would_send",
            pending_assisted_id="pending-i-1",
            reply_log_id="rl-i-1",
            audit_log_id="audit-i-1",
            final_guard_allowed=True,
            reason="dry_run_would_send",
        )
        handle_approve_pending_assisted(
            "pending-i-1",
            _approve_body(),
            service=mock_service,
        )
        port_send_mock.assert_not_called()
        send_text_mock.assert_not_called()

    def test_register_action_routes_noop_without_flask_app(self) -> None:
        register_pending_assisted_action_routes(None)

        mock_app = _MockFlaskApp()
        register_pending_assisted_action_routes(mock_app)
        self.assertEqual(len(mock_app.routes), 2)
        rules = {route[0] for route in mock_app.routes}
        self.assertIn(
            "/api/product/pending-assisted/<pending_assisted_id>/approve",
            rules,
        )
        self.assertIn(
            "/api/product/pending-assisted/<pending_assisted_id>/reject",
            rules,
        )


if __name__ == "__main__":
    unittest.main()

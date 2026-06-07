"""Phase 15l: PendingAssisted action route flag-gated registration tests."""

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
    apply_dashboard_action_route_bootstrap,
    get_local_dashboard_flask_app,
    handle_approve_pending_assisted,
    handle_reject_pending_assisted,
    register_pending_assisted_action_routes,
    reset_action_route_registration_state_for_tests,
)
from product_persistence.services.assisted_reply_service import AssistedReplyService

_REPO_ROOT = Path(__file__).resolve().parents[1]
_APP_SOURCE = _REPO_ROOT / "app.py"
_BOOTSTRAP_SOURCE = _REPO_ROOT / "product_persistence" / "pending_assisted_action_routes.py"
_DEFAULT_DB = _REPO_ROOT / "temp" / "product_gate.db"
_NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
_FUTURE = (
    datetime.now(timezone.utc) + timedelta(days=7)
).replace(microsecond=0).isoformat()
_SHOP_ID = "shop-l-1"


class _MockFlaskApp:
    def __init__(self) -> None:
        self.routes: list[tuple] = []

    def add_url_rule(self, rule, endpoint=None, view_func=None, methods=None) -> None:
        self.routes.append((rule, endpoint, view_func, methods))


def _approve_body(**overrides) -> dict:
    base = dict(
        workspace_id="ws-l-1",
        shop_id=_SHOP_ID,
        actor_user_id="op-l-1",
        actor_role="operator",
        client_request_id="req-l-approve-1",
        expected_pending_status="pending",
        dry_run_expected=True,
        csrf_token="csrf-l-1",
        confirm_checkbox=True,
        final_reply_override="您好，该商品目前有货，欢迎下单。",
    )
    base.update(overrides)
    return base


def _reject_body(**overrides) -> dict:
    base = dict(
        workspace_id="ws-l-1",
        shop_id=_SHOP_ID,
        actor_user_id="op-l-1",
        actor_role="operator",
        client_request_id="req-l-reject-1",
        expected_pending_status="pending",
        reject_reason="not suitable",
        csrf_token="csrf-l-1",
        confirm_checkbox=True,
    )
    base.update(overrides)
    return base


class TestPendingAssistedActionRoutesRegistration(unittest.TestCase):
    def setUp(self) -> None:
        reset_product_db_manager()
        reset_action_route_registration_state_for_tests()
        if _DEFAULT_DB.exists():
            _DEFAULT_DB.unlink()
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED",
            "PRODUCT_PERSISTENCE_ENABLED",
            "PRODUCT_ASSISTED_SEND_ENABLED",
            "PRODUCT_ASSISTED_SEND_DRY_RUN",
            "PRODUCT_DB_URL",
        ):
            os.environ.pop(key, None)
        importlib.reload(flags)

    def tearDown(self) -> None:
        reset_product_db_manager()
        reset_action_route_registration_state_for_tests()
        self._env_patch.stop()

    def test_l1_flag_default_false(self) -> None:
        self.assertFalse(flags.is_dashboard_action_routes_enabled())

    def test_l2_true_values_enable_flag(self) -> None:
        for val in ("true", "1", "yes", "on", "TRUE", " Yes "):
            with self.subTest(val=val):
                os.environ["PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED"] = val
                importlib.reload(flags)
                self.assertTrue(flags.is_dashboard_action_routes_enabled())

    def test_l3_false_values_disable_flag(self) -> None:
        for val in ("false", "0", "no", "off", "", "maybe"):
            with self.subTest(val=val):
                os.environ["PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED"] = val
                importlib.reload(flags)
                self.assertFalse(flags.is_dashboard_action_routes_enabled())

    def test_l4_app_startup_default_does_not_register_action_routes(self) -> None:
        mock_app = _MockFlaskApp()
        registered = apply_dashboard_action_route_bootstrap(mock_app)
        self.assertFalse(registered)
        self.assertEqual(len(mock_app.routes), 0)
        app_source = _APP_SOURCE.read_text(encoding="utf-8")
        self.assertIn("apply_dashboard_action_route_bootstrap", app_source)
        self.assertNotIn("register_pending_assisted_action_routes(", app_source)

    def test_l5_flag_on_registers_action_routes(self) -> None:
        os.environ["PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED"] = "true"
        importlib.reload(flags)
        mock_app = _MockFlaskApp()
        self.assertTrue(apply_dashboard_action_route_bootstrap(mock_app))
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

    def test_l6_repeated_registration_safe_or_no_duplicate_crash(self) -> None:
        os.environ["PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED"] = "true"
        importlib.reload(flags)
        mock_app = _MockFlaskApp()
        register_pending_assisted_action_routes(mock_app)
        register_pending_assisted_action_routes(mock_app)
        self.assertEqual(len(mock_app.routes), 2)

    def test_l7_registration_does_not_create_db_when_flags_off(self) -> None:
        db_path = _REPO_ROOT / "temp" / "phase15l_no_db.db"
        if db_path.exists():
            db_path.unlink()
        os.environ["PRODUCT_DB_URL"] = f"sqlite:///{db_path.as_posix()}"
        importlib.reload(flags)
        mock_app = _MockFlaskApp()
        apply_dashboard_action_route_bootstrap(mock_app)
        self.assertFalse(db_path.exists())

    def test_l8_registration_does_not_enable_live_send(self) -> None:
        os.environ["PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED"] = "true"
        importlib.reload(flags)
        self.assertFalse(flags.is_assisted_send_enabled())
        self.assertTrue(flags.is_assisted_send_dry_run())

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    @patch(
        "Message.handlers.ai_handler.AIReplyHandler._send_reply",
        new_callable=AsyncMock,
    )
    def test_l9_registration_does_not_call_sendmessage(
        self,
        send_reply_mock: AsyncMock,
        send_text_mock: MagicMock,
    ) -> None:
        os.environ["PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED"] = "true"
        importlib.reload(flags)
        mock_app = _MockFlaskApp()
        apply_dashboard_action_route_bootstrap(mock_app)
        send_reply_mock.assert_not_awaited()
        send_text_mock.assert_not_called()

    def test_l10_registration_does_not_import_pdd_doudian(self) -> None:
        import_lines = [
            line
            for line in _BOOTSTRAP_SOURCE.read_text(encoding="utf-8").splitlines()
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
            "LivePddAssistedOutboundPort",
        ):
            self.assertNotIn(token, block, msg=token)

    def test_l11_registration_failure_does_not_break_legacy_startup(self) -> None:
        os.environ["PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED"] = "true"
        importlib.reload(flags)
        mock_app = _MockFlaskApp()
        with patch(
            "product_persistence.pending_assisted_action_routes.register_pending_assisted_action_routes",
            side_effect=RuntimeError("registration boom"),
        ):
            registered = apply_dashboard_action_route_bootstrap(mock_app)
        self.assertFalse(registered)

    def test_l12_read_dashboard_routes_unchanged(self) -> None:
        bootstrap_source = _BOOTSTRAP_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("register_dashboard_read_routes", bootstrap_source)
        self.assertNotIn("register_pending_assisted_read_routes", bootstrap_source)

    def test_l13_approve_route_still_dry_run_required(self) -> None:
        status, body = handle_approve_pending_assisted(
            "pending-l-1",
            _approve_body(dry_run_expected=False),
        )
        self.assertEqual(status, 422)
        self.assertEqual(body["status"], "dry_run_required")

    def test_l14_reject_route_still_no_send(self) -> None:
        mock_service = MagicMock(spec=AssistedReplyService)
        mock_service._pending_repository.return_value.get_pending.return_value = MagicMock(
            workspace_id="ws-l-1",
            shop_id=_SHOP_ID,
            status="pending",
        )
        mock_service.reject_pending.return_value = MagicMock(
            success=True,
            action="reject_pending",
            status="rejected",
            pending_assisted_id="pending-l-1",
            reply_log_id="rl-l-1",
            audit_log_id="audit-l-1",
            reason="not suitable",
            final_guard_allowed=None,
            final_guard_block_code=None,
        )
        status, body = handle_reject_pending_assisted(
            "pending-l-1",
            _reject_body(),
            service=mock_service,
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["action"], "reject")

    def test_l15_pdd_queue_name_unchanged(self) -> None:
        from Message.queue_naming import pdd_queue_name

        self.assertEqual(pdd_queue_name("shop123"), "pdd_shop123")

    def test_registered_post_routes_unchanged(self) -> None:
        methods = {method for method, _path in REGISTERED_POST_ROUTES}
        self.assertEqual(methods, {"POST"})

    def test_flag_on_without_flask_app_is_noop_when_flask_missing(self) -> None:
        os.environ["PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED"] = "true"
        importlib.reload(flags)
        with patch(
            "product_persistence.pending_assisted_action_routes.get_local_dashboard_flask_app",
            return_value=None,
        ):
            self.assertFalse(apply_dashboard_action_route_bootstrap(None))

    def test_get_local_dashboard_flask_app_create_if_missing(self) -> None:
        try:
            import flask  # noqa: F401
        except ImportError:
            self.skipTest("Flask not installed")
        app = get_local_dashboard_flask_app(create_if_missing=True)
        self.assertIsNotNone(app)
        same = get_local_dashboard_flask_app(create_if_missing=False)
        self.assertIs(app, same)


if __name__ == "__main__":
    unittest.main()

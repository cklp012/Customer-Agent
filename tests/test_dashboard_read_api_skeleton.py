"""Phase 14o: Dashboard read API skeleton tests."""

from __future__ import annotations

import importlib
import os
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from Message.gates.consultation_intent_classifier import classify_consultation_intent
from Message.gates.guarded_send import evaluate_guarded_send
from Message.gates.preview_log import append_preview_log
from Message.gates.send_decision import build_send_decision
from product_persistence import flags
from product_persistence.api_read_routes import (
    REGISTERED_GET_ROUTES,
    dashboard_read_route_names,
    dispatch_dashboard_read_route,
    handle_get_reply_log_detail,
    handle_list_reply_logs,
    register_dashboard_read_routes,
)
from product_persistence.services.dashboard_read_service import DashboardReadService
from product_persistence.services.preview_reply_log_service import PreviewReplyLogService

_REPO_ROOT = Path(__file__).resolve().parents[1]
_API_SOURCE = _REPO_ROOT / "product_persistence" / "api_read_routes.py"


def _seed_one_log() -> str:
    cls = classify_consultation_intent("这款商品还有库存吗")
    decision = build_send_decision(cls, reply_mode="preview", product_gate_enabled=True)
    guarded = evaluate_guarded_send(decision, "建议回复")
    record = append_preview_log(
        message_text="这款商品还有库存吗",
        reply_text="建议回复",
        classification=cls,
        send_decision=decision,
        guarded_result=guarded,
        metadata={
            "workspace_id": "ws-api-1",
            "shop_id": "shop-api-1",
            "account_id": "acc-api-1",
            "from_uid": "buyer-api-1",
            "platform_id": "pinduoduo",
        },
        workspace_id="ws-api-1",
        shop_id="shop-api-1",
        account_id="acc-api-1",
        buyer_id="buyer-api-1",
        platform_id="pinduoduo",
    )
    return record.reply_log_id


class _MockFlaskApp:
    def __init__(self) -> None:
        self.routes: list[tuple] = []

    def add_url_rule(self, rule, endpoint=None, view_func=None, methods=None) -> None:
        self.routes.append((rule, endpoint, view_func, methods))


class TestDashboardReadApiSkeleton(unittest.TestCase):
    def setUp(self) -> None:
        PreviewReplyLogService.clear_in_memory_logs_for_tests()
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_PERSISTENCE_ENABLED",
            "PRODUCT_PERSISTENCE_READ_DASHBOARD",
        ):
            os.environ.pop(key, None)
        importlib.reload(flags)

    def tearDown(self) -> None:
        PreviewReplyLogService.clear_in_memory_logs_for_tests()
        self._env_patch.stop()

    def test_get_list_route_returns_json(self) -> None:
        _seed_one_log()
        status, body = handle_list_reply_logs({"shop_id": "shop-api-1"})
        self.assertEqual(status, 200)
        self.assertIn("items", body)
        self.assertIn("source", body)
        self.assertEqual(body["source"], "in_memory")
        self.assertEqual(body["total"], 1)

    def test_get_detail_route_returns_json(self) -> None:
        reply_log_id = _seed_one_log()
        status, body = handle_get_reply_log_detail(reply_log_id)
        self.assertEqual(status, 200)
        self.assertIsNotNone(body["reply_log"])
        self.assertEqual(body["reply_log"]["reply_log_id"], reply_log_id)
        self.assertEqual(body["send_decision_snapshots"], [])

    def test_dispatch_routes_are_read_only(self) -> None:
        for method, _path in REGISTERED_GET_ROUTES:
            self.assertIn(method, {"GET"})
        status, body = dispatch_dashboard_read_route(
            "POST",
            "/api/product/reply-logs",
        )
        self.assertEqual(status, 405)
        self.assertEqual(body["error"], "method_not_allowed")

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    @patch(
        "Message.handlers.ai_handler.AIReplyHandler._send_reply",
        new_callable=AsyncMock,
    )
    def test_routes_do_not_call_sendmessage_or_send_reply(
        self,
        send_reply_mock: AsyncMock,
        send_text_mock: MagicMock,
    ) -> None:
        reply_log_id = _seed_one_log()
        handle_list_reply_logs({})
        handle_get_reply_log_detail(reply_log_id)
        dispatch_dashboard_read_route("GET", "/api/product/reply-logs")
        dispatch_dashboard_read_route(
            "GET",
            f"/api/product/reply-logs/{reply_log_id}",
        )
        send_reply_mock.assert_not_awaited()
        send_text_mock.assert_not_called()

    def test_routes_do_not_modify_reply_mode_or_product_gate_flags(self) -> None:
        cls = classify_consultation_intent("这款商品还有库存吗")
        decision = build_send_decision(
            cls,
            reply_mode="preview",
            product_gate_enabled=True,
        )
        before_mode = decision.reply_mode
        before_gate = decision.product_gate_enabled
        _seed_one_log()
        handle_list_reply_logs({})
        self.assertEqual(decision.reply_mode, before_mode)
        self.assertEqual(decision.product_gate_enabled, before_gate)

    def test_no_post_put_delete_routes_registered(self) -> None:
        methods = {method for method, _path in REGISTERED_GET_ROUTES}
        self.assertEqual(methods, {"GET"})
        self.assertEqual(set(dashboard_read_route_names()), {"list_reply_logs", "get_reply_log_detail"})

    def test_register_dashboard_read_routes_importable_and_noop_safe(self) -> None:
        register_dashboard_read_routes(None)
        register_dashboard_read_routes(object())

        mock_app = _MockFlaskApp()
        register_dashboard_read_routes(mock_app)
        self.assertEqual(len(mock_app.routes), 2)
        rules = {route[0] for route in mock_app.routes}
        self.assertIn("/api/product/reply-logs", rules)
        self.assertIn("/api/product/reply-logs/<reply_log_id>", rules)
        for _rule, _endpoint, _view, methods in mock_app.routes:
            self.assertEqual(methods, ["GET"])

    def test_register_does_not_create_db_or_raise(self) -> None:
        default_db = _REPO_ROOT / "temp" / "product_gate.db"
        if default_db.exists():
            default_db.unlink()
        register_dashboard_read_routes(None)
        self.assertFalse(default_db.exists())

    def test_app_startup_not_broken(self) -> None:
        import app as app_module

        self.assertTrue(callable(app_module.main))

    def test_api_source_read_only_no_mutations(self) -> None:
        source = _API_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("SendMessage", source)
        self.assertNotIn("_send_reply", source)
        self.assertNotIn("record_preview", source)
        self.assertNotIn("create_snapshot", source)
        self.assertNotIn("@app.route('/api/product/reply-logs'", source)


if __name__ == "__main__":
    unittest.main()

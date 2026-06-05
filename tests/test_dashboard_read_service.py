"""Phase 14o: DashboardReadService read-only tests."""

from __future__ import annotations

import importlib
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from Message.gates.consultation_intent_classifier import classify_consultation_intent
from Message.gates.guarded_send import evaluate_guarded_send
from Message.gates.preview_log import append_preview_log, preview_log
from Message.gates.send_decision import build_send_decision
from product_persistence import flags
from product_persistence.services.dashboard_read_service import DashboardReadService
from product_persistence.services.preview_reply_log_service import PreviewReplyLogService

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SERVICE_SOURCE = (
    _REPO_ROOT / "product_persistence" / "services" / "dashboard_read_service.py"
)


def _seed_preview_log(
    *,
    shop_id: str = "shop-dash-1",
    send_status: str | None = None,
    risk_level_override: str | None = None,
    metadata_extra: dict | None = None,
) -> str:
    cls = classify_consultation_intent("这款商品还有库存吗")
    decision = build_send_decision(cls, reply_mode="preview", product_gate_enabled=True)
    guarded = evaluate_guarded_send(decision, "建议回复")
    meta = {
        "workspace_id": "ws-dash-1",
        "shop_id": shop_id,
        "account_id": "acc-dash-1",
        "from_uid": "buyer-dash-1",
        "platform_id": "pinduoduo",
        "password": "secret-should-not-leak",
        "api_key": "key-should-not-leak",
    }
    if metadata_extra:
        meta.update(metadata_extra)
    record = append_preview_log(
        message_text="这款商品还有库存吗",
        reply_text="建议回复",
        classification=cls,
        send_decision=decision,
        guarded_result=guarded,
        metadata=meta,
        workspace_id="ws-dash-1",
        shop_id=shop_id,
        account_id="acc-dash-1",
        buyer_id="buyer-dash-1",
        platform_id="pinduoduo",
    )
    if send_status is not None:
        object.__setattr__(record, "send_status", send_status)
    if risk_level_override is not None:
        object.__setattr__(record.classification, "risk_level", risk_level_override)
    return record.reply_log_id


class TestDashboardReadService(unittest.TestCase):
    def setUp(self) -> None:
        PreviewReplyLogService.clear_in_memory_logs_for_tests()
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_PERSISTENCE_ENABLED",
            "PRODUCT_PERSISTENCE_READ_DASHBOARD",
            "PRODUCT_DB_URL",
        ):
            os.environ.pop(key, None)
        importlib.reload(flags)

    def tearDown(self) -> None:
        PreviewReplyLogService.clear_in_memory_logs_for_tests()
        self._env_patch.stop()

    def test_list_from_in_memory_returns_items(self) -> None:
        _seed_preview_log()
        result = DashboardReadService().list_reply_logs()
        self.assertEqual(result.source, "in_memory")
        self.assertEqual(result.total, 1)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0]["shop_id"], "shop-dash-1")

    def test_filters_by_shop_id_send_status_risk_level(self) -> None:
        _seed_preview_log(shop_id="shop-a")
        _seed_preview_log(shop_id="shop-b")
        svc = DashboardReadService()
        by_shop = svc.list_reply_logs(shop_id="shop-a")
        self.assertEqual(by_shop.total, 1)
        self.assertEqual(by_shop.items[0]["shop_id"], "shop-a")

        status_item = svc.list_reply_logs(send_status="not_sent_preview")
        self.assertGreaterEqual(status_item.total, 1)

        risk_item = svc.list_reply_logs(risk_level="low")
        self.assertGreaterEqual(risk_item.total, 1)

    def test_page_size_capped_at_100(self) -> None:
        for idx in range(105):
            _seed_preview_log(shop_id=f"shop-page-{idx}")
        result = DashboardReadService().list_reply_logs(page=1, page_size=500)
        self.assertEqual(result.page_size, 100)
        self.assertEqual(len(result.items), 100)
        self.assertEqual(result.total, 105)

    def test_detail_by_reply_log_id(self) -> None:
        reply_log_id = _seed_preview_log()
        detail = DashboardReadService().get_reply_log_detail(reply_log_id)
        self.assertFalse(detail.not_found)
        self.assertIsNotNone(detail.reply_log)
        assert detail.reply_log is not None
        self.assertEqual(detail.reply_log["reply_log_id"], reply_log_id)
        self.assertEqual(detail.send_decision_snapshots, ())
        self.assertEqual(detail.audit_logs, ())
        self.assertIsNone(detail.pending_assisted_reply)
        self.assertEqual(detail.source, "in_memory")

    def test_missing_detail_not_found(self) -> None:
        detail = DashboardReadService().get_reply_log_detail("missing-id")
        self.assertTrue(detail.not_found)
        self.assertIsNone(detail.reply_log)

    def test_detail_includes_empty_snapshots(self) -> None:
        reply_log_id = _seed_preview_log()
        detail = DashboardReadService().get_reply_log_detail(reply_log_id)
        self.assertEqual(detail.send_decision_snapshots, ())

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    @patch("Message.handlers.ai_handler.AIReplyHandler._send_reply")
    def test_no_sendmessage_or_outbound_calls(
        self,
        send_reply_mock: MagicMock,
        send_text_mock: MagicMock,
    ) -> None:
        reply_log_id = _seed_preview_log()
        svc = DashboardReadService()
        svc.list_reply_logs()
        svc.get_reply_log_detail(reply_log_id)
        send_reply_mock.assert_not_called()
        send_text_mock.assert_not_called()

    def test_no_credential_leakage_fields(self) -> None:
        reply_log_id = _seed_preview_log(
            metadata_extra={"authorization": "Bearer secret-token"}
        )
        listed = DashboardReadService().list_reply_logs()
        detail = DashboardReadService().get_reply_log_detail(reply_log_id)
        for item in listed.items:
            self.assertNotIn("password", item)
            self.assertNotIn("api_key", item)
            self.assertNotIn("authorization", item)
        assert detail.reply_log is not None
        self.assertNotIn("password", detail.reply_log)
        self.assertNotIn("api_key", detail.reply_log)
        self.assertNotIn("authorization", detail.reply_log)

    def test_sqlite_read_flag_false_source_in_memory(self) -> None:
        os.environ.pop("PRODUCT_PERSISTENCE_READ_DASHBOARD", None)
        importlib.reload(flags)
        _seed_preview_log()
        result = DashboardReadService().list_reply_logs()
        self.assertEqual(result.source, "in_memory")
        self.assertFalse(flags.should_read_dashboard_from_product_db())

    @patch(
        "product_persistence.repositories.sqlite_reply_log_repository.ReplyLogRepositorySQLite.list_reply_logs",
        side_effect=RuntimeError("sqlite read down"),
    )
    def test_sqlite_read_failure_fallback_in_memory_with_warning(
        self,
        _list_mock: MagicMock,
    ) -> None:
        os.environ["PRODUCT_PERSISTENCE_ENABLED"] = "true"
        os.environ["PRODUCT_PERSISTENCE_READ_DASHBOARD"] = "true"
        importlib.reload(flags)
        _seed_preview_log()
        result = DashboardReadService().list_reply_logs()
        self.assertEqual(result.source, "in_memory")
        self.assertEqual(result.total, 1)
        self.assertTrue(result.warnings)
        self.assertIn("sqlite_read_failed_fallback_in_memory", result.warnings[0])

    def test_service_source_no_send_or_legacy_db(self) -> None:
        source = _SERVICE_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("SendMessage.send", source)
        self.assertNotIn("from Channel", source)
        self.assertNotIn("outbound_resolver", source)
        self.assertNotIn("send_text", source)
        self.assertNotIn("_send_reply", source)
        self.assertNotIn("database.models", source)
        self.assertNotIn("database.db_manager", source)


if __name__ == "__main__":
    unittest.main()

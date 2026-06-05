"""Phase 14g: PreviewReplyLogService in-memory adapter tests."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from Message.gates.consultation_intent_classifier import classify_consultation_intent
from Message.gates.guarded_send import evaluate_guarded_send
from Message.gates.preview_log import append_preview_log, preview_log
from Message.gates.send_decision import build_send_decision
from product_persistence.services.preview_reply_log_service import (
    PreviewReplyLogService,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PRODUCT_GATE_DB = _REPO_ROOT / "temp" / "product_gate.db"
_SERVICE_SOURCE = (
    _REPO_ROOT / "product_persistence" / "services" / "preview_reply_log_service.py"
)


def _seed_preview_log() -> None:
    cls = classify_consultation_intent("这款商品还有库存吗")
    decision = build_send_decision(cls, reply_mode="preview", product_gate_enabled=True)
    guarded = evaluate_guarded_send(decision, "建议回复")
    append_preview_log(
        message_text="这款商品还有库存吗",
        reply_text="建议回复",
        classification=cls,
        send_decision=decision,
        guarded_result=guarded,
        metadata={
            "workspace_id": "ws-svc-1",
            "shop_id": "shop-svc-1",
            "account_id": "acc-svc-1",
            "from_uid": "buyer-svc-1",
            "platform_id": "pinduoduo",
        },
    )


class TestPreviewReplyLogServiceInMemory(unittest.TestCase):
    def setUp(self) -> None:
        PreviewReplyLogService.clear_in_memory_logs_for_tests()
        if _PRODUCT_GATE_DB.exists():
            _PRODUCT_GATE_DB.unlink()

    def tearDown(self) -> None:
        PreviewReplyLogService.clear_in_memory_logs_for_tests()

    def test_service_importable(self) -> None:
        svc = PreviewReplyLogService()
        self.assertIsNone(svc.repository)

    def test_list_reply_logs_from_in_memory(self) -> None:
        _seed_preview_log()
        svc = PreviewReplyLogService()
        result = svc.list_reply_logs()
        self.assertTrue(result.success)
        self.assertEqual(result.source, "in_memory")
        self.assertEqual(len(result.records), 1)
        item = result.records[0]
        self.assertEqual(item.buyer_message, "这款商品还有库存吗")
        self.assertEqual(item.ai_suggested_reply, "建议回复")
        self.assertEqual(item.send_status, "not_sent_preview")
        self.assertEqual(item.shop_id, "shop-svc-1")
        self.assertEqual(item.intent_bucket, "allowed")

    def test_get_reply_log_by_id(self) -> None:
        _seed_preview_log()
        svc = PreviewReplyLogService()
        listed = svc.list_reply_logs()
        reply_log_id = listed.records[0].reply_log_id
        item = svc.get_reply_log(reply_log_id)
        self.assertIsNotNone(item)
        self.assertEqual(item.reply_log_id, reply_log_id)

    def test_get_reply_log_missing_returns_none(self) -> None:
        svc = PreviewReplyLogService()
        self.assertIsNone(svc.get_reply_log("missing-id"))

    def test_clear_in_memory_logs(self) -> None:
        _seed_preview_log()
        PreviewReplyLogService.clear_in_memory_logs_for_tests()
        result = PreviewReplyLogService().list_reply_logs()
        self.assertEqual(len(result.records), 0)

    def test_list_works_when_persistence_flag_off(self) -> None:
        _seed_preview_log()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PRODUCT_PERSISTENCE_ENABLED", None)
            result = PreviewReplyLogService().list_reply_logs()
        self.assertTrue(result.success)
        self.assertEqual(len(result.records), 1)

    def test_empty_log_returns_empty_list(self) -> None:
        result = PreviewReplyLogService().list_reply_logs()
        self.assertTrue(result.success)
        self.assertEqual(result.records, ())

    def test_list_filter_by_shop_id(self) -> None:
        _seed_preview_log()
        result = PreviewReplyLogService().list_reply_logs(shop_id="other-shop")
        self.assertEqual(len(result.records), 0)

    def test_record_preview_does_not_write_db_or_send(self) -> None:
        svc = PreviewReplyLogService()
        record = svc.record_preview(message_text="hi", reply_text="reply")
        self.assertFalse(record.recorded)
        self.assertEqual(record.reason, "product_persistence_disabled")
        self.assertFalse(_PRODUCT_GATE_DB.exists())
        self.assertEqual(len(preview_log.all()), 0)

    def test_service_does_not_create_product_gate_db(self) -> None:
        import product_persistence.services.preview_reply_log_service as mod

        importlib_reload = __import__("importlib").reload
        importlib_reload(mod)
        PreviewReplyLogService().list_reply_logs()
        self.assertFalse(_PRODUCT_GATE_DB.exists())

    def test_service_source_no_send_or_legacy_db(self) -> None:
        source = _SERVICE_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("SendMessage", source)
        self.assertNotIn("outbound_resolver", source)
        self.assertNotIn("send_text", source)
        self.assertNotIn("database.models", source)
        self.assertNotIn("database.db_manager", source)
        self.assertNotIn("create_all", source)
        self.assertNotIn("sqlalchemy", source.lower())


if __name__ == "__main__":
    unittest.main()

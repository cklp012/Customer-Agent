"""Phase 13b: shadow SendDecision logger unit tests."""

from __future__ import annotations

import unittest

from Message.gates.intent_types import IntentBucket, SendMode
from Message.gates.shadow_decision_logger import (
    InMemoryShadowDecisionLogger,
    build_shadow_decision_record,
    shadow_decision_logger,
)


class TestBuildShadowDecisionRecord(unittest.TestCase):
    def setUp(self) -> None:
        shadow_decision_logger.clear()

    def test_product_consultation_allowed(self) -> None:
        record = build_shadow_decision_record("这款商品还有库存吗", {"message_id": "m1"})
        self.assertEqual(record.classification.intent_bucket, IntentBucket.ALLOWED)
        self.assertFalse(record.send_decision.product_gate_enabled)
        self.assertTrue(record.send_decision.allowed_to_send)
        self.assertEqual(record.send_decision.send_mode, SendMode.LEGACY_PASSTHROUGH)

    def test_refund_blocked(self) -> None:
        record = build_shadow_decision_record("我要退款")
        self.assertEqual(record.classification.intent_bucket, IntentBucket.BLOCKED)
        self.assertEqual(record.classification.intent, "refund_request")
        self.assertFalse(record.send_decision.product_gate_enabled)

    def test_complaint_blocked(self) -> None:
        record = build_shadow_decision_record("投诉你们")
        self.assertEqual(record.classification.intent_bucket, IntentBucket.BLOCKED)

    def test_empty_text_no_exception(self) -> None:
        record = build_shadow_decision_record("")
        self.assertEqual(record.classification.intent_bucket, IntentBucket.UNCERTAIN)

    def test_none_text_no_exception(self) -> None:
        record = build_shadow_decision_record(None)
        self.assertEqual(record.message_text, "")


class TestInMemoryLogger(unittest.TestCase):
    def test_append_all_clear(self) -> None:
        logger = InMemoryShadowDecisionLogger()
        r1 = build_shadow_decision_record("库存")
        r2 = build_shadow_decision_record("退款")
        logger.append(r1)
        logger.append(r2)
        self.assertEqual(len(logger.all()), 2)
        logger.clear()
        self.assertEqual(len(logger.all()), 0)

    def test_module_does_not_import_send_paths(self) -> None:
        from pathlib import Path

        source_path = (
            Path(__file__).resolve().parents[1]
            / "Message"
            / "gates"
            / "shadow_decision_logger.py"
        )
        with open(source_path, encoding="utf-8") as f:
            source = f.read()
        self.assertNotIn("from Channel.pinduoduo.utils.API.send_message", source)
        self.assertNotIn("import SendMessage", source)
        self.assertNotIn("outbound_resolver", source)


if __name__ == "__main__":
    unittest.main()

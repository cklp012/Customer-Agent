"""Phase 13a: guarded send evaluator unit tests — no SendMessage."""

from __future__ import annotations

import sys
import unittest

from Message.gates.consultation_intent_classifier import classify_consultation_intent
from Message.gates.guarded_send import evaluate_guarded_send
from Message.gates.intent_types import ReplyMode, SendMode
from Message.gates.send_decision import build_send_decision


class TestPreviewZeroSend(unittest.TestCase):
    def test_preview_zero_send(self) -> None:
        clf = classify_consultation_intent("这款商品怎么样")
        decision = build_send_decision(
            clf,
            reply_mode=ReplyMode.PREVIEW,
            product_gate_enabled=True,
        )
        result = evaluate_guarded_send(decision, "亲，这款很好哦")
        self.assertFalse(result.should_send)
        self.assertEqual(result.send_status, "not_sent_preview")
        self.assertEqual(result.send_mode, SendMode.PREVIEW_ONLY)


class TestAssistedAndTakeover(unittest.TestCase):
    def test_assisted_zero_send_without_approval(self) -> None:
        clf = classify_consultation_intent("库存还有吗")
        decision = build_send_decision(
            clf,
            reply_mode=ReplyMode.ASSISTED,
            product_gate_enabled=True,
        )
        result = evaluate_guarded_send(decision, "有货的哦")
        self.assertFalse(result.should_send)
        self.assertEqual(result.send_status, "not_sent_assisted_required")

    def test_human_takeover_zero_send(self) -> None:
        clf = classify_consultation_intent("我要退款")
        decision = build_send_decision(
            clf,
            reply_mode=ReplyMode.AUTO,
            product_gate_enabled=True,
        )
        result = evaluate_guarded_send(decision, "好的给您退")
        self.assertFalse(result.should_send)
        self.assertEqual(result.send_status, "not_sent_human_takeover")

    def test_blocked_zero_send(self) -> None:
        clf = classify_consultation_intent("投诉")
        decision = build_send_decision(clf, reply_mode=ReplyMode.AUTO, product_gate_enabled=True)
        result = evaluate_guarded_send(decision, "回复")
        self.assertFalse(result.should_send)


class TestAutoSendAllowed(unittest.TestCase):
    def test_auto_send_should_send_true(self) -> None:
        clf = classify_consultation_intent("商品还有库存吗")
        decision = build_send_decision(
            clf,
            reply_mode=ReplyMode.AUTO,
            product_gate_enabled=True,
        )
        result = evaluate_guarded_send(decision, "有货的亲")
        self.assertTrue(result.should_send)
        self.assertEqual(result.send_status, "auto_send_allowed")
        self.assertEqual(result.send_mode, SendMode.AUTO_SEND)


class TestGateDisabled(unittest.TestCase):
    def test_product_gate_disabled_legacy_passthrough(self) -> None:
        clf = classify_consultation_intent("我要退款")
        decision = build_send_decision(
            clf,
            reply_mode=ReplyMode.PREVIEW,
            product_gate_enabled=False,
        )
        result = evaluate_guarded_send(decision, "any")
        self.assertTrue(result.should_send)
        self.assertEqual(result.send_status, "legacy_passthrough")
        self.assertEqual(result.reason, "gate_disabled")


class TestPaused(unittest.TestCase):
    def test_paused_zero_send(self) -> None:
        clf = classify_consultation_intent("推荐一款")
        decision = build_send_decision(
            clf,
            reply_mode=ReplyMode.AUTO,
            product_gate_enabled=True,
            workspace_pause=True,
        )
        result = evaluate_guarded_send(decision, "推荐这款")
        self.assertFalse(result.should_send)
        self.assertEqual(result.send_status, "not_sent_paused")


class TestNoSendMessageImport(unittest.TestCase):
    def test_guarded_send_module_does_not_import_send_message(self) -> None:
        """Regression: guarded_send must not pull in SendMessage."""
        import Message.gates.guarded_send as mod

        source_path = mod.__file__
        self.assertIsNotNone(source_path)
        with open(source_path, encoding="utf-8") as f:
            source = f.read()
        self.assertNotIn("from Channel.pinduoduo.utils.API.send_message", source)
        self.assertNotIn("import SendMessage", source)

    def test_evaluate_never_imports_send_message_at_runtime(self) -> None:
        send_mod = "Channel.pinduoduo.utils.API.send_message"
        # Module may be loaded elsewhere in full suite; ensure evaluate path doesn't load it fresh
        clf = classify_consultation_intent("库存")
        decision = build_send_decision(clf, product_gate_enabled=True)
        before = send_mod in sys.modules
        evaluate_guarded_send(decision, "test")
        if not before:
            self.assertNotIn(send_mod, sys.modules)


if __name__ == "__main__":
    unittest.main()

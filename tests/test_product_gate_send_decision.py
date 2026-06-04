"""Phase 13a: SendDecision builder unit tests."""

from __future__ import annotations

import unittest

from Message.gates.consultation_intent_classifier import IntentClassification, classify_consultation_intent
from Message.gates.intent_types import IntentBucket, ReplyMode, RiskLevel, SendMode
from Message.gates.send_decision import build_send_decision


def _allowed_classification() -> IntentClassification:
    return IntentClassification(
        intent="product_question",
        intent_bucket=IntentBucket.ALLOWED,
        confidence=0.92,
        risk_level=RiskLevel.LOW,
        matched_keywords=["商品"],
        source="rule",
    )


def _blocked_refund() -> IntentClassification:
    return classify_consultation_intent("我要退款")


class TestGateDisabled(unittest.TestCase):
    def test_gate_disabled_legacy_passthrough(self) -> None:
        d = build_send_decision(
            _allowed_classification(),
            reply_mode=ReplyMode.PREVIEW,
            product_gate_enabled=False,
        )
        self.assertFalse(d.product_gate_enabled)
        self.assertTrue(d.allowed_to_send)
        self.assertEqual(d.send_mode, SendMode.LEGACY_PASSTHROUGH)
        self.assertEqual(d.blocked_reason, "gate_disabled")

    def test_gate_disabled_does_not_force_preview_block(self) -> None:
        """Preview reply_mode with gate off must not set preview_only send_mode."""
        d = build_send_decision(
            _allowed_classification(),
            reply_mode="preview",
            product_gate_enabled=False,
        )
        self.assertNotEqual(d.send_mode, SendMode.PREVIEW_ONLY)
        self.assertTrue(d.allowed_to_send)


class TestPreviewAndAssisted(unittest.TestCase):
    def test_preview_no_send(self) -> None:
        d = build_send_decision(
            _allowed_classification(),
            reply_mode=ReplyMode.PREVIEW,
            product_gate_enabled=True,
        )
        self.assertTrue(d.allowed_to_generate)
        self.assertFalse(d.allowed_to_send)
        self.assertEqual(d.send_mode, SendMode.PREVIEW_ONLY)

    def test_assisted_no_send(self) -> None:
        d = build_send_decision(
            _allowed_classification(),
            reply_mode=ReplyMode.ASSISTED,
            product_gate_enabled=True,
        )
        self.assertFalse(d.allowed_to_send)
        self.assertEqual(d.send_mode, SendMode.ASSISTED_REQUIRED)


class TestAutoAllowed(unittest.TestCase):
    def test_allowed_auto_high_confidence(self) -> None:
        d = build_send_decision(
            _allowed_classification(),
            reply_mode=ReplyMode.AUTO,
            product_gate_enabled=True,
        )
        self.assertTrue(d.allowed_to_send)
        self.assertEqual(d.send_mode, SendMode.AUTO_SEND)

    def test_refund_auto_blocked_human_takeover(self) -> None:
        d = build_send_decision(
            _blocked_refund(),
            reply_mode=ReplyMode.AUTO,
            product_gate_enabled=True,
        )
        self.assertFalse(d.allowed_to_send)
        self.assertEqual(d.send_mode, SendMode.HUMAN_TAKEOVER)
        self.assertEqual(d.intent_bucket, IntentBucket.BLOCKED)

    def test_complaint_assisted_no_send(self) -> None:
        clf = classify_consultation_intent("投诉")
        d = build_send_decision(
            clf,
            reply_mode=ReplyMode.ASSISTED,
            product_gate_enabled=True,
        )
        self.assertFalse(d.allowed_to_send)
        self.assertEqual(d.send_mode, SendMode.HUMAN_TAKEOVER)

    def test_low_confidence_auto_no_send(self) -> None:
        low = IntentClassification(
            intent="product_question",
            intent_bucket=IntentBucket.ALLOWED,
            confidence=0.4,
            risk_level=RiskLevel.MEDIUM,
            source="rule",
        )
        d = build_send_decision(
            low,
            reply_mode=ReplyMode.AUTO,
            product_gate_enabled=True,
        )
        self.assertFalse(d.allowed_to_send)
        self.assertEqual(d.blocked_reason, "low_confidence")


class TestPausePriority(unittest.TestCase):
    def test_workspace_pause_overrides_auto(self) -> None:
        d = build_send_decision(
            _allowed_classification(),
            reply_mode=ReplyMode.AUTO,
            product_gate_enabled=True,
            workspace_pause=True,
        )
        self.assertFalse(d.allowed_to_send)
        self.assertEqual(d.send_mode, SendMode.NONE)
        self.assertEqual(d.reply_mode, ReplyMode.PAUSED)
        self.assertEqual(d.blocked_reason, "workspace_paused")

    def test_shop_pause_overrides_auto(self) -> None:
        d = build_send_decision(
            _allowed_classification(),
            reply_mode=ReplyMode.AUTO,
            product_gate_enabled=True,
            shop_pause=True,
        )
        self.assertFalse(d.allowed_to_send)
        self.assertEqual(d.blocked_reason, "shop_paused")

    def test_blocked_beats_auto_even_without_pause(self) -> None:
        d = build_send_decision(
            _blocked_refund(),
            reply_mode=ReplyMode.AUTO,
            product_gate_enabled=True,
        )
        self.assertFalse(d.allowed_to_send)
        self.assertEqual(d.send_mode, SendMode.HUMAN_TAKEOVER)


class TestUncertainAuto(unittest.TestCase):
    def test_uncertain_auto_forbidden(self) -> None:
        clf = classify_consultation_intent("嗯")
        d = build_send_decision(
            clf,
            reply_mode=ReplyMode.AUTO,
            product_gate_enabled=True,
        )
        self.assertEqual(clf.intent_bucket, IntentBucket.UNCERTAIN)
        self.assertFalse(d.allowed_to_send)


if __name__ == "__main__":
    unittest.main()

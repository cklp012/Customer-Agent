"""Phase 13a: consultation intent classifier unit tests."""

from __future__ import annotations

import unittest

from Message.gates.consultation_intent_classifier import (
    classify_consultation_intent,
    keyword_risk_scan,
)
from Message.gates.intent_types import IntentBucket, RiskLevel


class TestAllowedConsultation(unittest.TestCase):
    def test_product_question(self) -> None:
        c = classify_consultation_intent("这款商品怎么样")
        self.assertEqual(c.intent_bucket, IntentBucket.ALLOWED)
        self.assertIn(c.intent, ("product_question", "recommendation_question"))

    def test_size_spec(self) -> None:
        c = classify_consultation_intent("170穿多大尺码")
        self.assertEqual(c.intent_bucket, IntentBucket.ALLOWED)
        self.assertEqual(c.intent, "size_or_spec_question")

    def test_inventory(self) -> None:
        c = classify_consultation_intent("还有库存吗")
        self.assertEqual(c.intent_bucket, IntentBucket.ALLOWED)
        self.assertEqual(c.intent, "inventory_question")

    def test_promotion(self) -> None:
        c = classify_consultation_intent("有优惠券活动吗")
        self.assertEqual(c.intent_bucket, IntentBucket.ALLOWED)

    def test_recommendation(self) -> None:
        c = classify_consultation_intent("推荐一款洗面奶")
        self.assertEqual(c.intent_bucket, IntentBucket.ALLOWED)
        self.assertEqual(c.intent, "recommendation_question")

    def test_shipping(self) -> None:
        c = classify_consultation_intent("一般几天发货")
        self.assertEqual(c.intent_bucket, IntentBucket.ALLOWED)
        self.assertEqual(c.intent, "basic_shipping_question")


class TestBlockedIntents(unittest.TestCase):
    def test_refund(self) -> None:
        c = classify_consultation_intent("我要退款")
        self.assertEqual(c.intent_bucket, IntentBucket.BLOCKED)
        self.assertEqual(c.intent, "refund_request")
        self.assertEqual(c.source, "keyword_rule")

    def test_compensation(self) -> None:
        c = classify_consultation_intent("请赔偿我")
        self.assertEqual(c.intent_bucket, IntentBucket.BLOCKED)
        self.assertEqual(c.intent, "compensation_request")

    def test_complaint(self) -> None:
        c = classify_consultation_intent("我要投诉你们")
        self.assertEqual(c.intent_bucket, IntentBucket.BLOCKED)
        self.assertEqual(c.intent, "complaint")

    def test_bad_review(self) -> None:
        c = classify_consultation_intent("给差评")
        self.assertEqual(c.intent_bucket, IntentBucket.BLOCKED)
        self.assertEqual(c.intent, "bad_review_threat")

    def test_order_change(self) -> None:
        c = classify_consultation_intent("帮我取消订单")
        self.assertEqual(c.intent_bucket, IntentBucket.BLOCKED)
        self.assertEqual(c.intent, "order_change")

    def test_address_change(self) -> None:
        c = classify_consultation_intent("改地址可以吗")
        self.assertEqual(c.intent_bucket, IntentBucket.BLOCKED)
        self.assertEqual(c.intent, "address_change")

    def test_price_negotiation(self) -> None:
        c = classify_consultation_intent("能便宜点吗")
        self.assertEqual(c.intent_bucket, IntentBucket.BLOCKED)
        self.assertEqual(c.intent, "price_negotiation")

    def test_quality_dispute(self) -> None:
        c = classify_consultation_intent("质量问题坏了")
        self.assertEqual(c.intent_bucket, IntentBucket.BLOCKED)
        self.assertEqual(c.intent, "quality_dispute")


class TestUncertainAndEdge(unittest.TestCase):
    def test_empty_text(self) -> None:
        c = classify_consultation_intent("")
        self.assertEqual(c.intent_bucket, IntentBucket.UNCERTAIN)
        self.assertEqual(c.intent, "unclear_context")

    def test_none_text(self) -> None:
        c = classify_consultation_intent(None)
        self.assertEqual(c.intent_bucket, IntentBucket.UNCERTAIN)

    def test_whitespace_only(self) -> None:
        c = classify_consultation_intent("   ")
        self.assertEqual(c.intent_bucket, IntentBucket.UNCERTAIN)

    def test_unclassifiable(self) -> None:
        c = classify_consultation_intent("嗯嗯")
        self.assertEqual(c.intent_bucket, IntentBucket.UNCERTAIN)


class TestKeywordPriority(unittest.TestCase):
    def test_mixed_product_and_refund_must_be_blocked(self) -> None:
        c = classify_consultation_intent("这款商品不错，但我要求退款")
        self.assertEqual(c.intent_bucket, IntentBucket.BLOCKED)
        self.assertEqual(c.intent, "refund_request")
        self.assertTrue(any("退款" in k for k in c.matched_keywords))

    def test_keyword_risk_scan_blocks_before_allowed(self) -> None:
        blocked, intent, matched = keyword_risk_scan("咨询尺码，另外要退货")
        self.assertTrue(blocked)
        self.assertEqual(intent, "refund_request")
        self.assertTrue(matched)

    def test_blocked_not_overridden_by_product_keyword(self) -> None:
        c = classify_consultation_intent("商品有问题，要投诉")
        self.assertEqual(c.intent_bucket, IntentBucket.BLOCKED)
        self.assertNotEqual(c.intent, "product_question")


class TestRiskLevels(unittest.TestCase):
    def test_blocked_high_risk(self) -> None:
        c = classify_consultation_intent("退款")
        self.assertEqual(c.risk_level, RiskLevel.HIGH)

    def test_allowed_low_or_medium(self) -> None:
        c = classify_consultation_intent("库存还有吗")
        self.assertIn(c.risk_level, (RiskLevel.LOW, RiskLevel.MEDIUM))


if __name__ == "__main__":
    unittest.main()

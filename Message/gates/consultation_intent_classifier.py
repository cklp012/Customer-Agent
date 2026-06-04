"""
Rule-based consultation intent classifier (Phase 13a).

Keyword risk scan first; no AI API, DB, or network.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from Message.gates.intent_types import (
    AUTO_CONFIDENCE_THRESHOLD,
    IntentBucket,
    RiskLevel,
)

# (substring, intent_id) — order matters: earlier = higher priority within block list
_BLOCK_KEYWORD_RULES: Sequence[Tuple[str, str]] = (
    ("差评威胁", "bad_review_threat"),
    ("差评", "bad_review_threat"),
    ("全额退", "refund_request"),
    ("退款", "refund_request"),
    ("退钱", "refund_request"),
    ("退货款", "refund_request"),
    ("退货", "refund_request"),
    ("赔偿", "compensation_request"),
    ("赔你", "compensation_request"),
    ("补偿", "compensation_request"),
    ("投诉", "complaint"),
    ("举报", "complaint"),
    ("纠纷", "after_sales_dispute"),
    ("售后问题", "after_sales_dispute"),
    ("转售后", "after_sales_dispute"),
    ("质量问题", "quality_dispute"),
    ("假货", "quality_dispute"),
    ("坏了", "quality_dispute"),
    ("取消订单", "order_change"),
    ("改订单", "order_change"),
    ("改地址", "address_change"),
    ("换地址", "address_change"),
    ("改价", "price_negotiation"),
    ("便宜点", "price_negotiation"),
    ("平台介入", "platform_rule_dispute"),
    ("规则不公", "platform_rule_dispute"),
)

_ALLOWED_KEYWORD_RULES: Sequence[Tuple[str, str]] = (
    ("尺码", "size_or_spec_question"),
    ("规格", "size_or_spec_question"),
    ("多大码", "size_or_spec_question"),
    ("颜色", "size_or_spec_question"),
    ("材质", "size_or_spec_question"),
    ("库存", "inventory_question"),
    ("有货", "inventory_question"),
    ("补货", "inventory_question"),
    ("怎么用", "usage_question"),
    ("如何使用", "usage_question"),
    ("区别", "comparison_question"),
    ("对比", "comparison_question"),
    ("包邮", "store_faq"),
    ("运费", "store_faq"),
    ("活动", "promotion_question"),
    ("优惠券", "promotion_question"),
    ("满减", "promotion_question"),
    ("发货", "basic_shipping_question"),
    ("几天发", "basic_shipping_question"),
    ("推荐", "recommendation_question"),
    ("商品", "product_question"),
    ("这款", "product_question"),
)


@dataclass(frozen=True)
class IntentClassification:
    intent: str
    intent_bucket: IntentBucket
    confidence: float
    risk_level: RiskLevel
    matched_keywords: List[str] = field(default_factory=list)
    source: str = "combined"


def _normalize_text(text: Optional[str]) -> str:
    if text is None:
        return ""
    if not isinstance(text, str):
        return ""
    return text.strip().lower()


def _scan_keywords(
    normalized: str,
    rules: Sequence[Tuple[str, str]],
) -> Tuple[Optional[str], List[str]]:
    matched: List[str] = []
    intent: Optional[str] = None
    for keyword, intent_id in rules:
        if keyword.lower() in normalized:
            matched.append(keyword)
            if intent is None:
                intent = intent_id
    return intent, matched


def keyword_risk_scan(text: Optional[str]) -> Tuple[bool, Optional[str], List[str]]:
    """
    First-layer hard block scan.

    Returns (is_blocked, suggested_intent, matched_keywords).
    """
    normalized = _normalize_text(text)
    if not normalized:
        return False, None, []

    intent, matched = _scan_keywords(normalized, _BLOCK_KEYWORD_RULES)
    if intent is not None:
        return True, intent, matched
    return False, None, []


def classify_consultation_intent(text: Optional[str]) -> IntentClassification:
    """
    Classify buyer message for consultation-only product gate.

    Blocked keywords cannot be overridden by allowed heuristics.
    """
    normalized = _normalize_text(text)
    if not normalized:
        return IntentClassification(
            intent="unclear_context",
            intent_bucket=IntentBucket.UNCERTAIN,
            confidence=0.0,
            risk_level=RiskLevel.HIGH,
            matched_keywords=[],
            source="rule",
        )

    is_blocked, block_intent, block_matched = keyword_risk_scan(text)
    if is_blocked and block_intent:
        return IntentClassification(
            intent=block_intent,
            intent_bucket=IntentBucket.BLOCKED,
            confidence=0.95,
            risk_level=RiskLevel.HIGH,
            matched_keywords=block_matched,
            source="keyword_rule",
        )

    allowed_intent, allowed_matched = _scan_keywords(normalized, _ALLOWED_KEYWORD_RULES)
    if allowed_intent:
        confidence = 0.9 if len(allowed_matched) >= 1 else 0.75
        risk = RiskLevel.LOW if confidence >= AUTO_CONFIDENCE_THRESHOLD else RiskLevel.MEDIUM
        return IntentClassification(
            intent=allowed_intent,
            intent_bucket=IntentBucket.ALLOWED,
            confidence=confidence,
            risk_level=risk,
            matched_keywords=allowed_matched,
            source="rule",
        )

    if len(normalized) < 3:
        return IntentClassification(
            intent="unclear_context",
            intent_bucket=IntentBucket.UNCERTAIN,
            confidence=0.3,
            risk_level=RiskLevel.MEDIUM,
            matched_keywords=[],
            source="rule",
        )

    return IntentClassification(
        intent="unclear_context",
        intent_bucket=IntentBucket.UNCERTAIN,
        confidence=0.5,
        risk_level=RiskLevel.MEDIUM,
        matched_keywords=[],
        source="rule",
    )

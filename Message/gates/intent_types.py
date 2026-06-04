"""
Product gate intent / mode types (Phase 13a).

Pure constants — no handler, DB, or network.
"""

from __future__ import annotations

from enum import Enum


class IntentBucket(str, Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    UNCERTAIN = "uncertain"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReplyMode(str, Enum):
    PREVIEW = "preview"
    ASSISTED = "assisted"
    AUTO = "auto"
    PAUSED = "paused"


class SendMode(str, Enum):
    NONE = "none"
    PREVIEW_ONLY = "preview_only"
    ASSISTED_REQUIRED = "assisted_required"
    AUTO_SEND = "auto_send"
    HUMAN_TAKEOVER = "human_takeover"
    LEGACY_PASSTHROUGH = "legacy_passthrough"


# Allowed consultation intents (12b.1 SSOT)
ALLOWED_INTENTS = frozenset(
    {
        "product_question",
        "size_or_spec_question",
        "inventory_question",
        "usage_question",
        "comparison_question",
        "store_faq",
        "promotion_question",
        "basic_shipping_question",
        "recommendation_question",
    }
)

# Blocked / human takeover intents
BLOCKED_INTENTS = frozenset(
    {
        "refund_request",
        "compensation_request",
        "complaint",
        "bad_review_threat",
        "after_sales_dispute",
        "quality_dispute",
        "order_change",
        "address_change",
        "price_negotiation",
        "platform_rule_dispute",
    }
)

# Uncertain intents
UNCERTAIN_INTENTS = frozenset(
    {
        "mixed_intent",
        "low_confidence",
        "unclear_context",
        "missing_product_context",
        "emotional_message",
    }
)

AUTO_CONFIDENCE_THRESHOLD = 0.85

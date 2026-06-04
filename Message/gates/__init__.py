"""
Product gate pure functions (Phase 13a).

Not wired into handler chain — import explicitly for tests and future H2+.
"""

from Message.gates.consultation_intent_classifier import (
    IntentClassification,
    classify_consultation_intent,
    keyword_risk_scan,
)
from Message.gates.guarded_send import GuardedSendResult, evaluate_guarded_send
from Message.gates.intent_types import (
    ALLOWED_INTENTS,
    AUTO_CONFIDENCE_THRESHOLD,
    BLOCKED_INTENTS,
    UNCERTAIN_INTENTS,
    IntentBucket,
    ReplyMode,
    RiskLevel,
    SendMode,
)
from Message.gates.send_decision import SendDecision, build_send_decision
from Message.gates.shadow_decision_logger import (
    InMemoryShadowDecisionLogger,
    ShadowDecisionRecord,
    append_shadow_decision_from_handler,
    build_shadow_decision_record,
    shadow_decision_logger,
)

__all__ = [
    "ALLOWED_INTENTS",
    "AUTO_CONFIDENCE_THRESHOLD",
    "BLOCKED_INTENTS",
    "UNCERTAIN_INTENTS",
    "GuardedSendResult",
    "IntentBucket",
    "IntentClassification",
    "ReplyMode",
    "RiskLevel",
    "SendDecision",
    "SendMode",
    "InMemoryShadowDecisionLogger",
    "ShadowDecisionRecord",
    "append_shadow_decision_from_handler",
    "build_send_decision",
    "build_shadow_decision_record",
    "classify_consultation_intent",
    "evaluate_guarded_send",
    "keyword_risk_scan",
    "shadow_decision_logger",
]

"""
SendDecision builder (Phase 13a) — product-level gate, not env flags.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from Message.gates.consultation_intent_classifier import IntentClassification
from Message.gates.intent_types import (
    AUTO_CONFIDENCE_THRESHOLD,
    IntentBucket,
    ReplyMode,
    RiskLevel,
    SendMode,
)


@dataclass(frozen=True)
class SendDecision:
    intent: str
    intent_bucket: IntentBucket
    intent_confidence: float
    risk_level: RiskLevel
    reply_mode: ReplyMode
    workspace_pause: bool
    shop_pause: bool
    product_gate_enabled: bool
    allowed_to_generate: bool
    allowed_to_send: bool
    send_mode: SendMode
    blocked_reason: Optional[str] = None
    human_takeover_reason: Optional[str] = None
    decision_source: str = "combined"


def _effective_reply_mode(
    reply_mode: ReplyMode,
    workspace_pause: bool,
    shop_pause: bool,
) -> ReplyMode:
    if workspace_pause or shop_pause:
        return ReplyMode.PAUSED
    return reply_mode


def build_send_decision(
    classification: IntentClassification,
    *,
    reply_mode: ReplyMode | str = ReplyMode.PREVIEW,
    product_gate_enabled: bool = False,
    workspace_pause: bool = False,
    shop_pause: bool = False,
) -> SendDecision:
    """
    Build SendDecision from intent classification and shop controls.

    When product_gate_enabled is False, returns legacy passthrough semantics
    (does not force preview / blocked rules onto legacy handler).
    """
    if isinstance(reply_mode, str):
        reply_mode = ReplyMode(reply_mode)

    effective_mode = _effective_reply_mode(reply_mode, workspace_pause, shop_pause)

    if not product_gate_enabled:
        return SendDecision(
            intent=classification.intent,
            intent_bucket=classification.intent_bucket,
            intent_confidence=classification.confidence,
            risk_level=classification.risk_level,
            reply_mode=effective_mode,
            workspace_pause=workspace_pause,
            shop_pause=shop_pause,
            product_gate_enabled=False,
            allowed_to_generate=True,
            allowed_to_send=True,
            send_mode=SendMode.LEGACY_PASSTHROUGH,
            blocked_reason="gate_disabled",
            human_takeover_reason=None,
            decision_source="gate_disabled",
        )

    # --- product gate enabled ---
    bucket = classification.intent_bucket
    intent = classification.intent
    confidence = classification.confidence
    risk = classification.risk_level

    if workspace_pause:
        return SendDecision(
            intent=intent,
            intent_bucket=bucket,
            intent_confidence=confidence,
            risk_level=risk,
            reply_mode=ReplyMode.PAUSED,
            workspace_pause=True,
            shop_pause=shop_pause,
            product_gate_enabled=True,
            allowed_to_generate=True,
            allowed_to_send=False,
            send_mode=SendMode.NONE,
            blocked_reason="workspace_paused",
            decision_source=classification.source,
        )

    if shop_pause:
        return SendDecision(
            intent=intent,
            intent_bucket=bucket,
            intent_confidence=confidence,
            risk_level=risk,
            reply_mode=ReplyMode.PAUSED,
            workspace_pause=False,
            shop_pause=True,
            product_gate_enabled=True,
            allowed_to_generate=True,
            allowed_to_send=False,
            send_mode=SendMode.NONE,
            blocked_reason="shop_paused",
            decision_source=classification.source,
        )

    if bucket == IntentBucket.BLOCKED:
        return SendDecision(
            intent=intent,
            intent_bucket=bucket,
            intent_confidence=confidence,
            risk_level=risk,
            reply_mode=effective_mode,
            workspace_pause=False,
            shop_pause=False,
            product_gate_enabled=True,
            allowed_to_generate=effective_mode != ReplyMode.PAUSED,
            allowed_to_send=False,
            send_mode=SendMode.HUMAN_TAKEOVER,
            blocked_reason="intent_blocked",
            human_takeover_reason=classification.source,
            decision_source=classification.source,
        )

    if effective_mode == ReplyMode.PREVIEW:
        return SendDecision(
            intent=intent,
            intent_bucket=bucket,
            intent_confidence=confidence,
            risk_level=risk,
            reply_mode=ReplyMode.PREVIEW,
            workspace_pause=False,
            shop_pause=False,
            product_gate_enabled=True,
            allowed_to_generate=True,
            allowed_to_send=False,
            send_mode=SendMode.PREVIEW_ONLY,
            blocked_reason="preview_mode",
            decision_source=classification.source,
        )

    if effective_mode == ReplyMode.ASSISTED:
        return SendDecision(
            intent=intent,
            intent_bucket=bucket,
            intent_confidence=confidence,
            risk_level=risk,
            reply_mode=ReplyMode.ASSISTED,
            workspace_pause=False,
            shop_pause=False,
            product_gate_enabled=True,
            allowed_to_generate=True,
            allowed_to_send=False,
            send_mode=SendMode.ASSISTED_REQUIRED,
            blocked_reason="awaiting_approval",
            decision_source=classification.source,
        )

    # AUTO mode
    if bucket == IntentBucket.UNCERTAIN:
        return SendDecision(
            intent=intent,
            intent_bucket=bucket,
            intent_confidence=confidence,
            risk_level=risk,
            reply_mode=ReplyMode.AUTO,
            workspace_pause=False,
            shop_pause=False,
            product_gate_enabled=True,
            allowed_to_generate=True,
            allowed_to_send=False,
            send_mode=SendMode.PREVIEW_ONLY,
            blocked_reason="uncertain_intent",
            decision_source=classification.source,
        )

    if confidence < AUTO_CONFIDENCE_THRESHOLD:
        return SendDecision(
            intent=intent,
            intent_bucket=bucket,
            intent_confidence=confidence,
            risk_level=risk,
            reply_mode=ReplyMode.AUTO,
            workspace_pause=False,
            shop_pause=False,
            product_gate_enabled=True,
            allowed_to_generate=True,
            allowed_to_send=False,
            send_mode=SendMode.ASSISTED_REQUIRED,
            blocked_reason="low_confidence",
            decision_source=classification.source,
        )

    if risk != RiskLevel.LOW:
        return SendDecision(
            intent=intent,
            intent_bucket=bucket,
            intent_confidence=confidence,
            risk_level=risk,
            reply_mode=ReplyMode.AUTO,
            workspace_pause=False,
            shop_pause=False,
            product_gate_enabled=True,
            allowed_to_generate=True,
            allowed_to_send=False,
            send_mode=SendMode.ASSISTED_REQUIRED,
            blocked_reason="risk_not_low",
            decision_source=classification.source,
        )

    if bucket == IntentBucket.ALLOWED:
        return SendDecision(
            intent=intent,
            intent_bucket=bucket,
            intent_confidence=confidence,
            risk_level=risk,
            reply_mode=ReplyMode.AUTO,
            workspace_pause=False,
            shop_pause=False,
            product_gate_enabled=True,
            allowed_to_generate=True,
            allowed_to_send=True,
            send_mode=SendMode.AUTO_SEND,
            decision_source=classification.source,
        )

    return SendDecision(
        intent=intent,
        intent_bucket=bucket,
        intent_confidence=confidence,
        risk_level=risk,
        reply_mode=ReplyMode.AUTO,
        workspace_pause=False,
        shop_pause=False,
        product_gate_enabled=True,
        allowed_to_generate=True,
        allowed_to_send=False,
        send_mode=SendMode.PREVIEW_ONLY,
        blocked_reason="uncertain_intent",
        decision_source=classification.source,
    )

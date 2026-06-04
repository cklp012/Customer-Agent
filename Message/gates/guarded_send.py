"""
Guarded send evaluator (Phase 13a) — pure logic only, no SendMessage / outbound.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from Message.gates.send_decision import SendDecision
from Message.gates.intent_types import ReplyMode, SendMode


@dataclass(frozen=True)
class GuardedSendResult:
    should_send: bool
    send_mode: SendMode
    send_status: str
    reason: Optional[str]
    reply_text: str


def evaluate_guarded_send(
    send_decision: SendDecision,
    reply_text: str,
    *,
    merchant_approved: bool = False,
) -> GuardedSendResult:
    """
    Evaluate whether guarded send path would call platform send API.

    Does not invoke SendMessage, outbound, or database.
    """
    text = reply_text or ""

    if not send_decision.product_gate_enabled:
        return GuardedSendResult(
            should_send=True,
            send_mode=SendMode.LEGACY_PASSTHROUGH,
            send_status="legacy_passthrough",
            reason="gate_disabled",
            reply_text=text,
        )

    if send_decision.workspace_pause or send_decision.shop_pause:
        return GuardedSendResult(
            should_send=False,
            send_mode=SendMode.NONE,
            send_status="not_sent_paused",
            reason=send_decision.blocked_reason or "paused",
            reply_text=text,
        )

    if send_decision.send_mode == SendMode.HUMAN_TAKEOVER:
        return GuardedSendResult(
            should_send=False,
            send_mode=SendMode.HUMAN_TAKEOVER,
            send_status="not_sent_human_takeover",
            reason=send_decision.human_takeover_reason or "intent_blocked",
            reply_text=text,
        )

    if send_decision.send_mode == SendMode.PREVIEW_ONLY:
        return GuardedSendResult(
            should_send=False,
            send_mode=SendMode.PREVIEW_ONLY,
            send_status="not_sent_preview",
            reason=send_decision.blocked_reason or "preview_mode",
            reply_text=text,
        )

    if send_decision.send_mode == SendMode.ASSISTED_REQUIRED:
        if merchant_approved and send_decision.allowed_to_send:
            return GuardedSendResult(
                should_send=True,
                send_mode=SendMode.AUTO_SEND,
                send_status="assisted_sent",
                reason=None,
                reply_text=text,
            )
        return GuardedSendResult(
            should_send=False,
            send_mode=SendMode.ASSISTED_REQUIRED,
            send_status="not_sent_assisted_required",
            reason=send_decision.blocked_reason or "awaiting_approval",
            reply_text=text,
        )

    if send_decision.send_mode == SendMode.NONE:
        return GuardedSendResult(
            should_send=False,
            send_mode=SendMode.NONE,
            send_status="not_sent_paused",
            reason=send_decision.blocked_reason,
            reply_text=text,
        )

    if send_decision.send_mode == SendMode.AUTO_SEND and send_decision.allowed_to_send:
        return GuardedSendResult(
            should_send=True,
            send_mode=SendMode.AUTO_SEND,
            send_status="auto_send_allowed",
            reason=None,
            reply_text=text,
        )

    return GuardedSendResult(
        should_send=False,
        send_mode=send_decision.send_mode,
        send_status="not_sent_blocked",
        reason=send_decision.blocked_reason or "not_allowed",
        reply_text=text,
    )

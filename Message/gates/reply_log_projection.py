"""
Preview ReplyLog → Dashboard read model projection (Phase 13e).

In-memory only — aligns with phase12d/12e ReplyLog fields; no DB or send APIs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from uuid import uuid4

from Message.gates.intent_types import IntentBucket, RiskLevel, SendMode
from Message.gates.preview_log import PreviewLogRecord, preview_log


@dataclass(frozen=True)
class PreviewReplyLogListItem:
    reply_log_id: str
    workspace_id: Optional[str]
    platform_id: Optional[str]
    shop_id: Optional[str]
    account_id: Optional[str]
    buyer_id: Optional[str]
    buyer_message: str
    ai_suggested_reply: str
    final_reply: Optional[str]
    send_status: str
    send_mode: str
    intent: str
    intent_bucket: str
    intent_confidence: float
    risk_level: str
    blocked_reason: Optional[str]
    human_takeover_reason: Optional[str]
    not_sent_explanation: str
    created_at: str


def _safe_str(value: object, default: str = "") -> str:
    if value is None:
        return default
    try:
        text = str(value).strip()
        return text if text else default
    except Exception:
        return default


def _safe_optional_str(value: object) -> Optional[str]:
    text = _safe_str(value, "")
    return text if text else None


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _resolve_send_status(record: PreviewLogRecord) -> str:
    if record.send_status:
        return record.send_status
    try:
        return _safe_str(record.guarded_result.send_status, "not_sent_blocked")
    except Exception:
        return "not_sent_blocked"


def _resolve_send_mode(record: PreviewLogRecord) -> str:
    if record.send_mode:
        return record.send_mode
    try:
        mode = record.send_decision.send_mode
        return mode.value if isinstance(mode, SendMode) else _safe_str(mode, "preview_only")
    except Exception:
        return "preview_only"


def _resolve_intent_bucket(record: PreviewLogRecord) -> str:
    try:
        bucket = record.classification.intent_bucket
        return bucket.value if isinstance(bucket, IntentBucket) else _safe_str(bucket, "uncertain")
    except Exception:
        return "uncertain"


def _resolve_risk_level(record: PreviewLogRecord) -> str:
    try:
        risk = record.classification.risk_level
        return risk.value if isinstance(risk, RiskLevel) else _safe_str(risk, "low")
    except Exception:
        return "low"


def build_not_sent_explanation(
    *,
    send_status: str,
    send_mode: str,
    blocked_reason: Optional[str],
    human_takeover_reason: Optional[str],
) -> str:
    if send_status == "not_sent_human_takeover":
        reason = human_takeover_reason or blocked_reason or "intent_blocked"
        return (
            f"Human takeover required ({reason}): "
            "message not sent; route to merchant agent."
        )
    if send_status == "not_sent_preview":
        return (
            "Preview mode: AI suggestion recorded for merchant review; "
            "message not sent to buyer."
        )
    if send_status == "not_sent_paused":
        return f"Workspace or shop paused ({blocked_reason or 'paused'}): message not sent."
    if send_mode == SendMode.PREVIEW_ONLY.value or send_mode == "preview_only":
        return (
            "Preview mode: AI suggestion recorded for merchant review; "
            "message not sent to buyer."
        )
    return f"Message not sent ({send_status})."


def project_preview_record_to_reply_log(
    record: PreviewLogRecord,
) -> PreviewReplyLogListItem:
    """Project one PreviewLogRecord to dashboard ReplyLog list item (fail-safe)."""
    try:
        meta = record.metadata if isinstance(record.metadata, dict) else {}
        send_status = _resolve_send_status(record)
        send_mode = _resolve_send_mode(record)
        blocked_reason = record.blocked_reason or _safe_optional_str(
            getattr(record.send_decision, "blocked_reason", None)
        )
        human_takeover_reason = record.human_takeover_reason or _safe_optional_str(
            getattr(record.send_decision, "human_takeover_reason", None)
        )
        intent = _safe_str(getattr(record.classification, "intent", None), "unknown")

        return PreviewReplyLogListItem(
            reply_log_id=_safe_str(record.reply_log_id) or str(uuid4()),
            workspace_id=record.workspace_id or _safe_optional_str(meta.get("workspace_id")),
            platform_id=record.platform_id or _safe_optional_str(
                meta.get("platform_id") or meta.get("platform")
            ),
            shop_id=record.shop_id or _safe_optional_str(meta.get("shop_id")),
            account_id=record.account_id or _safe_optional_str(meta.get("account_id")),
            buyer_id=record.buyer_id
            or _safe_optional_str(meta.get("from_uid") or meta.get("buyer_id")),
            buyer_message=_safe_str(record.message_text),
            ai_suggested_reply=_safe_str(record.reply_text),
            final_reply=None,
            send_status=send_status,
            send_mode=send_mode,
            intent=intent,
            intent_bucket=_resolve_intent_bucket(record),
            intent_confidence=_safe_float(
                getattr(record.classification, "confidence", 0.0)
            ),
            risk_level=_resolve_risk_level(record),
            blocked_reason=blocked_reason,
            human_takeover_reason=human_takeover_reason,
            not_sent_explanation=build_not_sent_explanation(
                send_status=send_status,
                send_mode=send_mode,
                blocked_reason=blocked_reason,
                human_takeover_reason=human_takeover_reason,
            ),
            created_at=_safe_str(record.created_at),
        )
    except Exception:
        return PreviewReplyLogListItem(
            reply_log_id=str(uuid4()),
            workspace_id=None,
            platform_id=None,
            shop_id=None,
            account_id=None,
            buyer_id=None,
            buyer_message=_safe_str(getattr(record, "message_text", "")),
            ai_suggested_reply=_safe_str(getattr(record, "reply_text", "")),
            final_reply=None,
            send_status="not_sent_blocked",
            send_mode="preview_only",
            intent="unknown",
            intent_bucket="uncertain",
            intent_confidence=0.0,
            risk_level="low",
            blocked_reason="projection_error",
            human_takeover_reason=None,
            not_sent_explanation="Message not sent (projection_error).",
            created_at=_safe_str(getattr(record, "created_at", "")),
        )


def list_preview_reply_logs() -> List[PreviewReplyLogListItem]:
    """List all in-memory preview logs projected for dashboard read model."""
    return [project_preview_record_to_reply_log(r) for r in preview_log.all()]

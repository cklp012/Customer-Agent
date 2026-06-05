"""
Product persistence ORM placeholders (Phase 14f).

SQLAlchemy models for reply_logs / send_decision_snapshots /
pending_assisted_replies / audit_logs are deferred to Phase 14g+.
No Base.metadata · no create_all · no tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ReplyLogDTO:
    """Read model placeholder — aligns with phase14e repository DTO."""

    reply_log_id: str
    workspace_id: str
    shop_id: str
    account_id: str
    platform_id: str
    buyer_id: str
    buyer_message: str
    ai_suggested_reply: Optional[str]
    send_status: str
    send_mode: str
    intent: str
    intent_bucket: str
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class SendDecisionSnapshotDTO:
    send_decision_id: str
    reply_log_id: Optional[str]
    decision_phase: str
    intent: str
    send_mode: str


@dataclass(frozen=True)
class PendingAssistedReplyDTO:
    pending_reply_id: str
    reply_log_id: str
    status: str
    suggested_reply: str


@dataclass(frozen=True)
class AuditLogDTO:
    audit_log_id: str
    workspace_id: str
    action: str
    target_type: str
    target_id: str

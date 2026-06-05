"""
Product persistence models (Phase 14f DTOs · Phase 14l ReplyLog ORM).

Independent from legacy database.models — product_gate.db only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from sqlalchemy import Float, Index, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class ProductBase(DeclarativeBase):
    """SQLAlchemy base for product_gate.db only."""


class ReplyLogRow(ProductBase):
    __tablename__ = "reply_logs"

    reply_log_id: Mapped[str] = mapped_column(Text, primary_key=True)
    workspace_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shop_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    account_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    platform_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    buyer_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conversation_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    inbound_message_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    buyer_message: Mapped[str] = mapped_column(Text, nullable=False)
    ai_suggested_reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    final_reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reply_mode: Mapped[str] = mapped_column(Text, nullable=False)
    send_mode: Mapped[str] = mapped_column(Text, nullable=False)
    send_status: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    intent_bucket: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    intent_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    blocked_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    human_takeover_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    not_sent_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    product_gate_enabled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("idx_reply_logs_workspace_created_at", "workspace_id", "created_at"),
        Index("idx_reply_logs_shop_created_at", "shop_id", "created_at"),
        Index("idx_reply_logs_buyer_created_at", "buyer_id", "created_at"),
        Index("idx_reply_logs_send_status", "send_status"),
    )


class SendDecisionSnapshotRow(ProductBase):
    __tablename__ = "send_decision_snapshots"

    send_decision_id: Mapped[str] = mapped_column(Text, primary_key=True)
    reply_log_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    workspace_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shop_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    account_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    platform_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    inbound_message_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decision_phase: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    intent_bucket: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    intent_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reply_mode: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    workspace_pause: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shop_pause: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    product_gate_enabled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    allowed_to_generate: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    allowed_to_send: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    send_mode: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    blocked_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    human_takeover_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decision_source: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("idx_send_decisions_reply_log_id", "reply_log_id"),
        Index("idx_send_decisions_workspace_created_at", "workspace_id", "created_at"),
        Index("idx_send_decisions_shop_created_at", "shop_id", "created_at"),
        Index("idx_send_decisions_phase", "decision_phase"),
    )


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
    intent_bucket: Optional[str] = None
    risk_level: Optional[str] = None
    allowed_to_send: Optional[bool] = None
    allowed_to_generate: Optional[bool] = None
    decision_source: Optional[str] = None
    created_at: Optional[str] = None


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

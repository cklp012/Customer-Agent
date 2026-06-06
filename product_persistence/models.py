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


class PendingAssistedReplyRow(ProductBase):
    __tablename__ = "pending_assisted_replies"

    pending_assisted_id: Mapped[str] = mapped_column(Text, primary_key=True)
    reply_log_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    workspace_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shop_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    account_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    platform_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    buyer_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conversation_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    inbound_message_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    buyer_message: Mapped[str] = mapped_column(Text, nullable=False)
    ai_suggested_reply: Mapped[str] = mapped_column(Text, nullable=False)
    merchant_edited_reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    final_reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    intent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    intent_bucket: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    blocked_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    human_takeover_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejected_by: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index(
            "idx_pending_workspace_status_created_at",
            "workspace_id",
            "status",
            "created_at",
        ),
        Index("idx_pending_shop_status_created_at", "shop_id", "status", "created_at"),
        Index("idx_pending_reply_log_id", "reply_log_id"),
        Index("idx_pending_buyer_created_at", "buyer_id", "created_at"),
    )


class AuditLogRow(ProductBase):
    __tablename__ = "audit_logs"

    audit_log_id: Mapped[str] = mapped_column(Text, primary_key=True)
    workspace_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shop_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    account_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    platform_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actor_user_id: Mapped[str] = mapped_column(Text, nullable=False)
    actor_role: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[str] = mapped_column(Text, nullable=False)
    reply_log_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pending_assisted_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    before_state: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    after_state: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("idx_audit_workspace_created_at", "workspace_id", "created_at"),
        Index("idx_audit_shop_created_at", "shop_id", "created_at"),
        Index("idx_audit_actor_created_at", "actor_user_id", "created_at"),
        Index("idx_audit_target", "target_type", "target_id"),
    )


class MerchantSafetyPolicyRow(ProductBase):
    __tablename__ = "merchant_safety_policies"

    policy_id: Mapped[str] = mapped_column(Text, primary_key=True)
    workspace_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shop_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    intent_category: Mapped[str] = mapped_column(Text, nullable=False)
    ai_intervention_mode: Mapped[str] = mapped_column(Text, nullable=False)
    platform_mode_ceiling: Mapped[str] = mapped_column(Text, nullable=False)
    allowed_template_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    require_human_confirmation: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    allow_auto_reply: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    forbidden_keywords_extra: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    policy_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    enabled: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index(
            "idx_policy_workspace_shop_intent",
            "workspace_id",
            "shop_id",
            "intent_category",
        ),
        Index("idx_policy_workspace_enabled", "workspace_id", "enabled"),
        Index("idx_policy_shop_intent", "shop_id", "intent_category"),
        Index("idx_policy_updated_at", "updated_at"),
    )


class MerchantReplyTemplateRow(ProductBase):
    __tablename__ = "merchant_reply_templates"

    template_id: Mapped[str] = mapped_column(Text, primary_key=True)
    workspace_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shop_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    intent_category: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    validation_status: Mapped[str] = mapped_column(Text, nullable=False)
    validation_warnings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    enabled: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index(
            "idx_template_workspace_shop_intent",
            "workspace_id",
            "shop_id",
            "intent_category",
        ),
        Index("idx_template_workspace_enabled", "workspace_id", "enabled"),
        Index("idx_template_validation_status", "validation_status"),
        Index("idx_template_content_hash", "content_hash"),
    )


class OutboundIdempotencyRow(ProductBase):
    __tablename__ = "outbound_idempotency_keys"

    idempotency_key: Mapped[str] = mapped_column(Text, primary_key=True)
    workspace_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shop_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    account_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    platform_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pending_assisted_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reply_log_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    operation_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    provider_message_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    platform_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    locked_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_idempotency_workspace_shop", "workspace_id", "shop_id"),
        Index("idx_idempotency_pending_assisted", "pending_assisted_id"),
        Index("idx_idempotency_status", "status"),
        Index("idx_idempotency_operation_type", "operation_type"),
        Index("idx_idempotency_updated_at", "updated_at"),
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
    pending_assisted_id: str
    reply_log_id: str
    workspace_id: str
    shop_id: str
    account_id: str
    platform_id: str
    buyer_id: str
    buyer_message: str
    ai_suggested_reply: str
    status: str
    intent: str
    intent_bucket: str
    risk_level: str
    expires_at: str
    created_at: str
    updated_at: str
    merchant_edited_reply: Optional[str] = None
    final_reply: Optional[str] = None
    blocked_reason: Optional[str] = None
    human_takeover_reason: Optional[str] = None
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    rejected_by: Optional[str] = None
    conversation_id: Optional[str] = None
    inbound_message_id: Optional[str] = None


@dataclass(frozen=True)
class AuditLogDTO:
    audit_log_id: str
    workspace_id: str
    actor_user_id: str
    actor_role: str
    action: str
    target_type: str
    target_id: str
    created_at: str
    shop_id: Optional[str] = None
    account_id: Optional[str] = None
    platform_id: Optional[str] = None
    reply_log_id: Optional[str] = None
    pending_assisted_id: Optional[str] = None
    before_state: Optional[str] = None
    after_state: Optional[str] = None
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass(frozen=True)
class MerchantSafetyPolicyDTO:
    policy_id: str
    workspace_id: str
    shop_id: str
    intent_category: str
    ai_intervention_mode: str
    platform_mode_ceiling: str
    policy_version: int
    enabled: bool
    created_at: str
    updated_at: str
    allowed_template_ids: tuple[str, ...] = ()
    require_human_confirmation: bool = True
    allow_auto_reply: bool = False
    forbidden_keywords_extra: tuple[str, ...] = ()


@dataclass(frozen=True)
class MerchantReplyTemplateDTO:
    template_id: str
    workspace_id: str
    shop_id: str
    intent_category: str
    title: str
    content: str
    content_hash: str
    validation_status: str
    template_version: int
    enabled: bool
    created_at: str
    updated_at: str
    variables: Optional[Dict[str, Any]] = None
    validation_warnings: tuple[str, ...] = ()

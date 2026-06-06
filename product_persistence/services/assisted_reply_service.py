"""Assisted reply service skeleton (Phase 14x) — no send, no outbound."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from Message.gates.final_guard import FinalGuardInput, evaluate_final_guard
from product_persistence import flags
from product_persistence.db_manager import ProductDbManager, get_product_db_manager
from product_persistence.repositories.sqlite_audit_log_repository import (
    AuditLogRepositorySQLite,
)
from product_persistence.repositories.sqlite_pending_assisted_repository import (
    PendingAssistedRepositorySQLite,
)

_APPROVE_ROLES = frozenset({"operator", "admin", "owner"})
_TERMINAL_APPROVE_STATUSES = frozenset({"rejected", "expired", "sent", "approved"})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_iso(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _is_expired(expires_at: Optional[str], now: str) -> bool:
    if not expires_at:
        return False
    return _parse_iso(now) > _parse_iso(expires_at)


@dataclass(frozen=True)
class AssistedServiceResult:
    success: bool
    action: str
    status: str
    pending_assisted_id: Optional[str] = None
    reply_log_id: Optional[str] = None
    audit_log_id: Optional[str] = None
    final_guard_allowed: Optional[bool] = None
    final_guard_block_code: Optional[str] = None
    reason: Optional[str] = None
    error: Optional[str] = None


class AssistedReplyService:
    """Assisted confirmation flow skeleton — persistence + guard only, no outbound."""

    def __init__(
        self,
        *,
        db_manager: Optional[ProductDbManager] = None,
        pending_repo: Optional[PendingAssistedRepositorySQLite] = None,
        audit_repo: Optional[AuditLogRepositorySQLite] = None,
    ) -> None:
        self._db_manager = db_manager
        self._pending_repo = pending_repo
        self._audit_repo = audit_repo

    def _pending_repository(self) -> PendingAssistedRepositorySQLite:
        if self._pending_repo is not None:
            return self._pending_repo
        return PendingAssistedRepositorySQLite(
            db_manager=self._db_manager or get_product_db_manager()
        )

    def _audit_repository(self) -> AuditLogRepositorySQLite:
        if self._audit_repo is not None:
            return self._audit_repo
        return AuditLogRepositorySQLite(
            db_manager=self._db_manager or get_product_db_manager()
        )

    @staticmethod
    def _disabled(action: str) -> AssistedServiceResult:
        return AssistedServiceResult(
            success=False,
            action=action,
            status="disabled",
            reason="assisted_disabled",
        )

    @staticmethod
    def _role_denied(action: str) -> AssistedServiceResult:
        return AssistedServiceResult(
            success=False,
            action=action,
            status="permission_denied",
            reason="permission_denied",
        )

    def create_pending_from_preview(
        self,
        *,
        reply_log_id: str,
        workspace_id: str,
        shop_id: str,
        account_id: str,
        platform_id: str,
        buyer_id: str,
        buyer_message: str,
        ai_suggested_reply: str,
        intent: str,
        intent_bucket: str = "allowed",
        risk_level: str = "low",
        conversation_id: Optional[str] = None,
        inbound_message_id: Optional[str] = None,
        created_by: Optional[str] = None,
        expires_at: Optional[str] = None,
        actor_user_id: str = "system",
        actor_role: str = "system",
        **_kwargs: Any,
    ) -> AssistedServiceResult:
        if not flags.is_assisted_service_enabled():
            return self._disabled("create_pending")

        try:
            pending_id = self._pending_repository().create_pending(
                reply_log_id=reply_log_id,
                workspace_id=workspace_id,
                shop_id=shop_id,
                account_id=account_id,
                platform_id=platform_id,
                buyer_id=buyer_id,
                buyer_message=buyer_message,
                ai_suggested_reply=ai_suggested_reply,
                intent=intent,
                intent_bucket=intent_bucket,
                risk_level=risk_level,
                conversation_id=conversation_id,
                inbound_message_id=inbound_message_id,
                created_by=created_by,
                expires_at=expires_at,
            )
            audit_id = self._audit_repository().append_audit_log(
                workspace_id=workspace_id,
                shop_id=shop_id,
                account_id=account_id,
                platform_id=platform_id,
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                action="pending_assisted_created",
                target_type="pending_assisted",
                target_id=pending_id,
                reply_log_id=reply_log_id,
                pending_assisted_id=pending_id,
                after_state={"status": "pending"},
            )
            return AssistedServiceResult(
                success=True,
                action="create_pending",
                status="pending",
                pending_assisted_id=pending_id,
                reply_log_id=reply_log_id,
                audit_log_id=audit_id,
            )
        except Exception as exc:
            return AssistedServiceResult(
                success=False,
                action="create_pending",
                status="error",
                reply_log_id=reply_log_id,
                error=str(exc),
            )

    def approve_pending(
        self,
        pending_assisted_id: str,
        *,
        actor_user_id: str,
        actor_role: str,
        final_reply: Optional[str] = None,
        merchant_edited_reply: Optional[str] = None,
        effective_mode: Optional[str] = None,
        platform_mode_ceiling: Optional[str] = None,
        template_id: Optional[str] = None,
        template_version: Optional[int] = None,
        template_validation_status: Optional[str] = None,
        outbound_channel_status: str = "available",
        inbound_created_at: Optional[str] = None,
        now: Optional[str] = None,
        **_kwargs: Any,
    ) -> AssistedServiceResult:
        if not flags.is_assisted_service_enabled():
            return self._disabled("approve_pending")

        role = (actor_role or "").lower()
        if role not in _APPROVE_ROLES:
            return self._role_denied("approve_pending")

        pending = self._pending_repository().get_pending(pending_assisted_id)
        if pending is None:
            return AssistedServiceResult(
                success=False,
                action="approve_pending",
                status="not_found",
                pending_assisted_id=pending_assisted_id,
                reason="pending_not_found",
            )

        if pending.status in _TERMINAL_APPROVE_STATUSES:
            return AssistedServiceResult(
                success=False,
                action="approve_pending",
                status="terminal_state",
                pending_assisted_id=pending_assisted_id,
                reply_log_id=pending.reply_log_id,
                reason=f"pending status `{pending.status}` cannot approve",
            )

        resolved_final_reply = (
            final_reply
            or merchant_edited_reply
            or pending.merchant_edited_reply
            or pending.ai_suggested_reply
        )
        current_time = now or _utc_now_iso()
        guard_input = FinalGuardInput(
            product_gate_enabled=True,
            workspace_id=pending.workspace_id,
            shop_id=pending.shop_id,
            account_id=pending.account_id,
            platform_id=pending.platform_id,
            actor_user_id=actor_user_id,
            actor_role=role,
            reply_log_id=pending.reply_log_id,
            pending_assisted_id=pending.pending_assisted_id,
            buyer_id=pending.buyer_id,
            inbound_message_id=pending.inbound_message_id,
            buyer_message=pending.buyer_message,
            ai_suggested_reply=pending.ai_suggested_reply,
            merchant_edited_reply=merchant_edited_reply or pending.merchant_edited_reply,
            final_reply=resolved_final_reply,
            intent_category=pending.intent,
            intent=pending.intent,
            intent_bucket=pending.intent_bucket,
            risk_level=pending.risk_level,
            blocked_reason=pending.blocked_reason,
            human_takeover_reason=pending.human_takeover_reason,
            effective_mode=effective_mode or "assisted_only",
            platform_mode_ceiling=platform_mode_ceiling or "assisted_only",
            template_id=template_id,
            template_version=template_version,
            template_validation_status=template_validation_status,
            reply_mode="assisted",
            pending_status=pending.status,
            expires_at=pending.expires_at,
            inbound_created_at=inbound_created_at or pending.created_at,
            outbound_channel_status=outbound_channel_status,
            now=current_time,
        )
        guard_result = evaluate_final_guard(guard_input)

        if not guard_result.allowed_to_send:
            audit_id = self._audit_repository().append_audit_log(
                workspace_id=pending.workspace_id,
                shop_id=pending.shop_id,
                account_id=pending.account_id,
                platform_id=pending.platform_id,
                actor_user_id=actor_user_id,
                actor_role=role,
                action="final_guard_blocked",
                target_type="pending_assisted",
                target_id=pending.pending_assisted_id,
                reply_log_id=pending.reply_log_id,
                pending_assisted_id=pending.pending_assisted_id,
                before_state={"status": pending.status},
                after_state={
                    "status": pending.status,
                    "block_code": guard_result.block_code,
                },
                reason=guard_result.block_reason,
            )
            return AssistedServiceResult(
                success=False,
                action="approve_pending",
                status="guard_blocked",
                pending_assisted_id=pending.pending_assisted_id,
                reply_log_id=pending.reply_log_id,
                audit_log_id=audit_id,
                final_guard_allowed=False,
                final_guard_block_code=guard_result.block_code,
                reason=guard_result.block_reason,
            )

        audit_id = self._audit_repository().append_audit_log(
            workspace_id=pending.workspace_id,
            shop_id=pending.shop_id,
            account_id=pending.account_id,
            platform_id=pending.platform_id,
            actor_user_id=actor_user_id,
            actor_role=role,
            action="assisted_approved",
            target_type="pending_assisted",
            target_id=pending.pending_assisted_id,
            reply_log_id=pending.reply_log_id,
            pending_assisted_id=pending.pending_assisted_id,
            before_state={"status": pending.status},
            after_state={"status": pending.status, "send": "not_implemented"},
            reason="send_not_implemented",
        )
        return AssistedServiceResult(
            success=True,
            action="approve_pending",
            status="guard_passed_but_send_not_implemented",
            pending_assisted_id=pending.pending_assisted_id,
            reply_log_id=pending.reply_log_id,
            audit_log_id=audit_id,
            final_guard_allowed=True,
            reason="send_not_implemented",
        )

    def reject_pending(
        self,
        pending_assisted_id: str,
        *,
        actor_user_id: str,
        actor_role: str,
        reason: Optional[str] = None,
        **_kwargs: Any,
    ) -> AssistedServiceResult:
        if not flags.is_assisted_service_enabled():
            return self._disabled("reject_pending")

        role = (actor_role or "").lower()
        if role not in _APPROVE_ROLES:
            return self._role_denied("reject_pending")

        pending = self._pending_repository().get_pending(pending_assisted_id)
        if pending is None:
            return AssistedServiceResult(
                success=False,
                action="reject_pending",
                status="not_found",
                pending_assisted_id=pending_assisted_id,
                reason="pending_not_found",
            )

        if pending.status != "pending":
            return AssistedServiceResult(
                success=False,
                action="reject_pending",
                status="terminal_state",
                pending_assisted_id=pending_assisted_id,
                reply_log_id=pending.reply_log_id,
                reason=f"pending status `{pending.status}` cannot reject",
            )

        updated = self._pending_repository().mark_status(
            pending_assisted_id,
            "rejected",
            rejected_by=actor_user_id,
        )
        if not updated:
            return AssistedServiceResult(
                success=False,
                action="reject_pending",
                status="error",
                pending_assisted_id=pending_assisted_id,
                reason="reject_update_failed",
            )

        audit_id = self._audit_repository().append_audit_log(
            workspace_id=pending.workspace_id,
            shop_id=pending.shop_id,
            account_id=pending.account_id,
            platform_id=pending.platform_id,
            actor_user_id=actor_user_id,
            actor_role=role,
            action="assisted_rejected",
            target_type="pending_assisted",
            target_id=pending.pending_assisted_id,
            reply_log_id=pending.reply_log_id,
            pending_assisted_id=pending.pending_assisted_id,
            before_state={"status": "pending"},
            after_state={"status": "rejected"},
            reason=reason,
        )
        return AssistedServiceResult(
            success=True,
            action="reject_pending",
            status="rejected",
            pending_assisted_id=pending.pending_assisted_id,
            reply_log_id=pending.reply_log_id,
            audit_log_id=audit_id,
            reason=reason,
        )

    def expire_pending(
        self,
        pending_assisted_id: str,
        *,
        actor_user_id: str = "system",
        actor_role: str = "system",
        now: Optional[str] = None,
        **_kwargs: Any,
    ) -> AssistedServiceResult:
        if not flags.is_assisted_service_enabled():
            return self._disabled("expire_pending")

        pending = self._pending_repository().get_pending(pending_assisted_id)
        if pending is None:
            return AssistedServiceResult(
                success=False,
                action="expire_pending",
                status="not_found",
                pending_assisted_id=pending_assisted_id,
                reason="pending_not_found",
            )

        if pending.status != "pending":
            return AssistedServiceResult(
                success=False,
                action="expire_pending",
                status="terminal_state",
                pending_assisted_id=pending_assisted_id,
                reply_log_id=pending.reply_log_id,
                reason=f"pending status `{pending.status}` cannot expire",
            )

        current_time = now or _utc_now_iso()
        if not _is_expired(pending.expires_at, current_time):
            return AssistedServiceResult(
                success=False,
                action="expire_pending",
                status="not_expired",
                pending_assisted_id=pending.pending_assisted_id,
                reply_log_id=pending.reply_log_id,
                reason="pending_not_expired",
            )

        updated = self._pending_repository().mark_status(
            pending_assisted_id,
            "expired",
        )
        if not updated:
            return AssistedServiceResult(
                success=False,
                action="expire_pending",
                status="error",
                pending_assisted_id=pending_assisted_id,
                reason="expire_update_failed",
            )

        audit_id = self._audit_repository().append_audit_log(
            workspace_id=pending.workspace_id,
            shop_id=pending.shop_id,
            account_id=pending.account_id,
            platform_id=pending.platform_id,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            action="assisted_expired",
            target_type="pending_assisted",
            target_id=pending.pending_assisted_id,
            reply_log_id=pending.reply_log_id,
            pending_assisted_id=pending.pending_assisted_id,
            before_state={"status": "pending"},
            after_state={"status": "expired"},
            reason="pending_expired",
        )
        return AssistedServiceResult(
            success=True,
            action="expire_pending",
            status="expired",
            pending_assisted_id=pending.pending_assisted_id,
            reply_log_id=pending.reply_log_id,
            audit_log_id=audit_id,
            reason="pending_expired",
        )

    def approve_pending_reply(
        self,
        pending_reply_id: str,
        *,
        actor_member_id: str,
        final_reply: Optional[str] = None,
        **_kwargs: Any,
    ) -> AssistedServiceResult:
        """Backward-compatible alias for skeleton callers."""
        return self.approve_pending(
            pending_reply_id,
            actor_user_id=actor_member_id,
            actor_role=_kwargs.get("actor_role", "operator"),
            final_reply=final_reply,
            **_kwargs,
        )

    def reject_pending_reply(
        self,
        pending_reply_id: str,
        *,
        actor_member_id: str,
        reason: Optional[str] = None,
        **_kwargs: Any,
    ) -> AssistedServiceResult:
        """Backward-compatible alias for skeleton callers."""
        return self.reject_pending(
            pending_reply_id,
            actor_user_id=actor_member_id,
            actor_role=_kwargs.get("actor_role", "operator"),
            reason=reason,
            **_kwargs,
        )

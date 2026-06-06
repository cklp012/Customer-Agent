"""Assisted reply service skeleton (Phase 14x) — dry-run outbound wire (Phase 15f)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from Message.gates.final_guard import FinalGuardInput, evaluate_final_guard
from product_persistence import flags
from product_persistence.db_manager import ProductDbManager, get_product_db_manager
from product_persistence.repositories.sqlite_audit_log_repository import (
    AuditLogRepositorySQLite,
)
from product_persistence.repositories.sqlite_pending_assisted_repository import (
    PendingAssistedRepositorySQLite,
)
from product_persistence.services.assisted_outbound_port import (
    AssistedOutboundPort,
    DryRunAssistedOutboundPort,
    build_assisted_outbound_request,
)

_APPROVE_ROLES = frozenset({"operator", "admin", "owner"})
_TERMINAL_APPROVE_STATUSES = frozenset({"rejected", "expired", "sent", "approved"})
_IDEMPOTENCY_KEY_PREFIX = "assisted_send:"


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
    """Assisted confirmation flow — guard + dry-run outbound port (no live send)."""

    def __init__(
        self,
        *,
        db_manager: Optional[ProductDbManager] = None,
        pending_repo: Optional[PendingAssistedRepositorySQLite] = None,
        audit_repo: Optional[AuditLogRepositorySQLite] = None,
        idempotency_repo: Any = None,
        outbound_port: Optional[AssistedOutboundPort] = None,
    ) -> None:
        self._db_manager = db_manager
        self._pending_repo = pending_repo
        self._audit_repo = audit_repo
        self._idempotency_repo = idempotency_repo
        self._outbound_port = outbound_port

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

    def _idempotency_repository(self) -> Any:
        if self._idempotency_repo is not None:
            return self._idempotency_repo
        from product_persistence.repositories.sqlite_outbound_idempotency_repository import (
            OutboundIdempotencyRepositorySQLite,
        )

        return OutboundIdempotencyRepositorySQLite(
            db_manager=self._db_manager or get_product_db_manager()
        )

    def _outbound_port_instance(self) -> AssistedOutboundPort:
        if self._outbound_port is not None:
            return self._outbound_port
        return DryRunAssistedOutboundPort()

    @staticmethod
    def _idempotency_key(pending_assisted_id: str) -> str:
        return f"{_IDEMPOTENCY_KEY_PREFIX}{pending_assisted_id}"

    def _write_merchant_confirm_snapshot(
        self,
        pending: Any,
        *,
        current_time: str,
    ) -> None:
        if not flags.should_write_send_decision():
            return
        from product_persistence.models import SendDecisionSnapshotRow

        session = (self._db_manager or get_product_db_manager()).get_product_session()
        try:
            session.add(
                SendDecisionSnapshotRow(
                    send_decision_id=str(uuid4()),
                    reply_log_id=pending.reply_log_id,
                    workspace_id=pending.workspace_id,
                    shop_id=pending.shop_id,
                    account_id=pending.account_id,
                    platform_id=pending.platform_id,
                    inbound_message_id=pending.inbound_message_id,
                    decision_phase="merchant_confirm",
                    intent=pending.intent,
                    intent_bucket=pending.intent_bucket,
                    risk_level=pending.risk_level,
                    reply_mode="assisted",
                    workspace_pause=0,
                    shop_pause=0,
                    product_gate_enabled=1,
                    allowed_to_generate=1,
                    allowed_to_send=1,
                    send_mode="assisted_only",
                    decision_source="assisted_reply_service",
                    created_at=current_time,
                )
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _approve_after_guard_passed(
        self,
        pending: Any,
        *,
        actor_user_id: str,
        role: str,
        resolved_final_reply: str,
        current_time: str,
    ) -> AssistedServiceResult:
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
            after_state={"status": pending.status},
        )
        self._audit_repository().append_audit_log(
            workspace_id=pending.workspace_id,
            shop_id=pending.shop_id,
            account_id=pending.account_id,
            platform_id=pending.platform_id,
            actor_user_id=actor_user_id,
            actor_role=role,
            action="final_guard_passed",
            target_type="pending_assisted",
            target_id=pending.pending_assisted_id,
            reply_log_id=pending.reply_log_id,
            pending_assisted_id=pending.pending_assisted_id,
            before_state={"status": pending.status},
            after_state={"status": pending.status, "guard": "passed"},
        )
        try:
            self._write_merchant_confirm_snapshot(pending, current_time=current_time)
        except Exception as exc:
            return AssistedServiceResult(
                success=False,
                action="approve_pending",
                status="snapshot_failed",
                pending_assisted_id=pending.pending_assisted_id,
                reply_log_id=pending.reply_log_id,
                audit_log_id=audit_id,
                final_guard_allowed=True,
                reason="send_decision_snapshot_failed",
                error=str(exc),
            )

        if not flags.is_assisted_send_enabled():
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

        if not flags.is_assisted_send_dry_run():
            return AssistedServiceResult(
                success=False,
                action="approve_pending",
                status="live_send_not_implemented",
                pending_assisted_id=pending.pending_assisted_id,
                reply_log_id=pending.reply_log_id,
                audit_log_id=audit_id,
                final_guard_allowed=True,
                reason="live_send_not_implemented",
            )

        if not flags.is_assisted_dry_run_outbound_enabled():
            return AssistedServiceResult(
                success=False,
                action="approve_pending",
                status="dry_run_not_configured",
                pending_assisted_id=pending.pending_assisted_id,
                reply_log_id=pending.reply_log_id,
                audit_log_id=audit_id,
                final_guard_allowed=True,
                reason="outbound_idempotency_persistence_disabled",
            )

        if not flags.is_assisted_send_test_shop_allowlisted(pending.shop_id):
            return AssistedServiceResult(
                success=False,
                action="approve_pending",
                status="allowlist_denied",
                pending_assisted_id=pending.pending_assisted_id,
                reply_log_id=pending.reply_log_id,
                audit_log_id=audit_id,
                final_guard_allowed=True,
                reason="test_shop_not_allowlisted",
            )

        idempotency_key = self._idempotency_key(pending.pending_assisted_id)
        acquire_result = self._idempotency_repository().acquire(
            idempotency_key,
            workspace_id=pending.workspace_id,
            shop_id=pending.shop_id,
            account_id=pending.account_id,
            platform_id=pending.platform_id,
            pending_assisted_id=pending.pending_assisted_id,
            reply_log_id=pending.reply_log_id,
            metadata={"dry_run": True},
        )
        if not acquire_result.acquired:
            reason = acquire_result.reason or "idempotency_not_acquired"
            status_map = {
                "already_sent": "idempotency_already_sent",
                "already_in_progress": "idempotency_in_progress",
                "manual_review_required": "idempotency_manual_review_required",
            }
            return AssistedServiceResult(
                success=False,
                action="approve_pending",
                status=status_map.get(reason, "idempotency_denied"),
                pending_assisted_id=pending.pending_assisted_id,
                reply_log_id=pending.reply_log_id,
                audit_log_id=audit_id,
                final_guard_allowed=True,
                reason=reason,
            )

        trace_id = f"assisted-dry-run:{pending.pending_assisted_id}:{current_time}"
        outbound_result = self._outbound_port_instance().send(
            build_assisted_outbound_request(
                workspace_id=pending.workspace_id,
                shop_id=pending.shop_id,
                account_id=pending.account_id,
                platform_id=pending.platform_id,
                buyer_id=pending.buyer_id,
                pending_assisted_id=pending.pending_assisted_id,
                reply_log_id=pending.reply_log_id,
                final_reply=resolved_final_reply,
                idempotency_key=idempotency_key,
                trace_id=trace_id,
                dry_run=True,
            )
        )
        if not outbound_result.success or not outbound_result.would_send:
            return AssistedServiceResult(
                success=False,
                action="approve_pending",
                status="dry_run_rejected",
                pending_assisted_id=pending.pending_assisted_id,
                reply_log_id=pending.reply_log_id,
                audit_log_id=audit_id,
                final_guard_allowed=True,
                reason=outbound_result.error_code or "dry_run_rejected",
                error=outbound_result.error_message,
            )

        dry_run_audit_id = self._audit_repository().append_audit_log(
            workspace_id=pending.workspace_id,
            shop_id=pending.shop_id,
            account_id=pending.account_id,
            platform_id=pending.platform_id,
            actor_user_id=actor_user_id,
            actor_role=role,
            action="assisted_dry_run_would_send",
            target_type="pending_assisted",
            target_id=pending.pending_assisted_id,
            reply_log_id=pending.reply_log_id,
            pending_assisted_id=pending.pending_assisted_id,
            before_state={"status": pending.status},
            after_state={
                "status": pending.status,
                "dry_run": True,
                "would_send": True,
                "platform_status": outbound_result.platform_status,
            },
            reason="dry_run_would_send",
        )
        return AssistedServiceResult(
            success=True,
            action="approve_pending",
            status="dry_run_would_send",
            pending_assisted_id=pending.pending_assisted_id,
            reply_log_id=pending.reply_log_id,
            audit_log_id=dry_run_audit_id,
            final_guard_allowed=True,
            reason="dry_run_would_send",
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

        return self._approve_after_guard_passed(
            pending,
            actor_user_id=actor_user_id,
            role=role,
            resolved_final_reply=resolved_final_reply,
            current_time=current_time,
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

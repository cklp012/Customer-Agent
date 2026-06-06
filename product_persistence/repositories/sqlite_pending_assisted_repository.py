"""SQLite PendingAssisted repository (Phase 14q) — schema skeleton only, no send."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, Tuple
from uuid import uuid4

from product_persistence.db_manager import ProductDbManager, get_product_db_manager
from product_persistence.models import PendingAssistedReplyDTO, PendingAssistedReplyRow

_DEFAULT_STATUS = "pending"
_DEFAULT_CREATED_BY = "system"
_DEFAULT_LIST_STATUSES = ("pending", "failed")
_SORT_ALLOWLIST = frozenset(
    {"created_at", "updated_at", "expires_at", "risk_level", "status"}
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _default_expires_at(hours: int = 24) -> str:
    return (
        datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=hours)
    ).isoformat()


def _dto_from_row(row: PendingAssistedReplyRow) -> PendingAssistedReplyDTO:
    return PendingAssistedReplyDTO(
        pending_assisted_id=row.pending_assisted_id,
        reply_log_id=row.reply_log_id or "",
        workspace_id=row.workspace_id or "",
        shop_id=row.shop_id or "",
        account_id=row.account_id or "",
        platform_id=row.platform_id or "",
        buyer_id=row.buyer_id or "",
        buyer_message=row.buyer_message,
        ai_suggested_reply=row.ai_suggested_reply,
        status=row.status,
        intent=row.intent or "",
        intent_bucket=row.intent_bucket or "",
        risk_level=row.risk_level or "",
        expires_at=row.expires_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
        merchant_edited_reply=row.merchant_edited_reply,
        final_reply=row.final_reply,
        blocked_reason=row.blocked_reason,
        human_takeover_reason=row.human_takeover_reason,
        created_by=row.created_by,
        approved_by=row.approved_by,
        rejected_by=row.rejected_by,
        conversation_id=row.conversation_id,
        inbound_message_id=row.inbound_message_id,
    )


class PendingAssistedRepositorySQLite:
    """PendingAssisted persistence skeleton — no approve/send/outbound paths."""

    def __init__(self, db_manager: Optional[ProductDbManager] = None) -> None:
        self._db_manager = db_manager or get_product_db_manager()

    def create_pending(
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
        intent_bucket: str,
        risk_level: str,
        status: str = _DEFAULT_STATUS,
        pending_assisted_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        inbound_message_id: Optional[str] = None,
        merchant_edited_reply: Optional[str] = None,
        blocked_reason: Optional[str] = None,
        human_takeover_reason: Optional[str] = None,
        created_by: Optional[str] = None,
        expires_at: Optional[str] = None,
        created_at: Optional[str] = None,
        **_kwargs: Any,
    ) -> str:
        pending_id = pending_assisted_id or str(uuid4())
        now = created_at or _utc_now_iso()
        row = PendingAssistedReplyRow(
            pending_assisted_id=pending_id,
            reply_log_id=reply_log_id,
            workspace_id=workspace_id,
            shop_id=shop_id,
            account_id=account_id,
            platform_id=platform_id,
            buyer_id=buyer_id,
            conversation_id=conversation_id,
            inbound_message_id=inbound_message_id,
            buyer_message=buyer_message,
            ai_suggested_reply=ai_suggested_reply,
            merchant_edited_reply=merchant_edited_reply,
            final_reply=None,
            status=status or _DEFAULT_STATUS,
            intent=intent,
            intent_bucket=intent_bucket,
            risk_level=risk_level,
            blocked_reason=blocked_reason,
            human_takeover_reason=human_takeover_reason,
            created_by=created_by or _DEFAULT_CREATED_BY,
            approved_by=None,
            rejected_by=None,
            expires_at=expires_at or _default_expires_at(),
            created_at=now,
            updated_at=now,
        )
        session = self._db_manager.get_product_session()
        try:
            existing = session.get(PendingAssistedReplyRow, pending_id)
            if existing is not None:
                raise ValueError(
                    f"pending_assisted_id already exists: {pending_id}"
                )
            session.add(row)
            session.commit()
            return pending_id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_pending(
        self,
        pending_assisted_id: str,
    ) -> Optional[PendingAssistedReplyDTO]:
        session = self._db_manager.get_product_session()
        try:
            row = session.get(PendingAssistedReplyRow, pending_assisted_id)
            if row is None:
                return None
            return _dto_from_row(row)
        finally:
            session.close()

    def list_pending(
        self,
        *,
        workspace_id: Optional[str] = None,
        shop_id: Optional[str] = None,
        account_id: Optional[str] = None,
        platform_id: Optional[str] = None,
        status: Optional[str] = None,
        statuses: Optional[Tuple[str, ...]] = None,
        buyer_id: Optional[str] = None,
        intent_category: Optional[str] = None,
        risk_level: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        updated_after: Optional[str] = None,
        updated_before: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 100,
    ) -> Tuple[List[PendingAssistedReplyDTO], int]:
        session = self._db_manager.get_product_session()
        try:
            from sqlalchemy import func, select

            stmt = select(PendingAssistedReplyRow)
            if workspace_id is not None:
                stmt = stmt.where(PendingAssistedReplyRow.workspace_id == workspace_id)
            if shop_id is not None:
                stmt = stmt.where(PendingAssistedReplyRow.shop_id == shop_id)
            if account_id is not None:
                stmt = stmt.where(PendingAssistedReplyRow.account_id == account_id)
            if platform_id is not None:
                stmt = stmt.where(PendingAssistedReplyRow.platform_id == platform_id)
            if buyer_id is not None:
                stmt = stmt.where(PendingAssistedReplyRow.buyer_id == buyer_id)
            if intent_category is not None:
                stmt = stmt.where(
                    (PendingAssistedReplyRow.intent_bucket == intent_category)
                    | (PendingAssistedReplyRow.intent == intent_category)
                )
            if risk_level is not None:
                stmt = stmt.where(PendingAssistedReplyRow.risk_level == risk_level)
            if status is not None:
                stmt = stmt.where(PendingAssistedReplyRow.status == status)
            elif statuses is not None:
                stmt = stmt.where(PendingAssistedReplyRow.status.in_(statuses))
            else:
                stmt = stmt.where(
                    PendingAssistedReplyRow.status.in_(_DEFAULT_LIST_STATUSES)
                )
            if created_after is not None:
                stmt = stmt.where(PendingAssistedReplyRow.created_at >= created_after)
            if created_before is not None:
                stmt = stmt.where(PendingAssistedReplyRow.created_at <= created_before)
            if updated_after is not None:
                stmt = stmt.where(PendingAssistedReplyRow.updated_at >= updated_after)
            if updated_before is not None:
                stmt = stmt.where(PendingAssistedReplyRow.updated_at <= updated_before)

            sort_field = sort_by if sort_by in _SORT_ALLOWLIST else "created_at"
            sort_column = getattr(PendingAssistedReplyRow, sort_field)
            if sort_order.lower() == "asc":
                stmt = stmt.order_by(sort_column.asc())
            else:
                stmt = stmt.order_by(sort_column.desc())

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = int(session.scalar(count_stmt) or 0)

            safe_offset = max(0, int(offset or 0))
            safe_limit = min(max(1, int(limit or 100)), 100)
            stmt = stmt.offset(safe_offset).limit(safe_limit)
            rows = session.scalars(stmt).all()
            return ([_dto_from_row(row) for row in rows], total)
        finally:
            session.close()

    def mark_status(
        self,
        pending_assisted_id: str,
        status: str,
        *,
        approved_by: Optional[str] = None,
        rejected_by: Optional[str] = None,
        final_reply: Optional[str] = None,
    ) -> bool:
        """Update status fields only — no approve/send/final-guard semantics."""
        session = self._db_manager.get_product_session()
        try:
            row = session.get(PendingAssistedReplyRow, pending_assisted_id)
            if row is None:
                return False
            row.status = status
            row.updated_at = _utc_now_iso()
            if approved_by is not None:
                row.approved_by = approved_by
            if rejected_by is not None:
                row.rejected_by = rejected_by
            if final_reply is not None:
                row.final_reply = final_reply
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

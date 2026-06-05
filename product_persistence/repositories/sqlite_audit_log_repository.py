"""SQLite AuditLog repository (Phase 14q) — append-only, no send."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional
from uuid import uuid4

from product_persistence.db_manager import ProductDbManager, get_product_db_manager
from product_persistence.models import AuditLogDTO, AuditLogRow

_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "secret",
        "authorization",
        "cookie",
        "session_id",
    }
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sanitize_state(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        sanitized = {
            key: val
            for key, val in value.items()
            if str(key).lower() not in _SENSITIVE_KEYS
        }
        return json.dumps(sanitized, ensure_ascii=False, sort_keys=True)
    return json.dumps(value, ensure_ascii=False, default=str)


def _dto_from_row(row: AuditLogRow) -> AuditLogDTO:
    return AuditLogDTO(
        audit_log_id=row.audit_log_id,
        workspace_id=row.workspace_id or "",
        shop_id=row.shop_id,
        account_id=row.account_id,
        platform_id=row.platform_id,
        actor_user_id=row.actor_user_id,
        actor_role=row.actor_role,
        action=row.action,
        target_type=row.target_type,
        target_id=row.target_id,
        reply_log_id=row.reply_log_id,
        pending_assisted_id=row.pending_assisted_id,
        before_state=row.before_state,
        after_state=row.after_state,
        reason=row.reason,
        ip_address=row.ip_address,
        user_agent=row.user_agent,
        created_at=row.created_at,
    )


class AuditLogRepositorySQLite:
    """Append-only audit persistence — no update/delete/send paths."""

    def __init__(self, db_manager: Optional[ProductDbManager] = None) -> None:
        self._db_manager = db_manager or get_product_db_manager()

    def append_audit_log(
        self,
        *,
        workspace_id: str,
        actor_user_id: str,
        actor_role: str,
        action: str,
        target_type: str,
        target_id: str,
        audit_log_id: Optional[str] = None,
        shop_id: Optional[str] = None,
        account_id: Optional[str] = None,
        platform_id: Optional[str] = None,
        reply_log_id: Optional[str] = None,
        pending_assisted_id: Optional[str] = None,
        before_state: Any = None,
        after_state: Any = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        created_at: Optional[str] = None,
        **_kwargs: Any,
    ) -> str:
        log_id = audit_log_id or str(uuid4())
        row = AuditLogRow(
            audit_log_id=log_id,
            workspace_id=workspace_id,
            shop_id=shop_id,
            account_id=account_id,
            platform_id=platform_id,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            action=action,
            target_type=target_type,
            target_id=target_id,
            reply_log_id=reply_log_id,
            pending_assisted_id=pending_assisted_id,
            before_state=_sanitize_state(before_state),
            after_state=_sanitize_state(after_state),
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=created_at or _utc_now_iso(),
        )
        session = self._db_manager.get_product_session()
        try:
            existing = session.get(AuditLogRow, log_id)
            if existing is not None:
                raise ValueError(f"audit_log_id already exists: {log_id}")
            session.add(row)
            session.commit()
            return log_id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def list_audit_logs(
        self,
        *,
        workspace_id: Optional[str] = None,
        shop_id: Optional[str] = None,
        actor_user_id: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLogDTO]:
        session = self._db_manager.get_product_session()
        try:
            from sqlalchemy import select

            stmt = select(AuditLogRow)
            if workspace_id is not None:
                stmt = stmt.where(AuditLogRow.workspace_id == workspace_id)
            if shop_id is not None:
                stmt = stmt.where(AuditLogRow.shop_id == shop_id)
            if actor_user_id is not None:
                stmt = stmt.where(AuditLogRow.actor_user_id == actor_user_id)
            if target_type is not None:
                stmt = stmt.where(AuditLogRow.target_type == target_type)
            if target_id is not None:
                stmt = stmt.where(AuditLogRow.target_id == target_id)
            if action is not None:
                stmt = stmt.where(AuditLogRow.action == action)
            stmt = stmt.order_by(AuditLogRow.created_at.desc()).limit(limit)
            rows = session.scalars(stmt).all()
            return [_dto_from_row(row) for row in rows]
        finally:
            session.close()

    def get_audit_log(self, audit_log_id: str) -> Optional[AuditLogDTO]:
        session = self._db_manager.get_product_session()
        try:
            row = session.get(AuditLogRow, audit_log_id)
            if row is None:
                return None
            return _dto_from_row(row)
        finally:
            session.close()

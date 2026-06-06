"""SQLite outbound idempotency repository (Phase 15b) — lock skeleton only, no send."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional

from sqlalchemy.exc import IntegrityError

from product_persistence.db_manager import ProductDbManager, get_product_db_manager
from product_persistence.models import OutboundIdempotencyRow

_STATUS_IN_PROGRESS = "in_progress"
_STATUS_SUCCEEDED = "succeeded"
_STATUS_FAILED = "failed"
_DEFAULT_OPERATION_TYPE = "assisted_send"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json_metadata(value: Optional[Mapping[str, Any]]) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(dict(value), ensure_ascii=False, sort_keys=True)


def _parse_metadata(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        return None
    return parsed


@dataclass(frozen=True)
class IdempotencyAcquireResult:
    acquired: bool
    status: str
    reason: Optional[str]
    idempotency_key: str
    existing_status: Optional[str] = None
    attempt_count: Optional[int] = None


@dataclass(frozen=True)
class IdempotencyRecord:
    idempotency_key: str
    workspace_id: str
    shop_id: str
    account_id: str
    platform_id: str
    pending_assisted_id: str
    reply_log_id: str
    operation_type: str
    status: str
    attempt_count: int
    provider_message_id: Optional[str]
    platform_status: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    locked_at: Optional[str]
    completed_at: Optional[str]
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = None


def _record_from_row(row: OutboundIdempotencyRow) -> IdempotencyRecord:
    return IdempotencyRecord(
        idempotency_key=row.idempotency_key,
        workspace_id=row.workspace_id or "",
        shop_id=row.shop_id or "",
        account_id=row.account_id or "",
        platform_id=row.platform_id or "",
        pending_assisted_id=row.pending_assisted_id or "",
        reply_log_id=row.reply_log_id or "",
        operation_type=row.operation_type,
        status=row.status,
        attempt_count=row.attempt_count,
        provider_message_id=row.provider_message_id,
        platform_status=row.platform_status,
        error_code=row.error_code,
        error_message=row.error_message,
        locked_at=row.locked_at,
        completed_at=row.completed_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
        metadata=_parse_metadata(row.metadata_json),
    )


def _acquire_denied(
    *,
    idempotency_key: str,
    existing_status: str,
    attempt_count: int,
    reason: str,
) -> IdempotencyAcquireResult:
    return IdempotencyAcquireResult(
        acquired=False,
        status=existing_status,
        reason=reason,
        idempotency_key=idempotency_key,
        existing_status=existing_status,
        attempt_count=attempt_count,
    )


class OutboundIdempotencyRepositorySQLite:
    """Outbound idempotency lock persistence — no send/outbound paths."""

    def __init__(self, db_manager: Optional[ProductDbManager] = None) -> None:
        self._db_manager = db_manager or get_product_db_manager()

    def acquire(
        self,
        idempotency_key: str,
        *,
        workspace_id: str,
        shop_id: str,
        account_id: str,
        platform_id: str,
        pending_assisted_id: str,
        reply_log_id: str,
        operation_type: str = _DEFAULT_OPERATION_TYPE,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> IdempotencyAcquireResult:
        session = self._db_manager.get_product_session()
        try:
            existing = session.get(OutboundIdempotencyRow, idempotency_key)
            if existing is not None:
                return self._deny_for_existing(existing)

            now = _utc_now_iso()
            row = OutboundIdempotencyRow(
                idempotency_key=idempotency_key,
                workspace_id=workspace_id,
                shop_id=shop_id,
                account_id=account_id,
                platform_id=platform_id,
                pending_assisted_id=pending_assisted_id,
                reply_log_id=reply_log_id,
                operation_type=operation_type,
                status=_STATUS_IN_PROGRESS,
                attempt_count=1,
                locked_at=now,
                created_at=now,
                updated_at=now,
                metadata_json=_json_metadata(metadata),
            )
            session.add(row)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                raced = session.get(OutboundIdempotencyRow, idempotency_key)
                if raced is None:
                    raise
                return self._deny_for_existing(raced)

            return IdempotencyAcquireResult(
                acquired=True,
                status=_STATUS_IN_PROGRESS,
                reason=None,
                idempotency_key=idempotency_key,
                existing_status=None,
                attempt_count=1,
            )
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _deny_for_existing(
        self,
        row: OutboundIdempotencyRow,
    ) -> IdempotencyAcquireResult:
        if row.status == _STATUS_SUCCEEDED:
            reason = "already_sent"
        elif row.status == _STATUS_IN_PROGRESS:
            reason = "already_in_progress"
        elif row.status == _STATUS_FAILED:
            reason = "manual_review_required"
        else:
            reason = "invalid_status"
        return _acquire_denied(
            idempotency_key=row.idempotency_key,
            existing_status=row.status,
            attempt_count=row.attempt_count,
            reason=reason,
        )

    def get(self, idempotency_key: str) -> Optional[IdempotencyRecord]:
        session = self._db_manager.get_product_session()
        try:
            row = session.get(OutboundIdempotencyRow, idempotency_key)
            if row is None:
                return None
            return _record_from_row(row)
        finally:
            session.close()

    def mark_succeeded(
        self,
        idempotency_key: str,
        *,
        provider_message_id: Optional[str] = None,
        platform_status: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> IdempotencyRecord:
        return self._mark_terminal(
            idempotency_key,
            target_status=_STATUS_SUCCEEDED,
            provider_message_id=provider_message_id,
            platform_status=platform_status,
            metadata=metadata,
        )

    def mark_failed(
        self,
        idempotency_key: str,
        *,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        platform_status: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> IdempotencyRecord:
        return self._mark_terminal(
            idempotency_key,
            target_status=_STATUS_FAILED,
            error_code=error_code,
            error_message=error_message,
            platform_status=platform_status,
            metadata=metadata,
        )

    def _mark_terminal(
        self,
        idempotency_key: str,
        *,
        target_status: str,
        provider_message_id: Optional[str] = None,
        platform_status: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> IdempotencyRecord:
        session = self._db_manager.get_product_session()
        try:
            row = session.get(OutboundIdempotencyRow, idempotency_key)
            if row is None:
                raise ValueError(f"idempotency_key not found: {idempotency_key}")
            if row.status == _STATUS_SUCCEEDED:
                raise ValueError(
                    f"cannot transition from succeeded to {target_status}"
                )
            if row.status == _STATUS_FAILED:
                raise ValueError(f"cannot transition from failed to {target_status}")
            if row.status != _STATUS_IN_PROGRESS:
                raise ValueError(
                    f"cannot transition from {row.status} to {target_status}"
                )

            now = _utc_now_iso()
            row.status = target_status
            row.completed_at = now
            row.updated_at = now
            if provider_message_id is not None:
                row.provider_message_id = provider_message_id
            if platform_status is not None:
                row.platform_status = platform_status
            if error_code is not None:
                row.error_code = error_code
            if error_message is not None:
                row.error_message = error_message
            if metadata is not None:
                row.metadata_json = _json_metadata(metadata)

            session.commit()
            session.refresh(row)
            return _record_from_row(row)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

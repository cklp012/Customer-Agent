"""SQLite dashboard action idempotency repository (Phase 15j) — no send."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional

from sqlalchemy.exc import IntegrityError

from product_persistence.db_manager import ProductDbManager, get_product_db_manager
from product_persistence.models import DashboardActionIdempotencyRow

_STATUS_IN_PROGRESS = "in_progress"
_STATUS_COMPLETED = "completed"
_STATUS_FAILED = "failed"
_STATUS_CONFLICT = "conflict"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json_response(value: Optional[Mapping[str, Any]]) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(dict(value), ensure_ascii=False, sort_keys=True)


def _parse_response(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        return None
    return parsed


@dataclass(frozen=True)
class ActionIdempotencyAcquireResult:
    acquired: bool
    status: str
    reason: Optional[str]
    client_request_id: str
    existing_response: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ActionIdempotencyRecord:
    client_request_id: str
    workspace_id: str
    shop_id: str
    actor_user_id: str
    actor_role: str
    pending_assisted_id: str
    action: str
    payload_hash: str
    status: str
    response: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str


def _record_from_row(row: DashboardActionIdempotencyRow) -> ActionIdempotencyRecord:
    return ActionIdempotencyRecord(
        client_request_id=row.client_request_id,
        workspace_id=row.workspace_id or "",
        shop_id=row.shop_id or "",
        actor_user_id=row.actor_user_id or "",
        actor_role=row.actor_role or "",
        pending_assisted_id=row.pending_assisted_id or "",
        action=row.action,
        payload_hash=row.payload_hash,
        status=row.status,
        response=_parse_response(row.response_json),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class ActionIdempotencyRepositorySQLite:
    """Dashboard action idempotency persistence — no send/outbound paths."""

    def __init__(self, db_manager: Optional[ProductDbManager] = None) -> None:
        self._db_manager = db_manager or get_product_db_manager()

    @staticmethod
    def compute_payload_hash(payload: Mapping[str, Any]) -> str:
        canonical = json.dumps(
            dict(payload),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def acquire(
        self,
        client_request_id: str,
        *,
        workspace_id: str,
        shop_id: str,
        actor_user_id: str,
        actor_role: str,
        pending_assisted_id: str,
        action: str,
        payload: Mapping[str, Any],
    ) -> ActionIdempotencyAcquireResult:
        payload_hash = self.compute_payload_hash(payload)
        session = self._db_manager.get_product_session()
        try:
            existing = session.get(DashboardActionIdempotencyRow, client_request_id)
            if existing is not None:
                return self._deny_for_existing(existing, payload_hash)

            now = _utc_now_iso()
            row = DashboardActionIdempotencyRow(
                client_request_id=client_request_id,
                workspace_id=workspace_id,
                shop_id=shop_id,
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                pending_assisted_id=pending_assisted_id,
                action=action,
                payload_hash=payload_hash,
                status=_STATUS_IN_PROGRESS,
                response_json=None,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                raced = session.get(DashboardActionIdempotencyRow, client_request_id)
                if raced is None:
                    raise
                return self._deny_for_existing(raced, payload_hash)

            return ActionIdempotencyAcquireResult(
                acquired=True,
                status=_STATUS_IN_PROGRESS,
                reason=None,
                client_request_id=client_request_id,
                existing_response=None,
            )
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _deny_for_existing(
        self,
        row: DashboardActionIdempotencyRow,
        payload_hash: str,
    ) -> ActionIdempotencyAcquireResult:
        existing_response = _parse_response(row.response_json)
        if row.payload_hash != payload_hash:
            return ActionIdempotencyAcquireResult(
                acquired=False,
                status=_STATUS_CONFLICT,
                reason="client_request_conflict",
                client_request_id=row.client_request_id,
                existing_response=existing_response,
            )

        if row.status == _STATUS_COMPLETED:
            return ActionIdempotencyAcquireResult(
                acquired=False,
                status=_STATUS_COMPLETED,
                reason="replay_completed",
                client_request_id=row.client_request_id,
                existing_response=existing_response,
            )

        if row.status == _STATUS_IN_PROGRESS:
            return ActionIdempotencyAcquireResult(
                acquired=False,
                status=_STATUS_IN_PROGRESS,
                reason="already_in_progress",
                client_request_id=row.client_request_id,
                existing_response=existing_response,
            )

        if row.status == _STATUS_FAILED:
            return ActionIdempotencyAcquireResult(
                acquired=False,
                status=_STATUS_FAILED,
                reason="replay_failed",
                client_request_id=row.client_request_id,
                existing_response=existing_response,
            )

        return ActionIdempotencyAcquireResult(
            acquired=False,
            status=row.status,
            reason="invalid_status",
            client_request_id=row.client_request_id,
            existing_response=existing_response,
        )

    def complete(
        self,
        client_request_id: str,
        response: Mapping[str, Any],
    ) -> ActionIdempotencyRecord:
        session = self._db_manager.get_product_session()
        try:
            row = session.get(DashboardActionIdempotencyRow, client_request_id)
            if row is None:
                raise ValueError(f"client_request_id not found: {client_request_id}")
            if row.status != _STATUS_IN_PROGRESS:
                raise ValueError(
                    f"cannot complete from status {row.status} for {client_request_id}"
                )

            now = _utc_now_iso()
            row.status = _STATUS_COMPLETED
            row.response_json = _json_response(response)
            row.updated_at = now
            session.commit()
            session.refresh(row)
            return _record_from_row(row)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def fail(
        self,
        client_request_id: str,
        response: Optional[Mapping[str, Any]] = None,
    ) -> ActionIdempotencyRecord:
        session = self._db_manager.get_product_session()
        try:
            row = session.get(DashboardActionIdempotencyRow, client_request_id)
            if row is None:
                raise ValueError(f"client_request_id not found: {client_request_id}")
            if row.status not in {_STATUS_IN_PROGRESS, _STATUS_FAILED}:
                raise ValueError(
                    f"cannot fail from status {row.status} for {client_request_id}"
                )

            now = _utc_now_iso()
            row.status = _STATUS_FAILED
            if response is not None:
                row.response_json = _json_response(response)
            row.updated_at = now
            session.commit()
            session.refresh(row)
            return _record_from_row(row)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get(self, client_request_id: str) -> Optional[ActionIdempotencyRecord]:
        session = self._db_manager.get_product_session()
        try:
            row = session.get(DashboardActionIdempotencyRow, client_request_id)
            if row is None:
                return None
            return _record_from_row(row)
        finally:
            session.close()

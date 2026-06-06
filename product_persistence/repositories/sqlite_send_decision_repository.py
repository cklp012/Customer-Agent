"""SQLite SendDecision snapshot repository (Phase 14n) — append-only."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from Message.gates.preview_log import PreviewLogRecord
from product_persistence.db_manager import ProductDbManager, get_product_db_manager
from product_persistence.models import SendDecisionSnapshotDTO, SendDecisionSnapshotRow


def _enum_value(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _bool_int(value: Any) -> int:
    return 1 if bool(value) else 0


def _snapshot_row_from_preview_record(
    record: PreviewLogRecord,
    *,
    decision_phase: str,
    send_decision_id: Optional[str] = None,
) -> SendDecisionSnapshotRow:
    meta = record.metadata if isinstance(record.metadata, dict) else {}
    cls = record.classification
    decision = record.send_decision
    created_at = record.created_at or ""

    intent = _enum_value(getattr(cls, "intent", None), "unknown")
    intent_bucket = _enum_value(getattr(cls, "intent_bucket", None), "uncertain")
    risk_level = _enum_value(getattr(cls, "risk_level", None), "low")
    decision_source = (
        getattr(decision, "decision_source", None)
        or getattr(cls, "source", None)
        or "unknown"
    )

    return SendDecisionSnapshotRow(
        send_decision_id=send_decision_id or str(uuid4()),
        reply_log_id=record.reply_log_id,
        workspace_id=record.workspace_id or meta.get("workspace_id"),
        shop_id=record.shop_id or meta.get("shop_id"),
        account_id=record.account_id or meta.get("account_id"),
        platform_id=record.platform_id or meta.get("platform_id") or meta.get("platform"),
        inbound_message_id=meta.get("message_id"),
        decision_phase=decision_phase,
        intent=intent,
        intent_bucket=intent_bucket,
        intent_confidence=float(getattr(cls, "confidence", 0.0) or 0.0),
        risk_level=risk_level,
        reply_mode=_enum_value(getattr(decision, "reply_mode", None), "preview"),
        workspace_pause=_bool_int(getattr(decision, "workspace_pause", False)),
        shop_pause=_bool_int(getattr(decision, "shop_pause", False)),
        product_gate_enabled=_bool_int(getattr(decision, "product_gate_enabled", False)),
        allowed_to_generate=_bool_int(getattr(decision, "allowed_to_generate", False)),
        allowed_to_send=_bool_int(getattr(decision, "allowed_to_send", False)),
        send_mode=_enum_value(getattr(decision, "send_mode", None), "preview_only"),
        blocked_reason=getattr(decision, "blocked_reason", None),
        human_takeover_reason=getattr(decision, "human_takeover_reason", None),
        decision_source=str(decision_source),
        created_at=created_at,
    )


def _dto_from_row(row: SendDecisionSnapshotRow) -> SendDecisionSnapshotDTO:
    return SendDecisionSnapshotDTO(
        send_decision_id=row.send_decision_id,
        reply_log_id=row.reply_log_id,
        decision_phase=row.decision_phase,
        intent=row.intent or "",
        send_mode=row.send_mode or "",
        intent_bucket=row.intent_bucket,
        risk_level=row.risk_level,
        allowed_to_send=bool(row.allowed_to_send),
        allowed_to_generate=bool(row.allowed_to_generate),
        decision_source=row.decision_source,
        created_at=row.created_at,
    )


class SendDecisionRepositorySQLite:
    """Append-only SendDecision snapshot persistence — no send paths."""

    def __init__(self, db_manager: Optional[ProductDbManager] = None) -> None:
        self._db_manager = db_manager or get_product_db_manager()

    def create_snapshot(
        self,
        preview_record: PreviewLogRecord,
        *,
        decision_phase: str = "ai_preview",
    ) -> str:
        row = _snapshot_row_from_preview_record(
            preview_record,
            decision_phase=decision_phase,
        )
        session = self._db_manager.get_product_session()
        try:
            session.add(row)
            session.commit()
            return row.send_decision_id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def list_snapshots_by_reply_log(
        self,
        reply_log_id: str,
    ) -> List[SendDecisionSnapshotDTO]:
        session = self._db_manager.get_product_session()
        try:
            from sqlalchemy import select

            stmt = (
                select(SendDecisionSnapshotRow)
                .where(SendDecisionSnapshotRow.reply_log_id == reply_log_id)
                .order_by(SendDecisionSnapshotRow.created_at.asc())
            )
            rows = session.scalars(stmt).all()
            return [_dto_from_row(row) for row in rows]
        finally:
            session.close()

    def latest_for_reply_log(
        self,
        reply_log_id: str,
    ) -> Optional[Dict[str, Any]]:
        session = self._db_manager.get_product_session()
        try:
            from sqlalchemy import select

            stmt = (
                select(SendDecisionSnapshotRow)
                .where(SendDecisionSnapshotRow.reply_log_id == reply_log_id)
                .order_by(SendDecisionSnapshotRow.created_at.desc())
                .limit(1)
            )
            row = session.scalars(stmt).first()
            if row is None:
                return None
            return {
                "send_decision_id": row.send_decision_id,
                "reply_log_id": row.reply_log_id,
                "decision_phase": row.decision_phase,
                "intent": row.intent,
                "intent_bucket": row.intent_bucket,
                "intent_confidence": row.intent_confidence,
                "risk_level": row.risk_level,
                "reply_mode": row.reply_mode,
                "allowed_to_send": bool(row.allowed_to_send),
                "allowed_to_generate": bool(row.allowed_to_generate),
                "send_mode": row.send_mode,
                "blocked_reason": row.blocked_reason,
                "human_takeover_reason": row.human_takeover_reason,
                "decision_source": row.decision_source,
                "created_at": row.created_at,
            }
        finally:
            session.close()

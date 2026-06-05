"""SQLite ReplyLog repository (Phase 14l) — product_gate.db only."""

from __future__ import annotations

from typing import Any, List, Optional, Union

from Message.gates.preview_log import PreviewLogRecord
from Message.gates.reply_log_projection import (
    PreviewReplyLogListItem,
    project_preview_record_to_reply_log,
)
from product_persistence.db_manager import ProductDbManager, get_product_db_manager
from product_persistence.models import ReplyLogDTO, ReplyLogRow


def _enum_value(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _row_from_preview_record(record: PreviewLogRecord) -> ReplyLogRow:
    projected = project_preview_record_to_reply_log(record)
    meta = record.metadata if isinstance(record.metadata, dict) else {}
    reply_mode = _enum_value(getattr(record.send_decision, "reply_mode", None), "preview")
    created_at = projected.created_at or record.created_at
    updated_at = created_at
    product_gate_enabled = 1 if getattr(record.send_decision, "product_gate_enabled", False) else 0

    return ReplyLogRow(
        reply_log_id=projected.reply_log_id,
        workspace_id=projected.workspace_id,
        shop_id=projected.shop_id,
        account_id=projected.account_id,
        platform_id=projected.platform_id,
        buyer_id=projected.buyer_id,
        conversation_id=meta.get("conversation_id"),
        inbound_message_id=meta.get("message_id"),
        buyer_message=projected.buyer_message,
        ai_suggested_reply=projected.ai_suggested_reply,
        final_reply=projected.final_reply,
        reply_mode=reply_mode,
        send_mode=projected.send_mode,
        send_status=projected.send_status,
        intent=projected.intent,
        intent_bucket=projected.intent_bucket,
        intent_confidence=projected.intent_confidence,
        risk_level=projected.risk_level,
        blocked_reason=projected.blocked_reason,
        human_takeover_reason=projected.human_takeover_reason,
        not_sent_explanation=projected.not_sent_explanation,
        product_gate_enabled=product_gate_enabled,
        created_at=created_at,
        updated_at=updated_at,
    )


def _dto_from_row(row: ReplyLogRow) -> ReplyLogDTO:
    return ReplyLogDTO(
        reply_log_id=row.reply_log_id,
        workspace_id=row.workspace_id or "",
        shop_id=row.shop_id or "",
        account_id=row.account_id or "",
        platform_id=row.platform_id or "",
        buyer_id=row.buyer_id or "",
        buyer_message=row.buyer_message,
        ai_suggested_reply=row.ai_suggested_reply,
        send_status=row.send_status,
        send_mode=row.send_mode,
        intent=row.intent or "",
        intent_bucket=row.intent_bucket or "",
        metadata={},
    )


class ReplyLogRepositorySQLite:
    """Shadow ReplyLog persistence — no send paths, no legacy DB."""

    def __init__(self, db_manager: Optional[ProductDbManager] = None) -> None:
        self._db_manager = db_manager or get_product_db_manager()

    def create_preview_reply_log(
        self,
        record_or_projected_item: Union[PreviewLogRecord, PreviewReplyLogListItem, Any],
    ) -> str:
        if isinstance(record_or_projected_item, PreviewLogRecord):
            row = _row_from_preview_record(record_or_projected_item)
        elif isinstance(record_or_projected_item, PreviewReplyLogListItem):
            raise TypeError(
                "create_preview_reply_log requires PreviewLogRecord for full shadow write"
            )
        else:
            raise TypeError(
                f"Unsupported record type: {type(record_or_projected_item)!r}"
            )

        session = self._db_manager.get_product_session()
        try:
            existing = session.get(ReplyLogRow, row.reply_log_id)
            if existing is not None:
                return existing.reply_log_id
            session.add(row)
            session.commit()
            return row.reply_log_id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def list_reply_logs(
        self,
        *,
        workspace_id: Optional[str] = None,
        shop_id: Optional[str] = None,
        buyer_id: Optional[str] = None,
        send_status: Optional[str] = None,
        limit: int = 100,
    ) -> List[ReplyLogDTO]:
        session = self._db_manager.get_product_session()
        try:
            from sqlalchemy import select

            stmt = select(ReplyLogRow)
            if workspace_id is not None:
                stmt = stmt.where(ReplyLogRow.workspace_id == workspace_id)
            if shop_id is not None:
                stmt = stmt.where(ReplyLogRow.shop_id == shop_id)
            if buyer_id is not None:
                stmt = stmt.where(ReplyLogRow.buyer_id == buyer_id)
            if send_status is not None:
                stmt = stmt.where(ReplyLogRow.send_status == send_status)
            stmt = stmt.order_by(ReplyLogRow.created_at.desc()).limit(limit)
            rows = session.scalars(stmt).all()
            return [_dto_from_row(row) for row in rows]
        finally:
            session.close()

    def get_reply_log(self, reply_log_id: str) -> Optional[ReplyLogDTO]:
        session = self._db_manager.get_product_session()
        try:
            row = session.get(ReplyLogRow, reply_log_id)
            if row is None:
                return None
            return _dto_from_row(row)
        finally:
            session.close()

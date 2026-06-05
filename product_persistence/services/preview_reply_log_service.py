"""Preview ReplyLog service — in-memory + optional SQLite shadow (Phase 14g–14l)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from product_persistence import flags


@dataclass(frozen=True)
class PreviewRecordResult:
    recorded: bool
    persistence_enabled: bool
    reason: str
    source: Optional[str] = None
    reply_log_id: Optional[str] = None
    db_recorded: bool = False
    db_error: Optional[str] = None


@dataclass(frozen=True)
class PreviewReplyLogServiceResult:
    success: bool
    source: str
    records: tuple[Any, ...]
    error: Optional[str] = None


class PreviewReplyLogService:
    """
    Service-layer read/write boundary over Message/gates in-memory preview_log.

    SQLite shadow write behind flags (Phase 14l); handler wired in 14i.
    """

    def __init__(self, repository: Any = None) -> None:
        self.repository = repository

    def record_preview(
        self,
        *,
        message_text: str,
        reply_text: str,
        classification: Any = None,
        send_decision: Any = None,
        guarded_result: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
        buyer_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        platform_id: Optional[str] = None,
        shop_id: Optional[str] = None,
        account_id: Optional[str] = None,
        **_kwargs: Any,
    ) -> PreviewRecordResult:
        """
        Write preview ReplyLog to in-memory store; optional SQLite shadow when flagged.
        """
        if (
            classification is None
            or send_decision is None
            or guarded_result is None
        ):
            return PreviewRecordResult(
                recorded=False,
                persistence_enabled=flags.is_product_persistence_enabled(),
                reason=(
                    "product_persistence_disabled"
                    if not flags.is_product_persistence_enabled()
                    else "missing_preview_context"
                ),
            )

        from Message.gates.preview_log import append_preview_log

        record = append_preview_log(
            message_text=message_text,
            reply_text=reply_text,
            classification=classification,
            send_decision=send_decision,
            guarded_result=guarded_result,
            metadata=metadata,
            buyer_id=buyer_id,
            workspace_id=workspace_id,
            platform_id=platform_id,
            shop_id=shop_id,
            account_id=account_id,
        )

        common = dict(
            recorded=True,
            persistence_enabled=flags.is_product_persistence_enabled(),
            reason="recorded_in_memory",
            reply_log_id=record.reply_log_id,
        )

        if not flags.should_write_reply_log():
            return PreviewRecordResult(
                **common,
                source="in_memory",
                db_recorded=False,
                db_error=None,
            )

        try:
            repository = self.repository
            if repository is None:
                from product_persistence.repositories.sqlite_reply_log_repository import (
                    ReplyLogRepositorySQLite,
                )

                repository = ReplyLogRepositorySQLite()
            repository.create_preview_reply_log(record)
            return PreviewRecordResult(
                **common,
                source="in_memory+sqlite_shadow",
                db_recorded=True,
                db_error=None,
            )
        except Exception as exc:
            return PreviewRecordResult(
                **common,
                source="in_memory",
                db_recorded=False,
                db_error=str(exc),
            )

    def list_reply_logs(
        self,
        *,
        workspace_id: Optional[str] = None,
        shop_id: Optional[str] = None,
        buyer_id: Optional[str] = None,
        send_status: Optional[str] = None,
    ) -> PreviewReplyLogServiceResult:
        try:
            from Message.gates.reply_log_projection import list_preview_reply_logs

            items = list_preview_reply_logs()
            filtered = self._filter_items(
                items,
                workspace_id=workspace_id,
                shop_id=shop_id,
                buyer_id=buyer_id,
                send_status=send_status,
            )
            return PreviewReplyLogServiceResult(
                success=True,
                source="in_memory",
                records=tuple(filtered),
            )
        except Exception as exc:
            return PreviewReplyLogServiceResult(
                success=False,
                source="in_memory",
                records=(),
                error=str(exc),
            )

    def get_reply_log(
        self,
        reply_log_id: str,
    ) -> Optional[Any]:
        result = self.list_reply_logs()
        if not result.success:
            return None
        for item in result.records:
            if getattr(item, "reply_log_id", None) == reply_log_id:
                return item
        return None

    @staticmethod
    def clear_in_memory_logs_for_tests() -> None:
        from Message.gates.preview_log import preview_log

        preview_log.clear()

    @staticmethod
    def _filter_items(
        items: List[Any],
        *,
        workspace_id: Optional[str],
        shop_id: Optional[str],
        buyer_id: Optional[str],
        send_status: Optional[str],
    ) -> List[Any]:
        filtered = items
        if workspace_id is not None:
            filtered = [i for i in filtered if i.workspace_id == workspace_id]
        if shop_id is not None:
            filtered = [i for i in filtered if i.shop_id == shop_id]
        if buyer_id is not None:
            filtered = [i for i in filtered if i.buyer_id == buyer_id]
        if send_status is not None:
            filtered = [i for i in filtered if i.send_status == send_status]
        return filtered

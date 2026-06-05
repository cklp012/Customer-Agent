"""Preview ReplyLog service — in-memory adapter (Phase 14g). No DB, no send."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from product_persistence import flags


@dataclass(frozen=True)
class PreviewRecordResult:
    recorded: bool
    persistence_enabled: bool
    reason: str


@dataclass(frozen=True)
class PreviewReplyLogServiceResult:
    success: bool
    source: str
    records: tuple[Any, ...]
    error: Optional[str] = None


class PreviewReplyLogService:
    """
    Service-layer read model over Message/gates in-memory preview_log.

    DB repository write is reserved for Phase 14i+; handler not wired in 14g.
    """

    def __init__(self, repository: Any = None) -> None:
        self.repository = repository

    def record_preview(
        self,
        *,
        message_text: str,
        reply_text: str,
        metadata: Optional[Dict[str, Any]] = None,
        **_kwargs: Any,
    ) -> PreviewRecordResult:
        """
        Persistence write path deferred — handlers continue using append_preview_log.
        """
        if not flags.is_product_persistence_enabled():
            return PreviewRecordResult(
                recorded=False,
                persistence_enabled=False,
                reason="product_persistence_disabled",
            )
        if self.repository is not None and flags.should_write_reply_log():
            raise NotImplementedError(
                "DB ReplyLog write is not available until Phase 14i+"
            )
        return PreviewRecordResult(
            recorded=False,
            persistence_enabled=True,
            reason="in_memory_deferred",
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
            from Message.gates.reply_log_projection import (
                PreviewReplyLogListItem,
                list_preview_reply_logs,
            )

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

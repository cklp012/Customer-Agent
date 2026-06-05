"""ReplyLog repository Protocol (Phase 14f) — no DB implementation."""

from __future__ import annotations

from typing import Any, List, Optional, Protocol

from product_persistence.models import ReplyLogDTO


class ReplyLogRepository(Protocol):
    def create_preview_reply_log(self, **fields: Any) -> str:
        """Create preview ReplyLog row; returns reply_log_id."""
        ...

    def list_reply_logs(
        self,
        *,
        workspace_id: Optional[str] = None,
        shop_id: Optional[str] = None,
        buyer_id: Optional[str] = None,
        send_status: Optional[str] = None,
        limit: int = 100,
    ) -> List[ReplyLogDTO]:
        ...

    def get_reply_log(self, reply_log_id: str) -> Optional[ReplyLogDTO]:
        ...

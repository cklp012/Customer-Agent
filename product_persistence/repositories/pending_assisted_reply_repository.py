"""Pending assisted reply repository Protocol (Phase 14f)."""

from __future__ import annotations

from typing import Any, Optional, Protocol

from product_persistence.models import PendingAssistedReplyDTO


class PendingAssistedReplyRepository(Protocol):
    def create_pending(self, **fields: Any) -> str:
        ...

    def mark_approved(
        self,
        pending_reply_id: str,
        *,
        approved_by: str,
        edited_reply: Optional[str] = None,
    ) -> None:
        ...

    def mark_rejected(
        self,
        pending_reply_id: str,
        *,
        rejected_by: str,
        reason: Optional[str] = None,
    ) -> None:
        ...

    def mark_expired(self, pending_reply_id: str) -> None:
        ...

    def mark_superseded(
        self,
        pending_reply_id: str,
        *,
        superseded_by_message_id: str,
    ) -> None:
        ...

    def get_pending(self, pending_reply_id: str) -> Optional[PendingAssistedReplyDTO]:
        ...

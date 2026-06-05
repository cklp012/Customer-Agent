"""Assisted reply service stub (Phase 14f) — no send, not implemented."""

from __future__ import annotations

from typing import Any, Optional


class AssistedReplyService:
    """Merchant confirmation flow — deferred to post-14g phases."""

    def approve_pending_reply(
        self,
        pending_reply_id: str,
        *,
        actor_member_id: str,
        final_reply: Optional[str] = None,
        **_kwargs: Any,
    ) -> None:
        raise NotImplementedError(
            "AssistedReplyService.approve_pending_reply is not implemented"
        )

    def reject_pending_reply(
        self,
        pending_reply_id: str,
        *,
        actor_member_id: str,
        reason: Optional[str] = None,
        **_kwargs: Any,
    ) -> None:
        raise NotImplementedError(
            "AssistedReplyService.reject_pending_reply is not implemented"
        )

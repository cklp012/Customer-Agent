"""Preview ReplyLog service stub (Phase 14f) — no send, no DB write."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from product_persistence import flags


@dataclass(frozen=True)
class PreviewRecordResult:
    recorded: bool
    persistence_enabled: bool
    reason: str


class PreviewReplyLogService:
    """Orchestrates in-memory + optional DB preview logging (14g+)."""

    def record_preview(
        self,
        *,
        message_text: str,
        reply_text: str,
        metadata: Optional[Dict[str, Any]] = None,
        **_kwargs: Any,
    ) -> PreviewRecordResult:
        if not flags.is_product_persistence_enabled():
            return PreviewRecordResult(
                recorded=False,
                persistence_enabled=False,
                reason="product_persistence_disabled",
            )
        raise NotImplementedError(
            "PreviewReplyLogService.record_preview is not implemented until Phase 14g+"
        )

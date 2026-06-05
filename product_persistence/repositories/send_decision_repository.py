"""SendDecision snapshot repository Protocol (Phase 14f)."""

from __future__ import annotations

from typing import Any, List, Optional, Protocol

from product_persistence.models import SendDecisionSnapshotDTO


class SendDecisionRepository(Protocol):
    def create_snapshot(self, **fields: Any) -> str:
        """Append-only snapshot; returns send_decision_id."""
        ...

    def list_snapshots_by_reply_log(
        self,
        reply_log_id: str,
    ) -> List[SendDecisionSnapshotDTO]:
        ...

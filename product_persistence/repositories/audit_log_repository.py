"""AuditLog repository Protocol (Phase 14f) — append-only interface."""

from __future__ import annotations

from typing import Any, List, Optional, Protocol

from product_persistence.models import AuditLogDTO


class AuditLogRepository(Protocol):
    def append_audit_log(self, **fields: Any) -> str:
        ...

    def list_audit_logs(
        self,
        *,
        workspace_id: str,
        shop_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLogDTO]:
        ...

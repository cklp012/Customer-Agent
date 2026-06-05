"""Repository Protocol stubs (Phase 14f)."""

from product_persistence.repositories.audit_log_repository import AuditLogRepository
from product_persistence.repositories.pending_assisted_reply_repository import (
    PendingAssistedReplyRepository,
)
from product_persistence.repositories.reply_log_repository import ReplyLogRepository
from product_persistence.repositories.send_decision_repository import (
    SendDecisionRepository,
)

__all__ = [
    "AuditLogRepository",
    "PendingAssistedReplyRepository",
    "ReplyLogRepository",
    "SendDecisionRepository",
]

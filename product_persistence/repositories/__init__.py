"""Repository Protocol stubs (Phase 14f) + SQLite implementation (Phase 14l)."""

from product_persistence.repositories.audit_log_repository import AuditLogRepository
from product_persistence.repositories.pending_assisted_reply_repository import (
    PendingAssistedReplyRepository,
)
from product_persistence.repositories.reply_log_repository import ReplyLogRepository
from product_persistence.repositories.send_decision_repository import (
    SendDecisionRepository,
)
from product_persistence.repositories.sqlite_audit_log_repository import (
    AuditLogRepositorySQLite,
)
from product_persistence.repositories.sqlite_pending_assisted_repository import (
    PendingAssistedRepositorySQLite,
)
from product_persistence.repositories.sqlite_reply_log_repository import (
    ReplyLogRepositorySQLite,
)
from product_persistence.repositories.sqlite_send_decision_repository import (
    SendDecisionRepositorySQLite,
)
from product_persistence.repositories.sqlite_merchant_policy_repository import (
    MerchantPolicyRepositorySQLite,
)
from product_persistence.repositories.sqlite_reply_template_repository import (
    MerchantReplyTemplateRepositorySQLite,
)

__all__ = [
    "AuditLogRepository",
    "AuditLogRepositorySQLite",
    "MerchantPolicyRepositorySQLite",
    "MerchantReplyTemplateRepositorySQLite",
    "PendingAssistedReplyRepository",
    "PendingAssistedRepositorySQLite",
    "ReplyLogRepository",
    "ReplyLogRepositorySQLite",
    "SendDecisionRepository",
    "SendDecisionRepositorySQLite",
]

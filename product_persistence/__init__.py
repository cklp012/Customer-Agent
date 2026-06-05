"""
Product / SaaS shadow persistence (Phase 14f skeleton).

Independent of legacy database/ — default disabled, no DB at import.
"""

from product_persistence.flags import (
    is_product_persistence_enabled,
    should_read_dashboard_from_product_db,
    should_write_audit_log,
    should_write_pending_assisted,
    should_write_reply_log,
    should_write_send_decision,
)

__all__ = [
    "is_product_persistence_enabled",
    "should_read_dashboard_from_product_db",
    "should_write_audit_log",
    "should_write_pending_assisted",
    "should_write_reply_log",
    "should_write_send_decision",
]

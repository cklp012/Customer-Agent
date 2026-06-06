"""Product persistence feature flags (Phase 14f). Default off; no DB side effects."""

from __future__ import annotations

import os

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def _env_flag(name: str, default: str = "") -> bool:
    raw = os.environ.get(name, default)
    return raw.strip().lower() in _TRUE_VALUES


def is_product_persistence_enabled() -> bool:
    return _env_flag("PRODUCT_PERSISTENCE_ENABLED")


def should_write_reply_log() -> bool:
    return is_product_persistence_enabled() and _env_flag(
        "PRODUCT_PERSISTENCE_WRITE_REPLY_LOG"
    )


def should_write_send_decision() -> bool:
    return is_product_persistence_enabled() and _env_flag(
        "PRODUCT_PERSISTENCE_WRITE_SEND_DECISION"
    )


def should_write_audit_log() -> bool:
    return is_product_persistence_enabled() and _env_flag(
        "PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG"
    )


def should_write_pending_assisted() -> bool:
    return is_product_persistence_enabled() and _env_flag(
        "PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED"
    )


def should_read_dashboard_from_product_db() -> bool:
    return is_product_persistence_enabled() and _env_flag(
        "PRODUCT_PERSISTENCE_READ_DASHBOARD"
    )


def should_write_merchant_policy() -> bool:
    return is_product_persistence_enabled() and _env_flag(
        "PRODUCT_PERSISTENCE_WRITE_MERCHANT_POLICY"
    )


def should_write_reply_template() -> bool:
    return is_product_persistence_enabled() and _env_flag(
        "PRODUCT_PERSISTENCE_WRITE_REPLY_TEMPLATE"
    )


def should_read_merchant_policy() -> bool:
    return is_product_persistence_enabled() and _env_flag(
        "PRODUCT_PERSISTENCE_READ_MERCHANT_POLICY"
    )


def is_assisted_service_enabled() -> bool:
    return (
        is_product_persistence_enabled()
        and should_write_pending_assisted()
        and should_write_audit_log()
        and _env_flag("PRODUCT_ASSISTED_SERVICE_ENABLED")
    )


def should_write_outbound_idempotency() -> bool:
    return is_product_persistence_enabled() and _env_flag(
        "PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY"
    )


def is_assisted_send_enabled() -> bool:
    return _env_flag("PRODUCT_ASSISTED_SEND_ENABLED")


def is_assisted_send_dry_run() -> bool:
    raw = os.environ.get("PRODUCT_ASSISTED_SEND_DRY_RUN", "true")
    return raw.strip().lower() in _TRUE_VALUES


def get_assisted_send_test_shop_id() -> str:
    return os.environ.get("PRODUCT_ASSISTED_SEND_TEST_SHOP_ID", "").strip()


def would_assisted_send_live() -> bool:
    """Future live send gate — not used in Phase 15c (dry-run port only)."""
    allowlisted = get_assisted_send_test_shop_id()
    return (
        is_assisted_send_enabled()
        and not is_assisted_send_dry_run()
        and bool(allowlisted)
    )

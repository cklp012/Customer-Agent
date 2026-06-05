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

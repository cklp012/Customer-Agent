"""Unified outbound resolver 功能开关（Phase 8c）。"""

from __future__ import annotations

import os

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def use_unified_outbound_resolver() -> bool:
    """handler 是否使用 resolve_outbound。默认 False。"""
    raw = os.environ.get("USE_UNIFIED_OUTBOUND_RESOLVER", "")
    return raw.strip().lower() in _TRUE_VALUES

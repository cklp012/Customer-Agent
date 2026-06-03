"""UnifiedMessage shadow 功能开关（Phase 7c）。"""

from __future__ import annotations

import os

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def use_unified_message_shadow() -> bool:
    """是否旁路调用 pdd_to_unified 并打日志。默认 False。"""
    raw = os.environ.get("USE_UNIFIED_MESSAGE_SHADOW", "")
    return raw.strip().lower() in _TRUE_VALUES

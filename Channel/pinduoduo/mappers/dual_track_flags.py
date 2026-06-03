"""UnifiedMessage 双轨入队功能开关（Phase 7d）。"""

from __future__ import annotations

import os

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def use_unified_message_dual_track() -> bool:
    """是否在入队时附带 UnifiedMessage 副本。默认 False。"""
    raw = os.environ.get("USE_UNIFIED_MESSAGE_DUAL_TRACK", "")
    return raw.strip().lower() in _TRUE_VALUES

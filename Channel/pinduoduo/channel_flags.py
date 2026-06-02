"""拼多多 Channel 包装层功能开关（Phase 3b，供 AutoReplyThread 使用）。"""

from __future__ import annotations

import os

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def use_pinduoduo_channel_wrapper() -> bool:
    """是否使用 PinduoduoChannel 包装 legacy PDDChannel。默认 False。"""
    raw = os.environ.get("USE_PINDUODUO_CHANNEL_WRAPPER", "")
    return raw.strip().lower() in _TRUE_VALUES

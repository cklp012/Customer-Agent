"""AutoReply ChannelRegistry 创建开关（Phase 9a）。"""

from __future__ import annotations

import os

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def use_channel_registry_for_autoreply() -> bool:
    """AutoReply 是否在 wrapper 开启时经 ChannelRegistry.create 创建。默认 False。"""
    raw = os.environ.get("USE_CHANNEL_REGISTRY_FOR_AUTOREPLY", "")
    return raw.strip().lower() in _TRUE_VALUES

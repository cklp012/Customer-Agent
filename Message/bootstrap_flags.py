"""ChannelRegistry bootstrap 功能开关（Phase 8e）。"""

from __future__ import annotations

import os

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def use_demo_channel_registration() -> bool:
    """register_default_platforms 是否注册 Demo 工厂。默认 False。"""
    raw = os.environ.get("USE_DEMO_CHANNEL_REGISTRATION", "")
    return raw.strip().lower() in _TRUE_VALUES

"""抖店 ChannelRegistry 注册开关（Phase 11b）。"""

from __future__ import annotations

import os

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})


def use_doudian_channel_registration() -> bool:
    """
    register_default_platforms 是否注册 Doudian 工厂。

    - 未设置：False
    - true / 1 / yes / on：True
    - false / 0 / no / off / 空串 / 未知：False
    """
    raw = os.environ.get("USE_DOUDIAN_CHANNEL_REGISTRATION")
    if raw is None:
        return False
    value = raw.strip().lower()
    if not value:
        return False
    if value in _FALSE_VALUES:
        return False
    if value in _TRUE_VALUES:
        return True
    return False


__all__ = ["use_doudian_channel_registration"]

"""AutoReply ChannelRegistry 创建开关（Phase 9a，9d 默认开启）。"""

from __future__ import annotations

import os

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})


def use_channel_registry_for_autoreply() -> bool:
    """
    AutoReply 是否经 ChannelRegistry.create(PINDUODUO) 创建（Phase 9d 默认 True）。

    - 环境变量未设置 (None)：True（Registry path，经 create_pinduoduo_registry_channel）
    - 显式 false / 0 / no / off：False（回滚 legacy path，_create_auto_reply_legacy）
    - 显式 true / 1 / yes / on：True
    - 空字符串或未知值：False（保守关闭）

    尊重 USE_PINDUODUO_CHANNEL_WRAPPER（wrapper on/off 均可走 Registry，见 9b parity）。
    """
    raw = os.environ.get("USE_CHANNEL_REGISTRY_FOR_AUTOREPLY")
    if raw is None:
        return True
    value = raw.strip().lower()
    if not value:
        return False
    if value in _FALSE_VALUES:
        return False
    if value in _TRUE_VALUES:
        return True
    return False

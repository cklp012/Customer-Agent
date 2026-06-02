"""PinduoduoChannel 工厂与注册表（Phase 3a，不在 app.py 自动注册）。"""

from __future__ import annotations

from typing import Any

from Channel.base.registry import ChannelRegistry
from Channel.base.types import PlatformType
from Channel.pinduoduo.pinduoduo_channel import PinduoduoChannel


def create_pinduoduo_channel(**kwargs: Any) -> PinduoduoChannel:
    """创建 PinduoduoChannel 实例。"""
    return PinduoduoChannel(**kwargs)


def register_pinduoduo_channel() -> None:
    """向 ChannelRegistry 注册拼多多工厂（由测试或显式 bootstrap 调用）。"""
    ChannelRegistry.register(PlatformType.PINDUODUO, create_pinduoduo_channel)

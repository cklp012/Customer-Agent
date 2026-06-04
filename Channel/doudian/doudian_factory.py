"""DoudianMockChannel 工厂与 ChannelRegistry 注册（Phase 11b）。"""

from __future__ import annotations

from typing import Any

from Channel.base.registry import ChannelRegistry
from Channel.base.types import PlatformType
from Channel.doudian.doudian_channel import DoudianMockChannel


def create_doudian_mock_channel(**kwargs: Any) -> DoudianMockChannel:
    """创建 DoudianMockChannel 实例。"""
    return DoudianMockChannel(**kwargs)


def register_doudian_channel() -> None:
    """向 ChannelRegistry 注册抖店 mock 工厂。"""
    ChannelRegistry.register(PlatformType.DOUDIAN, create_doudian_mock_channel)


def unregister_doudian_channel() -> None:
    """从 ChannelRegistry 移除抖店工厂（测试 tearDown）。"""
    ChannelRegistry.unregister(PlatformType.DOUDIAN)


__all__ = [
    "create_doudian_mock_channel",
    "register_doudian_channel",
    "unregister_doudian_channel",
]

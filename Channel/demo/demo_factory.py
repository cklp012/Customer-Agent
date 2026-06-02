"""DemoChannel 工厂与 ChannelRegistry 注册（Phase 6b）。"""

from __future__ import annotations

from typing import Any

from Channel.base.registry import ChannelRegistry
from Channel.base.types import PlatformType
from Channel.demo.demo_channel import DemoChannel


def create_demo_channel(**kwargs: Any) -> DemoChannel:
    """创建 DemoChannel 实例。"""
    return DemoChannel(**kwargs)


def register_demo_channel() -> None:
    """向 ChannelRegistry 注册 Demo 工厂（由测试或显式 bootstrap 调用）。"""
    ChannelRegistry.register(PlatformType.DEMO, create_demo_channel)


def unregister_demo_channel() -> None:
    """从 ChannelRegistry 移除 Demo 工厂。"""
    ChannelRegistry.unregister(PlatformType.DEMO)

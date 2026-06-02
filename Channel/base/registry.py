"""
Channel 注册表与工厂（Phase 1 骨架）。

不注册真实 PDDChannel；Phase 2 由应用启动代码 register(PINDUODUO, factory)。
"""

from __future__ import annotations

from typing import Callable, Dict, TypeVar

from Channel.base.channel import BaseChannel
from Channel.base.types import PlatformType

ChannelFactory = Callable[..., BaseChannel]

T = TypeVar("T", bound=BaseChannel)


class ChannelRegistry:
    """平台 Channel 工厂注册表"""

    _factories: Dict[PlatformType, ChannelFactory] = {}

    @classmethod
    def register(cls, platform: PlatformType, factory: ChannelFactory) -> None:
        """注册某平台的 Channel 工厂"""
        cls._factories[platform] = factory

    @classmethod
    def unregister(cls, platform: PlatformType) -> None:
        """移除注册（主要用于测试）"""
        cls._factories.pop(platform, None)

    @classmethod
    def is_registered(cls, platform: PlatformType) -> bool:
        return platform in cls._factories

    @classmethod
    def create(cls, platform: PlatformType, **kwargs: object) -> BaseChannel:
        """创建指定平台的 Channel 实例"""
        factory = cls._factories.get(platform)
        if factory is None:
            raise KeyError(
                f"No Channel factory registered for platform={platform.value!r}. "
                "Register one with ChannelRegistry.register() in Phase 2+."
            )
        return factory(**kwargs)

    @classmethod
    def registered_platforms(cls) -> list[PlatformType]:
        return list(cls._factories.keys())

    @classmethod
    def clear(cls) -> None:
        """清空注册表（仅用于测试）"""
        cls._factories.clear()

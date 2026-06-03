"""
按平台 + 账号缓存 ChannelOutbound（Phase 8b）。

与 AccountOutboundRegistry（仅 PDD）并行；不自动迁移 PDD 注册。
"""

from __future__ import annotations

from threading import RLock
from typing import Any, Optional, Union

from Channel.base.types import PlatformType

_lock = RLock()
_registry: dict[str, Any] = {}


def _normalize_platform(platform: Union[str, PlatformType]) -> str:
    if isinstance(platform, PlatformType):
        return platform.value
    return str(platform).strip().lower()


def _make_key(platform: Union[str, PlatformType], shop_id: str, account_id: str) -> str:
    return f"{_normalize_platform(platform)}:{shop_id}:{account_id}"


def register(
    platform: Union[str, PlatformType],
    shop_id: str,
    account_id: str,
    outbound: Any,
) -> None:
    """注册平台账号出站实例。"""
    key = _make_key(platform, shop_id, account_id)
    with _lock:
        _registry[key] = outbound


def unregister(
    platform: Union[str, PlatformType],
    shop_id: str,
    account_id: str,
) -> None:
    """移除平台账号出站实例。"""
    key = _make_key(platform, shop_id, account_id)
    with _lock:
        _registry.pop(key, None)


def get(
    platform: Union[str, PlatformType],
    shop_id: str,
    account_id: str,
) -> Optional[Any]:
    """获取已注册出站实例，不存在则返回 None。"""
    key = _make_key(platform, shop_id, account_id)
    with _lock:
        return _registry.get(key)


def clear() -> None:
    """清空注册表（主要用于测试）。"""
    with _lock:
        _registry.clear()

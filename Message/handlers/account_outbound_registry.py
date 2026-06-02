"""
按账号缓存 PinduoduoOutbound（Phase 4a）。

供 outbound_resolver 查找；Phase 4b 由 PinduoduoChannel 在 start/stop 时注册。
"""

from __future__ import annotations

from threading import RLock
from typing import Any, Optional

from Channel.pinduoduo.pinduoduo_outbound import PinduoduoOutbound

_lock = RLock()
_registry: dict[str, PinduoduoOutbound] = {}


def _make_key(shop_id: str, user_id: str) -> str:
    return f"{shop_id}:{user_id}"


def register(shop_id: str, user_id: str, outbound: PinduoduoOutbound) -> None:
    """注册账号出站实例。"""
    key = _make_key(str(shop_id), str(user_id))
    with _lock:
        _registry[key] = outbound


def unregister(shop_id: str, user_id: str) -> None:
    """移除账号出站实例。"""
    key = _make_key(str(shop_id), str(user_id))
    with _lock:
        _registry.pop(key, None)


def get(shop_id: str, user_id: str) -> Optional[PinduoduoOutbound]:
    """获取已注册的出站实例，不存在则返回 None。"""
    key = _make_key(str(shop_id), str(user_id))
    with _lock:
        return _registry.get(key)


def clear() -> None:
    """清空注册表（主要用于测试）。"""
    with _lock:
        _registry.clear()

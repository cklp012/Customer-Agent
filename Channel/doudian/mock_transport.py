"""
抖店 mock inbound transport（Phase 10l）。

无网络、无线程；仅按序返回预设 raw dict 列表。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class DoudianMockTransport:
    """内存 mock transport：poll 逐条取出，poll_all 一次取完。"""

    def __init__(self, messages: Optional[List[Dict[str, Any]]] = None) -> None:
        self._pending: List[Dict[str, Any]] = list(messages or [])

    def poll(self) -> Optional[Dict[str, Any]]:
        """返回下一条 mock 消息；无剩余时返回 None。"""
        if not self._pending:
            return None
        return self._pending.pop(0)

    def poll_all(self) -> List[Dict[str, Any]]:
        """返回全部剩余消息并清空队列。"""
        batch = list(self._pending)
        self._pending.clear()
        return batch

    @property
    def pending_count(self) -> int:
        return len(self._pending)


__all__ = ["DoudianMockTransport"]

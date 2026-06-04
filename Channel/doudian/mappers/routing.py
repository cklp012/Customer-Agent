"""
抖店入站 routing 草案（Phase 10k）。

返回值仅：immediate | queue | drop。本阶段未使用 immediate。
"""

from __future__ import annotations

from typing import Literal

DoudianRouting = Literal["immediate", "queue", "drop"]

_QUEUE_TYPES = frozenset({"text", "product_inquiry"})
_DROP_TYPES = frozenset({"system_notice"})


def compute_doudian_routing(message_type: str) -> DoudianRouting:
    """
    由 mock fixture 的 message_type 决定 routing。

    - text / product_inquiry → queue
    - system_notice → drop
    - unknown → drop
    """
    normalized = (message_type or "").strip().lower()
    if normalized in _QUEUE_TYPES:
        return "queue"
    if normalized in _DROP_TYPES:
        return "drop"
    return "drop"


__all__ = ["DoudianRouting", "compute_doudian_routing"]

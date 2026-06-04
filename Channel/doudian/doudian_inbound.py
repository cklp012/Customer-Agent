"""
抖店 mock 入站入队（Phase 10l，仅测试 / spike）。

routing=queue 且 Context 非空时调用 enqueue_inbound_message；drop 不入队。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from bridge.context import Context
from Channel.base.models import UnifiedMessage
from Channel.doudian.mappers.doudian_to_context import doudian_raw_to_context
from Channel.doudian.mappers.doudian_to_unified import doudian_raw_to_unified
from Channel.doudian.mappers.routing import compute_doudian_routing
from Message.inbound_enqueue import enqueue_inbound_message
from Message.queue_naming import build_queue_name


@dataclass
class DoudianEnqueueResult:
    """enqueue_doudian_raw_message 结果（与 Demo 入队语义对齐的可测结构）。"""

    queued: bool
    queue_name: str
    routing: str
    context: Optional[Context]
    unified_message: UnifiedMessage
    message_id: Optional[str] = None


def _resolve_queue_name(raw: Dict[str, Any], queue_name: Optional[str]) -> str:
    if queue_name is not None:
        return queue_name
    shop_id = str(raw.get("shop_id") or "")
    return build_queue_name("doudian", shop_id)


async def enqueue_doudian_raw_message(
    raw: Dict[str, Any],
    *,
    queue_name: Optional[str] = None,
) -> DoudianEnqueueResult:
    """
    抖店 mock raw → mapper → 按 routing 决定是否入队。

    - routing == queue 且 context 非空：调用 enqueue_inbound_message
    - routing == drop：不入队，queued=False
    """
    message_type = str(raw.get("message_type") or "text")
    routing = compute_doudian_routing(message_type)
    unified = doudian_raw_to_unified(raw)
    context = doudian_raw_to_context(raw)
    resolved_queue = _resolve_queue_name(raw, queue_name)

    if routing != "queue" or context is None:
        return DoudianEnqueueResult(
            queued=False,
            queue_name=resolved_queue,
            routing=routing,
            context=context,
            unified_message=unified,
        )

    message_id = await enqueue_inbound_message(
        resolved_queue,
        context,
        unified_message=unified,
    )
    return DoudianEnqueueResult(
        queued=True,
        queue_name=resolved_queue,
        routing=routing,
        context=context,
        unified_message=unified,
        message_id=message_id,
    )


__all__ = ["DoudianEnqueueResult", "enqueue_doudian_raw_message"]

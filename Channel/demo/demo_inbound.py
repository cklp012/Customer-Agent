"""
Demo 平台入站入队（Phase 8a，仅测试 / runtime spike）。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from Channel.demo.mappers.demo_to_context import demo_raw_to_context
from Channel.demo.mappers.demo_to_unified import demo_raw_to_unified
from Message.inbound_enqueue import enqueue_inbound_message


async def enqueue_demo_message(
    raw: Dict[str, Any],
    shop_id: str,
    account_id: str,
    queue_name: str,
    *,
    from_uid: Optional[str] = None,
) -> str:
    """
    Demo raw → Context + UnifiedMessage → 统一入队。

    Returns:
        队列 message_id
    """
    context = demo_raw_to_context(raw, shop_id, account_id, from_uid=from_uid)
    unified = demo_raw_to_unified(raw, shop_id, account_id, from_uid=from_uid)
    return await enqueue_inbound_message(
        queue_name,
        context,
        unified_message=unified,
    )

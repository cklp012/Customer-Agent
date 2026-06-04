"""
抖店 mock raw dict → UnifiedMessage（Phase 10k）。
"""

from __future__ import annotations

from typing import Any, Dict

from Channel.base.models import UnifiedConversation, UnifiedMessage
from Channel.base.types import PlatformType
from Channel.doudian.mappers.routing import compute_doudian_routing


def doudian_raw_to_unified(raw: Dict[str, Any]) -> UnifiedMessage:
    """将抖店 mock fixture 转为 UnifiedMessage（含 extra.routing）。"""
    message_type = str(raw.get("message_type") or "text")
    routing = compute_doudian_routing(message_type)

    shop_id = str(raw.get("shop_id") or "")
    account_id = str(raw.get("account_id") or "")
    buyer_id = str(raw.get("buyer_id") or "")
    conversation_id = str(raw.get("conversation_id") or buyer_id)
    message_id = str(raw.get("message_id") or "")
    content = raw.get("content", "")

    return UnifiedMessage(
        platform=PlatformType.DOUDIAN,
        message_id=message_id,
        conversation=UnifiedConversation(
            platform=PlatformType.DOUDIAN,
            conversation_id=conversation_id,
            shop_id=shop_id,
            account_id=account_id,
            buyer_uid=buyer_id,
            extra={"routing": routing},
        ),
        direction="inbound",
        content_type=message_type,
        content=content,
        raw=dict(raw),
    )


__all__ = ["doudian_raw_to_unified"]

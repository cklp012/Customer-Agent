"""
Demo 入站 raw dict → UnifiedMessage（Phase 8a）。

纯映射；routing 默认 queue（TEXT 入队路径）。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from Channel.base.models import UnifiedConversation, UnifiedMessage
from Channel.base.types import PlatformType


def demo_raw_to_unified(
    raw: Dict[str, Any],
    shop_id: str,
    account_id: str,
    *,
    from_uid: Optional[str] = None,
) -> UnifiedMessage:
    """将 Demo 合成入站 dict 转为 UnifiedMessage。"""
    buyer = from_uid or raw.get("from_uid") or raw.get("buyer_uid") or "demo-buyer-1"
    message_id = str(raw.get("message_id") or "demo-msg-1")
    content_type = str(raw.get("content_type") or "text")
    content = raw.get("content", "")

    return UnifiedMessage(
        platform=PlatformType.DEMO,
        message_id=message_id,
        conversation=UnifiedConversation(
            platform=PlatformType.DEMO,
            conversation_id=str(buyer),
            shop_id=str(shop_id),
            account_id=str(account_id),
            buyer_uid=str(buyer),
            extra={"routing": "queue"},
        ),
        direction="inbound",
        content_type=content_type,
        content=content,
        raw=dict(raw),
    )

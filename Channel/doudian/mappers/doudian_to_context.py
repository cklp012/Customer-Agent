"""
抖店 mock raw dict → legacy Context（Phase 10k）。

不修改 bridge；routing=drop 时返回 None（不入队路径）。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from bridge.context import Context, ContextType

from Channel.doudian.mappers.routing import compute_doudian_routing

_MESSAGE_TYPE_TO_CONTEXT: dict[str, ContextType] = {
    "text": ContextType.TEXT,
    "product_inquiry": ContextType.GOODS_INQUIRY,
}


class _DoudianKwargs:
    """抖店入站 kwargs（供 Consumer metadata 兼容）。"""

    def __init__(
        self,
        shop_id: str,
        user_id: str,
        from_uid: str,
        *,
        channel_type: str = "doudian",
        message_id: Any = None,
        username: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> None:
        self.shop_id = shop_id
        self.user_id = user_id
        self.from_uid = from_uid
        self.channel_type = channel_type
        self.message_id = message_id
        self.username = username or user_id
        self.conversation_id = conversation_id


def _context_type_for_message_type(message_type: str) -> ContextType:
    normalized = (message_type or "").strip().lower()
    return _MESSAGE_TYPE_TO_CONTEXT.get(normalized, ContextType.TEXT)


def doudian_raw_to_context(raw: Dict[str, Any]) -> Optional[Context]:
    """将抖店 mock fixture 转为 Context；drop 类型返回 None。"""
    message_type = str(raw.get("message_type") or "text")
    if compute_doudian_routing(message_type) == "drop":
        return None

    shop_id = str(raw.get("shop_id") or "")
    account_id = str(raw.get("account_id") or "")
    buyer_id = str(raw.get("buyer_id") or "")
    content = raw.get("content", "")
    if not isinstance(content, str):
        content = str(content)

    kwargs = _DoudianKwargs(
        shop_id,
        account_id,
        buyer_id,
        channel_type="doudian",
        message_id=raw.get("message_id"),
        username=raw.get("username") or account_id,
        conversation_id=raw.get("conversation_id"),
    )

    return Context(
        type=_context_type_for_message_type(message_type),
        content=content,
        kwargs=kwargs,
    )


__all__ = ["doudian_raw_to_context"]

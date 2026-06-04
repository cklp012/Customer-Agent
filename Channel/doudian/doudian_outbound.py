"""
抖店 mock 出站适配器（Phase 10m）。

实现 ChannelOutbound Protocol；仅内存记录，不联网、不调真实 API。
"""

from __future__ import annotations

from datetime import datetime, timezone
from itertools import count
from typing import Any, Optional

from Channel.base.types import PlatformType

_PLATFORM = PlatformType.DOUDIAN.value

_STUB_PRODUCTS: list[dict[str, Any]] = [
    {"goods_id": 8001, "title": "Doudian Mock SKU A", "price_yuan": 29.9},
]

_STUB_ORDER: dict[str, Any] = {
    "order_id": "doudian-mock-order-001",
    "status": "paid",
    "total_yuan": 29.9,
}

_message_id_counter = count(1)


def _next_message_id() -> str:
    return f"doudian-mock-msg-{next(_message_id_counter)}"


class DoudianMockOutbound:
    """抖店 ChannelOutbound mock：记录发送调用，不真实发送。"""

    def __init__(self, shop_id: str, account_id: str) -> None:
        self._shop_id = str(shop_id)
        self._account_id = str(account_id)
        self.sent_messages: list[dict[str, Any]] = []

    @property
    def shop_id(self) -> str:
        return self._shop_id

    @property
    def account_id(self) -> str:
        return self._account_id

    def _append_sent(
        self,
        method: str,
        *,
        conversation_id: str,
        buyer_id: Optional[str] = None,
        content: Any = None,
        message_id: Optional[str] = None,
        **extra: Any,
    ) -> str:
        mid = message_id or _next_message_id()
        entry: dict[str, Any] = {
            "method": method,
            "platform": _PLATFORM,
            "shop_id": self._shop_id,
            "account_id": self._account_id,
            "conversation_id": conversation_id,
            "buyer_id": buyer_id if buyer_id is not None else conversation_id,
            "content": content,
            "message_id": mid,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **extra,
        }
        self.sent_messages.append(entry)
        return mid

    async def send_text(self, conversation_id: str, text: str) -> bool:
        self._append_sent(
            "send_text",
            conversation_id=conversation_id,
            content=text,
        )
        return True

    async def send_image(self, conversation_id: str, image_url: str) -> bool:
        self._append_sent(
            "send_image",
            conversation_id=conversation_id,
            content=image_url,
        )
        return True

    async def send_goods_card(
        self,
        conversation_id: str,
        goods_id: int,
        **kwargs: Any,
    ) -> bool:
        self._append_sent(
            "send_goods_card",
            conversation_id=conversation_id,
            content={"goods_id": goods_id, **kwargs},
        )
        return True

    async def transfer_to_human(
        self,
        conversation_id: str,
        reason: str = "",
    ) -> bool:
        self._append_sent(
            "transfer_to_human",
            conversation_id=conversation_id,
            content=reason,
        )
        return True

    async def fetch_products(
        self,
        shop_id: str,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        self._append_sent(
            "fetch_products",
            conversation_id="",
            content=None,
            fetch_shop_id=shop_id,
            filters=filters,
        )
        return list(_STUB_PRODUCTS)

    async def fetch_order(
        self,
        shop_id: str,
        order_id: str,
        **kwargs: Any,
    ) -> Optional[dict[str, Any]]:
        self._append_sent(
            "fetch_order",
            conversation_id="",
            content=None,
            fetch_shop_id=shop_id,
            order_id=order_id,
            kwargs=kwargs,
        )
        if not order_id:
            return None
        return {**_STUB_ORDER, "order_id": order_id, "shop_id": shop_id}


__all__ = ["DoudianMockOutbound"]

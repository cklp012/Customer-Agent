"""
Demo 平台出站适配器（Phase 6b）。

实现 ChannelOutbound Protocol；仅内存记录与固定 stub 数据，不联网。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

_DEMO_PRODUCTS: list[dict[str, Any]] = [
    {"goods_id": 9001, "title": "Demo SKU A", "price_yuan": 9.9},
    {"goods_id": 9002, "title": "Demo SKU B", "price_yuan": 19.9},
]

_DEMO_ORDER: dict[str, Any] = {
    "order_id": "demo-order-001",
    "status": "paid",
    "total_yuan": 9.9,
}


class DemoOutbound:
    """Demo ChannelOutbound 实现。"""

    def __init__(self, shop_id: str, user_id: str) -> None:
        self._shop_id = str(shop_id)
        self._user_id = str(user_id)
        self.sent_log: list[dict[str, Any]] = []

    @property
    def shop_id(self) -> str:
        return self._shop_id

    @property
    def user_id(self) -> str:
        return self._user_id

    def _append_log(self, method: str, **fields: Any) -> None:
        entry: dict[str, Any] = {
            "method": method,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **fields,
        }
        self.sent_log.append(entry)

    async def send_text(self, conversation_id: str, text: str) -> bool:
        self._append_log(
            "send_text",
            conversation_id=conversation_id,
            text=text,
        )
        return True

    async def send_image(self, conversation_id: str, image_url: str) -> bool:
        self._append_log(
            "send_image",
            conversation_id=conversation_id,
            image_url=image_url,
        )
        return True

    async def send_goods_card(
        self,
        conversation_id: str,
        goods_id: int,
        **kwargs: Any,
    ) -> bool:
        self._append_log(
            "send_goods_card",
            conversation_id=conversation_id,
            goods_id=goods_id,
            kwargs=kwargs,
        )
        return True

    async def transfer_to_human(
        self,
        conversation_id: str,
        reason: str = "",
    ) -> bool:
        self._append_log(
            "transfer_to_human",
            conversation_id=conversation_id,
            reason=reason,
        )
        return True

    async def fetch_products(
        self,
        shop_id: str,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        self._append_log("fetch_products", shop_id=shop_id, filters=filters)
        return list(_DEMO_PRODUCTS)

    async def fetch_order(
        self,
        shop_id: str,
        order_id: str,
        **kwargs: Any,
    ) -> Optional[dict[str, Any]]:
        self._append_log(
            "fetch_order",
            shop_id=shop_id,
            order_id=order_id,
            kwargs=kwargs,
        )
        if not order_id:
            return None
        return {**_DEMO_ORDER, "order_id": order_id, "shop_id": shop_id}

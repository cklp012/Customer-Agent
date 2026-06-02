"""
Channel 出站能力协议（Phase 1 骨架）。

具体实现由各平台 Adapter 在 Phase 2+ 提供（如 PinduoduoOutbound）。
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class ChannelOutbound(Protocol):
    """平台消息发送与店铺数据查询的统一接口"""

    async def send_text(self, conversation_id: str, text: str) -> bool:
        """发送文本消息。conversation_id 为平台侧会话/买家标识。"""
        ...

    async def send_image(self, conversation_id: str, image_url: str) -> bool:
        """发送图片消息（URL 或平台可识别的图片引用）。"""
        ...

    async def send_goods_card(
        self,
        conversation_id: str,
        goods_id: int,
        **kwargs: Any,
    ) -> bool:
        """发送商品卡片。"""
        ...

    async def transfer_to_human(
        self,
        conversation_id: str,
        reason: str = "",
    ) -> bool:
        """将会话转接给人工客服。"""
        ...

    async def fetch_products(
        self,
        shop_id: str,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """拉取店铺商品列表。"""
        ...

    async def fetch_order(
        self,
        shop_id: str,
        order_id: str,
        **kwargs: Any,
    ) -> Optional[dict[str, Any]]:
        """查询订单信息。"""
        ...

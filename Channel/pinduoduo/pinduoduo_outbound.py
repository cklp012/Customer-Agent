"""
拼多多出站适配器（Phase 2a）。

实现 ChannelOutbound Protocol，包装 SendMessage / ProductManager，不接入运行时。
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from Channel.pinduoduo.utils.API.product_manager import ProductManager
from Channel.pinduoduo.utils.API.send_message import SendMessage
from utils.logger_loguru import get_logger

logger = get_logger("PinduoduoOutbound")


def _normalize_send_result(result: Any) -> bool:
    """将 SendMessage 各方法返回值归一化为是否成功。"""
    if result is None:
        return False
    if isinstance(result, str):
        return False
    if isinstance(result, dict):
        return result.get("success") is True
    logger.debug(f"无法识别的发送结果类型: {type(result)!r}")
    return False


class PinduoduoOutbound:
    """拼多多 ChannelOutbound 实现。"""

    def __init__(self, shop_id: str, user_id: str) -> None:
        self._shop_id = str(shop_id)
        self._user_id = str(user_id)
        self._sender: Optional[SendMessage] = None
        self._product_manager: Optional[ProductManager] = None

    @property
    def shop_id(self) -> str:
        return self._shop_id

    @property
    def user_id(self) -> str:
        return self._user_id

    def _get_sender(self) -> SendMessage:
        if self._sender is None:
            self._sender = SendMessage(self._shop_id, self._user_id)
        return self._sender

    def _get_product_manager(self) -> ProductManager:
        if self._product_manager is None:
            self._product_manager = ProductManager(
                shop_id=self._shop_id,
                user_id=self._user_id,
            )
        return self._product_manager

    async def send_text(self, conversation_id: str, text: str) -> bool:
        try:
            result = await asyncio.to_thread(
                self._get_sender().send_text,
                conversation_id,
                text,
            )
            return _normalize_send_result(result)
        except Exception as e:
            logger.error(f"send_text 失败: {e}")
            return False

    async def send_image(self, conversation_id: str, image_url: str) -> bool:
        try:
            result = await asyncio.to_thread(
                self._get_sender().send_image,
                conversation_id,
                image_url,
            )
            return _normalize_send_result(result)
        except Exception as e:
            logger.error(f"send_image 失败: {e}")
            return False

    async def send_goods_card(
        self,
        conversation_id: str,
        goods_id: int,
        **kwargs: Any,
    ) -> bool:
        try:
            biz_type = kwargs.get("biz_type", 2)

            def _send() -> Any:
                return self._get_sender().send_mallGoodsCard(
                    conversation_id,
                    goods_id,
                    biz_type=biz_type,
                )

            result = await asyncio.to_thread(_send)
            return _normalize_send_result(result)
        except Exception as e:
            logger.error(f"send_goods_card 失败: {e}")
            return False

    async def transfer_to_human(
        self,
        conversation_id: str,
        reason: str = "",
    ) -> bool:
        del reason  # Phase 2a 不使用，避免改变转接附带文案行为
        try:
            sender = self._get_sender()
            cs_list = await asyncio.to_thread(sender.getAssignCsList)
            if not cs_list or not isinstance(cs_list, dict):
                logger.warning("transfer_to_human: 无法获取客服列表")
                return False

            my_cs_uid = f"cs_{self._shop_id}_{self._user_id}"
            available_cs_uids = [
                uid for uid in cs_list.keys() if uid != my_cs_uid
            ]
            if not available_cs_uids:
                logger.warning(
                    f"transfer_to_human: 无可用人工客服 (shop_id={self._shop_id})"
                )
                return False

            cs_uid = available_cs_uids[0]
            result = await asyncio.to_thread(
                sender.move_conversation,
                conversation_id,
                cs_uid,
            )
            return _normalize_send_result(result)
        except Exception as e:
            logger.error(f"transfer_to_human 失败: {e}")
            return False

    async def fetch_products(
        self,
        shop_id: str,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        if str(shop_id) != self._shop_id:
            logger.debug(
                f"fetch_products shop_id 参数 ({shop_id}) 与实例 ({self._shop_id}) 不一致，使用实例配置"
            )
        page = int(filters.get("page", 1))
        size = int(filters.get("size", 10))
        try:
            result = await asyncio.to_thread(
                self._get_product_manager().get_product_list,
                page,
                size,
            )
            if isinstance(result, dict) and result.get("success"):
                products = result.get("products")
                if isinstance(products, list):
                    return products
            return []
        except Exception as e:
            logger.error(f"fetch_products 失败: {e}")
            return []

    async def fetch_order(
        self,
        shop_id: str,
        order_id: str,
        **kwargs: Any,
    ) -> Optional[dict[str, Any]]:
        del shop_id, order_id, kwargs
        return None

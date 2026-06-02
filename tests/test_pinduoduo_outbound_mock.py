"""Phase 2a：PinduoduoOutbound mock 异步行为测试。"""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import MagicMock, patch

from Channel.pinduoduo.pinduoduo_outbound import PinduoduoOutbound


class TestPinduoduoOutboundMock(unittest.TestCase):
    @patch("Channel.pinduoduo.pinduoduo_outbound.SendMessage")
    @patch("Channel.pinduoduo.pinduoduo_outbound.ProductManager")
    def test_send_text_success(self, _pm_cls: MagicMock, sm_cls: MagicMock) -> None:
        sender = MagicMock()
        sender.send_text.return_value = {"success": True}
        sm_cls.return_value = sender

        outbound = PinduoduoOutbound("shop", "user")
        ok = asyncio.run(outbound.send_text("buyer_uid", "hello"))

        self.assertTrue(ok)
        sender.send_text.assert_called_once_with("buyer_uid", "hello")

    @patch("Channel.pinduoduo.pinduoduo_outbound.SendMessage")
    @patch("Channel.pinduoduo.pinduoduo_outbound.ProductManager")
    def test_send_text_failure_string(self, _pm_cls: MagicMock, sm_cls: MagicMock) -> None:
        sender = MagicMock()
        sender.send_text.return_value = "rate limited"
        sm_cls.return_value = sender

        outbound = PinduoduoOutbound("shop", "user")
        ok = asyncio.run(outbound.send_text("buyer_uid", "hello"))

        self.assertFalse(ok)

    @patch("Channel.pinduoduo.pinduoduo_outbound.SendMessage")
    @patch("Channel.pinduoduo.pinduoduo_outbound.ProductManager")
    def test_transfer_to_human_no_prompt_text(
        self, _pm_cls: MagicMock, sm_cls: MagicMock
    ) -> None:
        sender = MagicMock()
        sender.getAssignCsList.return_value = {
            "cs_shop_user": {"username": "self"},
            "cs_other": {"username": "other"},
        }
        sender.move_conversation.return_value = {"success": True}
        sm_cls.return_value = sender

        outbound = PinduoduoOutbound("shop", "user")
        ok = asyncio.run(outbound.transfer_to_human("buyer_uid", reason="test"))

        self.assertTrue(ok)
        sender.send_text.assert_not_called()
        sender.move_conversation.assert_called_once_with("buyer_uid", "cs_other")

    @patch("Channel.pinduoduo.pinduoduo_outbound.SendMessage")
    @patch("Channel.pinduoduo.pinduoduo_outbound.ProductManager")
    def test_fetch_products(self, pm_cls: MagicMock, _sm_cls: MagicMock) -> None:
        pm = MagicMock()
        pm.get_product_list.return_value = {
            "success": True,
            "products": [{"goods_id": 1}],
            "total": 1,
        }
        pm_cls.return_value = pm

        outbound = PinduoduoOutbound("shop", "user")
        products = asyncio.run(outbound.fetch_products("shop", page=1, size=5))

        self.assertEqual(products, [{"goods_id": 1}])
        pm.get_product_list.assert_called_once_with(1, 5)

    @patch("Channel.pinduoduo.pinduoduo_outbound.SendMessage")
    @patch("Channel.pinduoduo.pinduoduo_outbound.ProductManager")
    def test_fetch_order_returns_none(self, _pm_cls: MagicMock, _sm_cls: MagicMock) -> None:
        outbound = PinduoduoOutbound("shop", "user")
        order = asyncio.run(outbound.fetch_order("shop", "order123"))
        self.assertIsNone(order)


if __name__ == "__main__":
    unittest.main()

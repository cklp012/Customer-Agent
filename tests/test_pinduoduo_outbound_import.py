"""Phase 2a：PinduoduoOutbound 模块 import 冒烟测试。"""

from __future__ import annotations

import unittest

from Channel.base.outbound import ChannelOutbound
from Channel.pinduoduo.outbound_factory import create_pinduoduo_outbound
from Channel.pinduoduo.outbound_flags import use_pinduoduo_outbound
from Channel.pinduoduo.pinduoduo_outbound import (
    PinduoduoOutbound,
    _normalize_send_result,
)


class TestPinduoduoOutboundImport(unittest.TestCase):
    def test_import_and_protocol(self) -> None:
        outbound = PinduoduoOutbound("shop1", "user1")
        self.assertIsInstance(outbound, ChannelOutbound)

    def test_factory(self) -> None:
        outbound = create_pinduoduo_outbound("shop2", "user2")
        self.assertEqual(outbound.shop_id, "shop2")
        self.assertEqual(outbound.user_id, "user2")

    def test_flag_default_false(self) -> None:
        self.assertFalse(use_pinduoduo_outbound())

    def test_normalize_send_result(self) -> None:
        self.assertFalse(_normalize_send_result(None))
        self.assertFalse(_normalize_send_result("error"))
        self.assertTrue(_normalize_send_result({"success": True}))
        self.assertFalse(_normalize_send_result({"success": False}))
        self.assertFalse(_normalize_send_result({}))


if __name__ == "__main__":
    unittest.main()

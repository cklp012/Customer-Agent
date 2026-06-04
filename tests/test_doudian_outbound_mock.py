"""Phase 10m：抖店 mock outbound + channel_outbound_registry（无网络 / 无 PDD）。"""

from __future__ import annotations

import asyncio
import unittest
from pathlib import Path
from Channel.base import ChannelOutbound
from Channel.base.types import PlatformType
from Channel.doudian.doudian_outbound import DoudianMockOutbound
from Message.handlers import channel_outbound_registry as registry
from Message.queue_naming import build_queue_name, pdd_queue_name


class TestDoudianMockOutboundBasics(unittest.TestCase):
    def test_initial_state_no_network(self) -> None:
        outbound = DoudianMockOutbound("DD_SHOP_001", "DD_ACC_001")
        self.assertEqual(outbound.sent_messages, [])
        self.assertEqual(outbound.shop_id, "DD_SHOP_001")
        self.assertEqual(outbound.account_id, "DD_ACC_001")

    def test_implements_channel_outbound_protocol(self) -> None:
        outbound = DoudianMockOutbound("s", "u")
        self.assertIsInstance(outbound, ChannelOutbound)

    def test_send_appends_sent_messages(self) -> None:
        outbound = DoudianMockOutbound("DD_SHOP_001", "DD_ACC_001")

        async def run() -> bool:
            return await outbound.send_text("DD_BUYER_001", "mock reply")

        ok = asyncio.run(run())
        self.assertTrue(ok)
        self.assertEqual(len(outbound.sent_messages), 1)


class TestDoudianMockOutboundSendText(unittest.IsolatedAsyncioTestCase):
    async def test_send_text_fields(self) -> None:
        outbound = DoudianMockOutbound("DD_SHOP_001", "DD_ACC_001")
        conversation_id = "DD_CONV_001"
        content = "您好，这是 mock 回复"

        ok = await outbound.send_text(conversation_id, content)

        self.assertTrue(ok)
        self.assertEqual(len(outbound.sent_messages), 1)
        entry = outbound.sent_messages[0]
        self.assertEqual(entry["method"], "send_text")
        self.assertEqual(entry["platform"], "doudian")
        self.assertEqual(entry["shop_id"], "DD_SHOP_001")
        self.assertEqual(entry["account_id"], "DD_ACC_001")
        self.assertEqual(entry["conversation_id"], conversation_id)
        self.assertEqual(entry["buyer_id"], conversation_id)
        self.assertEqual(entry["content"], content)
        self.assertIn("message_id", entry)
        self.assertTrue(str(entry["message_id"]).startswith("doudian-mock-msg-"))


class TestDoudianOutboundIsolation(unittest.TestCase):
    def test_module_no_pinduoduo(self) -> None:
        from Channel.doudian import doudian_outbound

        source = Path(doudian_outbound.__file__).read_text(encoding="utf-8")
        self.assertNotIn("pinduoduo", source)
        self.assertNotIn("SendMessage", source)

    def test_queue_not_pdd(self) -> None:
        name = build_queue_name("doudian", "DD_SHOP_001")
        self.assertEqual(name, "doudian_DD_SHOP_001")
        self.assertNotEqual(name, pdd_queue_name("DD_SHOP_001"))

class TestDoudianOutboundRegistry(unittest.TestCase):
    def tearDown(self) -> None:
        registry.clear()

    def test_register_get_doudian(self) -> None:
        outbound = DoudianMockOutbound("DD_SHOP_001", "DD_ACC_001")
        registry.register(PlatformType.DOUDIAN, "DD_SHOP_001", "DD_ACC_001", outbound)
        self.assertIs(
            registry.get(PlatformType.DOUDIAN, "DD_SHOP_001", "DD_ACC_001"),
            outbound,
        )

    def test_doudian_isolated_from_demo_key(self) -> None:
        doudian_ob = DoudianMockOutbound("shared", "shared")
        registry.register(PlatformType.DOUDIAN, "shared", "shared", doudian_ob)
        self.assertIsNone(registry.get(PlatformType.DEMO, "shared", "shared"))


if __name__ == "__main__":
    unittest.main()

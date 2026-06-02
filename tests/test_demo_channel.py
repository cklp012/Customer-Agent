"""Phase 6b：DemoChannel / DemoOutbound 契约测试。"""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import MagicMock

from Channel.base import BaseChannel, ChannelOutbound, ChannelStatus, PlatformType
from Channel.demo import DemoChannel, DemoOutbound


class TestDemoChannel(unittest.TestCase):
    def test_is_base_channel(self) -> None:
        self.assertIsInstance(DemoChannel(), BaseChannel)

    def test_platform_is_demo(self) -> None:
        self.assertEqual(DemoChannel.platform, PlatformType.DEMO)

    def test_outbound_before_start_raises(self) -> None:
        channel = DemoChannel()
        with self.assertRaises(RuntimeError):
            _ = channel.outbound

    def test_start_sets_connected(self) -> None:
        channel = DemoChannel()
        asyncio.run(
            channel.start_account("s1", "u1", MagicMock(), MagicMock(), MagicMock())
        )
        self.assertEqual(channel.get_status("s1", "u1"), ChannelStatus.CONNECTED)

    def test_start_calls_on_success(self) -> None:
        channel = DemoChannel()
        on_success = MagicMock()
        asyncio.run(
            channel.start_account("s1", "u1", MagicMock(), on_success, MagicMock())
        )
        on_success.assert_called_once()

    def test_stop_sets_disconnected(self) -> None:
        channel = DemoChannel()

        async def run() -> None:
            await channel.start_account("s1", "u1", MagicMock(), MagicMock(), MagicMock())
            await channel.stop_account("s1", "u1")

        asyncio.run(run())
        self.assertEqual(channel.get_status("s1", "u1"), ChannelStatus.DISCONNECTED)

    def test_login_returns_true(self) -> None:
        channel = DemoChannel()
        ok = asyncio.run(channel.login("s", "u", {}))
        self.assertTrue(ok)

    def test_logout_delegates_stop(self) -> None:
        channel = DemoChannel()

        async def run() -> None:
            await channel.start_account("s1", "u1", MagicMock(), MagicMock(), MagicMock())
            await channel.logout("s1", "u1")

        asyncio.run(run())
        self.assertEqual(channel.get_status("s1", "u1"), ChannelStatus.DISCONNECTED)

    def test_reconnect_stop_start(self) -> None:
        channel = DemoChannel()
        on_message = MagicMock()
        on_success = MagicMock()
        on_failure = MagicMock()

        async def run() -> None:
            await channel.start_account("s1", "u1", on_message, on_success, on_failure)
            on_success.reset_mock()
            await channel.reconnect("s1", "u1")

        asyncio.run(run())
        self.assertEqual(channel.get_status("s1", "u1"), ChannelStatus.CONNECTED)
        self.assertEqual(on_success.call_count, 1)

    def test_inject_synthetic_message(self) -> None:
        channel = DemoChannel(inject_synthetic_message_on_start=True)
        on_message = MagicMock()
        asyncio.run(
            channel.start_account("s1", "u1", on_message, MagicMock(), MagicMock())
        )
        on_message.assert_called_once()
        payload = on_message.call_args[0][0]
        self.assertEqual(payload["platform"], "demo")

    def test_other_account_status_disconnected(self) -> None:
        channel = DemoChannel()
        asyncio.run(
            channel.start_account("s1", "u1", MagicMock(), MagicMock(), MagicMock())
        )
        self.assertEqual(channel.get_status("other", "u1"), ChannelStatus.DISCONNECTED)


class TestDemoOutbound(unittest.TestCase):
    def test_implements_channel_outbound_protocol(self) -> None:
        outbound = DemoOutbound("shop", "user")
        self.assertIsInstance(outbound, ChannelOutbound)

    def test_send_text_appends_sent_log(self) -> None:
        outbound = DemoOutbound("shop", "user")
        ok = asyncio.run(outbound.send_text("conv1", "hello"))
        self.assertTrue(ok)
        self.assertEqual(len(outbound.sent_log), 1)
        self.assertEqual(outbound.sent_log[0]["method"], "send_text")
        self.assertEqual(outbound.sent_log[0]["text"], "hello")

    def test_send_image_goods_transfer_logged(self) -> None:
        outbound = DemoOutbound("shop", "user")

        async def run() -> None:
            await outbound.send_image("c", "http://img")
            await outbound.send_goods_card("c", 42, title="x")
            await outbound.transfer_to_human("c", reason="need human")

        asyncio.run(run())
        methods = [e["method"] for e in outbound.sent_log]
        self.assertEqual(
            methods,
            ["send_image", "send_goods_card", "transfer_to_human"],
        )

    def test_fetch_products_stub(self) -> None:
        outbound = DemoOutbound("shop", "user")
        products = asyncio.run(outbound.fetch_products("shop"))
        self.assertGreaterEqual(len(products), 1)
        self.assertIn("goods_id", products[0])
        self.assertTrue(any(e["method"] == "fetch_products" for e in outbound.sent_log))

    def test_fetch_order_stub(self) -> None:
        outbound = DemoOutbound("shop", "user")
        order = asyncio.run(outbound.fetch_order("shop", "ord-1"))
        self.assertIsNotNone(order)
        self.assertEqual(order["order_id"], "ord-1")

    def test_fetch_order_empty_id_returns_none(self) -> None:
        outbound = DemoOutbound("shop", "user")
        order = asyncio.run(outbound.fetch_order("shop", ""))
        self.assertIsNone(order)


if __name__ == "__main__":
    unittest.main()

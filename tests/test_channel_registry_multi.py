"""Phase 6b：ChannelRegistry 同时注册 PINDUODUO 与 DEMO。"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from Channel.base import ChannelRegistry, PlatformType
from Channel.demo import DemoChannel, register_demo_channel, unregister_demo_channel
from Channel.pinduoduo.channel_factory import register_pinduoduo_channel
from Channel.pinduoduo.pinduoduo_channel import PinduoduoChannel


class TestChannelRegistryMulti(unittest.TestCase):
    def setUp(self) -> None:
        register_pinduoduo_channel()
        register_demo_channel()

    def tearDown(self) -> None:
        unregister_demo_channel()
        ChannelRegistry.unregister(PlatformType.PINDUODUO)

    def test_both_registered(self) -> None:
        platforms = ChannelRegistry.registered_platforms()
        self.assertIn(PlatformType.PINDUODUO, platforms)
        self.assertIn(PlatformType.DEMO, platforms)

    def test_create_pinduoduo(self) -> None:
        channel = ChannelRegistry.create(PlatformType.PINDUODUO, legacy=MagicMock())
        self.assertIsInstance(channel, PinduoduoChannel)

    def test_create_demo(self) -> None:
        channel = ChannelRegistry.create(PlatformType.DEMO)
        self.assertIsInstance(channel, DemoChannel)

    def test_create_demo_with_kwargs(self) -> None:
        channel = ChannelRegistry.create(
            PlatformType.DEMO,
            inject_synthetic_message_on_start=True,
        )
        self.assertTrue(channel._inject_synthetic_message_on_start)

    def test_create_unknown_raises(self) -> None:
        ChannelRegistry.unregister(PlatformType.DEMO)
        with self.assertRaises(KeyError):
            ChannelRegistry.create(PlatformType.DEMO)
        register_demo_channel()


if __name__ == "__main__":
    unittest.main()

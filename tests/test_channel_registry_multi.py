"""Phase 6b：ChannelRegistry 同时注册 PINDUODUO 与 DEMO。"""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from Channel.base import ChannelRegistry, PlatformType
from Channel.demo import DemoChannel, register_demo_channel, unregister_demo_channel
from Channel.pinduoduo.channel_factory import register_pinduoduo_channel
from Channel.pinduoduo.pdd_channel import PDDChannel
from Channel.pinduoduo.pinduoduo_channel import PinduoduoChannel


class TestChannelRegistryMulti(unittest.TestCase):
    def setUp(self) -> None:
        self._wrapper_backup = os.environ.get("USE_PINDUODUO_CHANNEL_WRAPPER")
        register_pinduoduo_channel()
        register_demo_channel()

    def tearDown(self) -> None:
        unregister_demo_channel()
        ChannelRegistry.unregister(PlatformType.PINDUODUO)
        if self._wrapper_backup is None:
            os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        else:
            os.environ["USE_PINDUODUO_CHANNEL_WRAPPER"] = self._wrapper_backup

    def test_both_registered(self) -> None:
        platforms = ChannelRegistry.registered_platforms()
        self.assertIn(PlatformType.PINDUODUO, platforms)
        self.assertIn(PlatformType.DEMO, platforms)

    @patch("Channel.pinduoduo.channel_factory.PDDChannel")
    def test_create_pinduoduo_wrapper_off(self, pdd_cls: MagicMock) -> None:
        os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        legacy = MagicMock()
        pdd_cls.return_value = legacy
        channel = ChannelRegistry.create(PlatformType.PINDUODUO)
        self.assertIs(channel, legacy)
        pdd_cls.assert_called_once()

    @patch("Channel.pinduoduo.channel_factory.create_pinduoduo_channel")
    def test_create_pinduoduo_wrapper_on(self, create_mock: MagicMock) -> None:
        os.environ["USE_PINDUODUO_CHANNEL_WRAPPER"] = "true"
        wrapper = MagicMock(spec=PinduoduoChannel)
        create_mock.return_value = wrapper
        channel = ChannelRegistry.create(PlatformType.PINDUODUO, legacy=MagicMock())
        self.assertIs(channel, wrapper)
        create_mock.assert_called_once()

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

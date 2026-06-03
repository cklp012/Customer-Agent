"""Phase 9a：AutoReply ChannelRegistry 门控创建测试。"""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from Channel.base.registry import ChannelRegistry
from Channel.base.types import PlatformType
from Channel.pinduoduo.channel_factory import (
    create_auto_reply_runtime_channel,
    register_pinduoduo_channel,
)
from Channel.pinduoduo.pinduoduo_channel import PinduoduoChannel


class TestAutoreplyRegistryChannel(unittest.TestCase):
    def setUp(self) -> None:
        self._wrapper_backup = os.environ.get("USE_PINDUODUO_CHANNEL_WRAPPER")
        self._registry_backup = os.environ.get("USE_CHANNEL_REGISTRY_FOR_AUTOREPLY")
        ChannelRegistry.clear()

    def tearDown(self) -> None:
        ChannelRegistry.clear()
        if self._wrapper_backup is None:
            os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        else:
            os.environ["USE_PINDUODUO_CHANNEL_WRAPPER"] = self._wrapper_backup
        if self._registry_backup is None:
            os.environ.pop("USE_CHANNEL_REGISTRY_FOR_AUTOREPLY", None)
        else:
            os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = self._registry_backup

    @patch("Channel.pinduoduo.channel_factory.PDDChannel")
    @patch("Channel.pinduoduo.channel_factory.ChannelRegistry.create")
    def test_registry_on_wrapper_off_no_registry_create(
        self,
        create_mock: MagicMock,
        pdd_cls: MagicMock,
    ) -> None:
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = "true"
        os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        legacy = MagicMock()
        pdd_cls.return_value = legacy
        register_pinduoduo_channel()

        channel = create_auto_reply_runtime_channel()

        self.assertIs(channel, legacy)
        create_mock.assert_not_called()
        pdd_cls.assert_called_once()

    @patch("Channel.pinduoduo.channel_factory.create_pinduoduo_channel")
    @patch("Channel.pinduoduo.channel_factory.ChannelRegistry.create")
    def test_registry_on_wrapper_on_registered_uses_create(
        self,
        registry_create: MagicMock,
        create_pinduoduo_mock: MagicMock,
    ) -> None:
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = "true"
        os.environ["USE_PINDUODUO_CHANNEL_WRAPPER"] = "true"
        wrapper = MagicMock(spec=PinduoduoChannel)
        registry_create.return_value = wrapper
        register_pinduoduo_channel()

        channel = create_auto_reply_runtime_channel()

        self.assertIs(channel, wrapper)
        registry_create.assert_called_once_with(PlatformType.PINDUODUO)
        create_pinduoduo_mock.assert_not_called()

    @patch("Channel.pinduoduo.channel_factory._warn_registry_fallback")
    @patch("Channel.pinduoduo.channel_factory.create_pinduoduo_channel")
    @patch("Channel.pinduoduo.channel_factory.ChannelRegistry.create")
    def test_not_registered_fallback(
        self,
        registry_create: MagicMock,
        create_pinduoduo_mock: MagicMock,
        warn_mock: MagicMock,
    ) -> None:
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = "true"
        os.environ["USE_PINDUODUO_CHANNEL_WRAPPER"] = "true"
        wrapper = MagicMock(spec=PinduoduoChannel)
        create_pinduoduo_mock.return_value = wrapper

        channel = create_auto_reply_runtime_channel()

        self.assertIs(channel, wrapper)
        registry_create.assert_not_called()
        create_pinduoduo_mock.assert_called_once()
        warn_mock.assert_called_once()

    @patch("Channel.pinduoduo.channel_factory._warn_registry_fallback")
    @patch("Channel.pinduoduo.channel_factory.create_pinduoduo_channel")
    @patch("Channel.pinduoduo.channel_factory.ChannelRegistry.create")
    def test_create_raises_fallback_no_exception(
        self,
        registry_create: MagicMock,
        create_pinduoduo_mock: MagicMock,
        warn_mock: MagicMock,
    ) -> None:
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = "true"
        os.environ["USE_PINDUODUO_CHANNEL_WRAPPER"] = "true"
        registry_create.side_effect = RuntimeError("boom")
        wrapper = MagicMock(spec=PinduoduoChannel)
        create_pinduoduo_mock.return_value = wrapper
        register_pinduoduo_channel()

        channel = create_auto_reply_runtime_channel()

        self.assertIs(channel, wrapper)
        registry_create.assert_called_once()
        create_pinduoduo_mock.assert_called_once()
        warn_mock.assert_called_once()
        _, kwargs = warn_mock.call_args
        self.assertIsNotNone(kwargs.get("exc"))


if __name__ == "__main__":
    unittest.main()

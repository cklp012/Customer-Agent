"""Phase 9a/9b：AutoReply ChannelRegistry 门控创建测试。"""

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
    def test_registry_on_wrapper_off_registered_uses_create(
        self,
        pdd_cls: MagicMock,
    ) -> None:
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = "true"
        os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        legacy = MagicMock()
        pdd_cls.return_value = legacy
        register_pinduoduo_channel()

        with patch.object(
            ChannelRegistry, "create", wraps=ChannelRegistry.create
        ) as create_spy:
            channel = create_auto_reply_runtime_channel()

        create_spy.assert_called_once_with(PlatformType.PINDUODUO)
        self.assertIs(channel, legacy)

    @patch("Channel.pinduoduo.channel_factory.create_pinduoduo_channel")
    def test_registry_on_wrapper_on_registered_uses_create(
        self,
        create_pinduoduo_mock: MagicMock,
    ) -> None:
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = "true"
        os.environ["USE_PINDUODUO_CHANNEL_WRAPPER"] = "true"
        wrapper = MagicMock(spec=PinduoduoChannel)
        create_pinduoduo_mock.return_value = wrapper
        register_pinduoduo_channel()

        with patch.object(
            ChannelRegistry, "create", wraps=ChannelRegistry.create
        ) as create_spy:
            channel = create_auto_reply_runtime_channel()

        create_spy.assert_called_once_with(PlatformType.PINDUODUO)
        self.assertIs(channel, wrapper)
        create_pinduoduo_mock.assert_called_once()

    @patch("Channel.pinduoduo.channel_factory._warn_registry_fallback")
    @patch("Channel.pinduoduo.channel_factory._create_auto_reply_legacy")
    @patch("Channel.pinduoduo.channel_factory.ChannelRegistry.create")
    def test_not_registered_fallback(
        self,
        registry_create: MagicMock,
        legacy_mock: MagicMock,
        warn_mock: MagicMock,
    ) -> None:
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = "true"
        os.environ["USE_PINDUODUO_CHANNEL_WRAPPER"] = "true"
        fallback = MagicMock(spec=PinduoduoChannel)
        legacy_mock.return_value = fallback

        channel = create_auto_reply_runtime_channel()

        self.assertIs(channel, fallback)
        registry_create.assert_not_called()
        legacy_mock.assert_called_once()
        warn_mock.assert_called_once()

    @patch("Channel.pinduoduo.channel_factory._warn_registry_fallback")
    @patch("Channel.pinduoduo.channel_factory.PDDChannel")
    @patch("Channel.pinduoduo.channel_factory.ChannelRegistry.create")
    def test_create_raises_fallback_wrapper_off(
        self,
        registry_create: MagicMock,
        pdd_cls: MagicMock,
        warn_mock: MagicMock,
    ) -> None:
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = "true"
        os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        registry_create.side_effect = RuntimeError("boom")
        legacy = MagicMock()
        pdd_cls.return_value = legacy
        register_pinduoduo_channel()

        channel = create_auto_reply_runtime_channel()

        self.assertIs(channel, legacy)
        registry_create.assert_called_once()
        pdd_cls.assert_called_once()
        warn_mock.assert_called_once()
        _, kwargs = warn_mock.call_args
        self.assertIsNotNone(kwargs.get("exc"))

    @patch("Channel.pinduoduo.channel_factory._warn_registry_fallback")
    @patch("Channel.pinduoduo.channel_factory.create_pinduoduo_channel")
    @patch("Channel.pinduoduo.channel_factory.ChannelRegistry.create")
    def test_create_raises_fallback_wrapper_on(
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


if __name__ == "__main__":
    unittest.main()

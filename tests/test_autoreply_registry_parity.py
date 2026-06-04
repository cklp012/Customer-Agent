"""Phase 9c：AutoReply registry path 与 legacy path parity 测试。"""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from Channel.base.registry import ChannelRegistry
from Channel.base.types import PlatformType
from Channel.pinduoduo.channel_factory import (
    _create_auto_reply_legacy,
    create_auto_reply_runtime_channel,
    register_pinduoduo_channel,
)
from Channel.pinduoduo.pdd_channel import PDDChannel
from Channel.pinduoduo.pinduoduo_channel import PinduoduoChannel
from Message.runtime_bootstrap import register_default_platforms


class _EnvIsolationMixin:
    """恢复 AutoReply / bootstrap 相关环境变量。"""

    def setUp(self) -> None:
        self._wrapper_backup = os.environ.get("USE_PINDUODUO_CHANNEL_WRAPPER")
        self._registry_backup = os.environ.get("USE_CHANNEL_REGISTRY_FOR_AUTOREPLY")
        self._demo_reg_backup = os.environ.get("USE_DEMO_CHANNEL_REGISTRATION")
        os.environ.pop("USE_DEMO_CHANNEL_REGISTRATION", None)
        ChannelRegistry.clear()

    def tearDown(self) -> None:
        ChannelRegistry.clear()
        for platform in list(ChannelRegistry.registered_platforms()):
            ChannelRegistry.unregister(platform)
        for key, backup in (
            ("USE_PINDUODUO_CHANNEL_WRAPPER", self._wrapper_backup),
            ("USE_CHANNEL_REGISTRY_FOR_AUTOREPLY", self._registry_backup),
            ("USE_DEMO_CHANNEL_REGISTRATION", self._demo_reg_backup),
        ):
            if backup is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = backup


class TestAutoreplyRegistryParity(_EnvIsolationMixin, unittest.TestCase):
    @patch("Channel.pinduoduo.channel_factory.PDDChannel")
    def test_registry_equals_legacy_wrapper_off(self, pdd_cls: MagicMock) -> None:
        os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = "true"
        channel = MagicMock(spec=PDDChannel)
        pdd_cls.return_value = channel
        register_pinduoduo_channel()

        via_registry = create_auto_reply_runtime_channel()
        via_legacy = _create_auto_reply_legacy()

        self.assertIs(via_registry, channel)
        self.assertIs(via_legacy, channel)
        self.assertEqual(pdd_cls.call_count, 2)

    @patch("Channel.pinduoduo.channel_factory.create_pinduoduo_channel")
    def test_registry_equals_legacy_wrapper_on(
        self, create_mock: MagicMock
    ) -> None:
        os.environ["USE_PINDUODUO_CHANNEL_WRAPPER"] = "true"
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = "true"
        wrapper = MagicMock(spec=PinduoduoChannel)
        create_mock.return_value = wrapper
        register_pinduoduo_channel()

        via_registry = create_auto_reply_runtime_channel()
        via_legacy = _create_auto_reply_legacy()

        self.assertIs(via_registry, wrapper)
        self.assertIs(via_legacy, wrapper)
        self.assertEqual(create_mock.call_count, 2)

    @patch("Channel.pinduoduo.channel_factory.ChannelRegistry.create")
    @patch("Channel.pinduoduo.channel_factory.PDDChannel")
    def test_default_flags_use_legacy_path(
        self,
        pdd_cls: MagicMock,
        registry_create: MagicMock,
    ) -> None:
        os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        os.environ.pop("USE_CHANNEL_REGISTRY_FOR_AUTOREPLY", None)
        legacy = MagicMock(spec=PDDChannel)
        pdd_cls.return_value = legacy
        register_pinduoduo_channel()

        channel = create_auto_reply_runtime_channel()

        self.assertIs(channel, legacy)
        registry_create.assert_not_called()
        pdd_cls.assert_called_once()

    @patch("Channel.pinduoduo.channel_factory._warn_registry_fallback")
    @patch("Channel.pinduoduo.channel_factory.PDDChannel")
    def test_app_bootstrap_then_autoreply_uses_registry_without_fallback(
        self,
        pdd_cls: MagicMock,
        warn_mock: MagicMock,
    ) -> None:
        os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = "true"
        legacy = MagicMock(spec=PDDChannel)
        pdd_cls.return_value = legacy

        register_default_platforms()

        with patch.object(
            ChannelRegistry, "create", wraps=ChannelRegistry.create
        ) as create_spy:
            channel = create_auto_reply_runtime_channel()

        create_spy.assert_called_once_with(PlatformType.PINDUODUO)
        self.assertIs(channel, legacy)
        warn_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()

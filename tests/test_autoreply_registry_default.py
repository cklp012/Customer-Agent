"""Phase 9d：USE_CHANNEL_REGISTRY_FOR_AUTOREPLY 默认 true 测试。"""

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
from Channel.pinduoduo.pdd_channel import PDDChannel
from Message.autoreply_registry_flags import use_channel_registry_for_autoreply


class _EnvIsolationMixin:
    def setUp(self) -> None:
        self._registry_backup = os.environ.get("USE_CHANNEL_REGISTRY_FOR_AUTOREPLY")
        self._wrapper_backup = os.environ.get("USE_PINDUODUO_CHANNEL_WRAPPER")
        self._demo_reg_backup = os.environ.get("USE_DEMO_CHANNEL_REGISTRATION")
        os.environ.pop("USE_DEMO_CHANNEL_REGISTRATION", None)
        ChannelRegistry.clear()

    def tearDown(self) -> None:
        ChannelRegistry.clear()
        for platform in list(ChannelRegistry.registered_platforms()):
            ChannelRegistry.unregister(platform)
        for key, backup in (
            ("USE_CHANNEL_REGISTRY_FOR_AUTOREPLY", self._registry_backup),
            ("USE_PINDUODUO_CHANNEL_WRAPPER", self._wrapper_backup),
            ("USE_DEMO_CHANNEL_REGISTRATION", self._demo_reg_backup),
        ):
            if backup is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = backup


class TestAutoreplyRegistryDefault(_EnvIsolationMixin, unittest.TestCase):
    def test_unset_env_defaults_true(self) -> None:
        os.environ.pop("USE_CHANNEL_REGISTRY_FOR_AUTOREPLY", None)
        self.assertTrue(use_channel_registry_for_autoreply())

    def test_explicit_false(self) -> None:
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = "false"
        self.assertFalse(use_channel_registry_for_autoreply())

    def test_empty_env_value_disables_registry(self) -> None:
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = ""
        self.assertFalse(use_channel_registry_for_autoreply())

    def test_unknown_env_value_disables_registry(self) -> None:
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = "maybe"
        self.assertFalse(use_channel_registry_for_autoreply())

    @patch("Channel.pinduoduo.channel_factory.PDDChannel")
    def test_default_unset_uses_registry_when_registered(
        self, pdd_cls: MagicMock
    ) -> None:
        os.environ.pop("USE_CHANNEL_REGISTRY_FOR_AUTOREPLY", None)
        os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        legacy = MagicMock(spec=PDDChannel)
        pdd_cls.return_value = legacy
        register_pinduoduo_channel()

        with patch.object(
            ChannelRegistry, "create", wraps=ChannelRegistry.create
        ) as create_spy:
            channel = create_auto_reply_runtime_channel()

        create_spy.assert_called_once_with(PlatformType.PINDUODUO)
        self.assertIs(channel, legacy)

    @patch("Channel.pinduoduo.channel_factory.ChannelRegistry.create")
    @patch("Channel.pinduoduo.channel_factory.PDDChannel")
    def test_opt_out_false_uses_legacy_path(
        self,
        pdd_cls: MagicMock,
        registry_create: MagicMock,
    ) -> None:
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = "false"
        os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        legacy = MagicMock(spec=PDDChannel)
        pdd_cls.return_value = legacy
        register_pinduoduo_channel()

        channel = create_auto_reply_runtime_channel()

        self.assertIs(channel, legacy)
        registry_create.assert_not_called()
        pdd_cls.assert_called_once()


if __name__ == "__main__":
    unittest.main()

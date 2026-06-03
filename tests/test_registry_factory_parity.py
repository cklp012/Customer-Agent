"""Phase 9b：PDD registry factory parity 测试。"""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from Channel.base.registry import ChannelRegistry
from Channel.base.types import PlatformType
from Channel.pinduoduo.channel_factory import (
    _create_auto_reply_legacy,
    create_pinduoduo_registry_channel,
    register_pinduoduo_channel,
)
from Channel.pinduoduo.pdd_channel import PDDChannel
from Channel.pinduoduo.pinduoduo_channel import PinduoduoChannel


class TestRegistryFactoryParity(unittest.TestCase):
    def setUp(self) -> None:
        self._wrapper_backup = os.environ.get("USE_PINDUODUO_CHANNEL_WRAPPER")
        ChannelRegistry.clear()

    def tearDown(self) -> None:
        ChannelRegistry.clear()
        ChannelRegistry.unregister(PlatformType.PINDUODUO)
        if self._wrapper_backup is None:
            os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        else:
            os.environ["USE_PINDUODUO_CHANNEL_WRAPPER"] = self._wrapper_backup

    @patch("Channel.pinduoduo.channel_factory.PDDChannel")
    def test_registry_channel_matches_legacy_wrapper_off(
        self, pdd_cls: MagicMock
    ) -> None:
        os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        legacy = MagicMock()
        pdd_cls.return_value = legacy

        from_legacy = _create_auto_reply_legacy()
        from_registry_fn = create_pinduoduo_registry_channel()

        self.assertIs(from_legacy, legacy)
        self.assertIs(from_registry_fn, legacy)
        self.assertEqual(pdd_cls.call_count, 2)

    @patch("Channel.pinduoduo.channel_factory.create_pinduoduo_channel")
    def test_registry_channel_matches_legacy_wrapper_on(
        self, create_mock: MagicMock
    ) -> None:
        os.environ["USE_PINDUODUO_CHANNEL_WRAPPER"] = "true"
        wrapper = MagicMock(spec=PinduoduoChannel)
        create_mock.return_value = wrapper

        from_legacy = _create_auto_reply_legacy()
        from_registry_fn = create_pinduoduo_registry_channel()

        self.assertIs(from_legacy, wrapper)
        self.assertIs(from_registry_fn, wrapper)
        self.assertEqual(create_mock.call_count, 2)

    @patch("Channel.pinduoduo.channel_factory.PDDChannel")
    def test_registry_create_matches_legacy_wrapper_off(
        self, pdd_cls: MagicMock
    ) -> None:
        os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        legacy = MagicMock()
        pdd_cls.return_value = legacy
        register_pinduoduo_channel()

        from_legacy = _create_auto_reply_legacy()
        from_create = ChannelRegistry.create(PlatformType.PINDUODUO)

        self.assertIs(from_legacy, legacy)
        self.assertIs(from_create, legacy)

    @patch("Channel.pinduoduo.channel_factory.create_pinduoduo_channel")
    def test_registry_create_matches_legacy_wrapper_on(
        self, create_mock: MagicMock
    ) -> None:
        os.environ["USE_PINDUODUO_CHANNEL_WRAPPER"] = "true"
        wrapper = MagicMock(spec=PinduoduoChannel)
        create_mock.return_value = wrapper
        register_pinduoduo_channel()

        from_legacy = _create_auto_reply_legacy()
        from_create = ChannelRegistry.create(PlatformType.PINDUODUO)

        self.assertIs(from_legacy, wrapper)
        self.assertIs(from_create, wrapper)


if __name__ == "__main__":
    unittest.main()

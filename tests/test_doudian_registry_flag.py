"""Phase 11b：USE_DOUDIAN_CHANNEL_REGISTRATION + ChannelRegistry bootstrap。"""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from Channel.base.registry import ChannelRegistry
from Channel.base.types import PlatformType
from Channel.doudian.doudian_channel import DoudianMockChannel
from Channel.doudian.doudian_flags import use_doudian_channel_registration
from Channel.pinduoduo.channel_factory import (
    create_auto_reply_runtime_channel,
    register_pinduoduo_channel,
)
from Channel.pinduoduo.pdd_channel import PDDChannel
from Message.runtime_bootstrap import (
    clear_channel_registry_for_tests,
    get_default_registration_plan,
    register_default_platforms,
)

_ENV_DOUDIAN = "USE_DOUDIAN_CHANNEL_REGISTRATION"
_ENV_DEMO = "USE_DEMO_CHANNEL_REGISTRATION"
_FALSE_LIKE = ("false", "0", "no", "off", "", "maybe", "FALSE")


class _RegistryTestBase(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop(_ENV_DOUDIAN, None)
        os.environ.pop(_ENV_DEMO, None)
        clear_channel_registry_for_tests()


class TestDoudianRegistrationFlag(_RegistryTestBase):
    def test_unset_defaults_false(self) -> None:
        os.environ.pop(_ENV_DOUDIAN, None)
        self.assertFalse(use_doudian_channel_registration())

    def test_true_like_values(self) -> None:
        for val in ("true", "1", "yes", "on", "TRUE"):
            os.environ[_ENV_DOUDIAN] = val
            self.assertTrue(use_doudian_channel_registration(), msg=val)

    def test_false_like_values(self) -> None:
        os.environ.pop(_ENV_DOUDIAN, None)
        self.assertFalse(use_doudian_channel_registration())
        for val in _FALSE_LIKE:
            os.environ[_ENV_DOUDIAN] = val
            self.assertFalse(use_doudian_channel_registration(), msg=repr(val))


class TestRegisterDefaultPlatformsDoudian(_RegistryTestBase):
    def test_default_no_doudian(self) -> None:
        os.environ.pop(_ENV_DOUDIAN, None)
        os.environ.pop(_ENV_DEMO, None)
        register_default_platforms()
        self.assertTrue(ChannelRegistry.is_registered(PlatformType.PINDUODUO))
        self.assertFalse(ChannelRegistry.is_registered(PlatformType.DOUDIAN))
        with self.assertRaises(KeyError):
            ChannelRegistry.create(PlatformType.DOUDIAN)

    def test_doudian_when_flag_true(self) -> None:
        os.environ[_ENV_DOUDIAN] = "true"
        os.environ.pop(_ENV_DEMO, None)
        registered = register_default_platforms()
        self.assertIn("doudian", registered)
        channel = ChannelRegistry.create(PlatformType.DOUDIAN)
        self.assertIsInstance(channel, DoudianMockChannel)
        self.assertEqual(channel.platform, PlatformType.DOUDIAN)

    def test_false_like_not_registered(self) -> None:
        os.environ.pop(_ENV_DEMO, None)
        for val in _FALSE_LIKE:
            clear_channel_registry_for_tests()
            os.environ[_ENV_DOUDIAN] = val
            register_default_platforms()
            self.assertFalse(
                ChannelRegistry.is_registered(PlatformType.DOUDIAN),
                msg=repr(val),
            )

    def test_plan_includes_doudian_only_when_flag(self) -> None:
        os.environ.pop(_ENV_DOUDIAN, None)
        self.assertNotIn("doudian", get_default_registration_plan())
        os.environ[_ENV_DOUDIAN] = "1"
        plan = get_default_registration_plan()
        self.assertIn("pinduoduo", plan)
        self.assertIn("doudian", plan)


class TestDoudianMockChannelNoNetwork(unittest.IsolatedAsyncioTestCase):
    def tearDown(self) -> None:
        os.environ.pop(_ENV_DOUDIAN, None)
        clear_channel_registry_for_tests()

    async def test_start_stop_memory_only(self) -> None:
        os.environ[_ENV_DOUDIAN] = "true"
        register_default_platforms()
        channel = ChannelRegistry.create(PlatformType.DOUDIAN)
        on_success = MagicMock()
        await channel.start_account("DD_SHOP_001", "DD_ACC_001", MagicMock(), on_success, MagicMock())
        on_success.assert_called_once()
        self.assertIsNotNone(channel.outbound)
        await channel.stop_account("DD_SHOP_001", "DD_ACC_001")


class TestPddParityWithDoudianFlag(_RegistryTestBase):
    def test_pdd_registered_when_doudian_flag_off(self) -> None:
        os.environ.pop(_ENV_DOUDIAN, None)
        register_default_platforms()
        self.assertTrue(ChannelRegistry.is_registered(PlatformType.PINDUODUO))

    def test_pdd_registered_when_doudian_flag_on(self) -> None:
        os.environ[_ENV_DOUDIAN] = "true"
        register_default_platforms()
        self.assertTrue(ChannelRegistry.is_registered(PlatformType.PINDUODUO))
        self.assertTrue(ChannelRegistry.is_registered(PlatformType.DOUDIAN))

    @patch("Channel.pinduoduo.channel_factory.PDDChannel")
    def test_auto_reply_still_pdd_only_legacy_path(self, pdd_cls: MagicMock) -> None:
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = "false"
        os.environ[_ENV_DOUDIAN] = "true"
        clear_channel_registry_for_tests()
        register_pinduoduo_channel()
        from Channel.doudian.doudian_factory import register_doudian_channel

        register_doudian_channel()
        legacy = MagicMock(spec=PDDChannel)
        pdd_cls.return_value = legacy
        channel = create_auto_reply_runtime_channel()
        self.assertIs(channel, legacy)
        pdd_cls.assert_called_once()

    @patch("Channel.pinduoduo.channel_factory._create_auto_reply_legacy")
    def test_auto_reply_registry_path_only_pinduoduo(
        self, legacy_factory: MagicMock
    ) -> None:
        os.environ.pop("USE_CHANNEL_REGISTRY_FOR_AUTOREPLY", None)
        os.environ[_ENV_DOUDIAN] = "true"
        clear_channel_registry_for_tests()
        register_pinduoduo_channel()
        from Channel.doudian.doudian_factory import register_doudian_channel

        register_doudian_channel()
        pdd_channel = MagicMock()
        legacy_factory.return_value = pdd_channel
        channel = create_auto_reply_runtime_channel()
        self.assertIs(channel, pdd_channel)
        legacy_factory.assert_called_once()
        self.assertNotIsInstance(channel, DoudianMockChannel)


if __name__ == "__main__":
    unittest.main()

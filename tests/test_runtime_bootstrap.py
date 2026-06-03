"""Phase 8e：runtime_bootstrap 单元测试。"""

from __future__ import annotations

import os
import unittest

from Channel.base.registry import ChannelRegistry
from Channel.base.types import PlatformType
from Message.runtime_bootstrap import (
    clear_channel_registry_for_tests,
    get_bootstrap_status,
    get_default_registration_plan,
    list_available_platforms,
    register_default_platforms,
)


class TestBootstrapFlags(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("USE_DEMO_CHANNEL_REGISTRATION", None)
        clear_channel_registry_for_tests()

    def test_default_plan_only_pinduoduo(self) -> None:
        os.environ.pop("USE_DEMO_CHANNEL_REGISTRATION", None)
        self.assertEqual(get_default_registration_plan(), ["pinduoduo"])

    def test_plan_includes_demo_when_flag_on(self) -> None:
        os.environ["USE_DEMO_CHANNEL_REGISTRATION"] = "true"
        plan = get_default_registration_plan()
        self.assertIn("pinduoduo", plan)
        self.assertIn("demo", plan)


class TestRegisterDefaultPlatforms(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("USE_DEMO_CHANNEL_REGISTRATION", None)
        clear_channel_registry_for_tests()

    def test_registers_pinduoduo_by_default(self) -> None:
        os.environ.pop("USE_DEMO_CHANNEL_REGISTRATION", None)
        registered = register_default_platforms()
        self.assertIn("pinduoduo", registered)
        self.assertTrue(ChannelRegistry.is_registered(PlatformType.PINDUODUO))
        self.assertFalse(ChannelRegistry.is_registered(PlatformType.DEMO))

    def test_demo_not_registered_without_flag(self) -> None:
        os.environ.pop("USE_DEMO_CHANNEL_REGISTRATION", None)
        register_default_platforms()
        self.assertFalse(ChannelRegistry.is_registered(PlatformType.DEMO))

    def test_demo_registered_when_flag_on(self) -> None:
        os.environ["USE_DEMO_CHANNEL_REGISTRATION"] = "1"
        register_default_platforms()
        self.assertTrue(ChannelRegistry.is_registered(PlatformType.DEMO))

    def test_idempotent_registration(self) -> None:
        os.environ.pop("USE_DEMO_CHANNEL_REGISTRATION", None)
        first = register_default_platforms()
        second = register_default_platforms()
        self.assertEqual(first, second)
        self.assertTrue(ChannelRegistry.is_registered(PlatformType.PINDUODUO))


class TestBootstrapStatus(unittest.TestCase):
    def tearDown(self) -> None:
        clear_channel_registry_for_tests()

    def test_not_applied_when_empty(self) -> None:
        clear_channel_registry_for_tests()
        status = get_bootstrap_status()
        self.assertEqual(status.status, "not_applied")
        self.assertEqual(status.registered, [])

    def test_default_applied_after_register(self) -> None:
        os.environ.pop("USE_DEMO_CHANNEL_REGISTRATION", None)
        register_default_platforms()
        status = get_bootstrap_status()
        self.assertEqual(status.status, "default_applied")
        self.assertIn("pinduoduo", status.registered)

    def test_available_lists_pinduoduo_and_demo(self) -> None:
        ids = {p.platform_id for p in list_available_platforms()}
        self.assertEqual(ids, {"pinduoduo", "demo"})


if __name__ == "__main__":
    unittest.main()

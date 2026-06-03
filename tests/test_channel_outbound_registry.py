"""Phase 8b：channel_outbound_registry 单元测试。"""

from __future__ import annotations

import unittest

from Channel.base.types import PlatformType
from Channel.demo.demo_outbound import DemoOutbound
from Message.handlers import channel_outbound_registry as registry


class TestChannelOutboundRegistry(unittest.TestCase):
    def tearDown(self) -> None:
        registry.clear()

    def test_register_get_unregister(self) -> None:
        outbound = DemoOutbound("shop-a", "user-a")
        registry.register(PlatformType.DEMO, "shop-a", "user-a", outbound)
        self.assertIs(registry.get(PlatformType.DEMO, "shop-a", "user-a"), outbound)
        registry.unregister(PlatformType.DEMO, "shop-a", "user-a")
        self.assertIsNone(registry.get(PlatformType.DEMO, "shop-a", "user-a"))

    def test_clear(self) -> None:
        registry.register("demo", "s", "u", DemoOutbound("s", "u"))
        registry.clear()
        self.assertIsNone(registry.get("demo", "s", "u"))

    def test_platform_key_isolation(self) -> None:
        demo_ob = DemoOutbound("shared-shop", "shared-user")
        pdd_ob = DemoOutbound("shared-shop", "shared-user")
        registry.register(PlatformType.DEMO, "shared-shop", "shared-user", demo_ob)
        registry.register(PlatformType.PINDUODUO, "shared-shop", "shared-user", pdd_ob)
        self.assertIs(
            registry.get(PlatformType.DEMO, "shared-shop", "shared-user"),
            demo_ob,
        )
        self.assertIs(
            registry.get(PlatformType.PINDUODUO, "shared-shop", "shared-user"),
            pdd_ob,
        )


if __name__ == "__main__":
    unittest.main()

"""Phase 10k：抖店队列命名 parity（隔离于 PDD）。"""

from __future__ import annotations

import unittest

from Channel.base.types import PlatformType
from Message.queue_naming import build_queue_name, pdd_queue_name


class TestDoudianQueueNaming(unittest.TestCase):
    def test_doudian_string_platform(self) -> None:
        self.assertEqual(
            build_queue_name("doudian", "DD_SHOP_001"),
            "doudian_DD_SHOP_001",
        )

    def test_doudian_platform_type_enum(self) -> None:
        self.assertEqual(
            build_queue_name(PlatformType.DOUDIAN, "DD_SHOP_001"),
            "doudian_DD_SHOP_001",
        )

    def test_not_pdd_prefix(self) -> None:
        name = build_queue_name("doudian", "DD_SHOP_001")
        self.assertNotEqual(name, "pdd_DD_SHOP_001")
        self.assertFalse(name.startswith("pdd_"))

    def test_pinduoduo_unchanged(self) -> None:
        self.assertEqual(build_queue_name("pinduoduo", "S1"), "pdd_S1")
        self.assertEqual(pdd_queue_name("S1"), "pdd_S1")


if __name__ == "__main__":
    unittest.main()

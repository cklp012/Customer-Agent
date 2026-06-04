"""Phase 10f：build_queue_name / normalize_platform_id 契约测试。"""

from __future__ import annotations

import unittest

from bridge.context import ChannelType
from Channel.base.types import PlatformType
from Message.queue_naming import (
    build_queue_name,
    normalize_platform_id,
    queue_prefix_for_platform,
)


class TestBuildQueueName(unittest.TestCase):
    def test_pinduoduo(self) -> None:
        self.assertEqual(build_queue_name("pinduoduo", "S1"), "pdd_S1")

    def test_pdd_alias(self) -> None:
        self.assertEqual(build_queue_name("pdd", "S1"), "pdd_S1")

    def test_demo(self) -> None:
        self.assertEqual(build_queue_name("demo", "S1"), "demo_S1")

    def test_doudian(self) -> None:
        self.assertEqual(build_queue_name("doudian", "S1"), "doudian_S1")

    def test_jingdong(self) -> None:
        self.assertEqual(build_queue_name("jingdong", "S1"), "jingdong_S1")

    def test_taobao(self) -> None:
        self.assertEqual(build_queue_name("taobao", "S1"), "taobao_S1")

    def test_unknown_platform(self) -> None:
        self.assertEqual(build_queue_name("unknown", "S1"), "unknown_S1")

    def test_none_platform_defaults_pdd(self) -> None:
        self.assertEqual(build_queue_name(None, "S1"), "pdd_S1")

    def test_numeric_shop_id(self) -> None:
        self.assertEqual(build_queue_name("pinduoduo", 123), "pdd_123")

    def test_platform_type_enum(self) -> None:
        self.assertEqual(build_queue_name(PlatformType.PINDUODUO, "S1"), "pdd_S1")

    def test_channel_type_enum(self) -> None:
        self.assertEqual(build_queue_name(ChannelType.PINDUODUO, "S1"), "pdd_S1")

    def test_case_insensitive_platform(self) -> None:
        self.assertEqual(build_queue_name("PinDuoDuo", "S1"), "pdd_S1")

    def test_shop_id_none_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_queue_name("pinduoduo", None)

    def test_shop_id_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_queue_name("pinduoduo", "")

    def test_shop_id_whitespace_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_queue_name("pinduoduo", "   ")


class TestNormalizePlatformId(unittest.TestCase):
    def test_none_defaults_pinduoduo(self) -> None:
        self.assertEqual(normalize_platform_id(None), "pinduoduo")

    def test_empty_defaults_pinduoduo(self) -> None:
        self.assertEqual(normalize_platform_id(""), "pinduoduo")

    def test_pdd_maps_to_pinduoduo_id_string(self) -> None:
        self.assertEqual(normalize_platform_id("pdd"), "pdd")

    def test_prefix_helper_pinduoduo(self) -> None:
        self.assertEqual(queue_prefix_for_platform("pinduoduo"), "pdd")

    def test_prefix_helper_unknown(self) -> None:
        self.assertEqual(queue_prefix_for_platform("custom_platform"), "custom_platform")


if __name__ == "__main__":
    unittest.main()

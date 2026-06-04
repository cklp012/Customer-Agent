"""Phase 10b：AutoReply 多平台 UI helper 与启动守卫测试。"""

from __future__ import annotations

import unittest

from ui.auto_reply.platform_ui import (
    AUTOREPLY_UNSUPPORTED_TOOLTIP,
    account_matches_platform_filter,
    is_autoreply_supported,
    normalize_channel_name,
    platform_display_name,
)


class TestNormalizeChannelName(unittest.TestCase):
    def test_missing_defaults_pinduoduo(self):
        self.assertEqual(normalize_channel_name(None), "pinduoduo")
        self.assertEqual(normalize_channel_name(""), "pinduoduo")
        self.assertEqual(normalize_channel_name("   "), "pinduoduo")

    def test_lowercases_known(self):
        self.assertEqual(normalize_channel_name("PinDuoDuo"), "pinduoduo")


class TestPlatformDisplayName(unittest.TestCase):
    def test_pinduoduo_chinese(self):
        self.assertEqual(platform_display_name("pinduoduo"), "拼多多")

    def test_known_platforms(self):
        self.assertEqual(platform_display_name("doudian"), "抖店")
        self.assertEqual(platform_display_name("demo"), "Demo")

    def test_unknown_raw(self):
        self.assertEqual(platform_display_name("custom_platform"), "custom_platform")

    def test_missing_shows_pinduoduo_label(self):
        self.assertEqual(platform_display_name(None), "拼多多")


class TestAutoreplySupportGuard(unittest.TestCase):
    def test_only_pinduoduo_supported(self):
        self.assertTrue(is_autoreply_supported("pinduoduo"))
        self.assertTrue(is_autoreply_supported(None))
        self.assertFalse(is_autoreply_supported("doudian"))
        self.assertFalse(is_autoreply_supported("demo"))

    def test_tooltip_constant(self):
        self.assertIn("即将支持", AUTOREPLY_UNSUPPORTED_TOOLTIP)


class TestPlatformFilter(unittest.TestCase):
    def test_all_filter(self):
        acc = {"channel_name": "doudian"}
        self.assertTrue(account_matches_platform_filter(acc, None))

    def test_pinduoduo_filter(self):
        pdd = {"channel_name": "pinduoduo"}
        other = {"channel_name": "taobao"}
        self.assertTrue(account_matches_platform_filter(pdd, "pinduoduo"))
        self.assertFalse(account_matches_platform_filter(other, "pinduoduo"))


if __name__ == "__main__":
    unittest.main()

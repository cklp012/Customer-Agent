"""Phase 10k：抖店 fixture + mapper 契约（无 Consumer / 无网络 / 无 PDD）。"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from bridge.context import ContextType
from Channel.base.types import PlatformType
from Channel.doudian.mappers import (
    compute_doudian_routing,
    doudian_raw_to_context,
    doudian_raw_to_unified,
)

_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "doudian_messages"


def _load(name: str) -> dict:
    with open(_FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class TestFixtureLoading(unittest.TestCase):
    def test_text_fixture(self) -> None:
        raw = _load("text.json")
        self.assertEqual(raw["platform"], "doudian")
        self.assertEqual(raw["message_type"], "text")

    def test_product_inquiry_fixture(self) -> None:
        raw = _load("product_inquiry.json")
        self.assertEqual(raw["message_type"], "product_inquiry")
        self.assertIn("product_id", raw)

    def test_system_notice_fixture(self) -> None:
        raw = _load("system_notice.json")
        self.assertEqual(raw["message_type"], "system_notice")
        self.assertIn("notice_type", raw)


class TestDoudianRouting(unittest.TestCase):
    def test_text_queue(self) -> None:
        self.assertEqual(compute_doudian_routing("text"), "queue")

    def test_product_inquiry_queue(self) -> None:
        self.assertEqual(compute_doudian_routing("product_inquiry"), "queue")

    def test_system_notice_drop(self) -> None:
        self.assertEqual(compute_doudian_routing("system_notice"), "drop")

    def test_unknown_drop(self) -> None:
        self.assertEqual(compute_doudian_routing("unknown_type"), "drop")
        self.assertEqual(compute_doudian_routing(""), "drop")


class TestDoudianUnifiedMapper(unittest.TestCase):
    def _unified(self, name: str):
        return doudian_raw_to_unified(_load(name))

    def test_text_unified(self) -> None:
        u = self._unified("text.json")
        self.assertEqual(u.platform, PlatformType.DOUDIAN)
        self.assertEqual(u.content_type, "text")
        self.assertEqual(u.conversation.extra["routing"], "queue")
        self.assertEqual(u.conversation.shop_id, "DD_SHOP_001")
        self.assertEqual(u.conversation.account_id, "DD_ACC_001")
        self.assertEqual(u.conversation.buyer_uid, "DD_BUYER_001")
        self.assertEqual(u.conversation.conversation_id, "DD_CONV_001")
        self.assertEqual(u.message_id, "DD_MSG_TEXT_001")
        self.assertEqual(u.content, "你好，这个商品还有货吗？")

    def test_product_inquiry_unified(self) -> None:
        u = self._unified("product_inquiry.json")
        self.assertEqual(u.content_type, "product_inquiry")
        self.assertEqual(u.conversation.extra["routing"], "queue")
        self.assertEqual(u.message_id, "DD_MSG_PRODUCT_001")

    def test_system_notice_unified_drop(self) -> None:
        u = self._unified("system_notice.json")
        self.assertEqual(u.platform, PlatformType.DOUDIAN)
        self.assertEqual(u.content_type, "system_notice")
        self.assertEqual(u.conversation.extra["routing"], "drop")


class TestDoudianContextMapper(unittest.TestCase):
    def test_text_context(self) -> None:
        ctx = doudian_raw_to_context(_load("text.json"))
        self.assertIsNotNone(ctx)
        assert ctx is not None
        self.assertEqual(ctx.type, ContextType.TEXT)
        self.assertEqual(ctx.kwargs.channel_type, "doudian")
        self.assertEqual(ctx.kwargs.shop_id, "DD_SHOP_001")
        self.assertEqual(ctx.kwargs.user_id, "DD_ACC_001")
        self.assertEqual(ctx.kwargs.from_uid, "DD_BUYER_001")

    def test_product_inquiry_context(self) -> None:
        ctx = doudian_raw_to_context(_load("product_inquiry.json"))
        self.assertIsNotNone(ctx)
        assert ctx is not None
        self.assertEqual(ctx.type, ContextType.GOODS_INQUIRY)

    def test_system_notice_no_context(self) -> None:
        self.assertIsNone(doudian_raw_to_context(_load("system_notice.json")))
        self.assertEqual(compute_doudian_routing("system_notice"), "drop")


class TestIsolation(unittest.TestCase):
    def test_no_pinduoduo_mapper_import_in_doudian_package(self) -> None:
        doudian_pkg = sys.modules.get("Channel.doudian.mappers")
        self.assertIsNotNone(doudian_pkg)
        for mod_name, mod in list(sys.modules.items()):
            if not mod_name.startswith("Channel.doudian"):
                continue
            if mod is None:
                continue
            mod_file = getattr(mod, "__file__", "") or ""
            if "Channel\\doudian" in mod_file or "Channel/doudian" in mod_file:
                self.assertNotIn("pinduoduo", mod_file)

    def test_mapper_modules_do_not_import_pdd_at_load(self) -> None:
        import importlib

        importlib.reload(importlib.import_module("Channel.doudian.mappers.routing"))
        ctx_mod = importlib.import_module("Channel.doudian.mappers.doudian_to_context")
        uni_mod = importlib.import_module("Channel.doudian.mappers.doudian_to_unified")
        for mod in (ctx_mod, uni_mod):
            source = Path(mod.__file__).read_text(encoding="utf-8")
            self.assertNotIn("pinduoduo", source)
            self.assertNotIn("pdd_", source)


if __name__ == "__main__":
    unittest.main()

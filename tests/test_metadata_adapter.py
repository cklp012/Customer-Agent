"""Phase 7e：metadata_adapter 单元测试。"""

from __future__ import annotations

import unittest

from bridge.context import Context, ContextType, ChannelType
from Message.handlers.outbound_resolver import extract_pdd_send_context
from Message.metadata_adapter import (
    get_account_id,
    get_buyer_uid,
    get_content_type,
    get_platform,
    get_routing,
    get_send_context,
    get_shop_id,
    has_unified_metadata,
)


def _legacy_context() -> Context:
    return Context.create_pinduoduo_context(
        content="hello",
        msg_id="m1",
        from_uid="buyer_legacy",
        user_msg_type=ContextType.TEXT,
        shop_id="shop_legacy",
        user_id="user_legacy",
        username="cs_user",
        shop_name="Shop",
        channel_type=ChannelType.PINDUODUO,
    )


def _legacy_metadata() -> dict:
    return {
        "message_id": "w1",
        "timestamp": 1.0,
        "retry_count": 0,
        "shop_id": "shop_legacy",
        "user_id": "user_legacy",
        "from_uid": "buyer_legacy",
    }


def _unified_enrich_metadata() -> dict:
    base = _legacy_metadata()
    base.update(
        {
            "has_unified": True,
            "platform": "pinduoduo",
            "account_id": "user_legacy",
            "buyer_uid": "buyer_legacy",
            "conversation_id": "buyer_legacy",
            "content_type": "text",
            "routing": "queue",
            "unified_message_id": "m1",
        }
    )
    return base


class TestLegacyOnly(unittest.TestCase):
    def test_has_unified_false(self) -> None:
        self.assertFalse(has_unified_metadata(_legacy_metadata()))

    def test_send_fields(self) -> None:
        meta = _legacy_metadata()
        ctx = _legacy_context()
        self.assertEqual(get_shop_id(meta, ctx), "shop_legacy")
        self.assertEqual(get_account_id(meta, ctx), "user_legacy")
        self.assertEqual(get_buyer_uid(meta, ctx), "buyer_legacy")

    def test_content_type_from_context(self) -> None:
        meta = _legacy_metadata()
        ctx = _legacy_context()
        self.assertEqual(get_content_type(meta, ctx), "text")

    def test_routing_from_context_type(self) -> None:
        meta = _legacy_metadata()
        ctx = _legacy_context()
        self.assertEqual(get_routing(meta, ctx), "queue")

    def test_platform_fallback(self) -> None:
        self.assertEqual(get_platform(_legacy_metadata(), _legacy_context()), "pinduoduo")


class TestLegacyPlusUnified(unittest.TestCase):
    def test_has_unified_true(self) -> None:
        self.assertTrue(has_unified_metadata(_unified_enrich_metadata()))

    def test_send_context_still_legacy(self) -> None:
        meta = _unified_enrich_metadata()
        ctx = _legacy_context()
        self.assertEqual(get_send_context(meta, ctx), ("shop_legacy", "user_legacy", "buyer_legacy"))

    def test_observability_fields(self) -> None:
        meta = _unified_enrich_metadata()
        ctx = _legacy_context()
        self.assertEqual(get_platform(meta, ctx), "pinduoduo")
        self.assertEqual(get_content_type(meta, ctx), "text")
        self.assertEqual(get_routing(meta, ctx), "queue")


class TestUnifiedLegacyConflict(unittest.TestCase):
    def test_legacy_wins_over_unified_keys(self) -> None:
        meta = _unified_enrich_metadata()
        meta["account_id"] = "user_UNIFIED_WRONG"
        meta["buyer_uid"] = "buyer_UNIFIED_WRONG"
        ctx = _legacy_context()
        self.assertEqual(get_shop_id(meta, ctx), "shop_legacy")
        self.assertEqual(get_account_id(meta, ctx), "user_legacy")
        self.assertEqual(get_buyer_uid(meta, ctx), "buyer_legacy")
        self.assertEqual(get_send_context(meta, ctx), ("shop_legacy", "user_legacy", "buyer_legacy"))


class TestUnifiedOnlyFallback(unittest.TestCase):
    def test_fallback_when_legacy_keys_missing(self) -> None:
        meta = {
            "has_unified": True,
            "platform": "pinduoduo",
            "shop_id": "shop_u",
            "account_id": "user_u",
            "buyer_uid": "buyer_u",
            "content_type": "text",
            "routing": "queue",
        }
        ctx = Context.create_pinduoduo_context(
            content="x",
            user_msg_type=ContextType.TEXT,
            channel_type=ChannelType.PINDUODUO,
        )
        self.assertEqual(get_shop_id(meta, ctx), "shop_u")
        self.assertEqual(get_account_id(meta, ctx), "user_u")
        self.assertEqual(get_buyer_uid(meta, ctx), "buyer_u")


class TestEquivalenceWithExtractPdd(unittest.TestCase):
    def test_matches_extract_pdd_send_context_legacy(self) -> None:
        meta = _legacy_metadata()
        ctx = _legacy_context()
        self.assertEqual(get_send_context(meta, ctx), extract_pdd_send_context(meta, ctx))

    def test_matches_extract_pdd_send_context_unified_enrich(self) -> None:
        meta = _unified_enrich_metadata()
        ctx = _legacy_context()
        self.assertEqual(get_send_context(meta, ctx), extract_pdd_send_context(meta, ctx))

    def test_unified_only_fallback_beyond_extract_pdd(self) -> None:
        """adapter 在 legacy 键缺失时可读 account_id/buyer_uid；extract_pdd 尚不支持（7f）。"""
        meta = {
            "has_unified": True,
            "shop_id": "s1",
            "account_id": "u1",
            "buyer_uid": "b1",
        }
        ctx = Context.create_pinduoduo_context(
            content="x",
            user_msg_type=ContextType.TEXT,
            channel_type=ChannelType.PINDUODUO,
        )
        self.assertEqual(get_send_context(meta, ctx), ("s1", "u1", "b1"))
        self.assertEqual(extract_pdd_send_context(meta, ctx), ("s1", None, None))


class TestWithdrawRouting(unittest.TestCase):
    def test_immediate_routing_without_unified(self) -> None:
        meta = _legacy_metadata()
        ctx = Context.create_pinduoduo_context(
            content="hint",
            user_msg_type=ContextType.WITHDRAW,
            shop_id="s",
            user_id="u",
            from_uid="b",
            channel_type=ChannelType.PINDUODUO,
        )
        self.assertEqual(get_routing(meta, ctx), "immediate")


if __name__ == "__main__":
    unittest.main()

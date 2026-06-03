"""Phase 7f：get_send_context_for_extract 与 extract_pdd_send_context 等价性测试。"""

from __future__ import annotations

import unittest

from bridge.context import Context, ContextType, ChannelType, PinduoduoKwargs
from Message.handlers.outbound_resolver import extract_pdd_send_context
from Message.metadata_adapter import get_send_context, get_send_context_for_extract


class TestGetSendContextForExtract(unittest.TestCase):
    def test_from_metadata_only(self) -> None:
        meta = {"shop_id": "s1", "user_id": "u1", "from_uid": "b1"}
        self.assertEqual(get_send_context_for_extract(meta), ("s1", "u1", "b1"))
        self.assertEqual(get_send_context_for_extract(meta, None), ("s1", "u1", "b1"))

    def test_from_kwargs_attr(self) -> None:
        ctx = Context(
            type=ContextType.TEXT,
            kwargs=PinduoduoKwargs(shop_id="s2", user_id="u2", from_uid="b2"),
        )
        self.assertEqual(get_send_context_for_extract({}, ctx), ("s2", "u2", "b2"))

    def test_from_kwargs_dict(self) -> None:
        ctx = Context(
            type=ContextType.TEXT,
            kwargs={"shop_id": "s3", "user_id": "u3", "from_uid": "b3"},
        )
        self.assertEqual(get_send_context_for_extract({}, ctx), ("s3", "u3", "b3"))

    def test_metadata_and_kwargs_mixed(self) -> None:
        ctx = Context(
            type=ContextType.TEXT,
            kwargs=PinduoduoKwargs(user_id="u4", from_uid="b4"),
        )
        meta = {"shop_id": "s4"}
        self.assertEqual(get_send_context_for_extract(meta, ctx), ("s4", "u4", "b4"))

    def test_empty_string_preserved(self) -> None:
        meta = {"shop_id": "", "user_id": "u", "from_uid": "b"}
        ctx = Context(
            type=ContextType.TEXT,
            kwargs=PinduoduoKwargs(shop_id="from_kwargs"),
        )
        self.assertEqual(get_send_context_for_extract(meta, ctx), ("", "u", "b"))

    def test_numeric_values_strified(self) -> None:
        meta = {"shop_id": 123, "user_id": 456, "from_uid": 789}
        self.assertEqual(get_send_context_for_extract(meta), ("123", "456", "789"))

    def test_legacy_wins_over_unified_keys(self) -> None:
        meta = {
            "has_unified": True,
            "shop_id": "shop_legacy",
            "user_id": "user_legacy",
            "from_uid": "buyer_legacy",
            "account_id": "user_UNIFIED_WRONG",
            "buyer_uid": "buyer_UNIFIED_WRONG",
        }
        ctx = Context.create_pinduoduo_context(
            content="x",
            user_msg_type=ContextType.TEXT,
            channel_type=ChannelType.PINDUODUO,
        )
        self.assertEqual(
            get_send_context_for_extract(meta, ctx),
            ("shop_legacy", "user_legacy", "buyer_legacy"),
        )

    def test_unified_only_does_not_use_account_or_buyer_keys(self) -> None:
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
        self.assertEqual(get_send_context_for_extract(meta, ctx), ("s1", None, None))
        self.assertEqual(get_send_context(meta, ctx), ("s1", "u1", "b1"))

    def test_matches_extract_pdd_send_context(self) -> None:
        cases = [
            ({"shop_id": "s1", "user_id": "u1", "from_uid": "b1"}, None),
            ({}, Context(type=ContextType.TEXT, kwargs={"shop_id": "s", "user_id": "u", "from_uid": "f"})),
            (
                {"shop_id": "s4"},
                Context(type=ContextType.TEXT, kwargs=PinduoduoKwargs(user_id="u4", from_uid="b4")),
            ),
            (
                {"shop_id": "", "user_id": None, "from_uid": "b"},
                Context(type=ContextType.TEXT, kwargs=PinduoduoKwargs(shop_id="kw")),
            ),
            (
                {"has_unified": True, "shop_id": "s1", "account_id": "u1", "buyer_uid": "b1"},
                Context.create_pinduoduo_context(
                    content="x",
                    user_msg_type=ContextType.TEXT,
                    channel_type=ChannelType.PINDUODUO,
                ),
            ),
        ]
        for meta, ctx in cases:
            with self.subTest(meta=meta, ctx=ctx):
                self.assertEqual(
                    extract_pdd_send_context(meta, ctx),
                    get_send_context_for_extract(meta, ctx),
                )


if __name__ == "__main__":
    unittest.main()

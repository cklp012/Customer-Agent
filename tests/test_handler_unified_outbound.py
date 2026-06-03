"""Phase 8c：handler 接入 resolve_outbound（Route B）。"""

from __future__ import annotations

import asyncio
import os
import unittest
from unittest.mock import patch

from bridge.context import Context, ContextType
from Channel.demo.demo_outbound import DemoOutbound
from Channel.demo.mappers.demo_to_context import demo_raw_to_context
from Message.handlers import channel_outbound_registry
from Message.handlers.ai_handler import AIReplyHandler
from Message.handlers.keyword_handler import KeywordDetectionHandler

_SHOP = "handler_demo_shop"
_ACCOUNT = "handler_demo_user"
_BUYER = "handler_demo_buyer"


def _demo_meta(**extra: object) -> dict:
    base = {
        "platform": "demo",
        "shop_id": _SHOP,
        "user_id": _ACCOUNT,
        "from_uid": _BUYER,
    }
    base.update(extra)
    return base


class _EnvRestore(unittest.TestCase):
    def setUp(self) -> None:
        self._unified_backup = os.environ.get("USE_UNIFIED_OUTBOUND_RESOLVER")
        self._pdd_backup = os.environ.get("USE_PINDUODUO_OUTBOUND")

    def tearDown(self) -> None:
        channel_outbound_registry.clear()
        if self._unified_backup is None:
            os.environ.pop("USE_UNIFIED_OUTBOUND_RESOLVER", None)
        else:
            os.environ["USE_UNIFIED_OUTBOUND_RESOLVER"] = self._unified_backup
        if self._pdd_backup is None:
            os.environ.pop("USE_PINDUODUO_OUTBOUND", None)
        else:
            os.environ["USE_PINDUODUO_OUTBOUND"] = self._pdd_backup


class TestHandlerResolverSelection(_EnvRestore):
    def test_ai_flag_off_calls_pinduoduo_resolver(self) -> None:
        os.environ.pop("USE_UNIFIED_OUTBOUND_RESOLVER", None)
        with patch(
            "Message.handlers.unified_outbound_resolver.resolve_outbound"
        ) as unified_mock, patch(
            "Message.handlers.outbound_resolver.resolve_pinduoduo_outbound"
        ) as pdd_mock:
            pdd_mock.return_value = None
            handler = AIReplyHandler(bot=None)
            meta = {"shop_id": "s", "user_id": "u", "from_uid": "f"}
            ctx = Context(type=ContextType.TEXT)
            with patch.object(handler, "_send_text_legacy", return_value=True):
                asyncio.run(handler._send_reply(ctx, "hi", meta))
            pdd_mock.assert_called_once()
            unified_mock.assert_not_called()

    def test_keyword_flag_off_calls_pinduoduo_resolver(self) -> None:
        os.environ.pop("USE_UNIFIED_OUTBOUND_RESOLVER", None)
        with patch(
            "Message.handlers.unified_outbound_resolver.resolve_outbound"
        ) as unified_mock, patch(
            "Message.handlers.outbound_resolver.resolve_pinduoduo_outbound"
        ) as pdd_mock:
            pdd_mock.return_value = None
            handler = KeywordDetectionHandler()
            handler.keywords = {"转人工"}
            ctx = Context(type=ContextType.TEXT, content="请转人工")
            meta = {"shop_id": "s", "user_id": "u", "from_uid": "f"}
            with patch.object(handler, "_transfer_to_human_legacy", return_value=False):
                asyncio.run(handler.handle(ctx, meta))
            pdd_mock.assert_called_once()
            unified_mock.assert_not_called()


class TestDemoHandlerOutbound(_EnvRestore):
    def setUp(self) -> None:
        super().setUp()
        os.environ["USE_UNIFIED_OUTBOUND_RESOLVER"] = "true"
        os.environ.pop("USE_PINDUODUO_OUTBOUND", None)

    def test_ai_demo_registry_send_text(self) -> None:
        outbound = DemoOutbound(_SHOP, _ACCOUNT)
        channel_outbound_registry.register("demo", _SHOP, _ACCOUNT, outbound)
        raw = {
            "platform": "demo",
            "message_id": "ai-demo-1",
            "content": "in",
            "from_uid": _BUYER,
        }
        ctx = demo_raw_to_context(raw, _SHOP, _ACCOUNT)
        meta = _demo_meta()
        handler = AIReplyHandler(bot=None)
        ok = asyncio.run(handler._send_reply(ctx, "demo-reply", meta))
        self.assertTrue(ok)
        self.assertGreaterEqual(len(outbound.sent_log), 1)
        self.assertEqual(outbound.sent_log[-1]["method"], "send_text")
        self.assertEqual(outbound.sent_log[-1]["conversation_id"], _BUYER)

    def test_keyword_demo_metadata_transfer(self) -> None:
        outbound = DemoOutbound(_SHOP, _ACCOUNT)
        handler = KeywordDetectionHandler()
        handler.keywords = {"转人工"}
        ctx = Context(type=ContextType.TEXT, content="我要转人工")
        meta = _demo_meta(outbound=outbound)
        ok = asyncio.run(handler.handle(ctx, meta))
        self.assertTrue(ok)
        methods = [e["method"] for e in outbound.sent_log]
        self.assertIn("transfer_to_human", methods)


class TestPddLegacyFallbackWithUnifiedOn(_EnvRestore):
    def test_pdd_unified_on_outbound_off_falls_back_legacy(self) -> None:
        os.environ["USE_UNIFIED_OUTBOUND_RESOLVER"] = "true"
        os.environ.pop("USE_PINDUODUO_OUTBOUND", None)
        handler = AIReplyHandler(bot=None)
        meta = {
            "platform": "pinduoduo",
            "shop_id": "pdd_s",
            "user_id": "pdd_u",
            "from_uid": "pdd_b",
        }
        ctx = Context(type=ContextType.TEXT)
        with patch.object(handler, "_send_text_legacy", return_value=True) as legacy_mock:
            ok = asyncio.run(handler._send_reply(ctx, "legacy-path", meta))
        self.assertTrue(ok)
        legacy_mock.assert_called_once_with("pdd_s", "pdd_u", "pdd_b", "legacy-path")


if __name__ == "__main__":
    unittest.main()

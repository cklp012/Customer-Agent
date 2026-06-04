"""Phase 11g：Doudian handler unified outbound path（测试内 USE_UNIFIED_OUTBOUND_RESOLVER=true）。"""

from __future__ import annotations

import asyncio
import os
import unittest
from unittest.mock import patch

from bridge.context import Context, ContextType
from Channel.base.types import PlatformType
from Channel.doudian.doudian_channel import DoudianMockChannel
from Channel.doudian.doudian_outbound import DoudianMockOutbound
from Message.handlers import channel_outbound_registry
from Message.handlers.ai_handler import AIReplyHandler
from Message.handlers.keyword_handler import KeywordDetectionHandler
from Message.handlers.unified_outbound_flags import use_unified_outbound_resolver
from Message.handlers.unified_outbound_resolver import resolve_outbound

_SHOP = "DD_SHOP_001"
_ACCOUNT = "DD_ACC_001"
_BUYER = "DD_BUYER_001"
_REPLY = "doudian-handler-reply"


def _doudian_meta(**extra: object) -> dict:
    base = {
        "platform": "doudian",
        "shop_id": _SHOP,
        "user_id": _ACCOUNT,
        "from_uid": _BUYER,
    }
    base.update(extra)
    return base


def _noop_success() -> None:
    return None


class _UnifiedEnvBase(unittest.TestCase):
    """测试内开启 unified resolver；tearDown 恢复 env 与 registry。"""

    def setUp(self) -> None:
        self._unified_backup = os.environ.get("USE_UNIFIED_OUTBOUND_RESOLVER")
        self._pdd_backup = os.environ.get("USE_PINDUODUO_OUTBOUND")
        os.environ["USE_UNIFIED_OUTBOUND_RESOLVER"] = "true"
        os.environ.pop("USE_PINDUODUO_OUTBOUND", None)
        channel_outbound_registry.clear()

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


class TestUnifiedFlagDefault(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("USE_UNIFIED_OUTBOUND_RESOLVER", None)

    def test_unset_defaults_false(self) -> None:
        os.environ.pop("USE_UNIFIED_OUTBOUND_RESOLVER", None)
        self.assertFalse(use_unified_outbound_resolver())


class TestDoudianHandlerOutboundH1a(_UnifiedEnvBase):
    def test_manual_register_send_reply_uses_doudian_mock(self) -> None:
        outbound = DoudianMockOutbound(_SHOP, _ACCOUNT)
        channel_outbound_registry.register(
            PlatformType.DOUDIAN,
            _SHOP,
            _ACCOUNT,
            outbound,
        )
        handler = AIReplyHandler(bot=None)
        ctx = Context(type=ContextType.TEXT)
        meta = _doudian_meta()

        with patch(
            "Message.handlers.outbound_resolver.resolve_pinduoduo_outbound"
        ) as pdd_resolver_mock, patch.object(
            handler, "_send_text_legacy"
        ) as legacy_mock:
            ok = asyncio.run(handler._send_reply(ctx, _REPLY, meta))

        self.assertTrue(ok)
        pdd_resolver_mock.assert_not_called()
        legacy_mock.assert_not_called()
        self.assertEqual(len(outbound.sent_messages), 1)
        entry = outbound.sent_messages[0]
        self.assertEqual(entry["method"], "send_text")
        self.assertEqual(entry["platform"], "doudian")
        self.assertEqual(entry["shop_id"], _SHOP)
        self.assertEqual(entry["account_id"], _ACCOUNT)
        self.assertEqual(entry["buyer_id"], _BUYER)
        self.assertEqual(entry["conversation_id"], _BUYER)
        self.assertEqual(entry["content"], _REPLY)


class TestDoudianHandlerOutboundH1b(_UnifiedEnvBase):
    def test_channel_start_send_reply_hits_channel_outbound(self) -> None:
        channel = DoudianMockChannel()
        outbound_ref: DoudianMockOutbound | None = None

        async def run() -> None:
            nonlocal outbound_ref
            await channel.start_account(
                _SHOP,
                _ACCOUNT,
                lambda *_a, **_k: None,
                _noop_success,
                lambda _msg: None,
            )
            outbound_ref = channel.outbound
            self.assertIs(resolve_outbound(_doudian_meta()), outbound_ref)
            handler = AIReplyHandler(bot=None)
            ctx = Context(type=ContextType.TEXT)
            with patch.object(handler, "_send_text_legacy") as legacy_mock:
                ok = await handler._send_reply(ctx, _REPLY, _doudian_meta())
            self.assertTrue(ok)
            legacy_mock.assert_not_called()
            await channel.stop_account(_SHOP, _ACCOUNT)
            self.assertIsNone(
                channel_outbound_registry.get(PlatformType.DOUDIAN, _SHOP, _ACCOUNT)
            )

        asyncio.run(run())
        assert outbound_ref is not None
        self.assertEqual(len(outbound_ref.sent_messages), 1)
        self.assertEqual(outbound_ref.sent_messages[0]["content"], _REPLY)


class TestDoudianHandlerOutboundH2(_UnifiedEnvBase):
    def test_keyword_transfer_to_human_via_registry(self) -> None:
        outbound = DoudianMockOutbound(_SHOP, _ACCOUNT)
        channel_outbound_registry.register(
            PlatformType.DOUDIAN,
            _SHOP,
            _ACCOUNT,
            outbound,
        )
        handler = KeywordDetectionHandler()
        handler.keywords = {"转人工"}
        ctx = Context(type=ContextType.TEXT, content="我要转人工")
        meta = _doudian_meta()

        with patch(
            "Message.handlers.outbound_resolver.resolve_pinduoduo_outbound"
        ) as pdd_resolver_mock, patch.object(
            handler, "_transfer_to_human_legacy"
        ) as legacy_mock:
            ok = asyncio.run(handler.handle(ctx, meta))

        self.assertTrue(ok)
        pdd_resolver_mock.assert_not_called()
        legacy_mock.assert_not_called()
        methods = [entry["method"] for entry in outbound.sent_messages]
        self.assertIn("transfer_to_human", methods)
        transfer = next(
            e for e in outbound.sent_messages if e["method"] == "transfer_to_human"
        )
        self.assertEqual(transfer["platform"], "doudian")
        self.assertEqual(transfer["conversation_id"], _BUYER)


class TestDoudianHandlerOutboundH3(_UnifiedEnvBase):
    def test_no_registry_does_not_call_pdd_resolver_falls_back_legacy(self) -> None:
        handler = AIReplyHandler(bot=None)
        ctx = Context(type=ContextType.TEXT)
        meta = _doudian_meta()

        with patch(
            "Message.handlers.outbound_resolver.resolve_pinduoduo_outbound"
        ) as pdd_resolver_mock, patch.object(
            handler, "_send_text_legacy", return_value=True
        ) as legacy_mock:
            ok = asyncio.run(handler._send_reply(ctx, _REPLY, meta))

        self.assertTrue(ok)
        pdd_resolver_mock.assert_not_called()
        legacy_mock.assert_called_once_with(_SHOP, _ACCOUNT, _BUYER, _REPLY)


if __name__ == "__main__":
    unittest.main()

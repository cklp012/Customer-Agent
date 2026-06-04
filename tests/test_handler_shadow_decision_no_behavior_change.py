"""Phase 13b: AIReplyHandler shadow logging must not change send behavior."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from bridge.context import Context, ContextType, ChannelType
from Message.gates.intent_types import IntentBucket, SendMode
from Message.gates.shadow_decision_logger import shadow_decision_logger
from Message.handlers.ai_handler import AIReplyHandler

_AI_REPLY = "shadow test reply"
_BUYER = "buyer_uid_12345678"


def _metadata() -> dict:
    return {
        "message_id": "w-shadow-1",
        "shop_id": "shop_1",
        "user_id": "user_1",
        "from_uid": _BUYER,
    }


def _context(*, content: str = "这款商品怎么样") -> Context:
    return Context.create_pinduoduo_context(
        content=content,
        from_uid=_BUYER,
        username="nick",
        user_msg_type=ContextType.TEXT,
        shop_id="shop_1",
        user_id="user_1",
        channel_type=ChannelType.PINDUODUO,
    )


class TestHandlerShadowNoBehaviorChange(unittest.TestCase):
    def setUp(self) -> None:
        shadow_decision_logger.clear()

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    def test_handle_still_calls_send_reply_and_logs_shadow(
        self,
        _ai_mock: AsyncMock,
        send_mock: AsyncMock,
    ) -> None:
        handler = AIReplyHandler(bot=MagicMock())
        ok = asyncio.run(handler.handle(_context(), _metadata()))

        self.assertTrue(ok)
        send_mock.assert_awaited_once()
        self.assertEqual(len(shadow_decision_logger), 1)
        record = shadow_decision_logger.all()[0]
        self.assertFalse(record.send_decision.product_gate_enabled)
        self.assertEqual(record.send_decision.send_mode, SendMode.LEGACY_PASSTHROUGH)
        self.assertEqual(record.classification.intent_bucket, IntentBucket.ALLOWED)

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    @patch(
        "Message.gates.shadow_decision_logger.append_shadow_decision_from_handler",
        side_effect=RuntimeError("shadow boom"),
    )
    def test_shadow_failure_still_sends(
        self,
        _shadow_mock: MagicMock,
        _ai_mock: AsyncMock,
        send_mock: AsyncMock,
    ) -> None:
        handler = AIReplyHandler(bot=MagicMock())
        ok = asyncio.run(handler.handle(_context(content="我要退款"), _metadata()))

        self.assertTrue(ok)
        send_mock.assert_awaited_once()

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    @patch("Message.gates.guarded_send.evaluate_guarded_send")
    def test_guarded_send_not_used_on_handle(
        self,
        guarded_mock: MagicMock,
        _ai_mock: AsyncMock,
        send_mock: AsyncMock,
    ) -> None:
        handler = AIReplyHandler(bot=MagicMock())
        asyncio.run(handler.handle(_context(), _metadata()))

        guarded_mock.assert_not_called()
        send_mock.assert_awaited_once()

    @patch("Message.handlers.ai_handler.AIReplyHandler._send_text_legacy")
    @patch("Message.handlers.outbound_resolver.resolve_pinduoduo_outbound", return_value=None)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    def test_legacy_send_path_unchanged_when_outbound_none(
        self,
        _ai_mock: AsyncMock,
        _resolve_mock: MagicMock,
        legacy_mock: MagicMock,
    ) -> None:
        legacy_mock.return_value = True
        handler = AIReplyHandler(bot=MagicMock())
        meta = _metadata()
        ctx = _context()
        ok = asyncio.run(handler._send_reply(ctx, _AI_REPLY, meta))

        self.assertTrue(ok)
        legacy_mock.assert_called_once()
        self.assertEqual(len(shadow_decision_logger), 0)


if __name__ == "__main__":
    unittest.main()

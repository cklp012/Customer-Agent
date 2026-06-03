"""Phase 7h：handler debug observability 接线测试。"""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from bridge.context import Context, ContextType, ChannelType
from Message.handlers.ai_handler import AIReplyHandler
from Message.handlers.keyword_handler import KeywordDetectionHandler
from Message.metadata_observability import log_handler_observation


_SECRET_CONTENT = "user_secret_message_xyz"
_FULL_BUYER_UID = "buyer_uid_12345678"


def _metadata() -> dict:
    return {
        "message_id": "w1",
        "retry_count": 0,
        "shop_id": "shop1",
        "user_id": "user1",
        "from_uid": _FULL_BUYER_UID,
    }


def _context(*, content: str = _SECRET_CONTENT) -> Context:
    return Context.create_pinduoduo_context(
        content=content,
        msg_id="m1",
        from_uid=_FULL_BUYER_UID,
        user_msg_type=ContextType.TEXT,
        shop_id="shop1",
        user_id="user1",
        channel_type=ChannelType.PINDUODUO,
    )


def _debug_output(debug_mock) -> str:
    return " ".join(str(call) for call in debug_mock.call_args_list)


class TestLogHandlerObservation(unittest.TestCase):
    def test_logs_handler_observation_line(self) -> None:
        logger = MagicMock()
        log_handler_observation(logger, _metadata(), _context(), "TestHandler")
        logger.debug.assert_called_once()
        args = logger.debug.call_args[0]
        self.assertIn("handler_observation", args[0])
        self.assertIn("platform=pinduoduo", args[1])


class TestAIHandlerObservationDebug(unittest.TestCase):
    @patch.object(AIReplyHandler, "_handle_fallback", new_callable=AsyncMock, return_value=True)
    def test_handle_logs_safe_observation(self, _fallback_mock) -> None:
        handler = AIReplyHandler(bot=None)
        with patch.object(handler.logger, "debug") as debug_mock:
            asyncio.run(handler.handle(_context(), _metadata()))

        output = _debug_output(debug_mock)
        self.assertIn("handler_observation", output)
        self.assertIn("platform=", output)
        self.assertNotIn(_SECRET_CONTENT, output)
        self.assertNotIn(_FULL_BUYER_UID, output)


class TestKeywordHandlerObservationDebug(unittest.TestCase):
    @patch("Message.handlers.outbound_resolver.resolve_pinduoduo_outbound")
    def test_handle_logs_safe_observation(self, resolve_mock) -> None:
        outbound = MagicMock()
        outbound.transfer_to_human = AsyncMock(return_value=True)
        resolve_mock.return_value = outbound

        handler = KeywordDetectionHandler()
        with patch.object(handler.logger, "debug") as debug_mock:
            asyncio.run(handler.handle(_context(), _metadata()))

        output = _debug_output(debug_mock)
        self.assertIn("handler_observation", output)
        self.assertIn("platform=", output)
        self.assertNotIn(_SECRET_CONTENT, output)
        self.assertNotIn(_FULL_BUYER_UID, output)

    def test_can_handle_does_not_log_full_content(self) -> None:
        handler = KeywordDetectionHandler()
        handler.keywords = {"转人工"}

        ctx = _context(content=f"请{_SECRET_CONTENT}转人工")
        with patch.object(handler.logger, "debug") as debug_mock:
            self.assertTrue(handler.can_handle(ctx))

        output = _debug_output(debug_mock)
        self.assertIn("转人工", output)
        self.assertNotIn(_SECRET_CONTENT, output)


if __name__ == "__main__":
    unittest.main()

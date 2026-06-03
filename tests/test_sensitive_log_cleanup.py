"""Phase 7i：sensitive INFO log cleanup 测试。"""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from bridge.context import Context, ContextType, ChannelType
from Message.core.handlers import CatchAllHandler
from Message.handlers.ai_handler import AIReplyHandler
from Message.handlers.base import BaseHandler


_SECRET_CONTENT = "secret_user_message_xyz"
_FULL_UID = "buyer_uid_12345678"
_AI_REPLY = "AI generated secret reply content"
_FALLBACK_REPLY = "亲，感谢您的咨询！客服正在为您处理，请稍等片刻。"


def _metadata() -> dict:
    return {
        "message_id": "w1",
        "shop_id": "s1",
        "user_id": _FULL_UID,
        "from_uid": _FULL_UID,
    }


def _context(*, content: str = _SECRET_CONTENT) -> Context:
    return Context.create_pinduoduo_context(
        content=content,
        from_uid=_FULL_UID,
        username="buyer_nickname",
        user_msg_type=ContextType.TEXT,
        shop_id="s1",
        user_id="u1",
        channel_type=ChannelType.PINDUODUO,
    )


def _info_output(info_mock) -> str:
    return " ".join(str(call) for call in info_mock.call_args_list)


class _TestHandler(BaseHandler):
    def can_handle(self, context: Context) -> bool:
        return True

    async def handle(self, context: Context, metadata: dict) -> bool:
        return True


class TestBaseHandlerLogMessage(unittest.TestCase):
    def test_no_secret_content(self) -> None:
        handler = _TestHandler("TestHandler")
        with patch.object(handler.logger, "info") as info_mock:
            asyncio.run(handler.log_message(_context(), "测试动作", "reply_len=10"))

        output = _info_output(info_mock)
        self.assertNotIn(_SECRET_CONTENT, output)
        self.assertIn("content_len=", output)
        self.assertIn("type=text", output)

    def test_no_full_uid(self) -> None:
        handler = _TestHandler("TestHandler")
        with patch.object(handler.logger, "info") as info_mock:
            asyncio.run(handler.log_message(_context(), "测试动作"))

        output = _info_output(info_mock)
        self.assertNotIn(_FULL_UID, output)
        self.assertIn("buyer=***5678", output)


class TestAIHandlerSensitiveLogs(unittest.TestCase):
    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    def test_success_path_reply_len_only(self, _reply_mock, _send_mock) -> None:
        handler = AIReplyHandler(bot=MagicMock())
        with patch.object(handler.logger, "info") as info_mock:
            asyncio.run(handler.handle(_context(), _metadata()))

        output = _info_output(info_mock)
        self.assertIn("reply_len=", output)
        self.assertNotIn(_AI_REPLY, output)

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=False)
    def test_fallback_reply_len_only(self, _send_mock) -> None:
        handler = AIReplyHandler(bot=None)
        with patch.object(handler.logger, "info") as info_mock:
            asyncio.run(handler.handle(_context(), _metadata()))

        output = _info_output(info_mock)
        self.assertIn(f"reply_len={len(_FALLBACK_REPLY)}", output)
        self.assertNotIn(_FALLBACK_REPLY, output)


class TestCatchAllHandlerSensitiveLogs(unittest.TestCase):
    def test_no_secret_content_or_full_user_id(self) -> None:
        handler = CatchAllHandler()
        with patch.object(handler.logger, "info") as info_mock:
            asyncio.run(handler.handle(_context(), _metadata()))

        output = _info_output(info_mock)
        self.assertNotIn(_SECRET_CONTENT, output)
        self.assertNotIn(_FULL_UID, output)
        self.assertIn("content_len", output)


if __name__ == "__main__":
    unittest.main()

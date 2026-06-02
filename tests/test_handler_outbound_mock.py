"""Phase 2b：handler outbound-first mock 测试（可选）。"""

from __future__ import annotations

import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from bridge.context import Context, ContextType
from Message.handlers.ai_handler import AIReplyHandler
from Message.handlers.keyword_handler import KeywordDetectionHandler


class TestAIHandlerOutboundMock(unittest.TestCase):
    def setUp(self) -> None:
        self._env_backup = os.environ.get("USE_PINDUODUO_OUTBOUND")

    def tearDown(self) -> None:
        if self._env_backup is None:
            os.environ.pop("USE_PINDUODUO_OUTBOUND", None)
        else:
            os.environ["USE_PINDUODUO_OUTBOUND"] = self._env_backup

    @patch("Message.handlers.outbound_resolver.resolve_pinduoduo_outbound")
    def test_outbound_success_skips_legacy(self, resolve_mock) -> None:
        outbound = MagicMock()
        outbound.send_text = AsyncMock(return_value=True)
        resolve_mock.return_value = outbound

        handler = AIReplyHandler(bot=None)
        meta = {"shop_id": "s", "user_id": "u", "from_uid": "f"}
        ctx = Context(type=ContextType.TEXT)
        ok = asyncio.run(handler._send_reply(ctx, "hi", meta))

        self.assertTrue(ok)
        outbound.send_text.assert_awaited_once_with("f", "hi")

    @patch("Message.handlers.ai_handler.AIReplyHandler._send_text_legacy")
    @patch("Message.handlers.outbound_resolver.resolve_pinduoduo_outbound")
    def test_outbound_fail_falls_back_legacy(
        self, resolve_mock, legacy_mock
    ) -> None:
        outbound = MagicMock()
        outbound.send_text = AsyncMock(return_value=False)
        resolve_mock.return_value = outbound
        legacy_mock.return_value = True

        handler = AIReplyHandler(bot=None)
        meta = {"shop_id": "s", "user_id": "u", "from_uid": "f"}
        ctx = Context(type=ContextType.TEXT)
        ok = asyncio.run(handler._send_reply(ctx, "hi", meta))

        self.assertTrue(ok)
        legacy_mock.assert_called_once()


class TestKeywordHandlerOutboundMock(unittest.TestCase):
    @patch("Message.handlers.keyword_handler.KeywordDetectionHandler._transfer_to_human_legacy")
    @patch("Message.handlers.outbound_resolver.resolve_pinduoduo_outbound")
    def test_outbound_success_skips_legacy(
        self, resolve_mock, legacy_mock
    ) -> None:
        outbound = MagicMock()
        outbound.transfer_to_human = AsyncMock(return_value=True)
        resolve_mock.return_value = outbound

        handler = KeywordDetectionHandler()
        ctx = Context(type=ContextType.TEXT, content="转人工")
        meta = {"shop_id": "s", "user_id": "u", "from_uid": "f"}

        ok = asyncio.run(handler.handle(ctx, meta))

        self.assertTrue(ok)
        legacy_mock.assert_not_called()

    @patch("Message.handlers.keyword_handler.KeywordDetectionHandler._transfer_to_human_legacy")
    @patch("Message.handlers.outbound_resolver.resolve_pinduoduo_outbound")
    def test_outbound_fail_falls_back_legacy(
        self, resolve_mock, legacy_mock
    ) -> None:
        outbound = MagicMock()
        outbound.transfer_to_human = AsyncMock(return_value=False)
        resolve_mock.return_value = outbound
        legacy_mock.return_value = False

        handler = KeywordDetectionHandler()
        ctx = Context(type=ContextType.TEXT, content="转人工")
        meta = {"shop_id": "s", "user_id": "u", "from_uid": "f"}

        ok = asyncio.run(handler.handle(ctx, meta))

        self.assertFalse(ok)
        legacy_mock.assert_called_once_with("s", "u", "f")


if __name__ == "__main__":
    unittest.main()

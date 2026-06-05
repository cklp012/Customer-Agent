"""Phase 13e: handler preview path → dashboard ReplyLog read model alignment."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from bridge.context import Context, ContextType, ChannelType
from Message.gates.intent_types import SendMode
from Message.gates.preview_log import preview_log
from Message.gates.product_gate_config import (
    TestShopAllowlistEntry,
    clear_test_shop_allowlist,
    set_test_shop_allowlist,
)
from Message.gates.reply_log_projection import list_preview_reply_logs
from Message.handlers.ai_handler import AIReplyHandler

_AI_REPLY = "aligned preview suggestion"
_BUYER = "buyer_uid_align_test"
_WS = "ws-test-0001"
_SHOP = "shop_pdd_preview_test"
_ACCOUNT = "acc_pdd_preview_test"
_BUYER_MSG = "这款商品还有库存吗"


def _allowlist() -> None:
    set_test_shop_allowlist(
        [
            TestShopAllowlistEntry(
                workspace_id=_WS,
                shop_id=_SHOP,
                account_id=_ACCOUNT,
            )
        ]
    )


def _test_metadata(**kwargs) -> dict:
    base = {
        "message_id": "w-align-1",
        "workspace_id": _WS,
        "shop_id": _SHOP,
        "account_id": _ACCOUNT,
        "user_id": "user_preview",
        "from_uid": _BUYER,
        "platform_id": "pinduoduo",
    }
    base.update(kwargs)
    return base


def _legacy_metadata(**kwargs) -> dict:
    base = {
        "message_id": "w-legacy-align",
        "shop_id": "shop_production_like",
        "account_id": "acc_production_like",
        "user_id": "user_1",
        "from_uid": _BUYER,
        "platform_id": "pinduoduo",
    }
    base.update(kwargs)
    return base


def _context(*, content: str = _BUYER_MSG, shop_id: str = _SHOP) -> Context:
    return Context.create_pinduoduo_context(
        content=content,
        from_uid=_BUYER,
        username="nick",
        user_msg_type=ContextType.TEXT,
        shop_id=shop_id,
        user_id="user_preview",
        channel_type=ChannelType.PINDUODUO,
    )


class TestHandlerPreviewReplyLogAlignment(unittest.TestCase):
    def setUp(self) -> None:
        preview_log.clear()
        clear_test_shop_allowlist()

    def tearDown(self) -> None:
        preview_log.clear()
        clear_test_shop_allowlist()

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    def test_test_shop_preview_projects_reply_log(
        self,
        send_text_mock: MagicMock,
        _ai_mock: AsyncMock,
        send_reply_mock: AsyncMock,
    ) -> None:
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        ok = asyncio.run(handler.handle(_context(), _test_metadata()))

        self.assertTrue(ok)
        send_reply_mock.assert_not_awaited()
        send_text_mock.assert_not_called()

        items = list_preview_reply_logs()
        self.assertEqual(len(items), 1)
        item = items[0]
        expected_buyer_message = AIReplyHandler(bot=MagicMock()).preprocessor.process(
            _BUYER_MSG, ContextType.TEXT
        )
        self.assertEqual(item.buyer_message, expected_buyer_message)
        self.assertEqual(item.ai_suggested_reply, _AI_REPLY)
        self.assertEqual(item.send_status, "not_sent_preview")
        self.assertEqual(item.send_mode, SendMode.PREVIEW_ONLY.value)
        self.assertEqual(item.workspace_id, _WS)
        self.assertEqual(item.platform_id, "pinduoduo")
        self.assertEqual(item.shop_id, _SHOP)
        self.assertEqual(item.account_id, _ACCOUNT)
        self.assertEqual(item.buyer_id, _BUYER)
        self.assertIsNone(item.final_reply)
        self.assertIn("Preview mode", item.not_sent_explanation)
        self.assertTrue(item.reply_log_id)

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    def test_blocked_refund_human_takeover_in_reply_log(
        self,
        _ai_mock: AsyncMock,
        send_mock: AsyncMock,
    ) -> None:
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        asyncio.run(handler.handle(_context(content="我要退款"), _test_metadata()))

        send_mock.assert_not_awaited()
        item = list_preview_reply_logs()[0]
        self.assertEqual(item.send_status, "not_sent_human_takeover")
        self.assertEqual(item.send_mode, SendMode.HUMAN_TAKEOVER.value)
        self.assertIn("Human takeover", item.not_sent_explanation)

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    def test_non_test_shop_no_preview_reply_log(
        self,
        _ai_mock: AsyncMock,
        send_mock: AsyncMock,
    ) -> None:
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        asyncio.run(
            handler.handle(_context(shop_id="shop_production_like"), _legacy_metadata())
        )

        send_mock.assert_awaited_once()
        self.assertEqual(list_preview_reply_logs(), [])


if __name__ == "__main__":
    unittest.main()

"""Phase 7j：remaining UID warning/debug 日志脱敏测试。"""

from __future__ import annotations

import asyncio
import os
import unittest
from unittest.mock import MagicMock, patch

from bridge.context import Context, ContextType, ChannelType
from Message.handlers.ai_handler import AIReplyHandler
from Message.handlers.keyword_handler import KeywordDetectionHandler
from Message.handlers.outbound_resolver import resolve_pinduoduo_outbound


_SHOP = "shop_12345"
_ACCOUNT = "user_account_999"
_BUYER = "buyer_uid_12345678"
_CS = "cs_staff_uid_abcdef12"


def _debug_or_warning_output(mock) -> str:
    return " ".join(str(call) for call in mock.call_args_list)


class TestAIHandlerSendWarning(unittest.TestCase):
    def test_missing_send_context_warning_redacted(self) -> None:
        handler = AIReplyHandler(bot=None)
        ctx = Context(type=ContextType.TEXT)
        meta = {"shop_id": _SHOP, "user_id": _ACCOUNT, "from_uid": None}

        with patch.object(handler.logger, "warning") as warn_mock:
            ok = asyncio.run(handler._send_reply(ctx, "hi", meta))

        self.assertFalse(ok)
        output = _debug_or_warning_output(warn_mock)
        self.assertIn("缺少发送信息", output)
        self.assertIn(f"shop_id={_SHOP}", output)
        self.assertNotIn(_ACCOUNT, output)
        self.assertNotIn(_BUYER, output)
        self.assertIn("account=***", output)
        self.assertIn("buyer=missing", output)


class TestKeywordHandlerCsUidLog(unittest.TestCase):
    @patch("Message.handlers.keyword_handler.SendMessage")
    def test_transfer_success_info_redacts_cs_uid(self, send_cls_mock) -> None:
        sender = MagicMock()
        send_cls_mock.return_value = sender
        sender.getAssignCsList.return_value = {
            _CS: {"username": "客服A"},
            f"cs_{_SHOP}_{_ACCOUNT}": {"username": "自己"},
        }
        sender.move_conversation.return_value = {"success": True}

        handler = KeywordDetectionHandler()
        ctx = Context.create_pinduoduo_context(
            content="转人工",
            from_uid=_BUYER,
            user_msg_type=ContextType.TEXT,
            shop_id=_SHOP,
            user_id=_ACCOUNT,
            channel_type=ChannelType.PINDUODUO,
        )

        with patch.object(handler.logger, "info") as info_mock:
            ok = handler._transfer_to_human_legacy(_SHOP, _ACCOUNT, _BUYER)

        self.assertTrue(ok)
        output = _debug_or_warning_output(info_mock)
        self.assertIn("客服A", output)
        self.assertNotIn(_CS, output)
        self.assertIn("cs=***", output)


class TestOutboundResolverUidLogs(unittest.TestCase):
    def setUp(self) -> None:
        self._env_backup = os.environ.get("USE_PINDUODUO_OUTBOUND")

    def tearDown(self) -> None:
        if self._env_backup is None:
            os.environ.pop("USE_PINDUODUO_OUTBOUND", None)
        else:
            os.environ["USE_PINDUODUO_OUTBOUND"] = self._env_backup

    @patch("Message.handlers.outbound_resolver.logger")
    def test_missing_fields_debug_redacted(self, log_mock) -> None:
        os.environ["USE_PINDUODUO_OUTBOUND"] = "true"
        meta = {"shop_id": _SHOP, "user_id": _ACCOUNT}
        resolve_pinduoduo_outbound(meta)

        output = _debug_or_warning_output(log_mock.debug)
        self.assertIn("无法解析 outbound", output)
        self.assertIn(f"shop_id={_SHOP}", output)
        self.assertNotIn(_ACCOUNT, output)
        self.assertNotIn(_BUYER, output)

    @patch("Message.handlers.outbound_resolver.create_pinduoduo_outbound")
    @patch("Message.handlers.outbound_resolver.logger")
    def test_mismatch_debug_redacted(self, log_mock, create_mock) -> None:
        os.environ["USE_PINDUODUO_OUTBOUND"] = "true"
        create_mock.return_value = MagicMock()

        class _Outbound:
            shop_id = _SHOP
            user_id = "other_account_full_id_xyz"

            async def send_text(self, *_a, **_k):
                return True

            async def transfer_to_human(self, *_a, **_k):
                return True

        meta = {
            "shop_id": _SHOP,
            "user_id": _ACCOUNT,
            "from_uid": _BUYER,
            "outbound": _Outbound(),
        }
        resolve_pinduoduo_outbound(meta)

        output = _debug_or_warning_output(log_mock.debug)
        self.assertIn("账号不匹配", output)
        self.assertNotIn("other_account_full_id_xyz", output)
        self.assertNotIn(_ACCOUNT, output)


if __name__ == "__main__":
    unittest.main()

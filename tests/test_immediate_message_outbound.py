"""Phase 2c：pdd_message_handler 即时消息 outbound-first + legacy fallback 测试。"""

from __future__ import annotations

import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from bridge.context import Context, ContextType
from Channel.pinduoduo.core.pdd_message_handler import MessageHandlerMixin


class _Host(MessageHandlerMixin):
    """最小宿主类，提供 logger 供 Mixin 方法使用。"""

    def __init__(self) -> None:
        self.logger = MagicMock()


def _make_context(context_type: ContextType, content: str = "x") -> Context:
    return Context.create_pinduoduo_context(
        content=content,
        from_uid="buyer1",
        shop_id="shop1",
        user_id="user1",
        username="seller",
        user_msg_type=context_type,
        channel_type=None,
    )


class TestImmediateMessageOutbound(unittest.TestCase):
    def setUp(self) -> None:
        self._env_backup = os.environ.get("USE_PINDUODUO_OUTBOUND")
        self.host = _Host()

    def tearDown(self) -> None:
        if self._env_backup is None:
            os.environ.pop("USE_PINDUODUO_OUTBOUND", None)
        else:
            os.environ["USE_PINDUODUO_OUTBOUND"] = self._env_backup

    @patch("Channel.pinduoduo.core.pdd_message_handler.MessageHandlerMixin._send_immediate_text_legacy")
    @patch("Message.handlers.outbound_resolver.resolve_pinduoduo_outbound")
    def test_flag_off_withdraw_uses_legacy(self, resolve_mock, legacy_mock) -> None:
        os.environ.pop("USE_PINDUODUO_OUTBOUND", None)
        resolve_mock.return_value = None
        legacy_mock.return_value = True
        ctx = _make_context(ContextType.WITHDRAW)

        asyncio.run(self.host._handle_immediate_message(ctx, "shop1", "user1"))

        legacy_mock.assert_called_once_with("shop1", "user1", "buyer1", "[玫瑰]")

    @patch("Channel.pinduoduo.core.pdd_message_handler.MessageHandlerMixin._send_immediate_text_legacy")
    @patch("Message.handlers.outbound_resolver.resolve_pinduoduo_outbound")
    def test_flag_off_transfer_uses_legacy(self, resolve_mock, legacy_mock) -> None:
        os.environ.pop("USE_PINDUODUO_OUTBOUND", None)
        resolve_mock.return_value = None
        legacy_mock.return_value = True
        ctx = _make_context(ContextType.TRANSFER)

        asyncio.run(self.host._handle_immediate_message(ctx, "shop1", "user1"))

        legacy_mock.assert_called_once_with("shop1", "user1", "buyer1", "[玫瑰]")

    @patch("Channel.pinduoduo.core.pdd_message_handler.MessageHandlerMixin._send_immediate_text_legacy")
    @patch("Message.handlers.outbound_resolver.resolve_pinduoduo_outbound")
    def test_outbound_success_skips_legacy(self, resolve_mock, legacy_mock) -> None:
        outbound = MagicMock()
        outbound.send_text = AsyncMock(return_value=True)
        resolve_mock.return_value = outbound
        ctx = _make_context(ContextType.WITHDRAW)

        asyncio.run(self.host._handle_immediate_message(ctx, "shop1", "user1"))

        outbound.send_text.assert_awaited_once_with("buyer1", "[玫瑰]")
        legacy_mock.assert_not_called()

    @patch("Channel.pinduoduo.core.pdd_message_handler.MessageHandlerMixin._send_immediate_text_legacy")
    @patch("Message.handlers.outbound_resolver.resolve_pinduoduo_outbound")
    def test_outbound_fail_falls_back_legacy(self, resolve_mock, legacy_mock) -> None:
        outbound = MagicMock()
        outbound.send_text = AsyncMock(return_value=False)
        resolve_mock.return_value = outbound
        legacy_mock.return_value = True
        ctx = _make_context(ContextType.WITHDRAW)

        asyncio.run(self.host._handle_immediate_message(ctx, "shop1", "user1"))

        outbound.send_text.assert_awaited_once_with("buyer1", "[玫瑰]")
        legacy_mock.assert_called_once_with("shop1", "user1", "buyer1", "[玫瑰]")

    @patch("Channel.pinduoduo.core.pdd_message_handler.MessageHandlerMixin._send_immediate_text_legacy")
    @patch("Message.handlers.outbound_resolver.resolve_pinduoduo_outbound")
    def test_non_send_types_do_not_send(self, resolve_mock, legacy_mock) -> None:
        outbound = MagicMock()
        outbound.send_text = AsyncMock(return_value=True)
        resolve_mock.return_value = outbound

        for ctx_type in (
            ContextType.AUTH,
            ContextType.SYSTEM_STATUS,
            ContextType.SYSTEM_HINT,
            ContextType.MALL_CS,
        ):
            ctx = _make_context(ctx_type)
            asyncio.run(self.host._handle_immediate_message(ctx, "shop1", "user1"))

        outbound.send_text.assert_not_called()
        legacy_mock.assert_not_called()

    @patch("Channel.pinduoduo.core.pdd_message_handler.MessageHandlerMixin._send_immediate_text_legacy")
    @patch("Message.handlers.outbound_resolver.resolve_pinduoduo_outbound")
    def test_message_text_is_rose(self, resolve_mock, legacy_mock) -> None:
        outbound = MagicMock()
        outbound.send_text = AsyncMock(return_value=True)
        resolve_mock.return_value = outbound
        ctx = _make_context(ContextType.TRANSFER)

        asyncio.run(self.host._handle_immediate_message(ctx, "shop1", "user1"))

        _, sent_text = outbound.send_text.await_args.args
        self.assertEqual(sent_text, "[玫瑰]")


if __name__ == "__main__":
    unittest.main()

"""Phase 13d: single test shop preview gate handler integration (Z1–Z8)."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from bridge.context import Context, ContextType, ChannelType
from Message.gates.intent_types import IntentBucket, SendMode
from Message.gates.preview_log import preview_log
from Message.gates.product_gate_config import (
    TestShopAllowlistEntry,
    clear_test_shop_allowlist,
    set_test_shop_allowlist,
)
from Message.handlers.ai_handler import AIReplyHandler

_AI_REPLY = "preview suggestion text"
_BUYER = "buyer_uid_preview_test"
_WS = "ws-test-0001"
_SHOP = "shop_pdd_preview_test"
_ACCOUNT = "acc_pdd_preview_test"


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
        "message_id": "w-preview-1",
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
        "message_id": "w-legacy-1",
        "shop_id": "shop_production_like",
        "account_id": "acc_production_like",
        "user_id": "user_1",
        "from_uid": _BUYER,
        "platform_id": "pinduoduo",
    }
    base.update(kwargs)
    return base


def _context(*, content: str = "这款商品还有库存吗", shop_id: str = _SHOP) -> Context:
    return Context.create_pinduoduo_context(
        content=content,
        from_uid=_BUYER,
        username="nick",
        user_msg_type=ContextType.TEXT,
        shop_id=shop_id,
        user_id="user_preview",
        channel_type=ChannelType.PINDUODUO,
    )


class TestSingleTestShopPreviewGate(unittest.TestCase):
    def setUp(self) -> None:
        preview_log.clear()
        clear_test_shop_allowlist()

    def tearDown(self) -> None:
        preview_log.clear()
        clear_test_shop_allowlist()

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    def test_z1_test_shop_preview_zero_send(
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
        self.assertEqual(len(preview_log), 1)
        record = preview_log.all()[0]
        self.assertFalse(record.guarded_result.should_send)
        self.assertEqual(record.guarded_result.send_status, "not_sent_preview")
        self.assertTrue(record.send_decision.product_gate_enabled)
        self.assertEqual(record.send_decision.send_mode, SendMode.PREVIEW_ONLY)

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    def test_z2_non_test_shop_legacy_unchanged(
        self,
        _ai_mock: AsyncMock,
        send_mock: AsyncMock,
    ) -> None:
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        ok = asyncio.run(handler.handle(_context(shop_id="shop_production_like"), _legacy_metadata()))

        self.assertTrue(ok)
        send_mock.assert_awaited_once()
        self.assertEqual(len(preview_log), 0)

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    def test_z3_blocked_intent_preview_no_send(
        self,
        _ai_mock: AsyncMock,
        send_mock: AsyncMock,
    ) -> None:
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        ok = asyncio.run(
            handler.handle(_context(content="我要退款"), _test_metadata())
        )

        self.assertTrue(ok)
        send_mock.assert_not_awaited()
        self.assertEqual(len(preview_log), 1)
        record = preview_log.all()[0]
        self.assertEqual(record.classification.intent_bucket, IntentBucket.BLOCKED)
        self.assertEqual(record.send_decision.send_mode, SendMode.HUMAN_TAKEOVER)
        self.assertEqual(record.guarded_result.send_status, "not_sent_human_takeover")
        self.assertFalse(record.guarded_result.should_send)

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    @patch(
        "Message.gates.consultation_intent_classifier.classify_consultation_intent",
        side_effect=RuntimeError("classifier boom"),
    )
    def test_z4_classifier_failure_test_shop_safe(
        self,
        _classify_mock: MagicMock,
        _ai_mock: AsyncMock,
        send_mock: AsyncMock,
    ) -> None:
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        ok = asyncio.run(handler.handle(_context(), _test_metadata()))

        self.assertFalse(ok)
        send_mock.assert_not_awaited()
        self.assertEqual(len(preview_log), 0)

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    def test_z5_doudian_not_enabled(
        self,
        _ai_mock: AsyncMock,
        send_mock: AsyncMock,
    ) -> None:
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        meta = _test_metadata(platform_id="doudian", platform="doudian")
        ok = asyncio.run(handler.handle(_context(), meta))

        self.assertTrue(ok)
        send_mock.assert_awaited_once()
        self.assertEqual(len(preview_log), 0)

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    @patch("Message.handlers.outbound_resolver.resolve_pinduoduo_outbound", return_value=None)
    def test_z6_no_direct_send_bypass(
        self,
        _resolve_mock: MagicMock,
        send_text_mock: MagicMock,
        _ai_mock: AsyncMock,
        send_reply_mock: AsyncMock,
    ) -> None:
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        asyncio.run(handler.handle(_context(), _test_metadata()))

        send_reply_mock.assert_not_awaited()
        send_text_mock.assert_not_called()

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    def test_z7_product_gate_disabled_legacy(
        self,
        _ai_mock: AsyncMock,
        send_mock: AsyncMock,
    ) -> None:
        clear_test_shop_allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        ok = asyncio.run(handler.handle(_context(), _test_metadata()))

        self.assertTrue(ok)
        send_mock.assert_awaited_once()

    def test_z8_preview_log_status_allowed_and_blocked(self) -> None:
        from Message.gates.consultation_intent_classifier import classify_consultation_intent
        from Message.gates.guarded_send import evaluate_guarded_send
        from Message.gates.preview_log import append_preview_log
        from Message.gates.send_decision import build_send_decision

        allowed_cls = classify_consultation_intent("这款商品还有库存吗")
        allowed_decision = build_send_decision(
            allowed_cls,
            reply_mode="preview",
            product_gate_enabled=True,
        )
        allowed_guarded = evaluate_guarded_send(allowed_decision, "suggestion")
        append_preview_log(
            message_text="这款商品还有库存吗",
            reply_text="suggestion",
            classification=allowed_cls,
            send_decision=allowed_decision,
            guarded_result=allowed_guarded,
        )
        self.assertEqual(preview_log.all()[-1].guarded_result.send_status, "not_sent_preview")

        blocked_cls = classify_consultation_intent("我要投诉")
        blocked_decision = build_send_decision(
            blocked_cls,
            reply_mode="preview",
            product_gate_enabled=True,
        )
        blocked_guarded = evaluate_guarded_send(blocked_decision, "suggestion")
        append_preview_log(
            message_text="我要投诉",
            reply_text="suggestion",
            classification=blocked_cls,
            send_decision=blocked_decision,
            guarded_result=blocked_guarded,
        )
        self.assertEqual(
            preview_log.all()[-1].guarded_result.send_status,
            "not_sent_human_takeover",
        )


if __name__ == "__main__":
    unittest.main()

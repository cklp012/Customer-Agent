"""Phase 14i: PreviewReplyLogService handler integration (H1–H10)."""

from __future__ import annotations

import asyncio
import os
import unittest
from pathlib import Path
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
from product_persistence.services.preview_reply_log_service import (
    PreviewRecordResult,
    PreviewReplyLogService,
)

_AI_REPLY = "preview suggestion text"
_BUYER = "buyer_uid_preview_test"
_WS = "ws-test-0001"
_SHOP = "shop_pdd_preview_test"
_ACCOUNT = "acc_pdd_preview_test"
_REPO_ROOT = Path(__file__).resolve().parents[1]
_PRODUCT_GATE_DB = _REPO_ROOT / "temp" / "product_gate.db"
_HANDLER_SOURCE = _REPO_ROOT / "Message" / "handlers" / "ai_handler.py"


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


class TestHandlerPreviewReplyLogServiceIntegration(unittest.TestCase):
    def setUp(self) -> None:
        preview_log.clear()
        clear_test_shop_allowlist()
        if _PRODUCT_GATE_DB.exists():
            _PRODUCT_GATE_DB.unlink()

    def tearDown(self) -> None:
        preview_log.clear()
        clear_test_shop_allowlist()

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    def test_h1_test_shop_preview_still_zero_send(
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

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    @patch.object(PreviewReplyLogService, "record_preview")
    def test_h2_service_record_called_for_test_shop(
        self,
        record_mock: MagicMock,
        _ai_mock: AsyncMock,
        _send_mock: AsyncMock,
    ) -> None:
        record_mock.side_effect = lambda **kwargs: PreviewRecordResult(
            recorded=True,
            persistence_enabled=False,
            reason="recorded_in_memory",
            source="in_memory",
            reply_log_id="mock-id",
        )
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        asyncio.run(handler.handle(_context(), _test_metadata()))

        record_mock.assert_called_once()
        call_kwargs = record_mock.call_args.kwargs
        self.assertIn("这款商品还有库存吗", call_kwargs["message_text"])
        self.assertEqual(call_kwargs["reply_text"], _AI_REPLY)
        self.assertIsNotNone(call_kwargs["classification"])
        self.assertIsNotNone(call_kwargs["send_decision"])
        self.assertIsNotNone(call_kwargs["guarded_result"])

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    @patch.object(PreviewReplyLogService, "record_preview")
    def test_h3_non_test_shop_service_not_called(
        self,
        record_mock: MagicMock,
        _ai_mock: AsyncMock,
        send_mock: AsyncMock,
    ) -> None:
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        ok = asyncio.run(
            handler.handle(_context(shop_id="shop_production_like"), _legacy_metadata())
        )

        self.assertTrue(ok)
        record_mock.assert_not_called()
        send_mock.assert_awaited_once()
        self.assertEqual(len(preview_log), 0)

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    @patch.object(PreviewReplyLogService, "record_preview", side_effect=RuntimeError("service down"))
    def test_h4_service_failure_test_shop_no_send(
        self,
        _record_mock: MagicMock,
        send_text_mock: MagicMock,
        _ai_mock: AsyncMock,
        send_reply_mock: AsyncMock,
    ) -> None:
        """Fail-open: service exception → append_preview_log fallback → True, still zero-send."""
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        ok = asyncio.run(handler.handle(_context(), _test_metadata()))

        self.assertTrue(ok)
        send_reply_mock.assert_not_awaited()
        send_text_mock.assert_not_called()
        self.assertEqual(len(preview_log), 1)

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    @patch.object(PreviewReplyLogService, "record_preview", side_effect=RuntimeError("service down"))
    def test_h5_service_failure_non_test_shop_legacy_unchanged(
        self,
        record_mock: MagicMock,
        _ai_mock: AsyncMock,
        send_mock: AsyncMock,
    ) -> None:
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        ok = asyncio.run(
            handler.handle(_context(shop_id="shop_production_like"), _legacy_metadata())
        )

        self.assertTrue(ok)
        record_mock.assert_not_called()
        send_mock.assert_awaited_once()

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    @patch.object(
        PreviewReplyLogService,
        "record_preview",
        wraps=PreviewReplyLogService.record_preview,
    )
    def test_h6_blocked_intent_records_human_takeover(
        self,
        record_mock: MagicMock,
        _ai_mock: AsyncMock,
        send_mock: AsyncMock,
    ) -> None:
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        ok = asyncio.run(
            handler.handle(_context(content="我要退款"), _test_metadata())
        )

        self.assertTrue(ok)
        record_mock.assert_called_once()
        send_mock.assert_not_awaited()
        self.assertEqual(len(preview_log), 1)
        record = preview_log.all()[0]
        self.assertEqual(record.classification.intent_bucket, IntentBucket.BLOCKED)
        self.assertEqual(record.send_decision.send_mode, SendMode.HUMAN_TAKEOVER)
        self.assertEqual(record.guarded_result.send_status, "not_sent_human_takeover")

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    def test_h7_no_db_created(
        self,
        _ai_mock: AsyncMock,
        _send_mock: AsyncMock,
    ) -> None:
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        asyncio.run(handler.handle(_context(), _test_metadata()))
        PreviewReplyLogService().list_reply_logs()
        self.assertFalse(_PRODUCT_GATE_DB.exists())

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    def test_h8_flags_default_off(
        self,
        _ai_mock: AsyncMock,
        _send_mock: AsyncMock,
    ) -> None:
        _allowlist()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PRODUCT_PERSISTENCE_ENABLED", None)
            handler = AIReplyHandler(bot=MagicMock())
            ok = asyncio.run(handler.handle(_context(), _test_metadata()))

        self.assertTrue(ok)
        self.assertEqual(len(preview_log), 1)
        result = PreviewReplyLogService().list_reply_logs()
        self.assertTrue(result.success)
        self.assertEqual(len(result.records), 1)

    def test_h9_no_direct_db_import_in_handler(self) -> None:
        source = _HANDLER_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("product_persistence.db_manager", source)
        self.assertNotIn("product_persistence.models", source)
        self.assertNotIn("product_persistence.repositories", source)
        self.assertNotIn("database.models", source)
        self.assertNotIn("database.db_manager", source)
        self.assertIn("product_persistence.services", source)

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    @patch.object(PreviewReplyLogService, "record_preview")
    def test_h10_doudian_not_enabled(
        self,
        record_mock: MagicMock,
        _ai_mock: AsyncMock,
        send_mock: AsyncMock,
    ) -> None:
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        meta = _test_metadata(platform_id="doudian", platform="doudian")
        ok = asyncio.run(handler.handle(_context(), meta))

        self.assertTrue(ok)
        record_mock.assert_not_called()
        send_mock.assert_awaited_once()
        self.assertEqual(len(preview_log), 0)


if __name__ == "__main__":
    unittest.main()

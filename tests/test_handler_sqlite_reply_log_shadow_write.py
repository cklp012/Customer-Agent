"""Phase 14l: handler + SQLite shadow write integration tests."""

from __future__ import annotations

import asyncio
import importlib
import os
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from bridge.context import Context, ContextType, ChannelType
from Message.gates.preview_log import preview_log
from Message.gates.product_gate_config import (
    TestShopAllowlistEntry,
    clear_test_shop_allowlist,
    set_test_shop_allowlist,
)
from Message.handlers.ai_handler import AIReplyHandler
from product_persistence.db_manager import ProductDbManager, reset_product_db_manager
from product_persistence.models import ReplyLogRow
from product_persistence.repositories.sqlite_reply_log_repository import (
    ReplyLogRepositorySQLite,
)
from product_persistence.services.preview_reply_log_service import PreviewReplyLogService

_AI_REPLY = "preview suggestion text"
_BUYER = "buyer_uid_preview_test"
_WS = "ws-test-0001"
_SHOP = "shop_pdd_preview_test"
_ACCOUNT = "acc_pdd_preview_test"
_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_PRODUCT_GATE_DB = _REPO_ROOT / "temp" / "product_gate.db"
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


class TestHandlerSqliteReplyLogShadowWrite(unittest.TestCase):
    _db_manager: ProductDbManager | None = None

    def setUp(self) -> None:
        self._db_manager = None
        preview_log.clear()
        clear_test_shop_allowlist()
        reset_product_db_manager()
        self._tmpdir = _REPO_ROOT / "temp" / "phase14l_handler_tests"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._tmpdir / "product_gate_handler_test.db"
        if self._db_path.exists():
            self._db_path.unlink()
        if _DEFAULT_PRODUCT_GATE_DB.exists():
            _DEFAULT_PRODUCT_GATE_DB.unlink()
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_PERSISTENCE_ENABLED",
            "PRODUCT_PERSISTENCE_WRITE_REPLY_LOG",
            "PRODUCT_DB_URL",
        ):
            os.environ.pop(key, None)
        importlib.reload(importlib.import_module("product_persistence.flags"))

    def tearDown(self) -> None:
        preview_log.clear()
        clear_test_shop_allowlist()
        if self._db_manager is not None:
            self._db_manager.close_product_db()
        reset_product_db_manager()
        if self._db_path.exists():
            self._db_path.unlink(missing_ok=True)
        self._env_patch.stop()

    def _enable_write_flags(self) -> ProductDbManager:
        os.environ["PRODUCT_PERSISTENCE_ENABLED"] = "true"
        os.environ["PRODUCT_PERSISTENCE_WRITE_REPLY_LOG"] = "true"
        os.environ["PRODUCT_DB_URL"] = f"sqlite:///{self._db_path.as_posix()}"
        importlib.reload(importlib.import_module("product_persistence.flags"))
        reset_product_db_manager()
        self._db_manager = ProductDbManager(db_url=os.environ["PRODUCT_DB_URL"])
        return self._db_manager

    def _db_row_count(self, db_manager: ProductDbManager) -> int:
        session = db_manager.get_product_session()
        try:
            from sqlalchemy import func, select

            return session.scalar(select(func.count()).select_from(ReplyLogRow)) or 0
        finally:
            session.close()

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    def test_test_shop_flags_on_zero_send_with_db_row(
        self,
        send_text_mock: MagicMock,
        _ai_mock: AsyncMock,
        send_reply_mock: AsyncMock,
    ) -> None:
        self._enable_write_flags()
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        ok = asyncio.run(handler.handle(_context(), _test_metadata()))

        self.assertTrue(ok)
        send_reply_mock.assert_not_awaited()
        send_text_mock.assert_not_called()
        self.assertEqual(len(preview_log.all()), 1)
        self.assertTrue(self._db_path.exists())
        self.assertEqual(self._db_row_count(self._db_manager), 1)

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    @patch(
        "product_persistence.repositories.sqlite_reply_log_repository.ReplyLogRepositorySQLite.create_preview_reply_log",
        side_effect=RuntimeError("sqlite down"),
    )
    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    def test_sqlite_write_failure_no_send_in_memory_retained(
        self,
        send_text_mock: MagicMock,
        _repo_mock: MagicMock,
        _ai_mock: AsyncMock,
        send_reply_mock: AsyncMock,
    ) -> None:
        self._enable_write_flags()
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        ok = asyncio.run(handler.handle(_context(), _test_metadata()))

        self.assertTrue(ok)
        send_reply_mock.assert_not_awaited()
        send_text_mock.assert_not_called()
        self.assertEqual(len(preview_log.all()), 1)

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    def test_non_test_shop_flags_on_legacy_no_db_write(
        self,
        _ai_mock: AsyncMock,
        send_mock: AsyncMock,
    ) -> None:
        self._enable_write_flags()
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        ok = asyncio.run(
            handler.handle(_context(shop_id="shop_production_like"), _legacy_metadata())
        )

        self.assertTrue(ok)
        send_mock.assert_awaited_once()
        self.assertFalse(self._db_path.exists())
        self.assertEqual(len(preview_log.all()), 0)

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    def test_doudian_flags_on_no_db_write(
        self,
        _ai_mock: AsyncMock,
        send_mock: AsyncMock,
    ) -> None:
        self._enable_write_flags()
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        meta = _test_metadata(platform_id="doudian", platform="doudian")
        ok = asyncio.run(handler.handle(_context(), meta))

        self.assertTrue(ok)
        send_mock.assert_awaited_once()
        self.assertFalse(self._db_path.exists())

    @patch.object(AIReplyHandler, "_send_reply", new_callable=AsyncMock, return_value=True)
    @patch.object(AIReplyHandler, "_get_ai_reply", new_callable=AsyncMock, return_value=_AI_REPLY)
    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    def test_flags_off_no_product_gate_db(
        self,
        send_text_mock: MagicMock,
        _ai_mock: AsyncMock,
        _send_mock: AsyncMock,
    ) -> None:
        _allowlist()
        handler = AIReplyHandler(bot=MagicMock())
        asyncio.run(handler.handle(_context(), _test_metadata()))
        self.assertFalse(_DEFAULT_PRODUCT_GATE_DB.exists())
        self.assertFalse(self._db_path.exists())
        send_text_mock.assert_not_called()

    def test_handler_no_direct_db_imports(self) -> None:
        source = _HANDLER_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("product_persistence.db_manager", source)
        self.assertNotIn("product_persistence.models", source)
        self.assertNotIn("database.models", source)
        self.assertNotIn("database.db_manager", source)


if __name__ == "__main__":
    unittest.main()

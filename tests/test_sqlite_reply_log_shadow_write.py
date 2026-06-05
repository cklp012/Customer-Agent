"""Phase 14l: SQLite ReplyLog shadow write tests (S1–S8)."""

from __future__ import annotations

import importlib
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from Message.gates.consultation_intent_classifier import classify_consultation_intent
from Message.gates.guarded_send import evaluate_guarded_send
from Message.gates.preview_log import preview_log
from Message.gates.send_decision import build_send_decision
from product_persistence.db_manager import ProductDbManager, reset_product_db_manager
from product_persistence.models import ReplyLogRow
from product_persistence.repositories.sqlite_reply_log_repository import (
    ReplyLogRepositorySQLite,
)
from product_persistence.services.preview_reply_log_service import PreviewReplyLogService

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LEGACY_DB = _REPO_ROOT / "temp" / "channel_shop.db"
_PERSISTENCE_SOURCES = (
    _REPO_ROOT / "product_persistence" / "db_manager.py",
    _REPO_ROOT / "product_persistence" / "models.py",
    _REPO_ROOT / "product_persistence" / "repositories" / "sqlite_reply_log_repository.py",
    _REPO_ROOT / "product_persistence" / "services" / "preview_reply_log_service.py",
)


def _preview_kwargs() -> dict:
    cls = classify_consultation_intent("这款商品还有库存吗")
    decision = build_send_decision(cls, reply_mode="preview", product_gate_enabled=True)
    guarded = evaluate_guarded_send(decision, "建议回复")
    return dict(
        message_text="这款商品还有库存吗",
        reply_text="建议回复",
        classification=cls,
        send_decision=decision,
        guarded_result=guarded,
        metadata={
            "message_id": "w-sqlite-1",
            "workspace_id": "ws-sqlite-1",
            "shop_id": "shop-sqlite-1",
            "account_id": "acc-sqlite-1",
            "from_uid": "buyer-sqlite-1",
            "platform_id": "pinduoduo",
        },
        workspace_id="ws-sqlite-1",
        shop_id="shop-sqlite-1",
        account_id="acc-sqlite-1",
        buyer_id="buyer-sqlite-1",
        platform_id="pinduoduo",
    )


class _SqliteShadowTestCase(unittest.TestCase):
    _db_manager: ProductDbManager | None = None

    def setUp(self) -> None:
        self._db_manager = None
        PreviewReplyLogService.clear_in_memory_logs_for_tests()
        reset_product_db_manager()
        self._tmpdir = _REPO_ROOT / "temp" / "phase14l_tests"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._tmpdir / "product_gate_test.db"
        if self._db_path.exists():
            self._db_path.unlink()
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
        PreviewReplyLogService.clear_in_memory_logs_for_tests()
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

    def _count_db_rows(self, db_manager: ProductDbManager) -> int:
        session = db_manager.get_product_session()
        try:
            from sqlalchemy import func, select

            return session.scalar(select(func.count()).select_from(ReplyLogRow)) or 0
        finally:
            session.close()


class TestSqliteReplyLogShadowWrite(_SqliteShadowTestCase):
    def test_s1_flags_off_in_memory_only(self) -> None:
        default_db = _REPO_ROOT / "temp" / "product_gate.db"
        if default_db.exists():
            default_db.unlink()
        result = PreviewReplyLogService().record_preview(**_preview_kwargs())
        self.assertTrue(result.recorded)
        self.assertFalse(result.db_recorded)
        self.assertEqual(result.source, "in_memory")
        self.assertFalse(default_db.exists())
        self.assertEqual(len(preview_log.all()), 1)

    def test_s2_flags_on_creates_product_gate_db(self) -> None:
        db_manager = self._enable_write_flags()
        result = PreviewReplyLogService(
            repository=ReplyLogRepositorySQLite(db_manager=db_manager)
        ).record_preview(**_preview_kwargs())
        self.assertTrue(result.recorded)
        self.assertTrue(result.db_recorded)
        self.assertEqual(result.source, "in_memory+sqlite_shadow")
        self.assertTrue(self._db_path.exists())
        self.assertEqual(self._count_db_rows(db_manager), 1)

    def test_s3_schema_fields(self) -> None:
        db_manager = self._enable_write_flags()
        repo = ReplyLogRepositorySQLite(db_manager=db_manager)
        result = PreviewReplyLogService(repository=repo).record_preview(**_preview_kwargs())
        session = db_manager.get_product_session()
        try:
            row = session.get(ReplyLogRow, result.reply_log_id)
            assert row is not None
            self.assertEqual(row.send_status, "not_sent_preview")
            self.assertEqual(row.intent_bucket, "allowed")
            self.assertEqual(row.risk_level, "low")
            self.assertEqual(row.shop_id, "shop-sqlite-1")
            self.assertEqual(row.buyer_id, "buyer-sqlite-1")
        finally:
            session.close()

    def test_s4_list_get(self) -> None:
        db_manager = self._enable_write_flags()
        repo = ReplyLogRepositorySQLite(db_manager=db_manager)
        result = PreviewReplyLogService(repository=repo).record_preview(**_preview_kwargs())
        listed = repo.list_reply_logs(shop_id="shop-sqlite-1")
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].reply_log_id, result.reply_log_id)
        got = repo.get_reply_log(result.reply_log_id)
        assert got is not None
        self.assertEqual(got.buyer_message, "这款商品还有库存吗")

    def test_s5_duplicate_safe(self) -> None:
        db_manager = self._enable_write_flags()
        repo = ReplyLogRepositorySQLite(db_manager=db_manager)
        result = PreviewReplyLogService(repository=repo).record_preview(**_preview_kwargs())
        record = preview_log.all()[0]
        again = repo.create_preview_reply_log(record)
        self.assertEqual(again, result.reply_log_id)
        self.assertEqual(self._count_db_rows(db_manager), 1)

    def test_s6_no_legacy_import(self) -> None:
        for path in _PERSISTENCE_SOURCES:
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("from database.models", source)
            self.assertNotIn("from database.db_manager", source)
            self.assertNotIn("import database.models", source)
            self.assertNotIn("import database.db_manager", source)

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    def test_s7_no_send_side_effect(self, send_text_mock) -> None:
        db_manager = self._enable_write_flags()
        PreviewReplyLogService(
            repository=ReplyLogRepositorySQLite(db_manager=db_manager)
        ).record_preview(**_preview_kwargs())
        send_text_mock.assert_not_called()

    def test_s8_rollback_flags(self) -> None:
        db_manager = self._enable_write_flags()
        repo = ReplyLogRepositorySQLite(db_manager=db_manager)
        PreviewReplyLogService(repository=repo).record_preview(**_preview_kwargs())
        self.assertEqual(self._count_db_rows(db_manager), 1)
        os.environ.pop("PRODUCT_PERSISTENCE_ENABLED", None)
        os.environ.pop("PRODUCT_PERSISTENCE_WRITE_REPLY_LOG", None)
        importlib.reload(importlib.import_module("product_persistence.flags"))
        PreviewReplyLogService.clear_in_memory_logs_for_tests()
        second = PreviewReplyLogService().record_preview(**_preview_kwargs())
        self.assertTrue(second.recorded)
        self.assertFalse(second.db_recorded)
        self.assertEqual(self._count_db_rows(db_manager), 1)
        self.assertEqual(len(preview_log.all()), 1)

    def test_legacy_channel_shop_db_untouched(self) -> None:
        if not _LEGACY_DB.exists():
            return
        mtime_before = _LEGACY_DB.stat().st_mtime
        db_manager = self._enable_write_flags()
        PreviewReplyLogService(
            repository=ReplyLogRepositorySQLite(db_manager=db_manager)
        ).record_preview(**_preview_kwargs())
        self.assertEqual(_LEGACY_DB.stat().st_mtime, mtime_before)


if __name__ == "__main__":
    unittest.main()

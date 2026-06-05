"""Phase 14n: SendDecision snapshot SQLite shadow write tests (M1–M7)."""

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
from product_persistence.models import ReplyLogRow, SendDecisionSnapshotRow
from product_persistence.repositories.sqlite_reply_log_repository import (
    ReplyLogRepositorySQLite,
)
from product_persistence.repositories.sqlite_send_decision_repository import (
    SendDecisionRepositorySQLite,
)
from product_persistence.services.preview_reply_log_service import PreviewReplyLogService

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PERSISTENCE_SOURCES = (
    _REPO_ROOT / "product_persistence" / "db_manager.py",
    _REPO_ROOT / "product_persistence" / "models.py",
    _REPO_ROOT / "product_persistence" / "repositories" / "sqlite_send_decision_repository.py",
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
            "message_id": "w-snap-1",
            "workspace_id": "ws-snap-1",
            "shop_id": "shop-snap-1",
            "account_id": "acc-snap-1",
            "from_uid": "buyer-snap-1",
            "platform_id": "pinduoduo",
        },
        workspace_id="ws-snap-1",
        shop_id="shop-snap-1",
        account_id="acc-snap-1",
        buyer_id="buyer-snap-1",
        platform_id="pinduoduo",
    )


class _SnapshotShadowTestCase(unittest.TestCase):
    _db_manager: ProductDbManager | None = None

    def setUp(self) -> None:
        self._db_manager = None
        PreviewReplyLogService.clear_in_memory_logs_for_tests()
        reset_product_db_manager()
        self._tmpdir = _REPO_ROOT / "temp" / "phase14n_tests"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._tmpdir / "product_gate_snapshot_test.db"
        if self._db_path.exists():
            self._db_path.unlink()
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_PERSISTENCE_ENABLED",
            "PRODUCT_PERSISTENCE_WRITE_REPLY_LOG",
            "PRODUCT_PERSISTENCE_WRITE_SEND_DECISION",
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

    def _enable_all_write_flags(self) -> ProductDbManager:
        os.environ["PRODUCT_PERSISTENCE_ENABLED"] = "true"
        os.environ["PRODUCT_PERSISTENCE_WRITE_REPLY_LOG"] = "true"
        os.environ["PRODUCT_PERSISTENCE_WRITE_SEND_DECISION"] = "true"
        os.environ["PRODUCT_DB_URL"] = f"sqlite:///{self._db_path.as_posix()}"
        importlib.reload(importlib.import_module("product_persistence.flags"))
        reset_product_db_manager()
        self._db_manager = ProductDbManager(db_url=os.environ["PRODUCT_DB_URL"])
        return self._db_manager

    def _service(self) -> PreviewReplyLogService:
        assert self._db_manager is not None
        return PreviewReplyLogService(
            repository=ReplyLogRepositorySQLite(db_manager=self._db_manager),
            snapshot_repository=SendDecisionRepositorySQLite(
                db_manager=self._db_manager
            ),
        )

    def _count_rows(self, model) -> int:
        assert self._db_manager is not None
        session = self._db_manager.get_product_session()
        try:
            from sqlalchemy import func, select

            return session.scalar(select(func.count()).select_from(model)) or 0
        finally:
            session.close()


class TestSqliteSendDecisionSnapshotWrite(_SnapshotShadowTestCase):
    def test_m1_flags_off_no_snapshot(self) -> None:
        default_db = _REPO_ROOT / "temp" / "product_gate.db"
        if default_db.exists():
            default_db.unlink()
        result = PreviewReplyLogService().record_preview(**_preview_kwargs())
        self.assertTrue(result.recorded)
        self.assertFalse(result.snapshot_recorded)
        self.assertFalse(default_db.exists())
        self.assertEqual(len(preview_log.all()), 1)

    def test_m2_flags_on_writes_snapshot(self) -> None:
        self._enable_all_write_flags()
        result = self._service().record_preview(**_preview_kwargs())
        self.assertTrue(result.recorded)
        self.assertTrue(result.db_recorded)
        self.assertTrue(result.snapshot_recorded)
        self.assertIsNotNone(result.send_decision_id)
        self.assertTrue(self._db_path.exists())
        self.assertEqual(self._count_rows(ReplyLogRow), 1)
        self.assertEqual(self._count_rows(SendDecisionSnapshotRow), 1)

    @patch.object(
        ReplyLogRepositorySQLite,
        "create_preview_reply_log",
        side_effect=RuntimeError("reply log down"),
    )
    def test_m3_replylog_failure_no_snapshot(self, _reply_mock) -> None:
        self._enable_all_write_flags()
        result = self._service().record_preview(**_preview_kwargs())
        self.assertTrue(result.recorded)
        self.assertFalse(result.db_recorded)
        self.assertFalse(result.snapshot_recorded)
        self.assertEqual(len(preview_log.all()), 1)
        self.assertEqual(self._count_rows(SendDecisionSnapshotRow), 0)

    @patch.object(
        SendDecisionRepositorySQLite,
        "create_snapshot",
        side_effect=RuntimeError("snapshot down"),
    )
    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    def test_m4_snapshot_failure_no_send(
        self,
        send_text_mock,
        _snap_mock,
    ) -> None:
        self._enable_all_write_flags()
        result = self._service().record_preview(**_preview_kwargs())
        self.assertTrue(result.recorded)
        self.assertTrue(result.db_recorded)
        self.assertFalse(result.snapshot_recorded)
        self.assertEqual(result.snapshot_error, "snapshot down")
        send_text_mock.assert_not_called()
        self.assertEqual(len(preview_log.all()), 1)

    def test_m5_snapshot_fields(self) -> None:
        self._enable_all_write_flags()
        result = self._service().record_preview(**_preview_kwargs())
        assert self._db_manager is not None
        session = self._db_manager.get_product_session()
        try:
            row = session.get(SendDecisionSnapshotRow, result.send_decision_id)
            assert row is not None
            self.assertEqual(row.decision_phase, "ai_preview")
            self.assertEqual(row.intent_bucket, "allowed")
            self.assertEqual(row.risk_level, "low")
            self.assertEqual(row.send_mode, "preview_only")
            self.assertEqual(row.allowed_to_send, 0)
        finally:
            session.close()

    def test_m6_append_only(self) -> None:
        self._enable_all_write_flags()
        svc = self._service()
        first = svc.record_preview(**_preview_kwargs())
        second = svc.record_preview(**_preview_kwargs())
        self.assertNotEqual(first.reply_log_id, second.reply_log_id)
        self.assertNotEqual(first.send_decision_id, second.send_decision_id)
        self.assertEqual(self._count_rows(SendDecisionSnapshotRow), 2)

    def test_m7_list_snapshots_by_reply_log(self) -> None:
        self._enable_all_write_flags()
        result = self._service().record_preview(**_preview_kwargs())
        assert self._db_manager is not None
        repo = SendDecisionRepositorySQLite(db_manager=self._db_manager)
        snapshots = repo.list_snapshots_by_reply_log(result.reply_log_id)
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].send_decision_id, result.send_decision_id)
        self.assertEqual(snapshots[0].decision_phase, "ai_preview")

    def test_no_legacy_import(self) -> None:
        for path in _PERSISTENCE_SOURCES:
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("from database.models", source)
            self.assertNotIn("from database.db_manager", source)


if __name__ == "__main__":
    unittest.main()

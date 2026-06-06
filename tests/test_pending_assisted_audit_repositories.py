"""Phase 14q: PendingAssisted / AuditLog repository tests."""

from __future__ import annotations

import importlib
import json
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from product_persistence.db_manager import ProductDbManager, reset_product_db_manager
from product_persistence.models import AuditLogRow, PendingAssistedReplyRow
from product_persistence.repositories.sqlite_audit_log_repository import (
    AuditLogRepositorySQLite,
)
from product_persistence.repositories.sqlite_pending_assisted_repository import (
    PendingAssistedRepositorySQLite,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REPO_SOURCES = (
    _REPO_ROOT / "product_persistence" / "repositories" / "sqlite_pending_assisted_repository.py",
    _REPO_ROOT / "product_persistence" / "repositories" / "sqlite_audit_log_repository.py",
)


def _pending_kwargs(**overrides) -> dict:
    base = dict(
        reply_log_id="rl-q-1",
        workspace_id="ws-q-1",
        shop_id="shop-q-1",
        account_id="acc-q-1",
        platform_id="pinduoduo",
        buyer_id="buyer-q-1",
        buyer_message="这款商品还有库存吗",
        ai_suggested_reply="建议回复",
        intent="stock_inquiry",
        intent_bucket="allowed",
        risk_level="low",
    )
    base.update(overrides)
    return base


class _RepositoryTestCase(unittest.TestCase):
    _db_manager: ProductDbManager | None = None

    def setUp(self) -> None:
        self._db_manager = None
        reset_product_db_manager()
        self._tmpdir = _REPO_ROOT / "temp" / "phase14q_repo_tests"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._tmpdir / "product_gate_repo_test.db"
        if self._db_path.exists():
            self._db_path.unlink()
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_PERSISTENCE_ENABLED",
            "PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED",
            "PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG",
            "PRODUCT_PERSISTENCE_WRITE_REPLY_LOG",
            "PRODUCT_PERSISTENCE_WRITE_SEND_DECISION",
            "PRODUCT_PERSISTENCE_READ_DASHBOARD",
            "PRODUCT_DB_URL",
        ):
            os.environ.pop(key, None)
        importlib.reload(importlib.import_module("product_persistence.flags"))

    def tearDown(self) -> None:
        if self._db_manager is not None:
            self._db_manager.close_product_db()
        reset_product_db_manager()
        if self._db_path.exists():
            self._db_path.unlink(missing_ok=True)
        self._env_patch.stop()

    def _enable_flags(self, *, pending: bool = True, audit: bool = True) -> ProductDbManager:
        os.environ["PRODUCT_PERSISTENCE_ENABLED"] = "true"
        if pending:
            os.environ["PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED"] = "true"
        if audit:
            os.environ["PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG"] = "true"
        os.environ["PRODUCT_DB_URL"] = f"sqlite:///{self._db_path.as_posix()}"
        importlib.reload(importlib.import_module("product_persistence.flags"))
        reset_product_db_manager()
        self._db_manager = ProductDbManager(db_url=os.environ["PRODUCT_DB_URL"])
        return self._db_manager


class TestPendingAssistedAuditRepositories(_RepositoryTestCase):
    def test_flags_off_session_not_available(self) -> None:
        repo = PendingAssistedRepositorySQLite(
            db_manager=ProductDbManager(
                db_url=f"sqlite:///{self._db_path.as_posix()}"
            )
        )
        with self.assertRaises(NotImplementedError):
            repo.create_pending(**_pending_kwargs())

    def test_create_get_list_pending(self) -> None:
        db = self._enable_flags(pending=True, audit=False)
        repo = PendingAssistedRepositorySQLite(db_manager=db)
        pending_id = repo.create_pending(**_pending_kwargs())
        item = repo.get_pending(pending_id)
        assert item is not None
        self.assertEqual(item.pending_assisted_id, pending_id)
        self.assertEqual(item.status, "pending")
        listed, total = repo.list_pending(workspace_id="ws-q-1", status="pending")
        self.assertEqual(total, 1)
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].pending_assisted_id, pending_id)

    def test_pending_default_status_pending(self) -> None:
        db = self._enable_flags(pending=True, audit=False)
        repo = PendingAssistedRepositorySQLite(db_manager=db)
        pending_id = repo.create_pending(**_pending_kwargs())
        session = db.get_product_session()
        try:
            row = session.get(PendingAssistedReplyRow, pending_id)
            assert row is not None
            self.assertEqual(row.status, "pending")
        finally:
            session.close()

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    @patch("Message.handlers.ai_handler.AIReplyHandler._send_reply")
    def test_mark_status_only_updates_status_no_send(
        self,
        send_reply_mock: MagicMock,
        send_text_mock: MagicMock,
    ) -> None:
        db = self._enable_flags(pending=True, audit=False)
        repo = PendingAssistedRepositorySQLite(db_manager=db)
        pending_id = repo.create_pending(**_pending_kwargs())
        ok = repo.mark_status(
            pending_id,
            "approved",
            approved_by="operator-1",
        )
        self.assertTrue(ok)
        item = repo.get_pending(pending_id)
        assert item is not None
        self.assertEqual(item.status, "approved")
        self.assertEqual(item.approved_by, "operator-1")
        send_reply_mock.assert_not_called()
        send_text_mock.assert_not_called()

    def test_duplicate_pending_id_raises(self) -> None:
        db = self._enable_flags(pending=True, audit=False)
        repo = PendingAssistedRepositorySQLite(db_manager=db)
        repo.create_pending(**_pending_kwargs(), pending_assisted_id="dup-id")
        with self.assertRaises(ValueError):
            repo.create_pending(**_pending_kwargs(), pending_assisted_id="dup-id")

    def test_append_list_get_audit(self) -> None:
        db = self._enable_flags(pending=False, audit=True)
        repo = AuditLogRepositorySQLite(db_manager=db)
        log_id = repo.append_audit_log(
            workspace_id="ws-q-1",
            actor_user_id="operator-1",
            actor_role="operator",
            action="pending_assisted_created",
            target_type="pending_assisted",
            target_id="pending-1",
            shop_id="shop-q-1",
        )
        item = repo.get_audit_log(log_id)
        assert item is not None
        self.assertEqual(item.action, "pending_assisted_created")
        listed = repo.list_audit_logs(workspace_id="ws-q-1")
        self.assertEqual(len(listed), 1)

    def test_audit_append_only_no_update_delete_methods(self) -> None:
        repo = AuditLogRepositorySQLite(
            db_manager=self._enable_flags(pending=False, audit=True)
        )
        self.assertFalse(hasattr(repo, "update_audit_log"))
        self.assertFalse(hasattr(repo, "delete_audit_log"))

    def test_audit_sanitizes_sensitive_state(self) -> None:
        db = self._enable_flags(pending=False, audit=True)
        repo = AuditLogRepositorySQLite(db_manager=db)
        log_id = repo.append_audit_log(
            workspace_id="ws-q-1",
            actor_user_id="operator-1",
            actor_role="operator",
            action="assisted_approved",
            target_type="pending_assisted",
            target_id="pending-1",
            before_state={"status": "pending", "password": "secret"},
            after_state={"status": "approved", "api_key": "key"},
        )
        item = repo.get_audit_log(log_id)
        assert item is not None
        before = json.loads(item.before_state or "{}")
        after = json.loads(item.after_state or "{}")
        self.assertEqual(before.get("status"), "pending")
        self.assertNotIn("password", before)
        self.assertNotIn("api_key", after)

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    def test_repositories_do_not_call_sendmessage(self, send_text_mock: MagicMock) -> None:
        db = self._enable_flags(pending=True, audit=True)
        pending_repo = PendingAssistedRepositorySQLite(db_manager=db)
        audit_repo = AuditLogRepositorySQLite(db_manager=db)
        pending_id = pending_repo.create_pending(**_pending_kwargs())
        pending_repo.mark_status(pending_id, "rejected", rejected_by="operator-1")
        audit_repo.append_audit_log(
            workspace_id="ws-q-1",
            actor_user_id="operator-1",
            actor_role="operator",
            action="assisted_rejected",
            target_type="pending_assisted",
            target_id=pending_id,
        )
        send_text_mock.assert_not_called()

    def test_db_failure_raises_no_send_metadata_only(self) -> None:
        db = self._enable_flags(pending=True, audit=False)
        repo = PendingAssistedRepositorySQLite(db_manager=db)
        with patch.object(
            db,
            "get_product_session",
            side_effect=RuntimeError("db down"),
        ):
            with self.assertRaises(RuntimeError):
                repo.create_pending(**_pending_kwargs())

    def test_repository_sources_no_legacy_or_handler_imports(self) -> None:
        for path in _REPO_SOURCES:
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("SendMessage", source)
            self.assertNotIn("_send_reply", source)
            self.assertNotIn("ai_handler", source)
            self.assertNotIn("from database.models", source)
            self.assertNotIn("from database.db_manager", source)


if __name__ == "__main__":
    unittest.main()

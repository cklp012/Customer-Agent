"""Phase 15j: Dashboard action idempotency repository tests."""

from __future__ import annotations

import importlib
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from sqlalchemy import inspect

from product_persistence.db_manager import ProductDbManager, reset_product_db_manager
from product_persistence.models import DashboardActionIdempotencyRow
from product_persistence.repositories.sqlite_action_idempotency_repository import (
    ActionIdempotencyRepositorySQLite,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REPO_SOURCE = (
    _REPO_ROOT
    / "product_persistence"
    / "repositories"
    / "sqlite_action_idempotency_repository.py"
)
_DEFAULT_DB = _REPO_ROOT / "temp" / "product_gate.db"

_ACTION_COLUMNS = {
    "client_request_id",
    "workspace_id",
    "shop_id",
    "actor_user_id",
    "actor_role",
    "pending_assisted_id",
    "action",
    "payload_hash",
    "status",
    "response_json",
    "created_at",
    "updated_at",
}

_ACTION_INDEXES = {
    "idx_action_idempotency_workspace_shop",
    "idx_action_idempotency_pending_action",
    "idx_action_idempotency_actor",
    "idx_action_idempotency_status",
    "idx_action_idempotency_updated_at",
}


def _acquire_kwargs(**overrides) -> dict:
    base = dict(
        client_request_id="req-j-1",
        workspace_id="ws-j-1",
        shop_id="shop-j-1",
        actor_user_id="op-j-1",
        actor_role="operator",
        pending_assisted_id="pending-j-1",
        action="approve",
        payload={
            "action": "approve",
            "pending_assisted_id": "pending-j-1",
            "workspace_id": "ws-j-1",
            "shop_id": "shop-j-1",
            "dry_run_expected": True,
        },
    )
    base.update(overrides)
    return base


class _RepositoryTestCase(unittest.TestCase):
    _db_manager: ProductDbManager | None = None

    def setUp(self) -> None:
        self._db_manager = None
        reset_product_db_manager()
        self._tmpdir = _REPO_ROOT / "temp" / "phase15j_repo_tests"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._tmpdir / "product_gate_action_idempotency.db"
        if self._db_path.exists():
            self._db_path.unlink()
        if _DEFAULT_DB.exists():
            _DEFAULT_DB.unlink()
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_PERSISTENCE_ENABLED",
            "PRODUCT_PERSISTENCE_WRITE_ACTION_IDEMPOTENCY",
            "PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY",
            "PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED",
            "PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG",
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

    def _enable_flags(self) -> ProductDbManager:
        os.environ["PRODUCT_PERSISTENCE_ENABLED"] = "true"
        os.environ["PRODUCT_PERSISTENCE_WRITE_ACTION_IDEMPOTENCY"] = "true"
        os.environ["PRODUCT_DB_URL"] = f"sqlite:///{self._db_path.as_posix()}"
        importlib.reload(importlib.import_module("product_persistence.flags"))
        reset_product_db_manager()
        self._db_manager = ProductDbManager(db_url=os.environ["PRODUCT_DB_URL"])
        self._db_manager.init_product_db()
        return self._db_manager

    def _repo(self) -> ActionIdempotencyRepositorySQLite:
        assert self._db_manager is not None
        return ActionIdempotencyRepositorySQLite(db_manager=self._db_manager)

    def _column_names(self, table: str) -> set[str]:
        assert self._db_manager is not None
        assert self._db_manager._engine is not None
        return {col["name"] for col in inspect(self._db_manager._engine).get_columns(table)}

    def _index_names(self, table: str) -> set[str]:
        assert self._db_manager is not None
        assert self._db_manager._engine is not None
        return {idx["name"] for idx in inspect(self._db_manager._engine).get_indexes(table)}


class TestActionIdempotencyRepository(_RepositoryTestCase):
    def test_flag_default_false(self) -> None:
        from product_persistence import flags

        self.assertFalse(flags.should_write_action_idempotency())

    def test_flags_off_repository_path_does_not_create_db(self) -> None:
        repo = ActionIdempotencyRepositorySQLite(
            db_manager=ProductDbManager(db_url=f"sqlite:///{self._db_path.as_posix()}")
        )
        with self.assertRaises(NotImplementedError):
            repo.acquire(**_acquire_kwargs())
        self.assertFalse(self._db_path.exists())

    def test_flag_on_creates_table(self) -> None:
        self._enable_flags()
        self.assertTrue(self._db_path.exists())
        self.assertEqual(
            self._column_names("dashboard_action_idempotency_keys"),
            _ACTION_COLUMNS,
        )

    def test_schema_fields_and_indexes_complete(self) -> None:
        self._enable_flags()
        indexes = self._index_names("dashboard_action_idempotency_keys")
        self.assertTrue(_ACTION_INDEXES.issubset(indexes))

    def test_acquire_new_key_success(self) -> None:
        self._enable_flags()
        repo = self._repo()
        result = repo.acquire(**_acquire_kwargs())
        self.assertTrue(result.acquired)
        self.assertEqual(result.status, "in_progress")
        self.assertIsNone(result.reason)
        record = repo.get("req-j-1")
        assert record is not None
        self.assertEqual(record.status, "in_progress")

    def test_acquire_same_payload_completed_returns_previous_response(self) -> None:
        self._enable_flags()
        repo = self._repo()
        stored = {"http_status": 200, "body": {"success": True, "status": "rejected"}}
        repo.acquire(**_acquire_kwargs())
        repo.complete("req-j-1", stored)
        result = repo.acquire(**_acquire_kwargs())
        self.assertFalse(result.acquired)
        self.assertEqual(result.reason, "replay_completed")
        self.assertEqual(result.existing_response, stored)

    def test_acquire_same_payload_in_progress_returns_already_in_progress(self) -> None:
        self._enable_flags()
        repo = self._repo()
        repo.acquire(**_acquire_kwargs())
        result = repo.acquire(**_acquire_kwargs())
        self.assertFalse(result.acquired)
        self.assertEqual(result.reason, "already_in_progress")

    def test_acquire_different_payload_returns_conflict(self) -> None:
        self._enable_flags()
        repo = self._repo()
        repo.acquire(**_acquire_kwargs())
        result = repo.acquire(
            **_acquire_kwargs(
                payload={
                    "action": "approve",
                    "pending_assisted_id": "pending-j-1",
                    "workspace_id": "ws-j-1",
                    "shop_id": "shop-j-1",
                    "dry_run_expected": False,
                }
            )
        )
        self.assertFalse(result.acquired)
        self.assertEqual(result.reason, "client_request_conflict")

    def test_complete_stores_response_json(self) -> None:
        self._enable_flags()
        repo = self._repo()
        repo.acquire(**_acquire_kwargs())
        stored = {"http_status": 200, "body": {"success": True, "action": "approve"}}
        record = repo.complete("req-j-1", stored)
        self.assertEqual(record.status, "completed")
        self.assertEqual(record.response, stored)
        assert self._db_manager is not None
        session = self._db_manager.get_product_session()
        try:
            row = session.get(DashboardActionIdempotencyRow, "req-j-1")
            assert row is not None
            self.assertEqual(json.loads(row.response_json), stored)
        finally:
            session.close()

    def test_fail_stores_error_response(self) -> None:
        self._enable_flags()
        repo = self._repo()
        repo.acquire(**_acquire_kwargs())
        stored = {"http_status": 500, "body": {"success": False, "status": "internal_error"}}
        record = repo.fail("req-j-1", stored)
        self.assertEqual(record.status, "failed")
        self.assertEqual(record.response, stored)

    def test_duplicate_insert_race_safe(self) -> None:
        self._enable_flags()
        repo = self._repo()
        first = repo.acquire(**_acquire_kwargs())
        self.assertTrue(first.acquired)
        second = repo.acquire(**_acquire_kwargs())
        self.assertFalse(second.acquired)
        self.assertEqual(second.reason, "already_in_progress")

    def test_payload_hash_stable(self) -> None:
        payload = {"action": "approve", "shop_id": "shop-j-1", "dry_run_expected": True}
        first = ActionIdempotencyRepositorySQLite.compute_payload_hash(payload)
        second = ActionIdempotencyRepositorySQLite.compute_payload_hash(
            {"dry_run_expected": True, "shop_id": "shop-j-1", "action": "approve"}
        )
        self.assertEqual(first, second)

    def test_import_repository_no_db_side_effect(self) -> None:
        if _DEFAULT_DB.exists():
            _DEFAULT_DB.unlink()
        module_name = (
            "product_persistence.repositories.sqlite_action_idempotency_repository"
        )
        if module_name in sys.modules:
            del sys.modules[module_name]
        import product_persistence.repositories.sqlite_action_idempotency_repository  # noqa: F401

        self.assertFalse(_DEFAULT_DB.exists())

    def test_repository_static_no_send_imports(self) -> None:
        import_lines = [
            line
            for line in _REPO_SOURCE.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        import_block = "\n".join(import_lines)
        for token in (
            "SendMessage",
            "Message.handlers",
            "outbound_resolver",
            "Channel.pinduoduo",
            "Channel.doudian",
            "database.models",
            "database.db_manager",
        ):
            self.assertNotIn(token, import_block, msg=token)

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    @patch("Message.handlers.ai_handler.AIReplyHandler._send_reply")
    def test_no_send_side_effect(
        self,
        send_reply_mock: MagicMock,
        send_text_mock: MagicMock,
    ) -> None:
        self._enable_flags()
        repo = self._repo()
        repo.acquire(**_acquire_kwargs())
        repo.complete("req-j-1", {"http_status": 200, "body": {"success": True}})
        send_reply_mock.assert_not_called()
        send_text_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()

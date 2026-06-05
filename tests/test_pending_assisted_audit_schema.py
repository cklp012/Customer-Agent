"""Phase 14q: PendingAssisted / AuditLog schema tests."""

from __future__ import annotations

import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from product_persistence.db_manager import ProductDbManager, reset_product_db_manager

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_DB = _REPO_ROOT / "temp" / "product_gate.db"
_PERSISTENCE_SOURCES = (
    _REPO_ROOT / "product_persistence" / "db_manager.py",
    _REPO_ROOT / "product_persistence" / "models.py",
    _REPO_ROOT / "product_persistence" / "repositories" / "sqlite_pending_assisted_repository.py",
    _REPO_ROOT / "product_persistence" / "repositories" / "sqlite_audit_log_repository.py",
)

_PENDING_COLUMNS = {
    "pending_assisted_id",
    "reply_log_id",
    "workspace_id",
    "shop_id",
    "account_id",
    "platform_id",
    "buyer_id",
    "conversation_id",
    "inbound_message_id",
    "buyer_message",
    "ai_suggested_reply",
    "merchant_edited_reply",
    "final_reply",
    "status",
    "intent",
    "intent_bucket",
    "risk_level",
    "blocked_reason",
    "human_takeover_reason",
    "created_by",
    "approved_by",
    "rejected_by",
    "expires_at",
    "created_at",
    "updated_at",
}

_PENDING_INDEXES = {
    "idx_pending_workspace_status_created_at",
    "idx_pending_shop_status_created_at",
    "idx_pending_reply_log_id",
    "idx_pending_buyer_created_at",
}

_AUDIT_COLUMNS = {
    "audit_log_id",
    "workspace_id",
    "shop_id",
    "account_id",
    "platform_id",
    "actor_user_id",
    "actor_role",
    "action",
    "target_type",
    "target_id",
    "reply_log_id",
    "pending_assisted_id",
    "before_state",
    "after_state",
    "reason",
    "ip_address",
    "user_agent",
    "created_at",
}

_AUDIT_INDEXES = {
    "idx_audit_workspace_created_at",
    "idx_audit_shop_created_at",
    "idx_audit_actor_created_at",
    "idx_audit_target",
}


class _SchemaTestCase(unittest.TestCase):
    _db_manager: ProductDbManager | None = None

    def setUp(self) -> None:
        self._db_manager = None
        reset_product_db_manager()
        self._tmpdir = _REPO_ROOT / "temp" / "phase14q_schema_tests"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._tmpdir / "product_gate_schema_test.db"
        if self._db_path.exists():
            self._db_path.unlink()
        if _DEFAULT_DB.exists():
            _DEFAULT_DB.unlink()
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

    def _init_with_flags(self, *, pending: bool = False, audit: bool = False) -> ProductDbManager:
        os.environ["PRODUCT_PERSISTENCE_ENABLED"] = "true"
        if pending:
            os.environ["PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED"] = "true"
        else:
            os.environ.pop("PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED", None)
        if audit:
            os.environ["PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG"] = "true"
        else:
            os.environ.pop("PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG", None)
        os.environ["PRODUCT_DB_URL"] = f"sqlite:///{self._db_path.as_posix()}"
        importlib.reload(importlib.import_module("product_persistence.flags"))
        reset_product_db_manager()
        self._db_manager = ProductDbManager(db_url=os.environ["PRODUCT_DB_URL"])
        self._db_manager.init_product_db()
        return self._db_manager

    def _table_names(self) -> set[str]:
        assert self._db_manager is not None
        from sqlalchemy import inspect

        engine = self._db_manager._engine
        assert engine is not None
        return set(inspect(engine).get_table_names())

    def _column_names(self, table: str) -> set[str]:
        assert self._db_manager is not None
        from sqlalchemy import inspect

        engine = self._db_manager._engine
        assert engine is not None
        return {col["name"] for col in inspect(engine).get_columns(table)}

    def _index_names(self, table: str) -> set[str]:
        assert self._db_manager is not None
        from sqlalchemy import inspect

        engine = self._db_manager._engine
        assert engine is not None
        return {idx["name"] for idx in inspect(engine).get_indexes(table)}


class TestPendingAssistedAuditSchema(_SchemaTestCase):
    def test_flags_off_no_db(self) -> None:
        from product_persistence.db_manager import ProductDbManager

        mgr = ProductDbManager()
        mgr.init_product_db()
        self.assertFalse(_DEFAULT_DB.exists())
        self.assertFalse(self._db_path.exists())

    def test_pending_flag_creates_pending_table(self) -> None:
        self._init_with_flags(pending=True)
        tables = self._table_names()
        self.assertIn("pending_assisted_replies", tables)

    def test_audit_flag_creates_audit_table(self) -> None:
        self._init_with_flags(audit=True)
        tables = self._table_names()
        self.assertIn("audit_logs", tables)

    def test_pending_schema_fields_complete(self) -> None:
        self._init_with_flags(pending=True)
        columns = self._column_names("pending_assisted_replies")
        self.assertTrue(_PENDING_COLUMNS.issubset(columns))

    def test_pending_indexes_exist(self) -> None:
        self._init_with_flags(pending=True)
        indexes = self._index_names("pending_assisted_replies")
        self.assertTrue(_PENDING_INDEXES.issubset(indexes))

    def test_audit_schema_fields_complete(self) -> None:
        self._init_with_flags(audit=True)
        columns = self._column_names("audit_logs")
        self.assertTrue(_AUDIT_COLUMNS.issubset(columns))

    def test_audit_indexes_exist(self) -> None:
        self._init_with_flags(audit=True)
        indexes = self._index_names("audit_logs")
        self.assertTrue(_AUDIT_INDEXES.issubset(indexes))

    def test_import_module_no_db_side_effect(self) -> None:
        if _DEFAULT_DB.exists():
            _DEFAULT_DB.unlink()
        for name in (
            "product_persistence.repositories.sqlite_pending_assisted_repository",
            "product_persistence.repositories.sqlite_audit_log_repository",
        ):
            sys.modules.pop(name, None)
        import product_persistence.repositories.sqlite_pending_assisted_repository  # noqa: F401
        import product_persistence.repositories.sqlite_audit_log_repository  # noqa: F401

        self.assertFalse(_DEFAULT_DB.exists())

    def test_no_legacy_database_import(self) -> None:
        for path in _PERSISTENCE_SOURCES:
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("from database.models", source)
            self.assertNotIn("from database.db_manager", source)


if __name__ == "__main__":
    unittest.main()

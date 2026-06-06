"""Phase 15b: Outbound idempotency schema tests."""

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
    _REPO_ROOT
    / "product_persistence"
    / "repositories"
    / "sqlite_outbound_idempotency_repository.py",
)

_IDEMPOTENCY_COLUMNS = {
    "idempotency_key",
    "workspace_id",
    "shop_id",
    "account_id",
    "platform_id",
    "pending_assisted_id",
    "reply_log_id",
    "operation_type",
    "status",
    "attempt_count",
    "provider_message_id",
    "platform_status",
    "error_code",
    "error_message",
    "locked_at",
    "completed_at",
    "created_at",
    "updated_at",
    "metadata_json",
}

_IDEMPOTENCY_INDEXES = {
    "idx_idempotency_workspace_shop",
    "idx_idempotency_pending_assisted",
    "idx_idempotency_status",
    "idx_idempotency_operation_type",
    "idx_idempotency_updated_at",
}


class _SchemaTestCase(unittest.TestCase):
    _db_manager: ProductDbManager | None = None

    def setUp(self) -> None:
        self._db_manager = None
        reset_product_db_manager()
        self._tmpdir = _REPO_ROOT / "temp" / "phase15b_schema_tests"
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
            "PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY",
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

    def _init_with_flag(self) -> ProductDbManager:
        os.environ["PRODUCT_PERSISTENCE_ENABLED"] = "true"
        os.environ["PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY"] = "true"
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


class TestOutboundIdempotencySchema(_SchemaTestCase):
    def test_flag_default_false(self) -> None:
        from product_persistence import flags

        self.assertFalse(flags.should_write_outbound_idempotency())

    def test_flags_off_no_db(self) -> None:
        mgr = ProductDbManager()
        mgr.init_product_db()
        self.assertFalse(_DEFAULT_DB.exists())
        self.assertFalse(self._db_path.exists())

    def test_flag_on_creates_idempotency_table(self) -> None:
        self._init_with_flag()
        tables = self._table_names()
        self.assertIn("outbound_idempotency_keys", tables)

    def test_schema_fields_complete(self) -> None:
        self._init_with_flag()
        columns = self._column_names("outbound_idempotency_keys")
        self.assertTrue(_IDEMPOTENCY_COLUMNS.issubset(columns))

    def test_indexes_exist(self) -> None:
        self._init_with_flag()
        indexes = self._index_names("outbound_idempotency_keys")
        self.assertTrue(_IDEMPOTENCY_INDEXES.issubset(indexes))

    def test_import_module_no_db_side_effect(self) -> None:
        if _DEFAULT_DB.exists():
            _DEFAULT_DB.unlink()
        sys.modules.pop(
            "product_persistence.repositories.sqlite_outbound_idempotency_repository",
            None,
        )
        import product_persistence.repositories.sqlite_outbound_idempotency_repository  # noqa: F401

        self.assertFalse(_DEFAULT_DB.exists())

    def test_no_legacy_database_import(self) -> None:
        for path in _PERSISTENCE_SOURCES:
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("from database.models", source)
            self.assertNotIn("from database.db_manager", source)

    def test_no_send_handler_outbound_import(self) -> None:
        repo_source = _PERSISTENCE_SOURCES[2].read_text(encoding="utf-8")
        import_lines = [
            line
            for line in repo_source.splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        import_block = "\n".join(import_lines)
        for token in (
            "SendMessage",
            "Message.handlers",
            "outbound_resolver",
            "Channel.pinduoduo",
            "Channel.doudian",
        ):
            self.assertNotIn(token, import_block, msg=token)


if __name__ == "__main__":
    unittest.main()

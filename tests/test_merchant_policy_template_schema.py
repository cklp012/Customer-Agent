"""Phase 14u: MerchantSafetyPolicy / MerchantReplyTemplate schema tests."""

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
    _REPO_ROOT / "product_persistence" / "repositories" / "sqlite_merchant_policy_repository.py",
    _REPO_ROOT / "product_persistence" / "repositories" / "sqlite_reply_template_repository.py",
)

_POLICY_COLUMNS = {
    "policy_id",
    "workspace_id",
    "shop_id",
    "intent_category",
    "ai_intervention_mode",
    "platform_mode_ceiling",
    "allowed_template_ids",
    "require_human_confirmation",
    "allow_auto_reply",
    "forbidden_keywords_extra",
    "policy_version",
    "enabled",
    "created_at",
    "updated_at",
}

_POLICY_INDEXES = {
    "idx_policy_workspace_shop_intent",
    "idx_policy_workspace_enabled",
    "idx_policy_shop_intent",
    "idx_policy_updated_at",
}

_TEMPLATE_COLUMNS = {
    "template_id",
    "workspace_id",
    "shop_id",
    "intent_category",
    "title",
    "content",
    "variables",
    "content_hash",
    "validation_status",
    "validation_warnings",
    "template_version",
    "enabled",
    "created_at",
    "updated_at",
}

_TEMPLATE_INDEXES = {
    "idx_template_workspace_shop_intent",
    "idx_template_workspace_enabled",
    "idx_template_validation_status",
    "idx_template_content_hash",
}


class _SchemaTestCase(unittest.TestCase):
    _db_manager: ProductDbManager | None = None

    def setUp(self) -> None:
        self._db_manager = None
        reset_product_db_manager()
        self._tmpdir = _REPO_ROOT / "temp" / "phase14u_schema_tests"
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
            "PRODUCT_PERSISTENCE_WRITE_MERCHANT_POLICY",
            "PRODUCT_PERSISTENCE_WRITE_REPLY_TEMPLATE",
            "PRODUCT_PERSISTENCE_READ_MERCHANT_POLICY",
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

    def _init_with_flags(
        self,
        *,
        policy: bool = False,
        template: bool = False,
        read_policy: bool = False,
    ) -> ProductDbManager:
        os.environ["PRODUCT_PERSISTENCE_ENABLED"] = "true"
        if policy:
            os.environ["PRODUCT_PERSISTENCE_WRITE_MERCHANT_POLICY"] = "true"
        else:
            os.environ.pop("PRODUCT_PERSISTENCE_WRITE_MERCHANT_POLICY", None)
        if template:
            os.environ["PRODUCT_PERSISTENCE_WRITE_REPLY_TEMPLATE"] = "true"
        else:
            os.environ.pop("PRODUCT_PERSISTENCE_WRITE_REPLY_TEMPLATE", None)
        if read_policy:
            os.environ["PRODUCT_PERSISTENCE_READ_MERCHANT_POLICY"] = "true"
        else:
            os.environ.pop("PRODUCT_PERSISTENCE_READ_MERCHANT_POLICY", None)
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


class TestMerchantPolicyTemplateSchema(_SchemaTestCase):
    def test_flags_default_false(self) -> None:
        from product_persistence import flags

        self.assertFalse(flags.should_write_merchant_policy())
        self.assertFalse(flags.should_write_reply_template())
        self.assertFalse(flags.should_read_merchant_policy())

    def test_flags_off_no_db(self) -> None:
        mgr = ProductDbManager()
        mgr.init_product_db()
        self.assertFalse(_DEFAULT_DB.exists())
        self.assertFalse(self._db_path.exists())

    def test_policy_flag_creates_policy_table(self) -> None:
        self._init_with_flags(policy=True)
        tables = self._table_names()
        self.assertIn("merchant_safety_policies", tables)

    def test_template_flag_creates_template_table(self) -> None:
        self._init_with_flags(template=True)
        tables = self._table_names()
        self.assertIn("merchant_reply_templates", tables)

    def test_read_policy_flag_creates_policy_table(self) -> None:
        self._init_with_flags(read_policy=True)
        tables = self._table_names()
        self.assertIn("merchant_safety_policies", tables)

    def test_policy_schema_fields_complete(self) -> None:
        self._init_with_flags(policy=True)
        columns = self._column_names("merchant_safety_policies")
        self.assertTrue(_POLICY_COLUMNS.issubset(columns))

    def test_policy_indexes_exist(self) -> None:
        self._init_with_flags(policy=True)
        indexes = self._index_names("merchant_safety_policies")
        self.assertTrue(_POLICY_INDEXES.issubset(indexes))

    def test_template_schema_fields_complete(self) -> None:
        self._init_with_flags(template=True)
        columns = self._column_names("merchant_reply_templates")
        self.assertTrue(_TEMPLATE_COLUMNS.issubset(columns))

    def test_template_indexes_exist(self) -> None:
        self._init_with_flags(template=True)
        indexes = self._index_names("merchant_reply_templates")
        self.assertTrue(_TEMPLATE_INDEXES.issubset(indexes))

    def test_import_module_no_db_side_effect(self) -> None:
        if _DEFAULT_DB.exists():
            _DEFAULT_DB.unlink()
        for name in (
            "product_persistence.repositories.sqlite_merchant_policy_repository",
            "product_persistence.repositories.sqlite_reply_template_repository",
        ):
            sys.modules.pop(name, None)
        import product_persistence.repositories.sqlite_merchant_policy_repository  # noqa: F401
        import product_persistence.repositories.sqlite_reply_template_repository  # noqa: F401

        self.assertFalse(_DEFAULT_DB.exists())

    def test_no_legacy_database_import(self) -> None:
        for path in _PERSISTENCE_SOURCES:
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("from database.models", source)
            self.assertNotIn("from database.db_manager", source)


if __name__ == "__main__":
    unittest.main()

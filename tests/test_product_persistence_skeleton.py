"""Phase 14f: product_persistence skeleton — import, flags, no side effects."""

from __future__ import annotations

import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PRODUCT_GATE_DB = _REPO_ROOT / "temp" / "product_gate.db"

_PACKAGE_MODULES = (
    "product_persistence",
    "product_persistence.flags",
    "product_persistence.db_manager",
    "product_persistence.models",
    "product_persistence.repositories",
    "product_persistence.repositories.reply_log_repository",
    "product_persistence.repositories.send_decision_repository",
    "product_persistence.repositories.pending_assisted_reply_repository",
    "product_persistence.repositories.audit_log_repository",
    "product_persistence.services",
    "product_persistence.services.preview_reply_log_service",
    "product_persistence.services.assisted_reply_service",
)

_SOURCE_NO_LEGACY = (
    _REPO_ROOT / "product_persistence" / "flags.py",
    _REPO_ROOT / "product_persistence" / "db_manager.py",
    _REPO_ROOT / "product_persistence" / "services" / "preview_reply_log_service.py",
    _REPO_ROOT / "product_persistence" / "services" / "assisted_reply_service.py",
)


class TestProductPersistenceFlags(unittest.TestCase):
    def setUp(self) -> None:
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_PERSISTENCE_ENABLED",
            "PRODUCT_PERSISTENCE_WRITE_REPLY_LOG",
            "PRODUCT_PERSISTENCE_WRITE_SEND_DECISION",
            "PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG",
            "PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED",
            "PRODUCT_PERSISTENCE_WRITE_MERCHANT_POLICY",
            "PRODUCT_PERSISTENCE_WRITE_REPLY_TEMPLATE",
            "PRODUCT_PERSISTENCE_READ_MERCHANT_POLICY",
            "PRODUCT_ASSISTED_SERVICE_ENABLED",
            "PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY",
            "PRODUCT_PERSISTENCE_READ_DASHBOARD",
        ):
            os.environ.pop(key, None)
        importlib.reload(importlib.import_module("product_persistence.flags"))

    def tearDown(self) -> None:
        self._env_patch.stop()

    def test_flags_default_false(self) -> None:
        from product_persistence import flags

        self.assertFalse(flags.is_product_persistence_enabled())
        self.assertFalse(flags.should_write_reply_log())
        self.assertFalse(flags.should_write_send_decision())
        self.assertFalse(flags.should_write_audit_log())
        self.assertFalse(flags.should_write_pending_assisted())
        self.assertFalse(flags.should_write_merchant_policy())
        self.assertFalse(flags.should_write_reply_template())
        self.assertFalse(flags.should_read_merchant_policy())
        self.assertFalse(flags.is_assisted_service_enabled())
        self.assertFalse(flags.should_write_outbound_idempotency())
        self.assertFalse(flags.should_read_dashboard_from_product_db())

    def test_true_values(self) -> None:
        from product_persistence import flags

        for val in ("true", "1", "yes", "on", "TRUE", " Yes "):
            with self.subTest(val=val):
                os.environ["PRODUCT_PERSISTENCE_ENABLED"] = val
                os.environ["PRODUCT_PERSISTENCE_WRITE_REPLY_LOG"] = val
                importlib.reload(flags)
                self.assertTrue(flags.is_product_persistence_enabled())
                self.assertTrue(flags.should_write_reply_log())

    def test_false_values(self) -> None:
        from product_persistence import flags

        for val in ("false", "0", "no", "off", "", "maybe"):
            with self.subTest(val=val):
                os.environ["PRODUCT_PERSISTENCE_ENABLED"] = val
                importlib.reload(flags)
                self.assertFalse(flags.is_product_persistence_enabled())

    def test_child_flag_requires_enabled(self) -> None:
        from product_persistence import flags

        os.environ["PRODUCT_PERSISTENCE_WRITE_REPLY_LOG"] = "true"
        importlib.reload(flags)
        self.assertFalse(flags.should_write_reply_log())


class TestProductDbManagerSkeleton(unittest.TestCase):
    def test_default_db_url(self) -> None:
        from product_persistence.db_manager import ProductDbManager

        mgr = ProductDbManager()
        self.assertEqual(mgr.get_db_url(), "sqlite:///./temp/product_gate.db")

    def test_init_product_db_no_op(self) -> None:
        from product_persistence.db_manager import ProductDbManager

        mgr = ProductDbManager()
        mgr.init_product_db()
        self.assertFalse(_PRODUCT_GATE_DB.exists())

    def test_get_product_session_not_implemented(self) -> None:
        from product_persistence.db_manager import ProductDbManager

        mgr = ProductDbManager()
        with self.assertRaises(NotImplementedError):
            mgr.get_product_session()


class TestProductPersistenceNoSideEffects(unittest.TestCase):
    def test_import_does_not_create_product_gate_db(self) -> None:
        if _PRODUCT_GATE_DB.exists():
            _PRODUCT_GATE_DB.unlink()
        for name in _PACKAGE_MODULES:
            if name in sys.modules:
                del sys.modules[name]
        import product_persistence  # noqa: F401

        self.assertFalse(_PRODUCT_GATE_DB.exists())

    def test_repository_protocols_importable(self) -> None:
        from product_persistence.repositories import (
            AuditLogRepository,
            PendingAssistedReplyRepository,
            ReplyLogRepository,
            SendDecisionRepository,
        )

        self.assertTrue(hasattr(ReplyLogRepository, "create_preview_reply_log"))

    def test_service_stubs_importable(self) -> None:
        from product_persistence.services import (
            AssistedReplyService,
            PreviewReplyLogService,
        )

        for key in (
            "PRODUCT_PERSISTENCE_ENABLED",
            "PRODUCT_PERSISTENCE_WRITE_REPLY_LOG",
        ):
            os.environ.pop(key, None)

        preview = PreviewReplyLogService()
        result = preview.record_preview(message_text="hi", reply_text="suggestion")
        self.assertFalse(result.recorded)
        self.assertEqual(result.reason, "product_persistence_disabled")

        assisted = AssistedReplyService()
        result = assisted.approve_pending(
            "p1",
            actor_user_id="m1",
            actor_role="operator",
        )
        self.assertFalse(result.success)
        self.assertEqual(result.status, "disabled")
        self.assertEqual(result.reason, "assisted_disabled")

    def test_services_do_not_reference_send_paths(self) -> None:
        for path in (
            _REPO_ROOT / "product_persistence" / "services" / "preview_reply_log_service.py",
            _REPO_ROOT / "product_persistence" / "services" / "assisted_reply_service.py",
        ):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("SendMessage", source)
            self.assertNotIn("outbound_resolver", source)
            self.assertNotIn("send_text", source)

    def test_no_legacy_database_imports_in_sources(self) -> None:
        for path in _SOURCE_NO_LEGACY:
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("from database.models", source)
            self.assertNotIn("from database.db_manager", source)
            self.assertNotIn("import database.models", source)
            self.assertNotIn("import database.db_manager", source)


if __name__ == "__main__":
    unittest.main()

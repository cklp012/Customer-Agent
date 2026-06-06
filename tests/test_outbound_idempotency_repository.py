"""Phase 15b: Outbound idempotency repository tests."""

from __future__ import annotations

import importlib
import json
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from product_persistence.db_manager import ProductDbManager, reset_product_db_manager
from product_persistence.models import OutboundIdempotencyRow
from product_persistence.repositories.sqlite_outbound_idempotency_repository import (
    OutboundIdempotencyRepositorySQLite,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REPO_SOURCE = (
    _REPO_ROOT
    / "product_persistence"
    / "repositories"
    / "sqlite_outbound_idempotency_repository.py"
)


def _acquire_kwargs(**overrides) -> dict:
    base = dict(
        idempotency_key="assisted_send:pending-b-1",
        workspace_id="ws-b-1",
        shop_id="shop-b-1",
        account_id="acc-b-1",
        platform_id="pinduoduo",
        pending_assisted_id="pending-b-1",
        reply_log_id="rl-b-1",
    )
    base.update(overrides)
    return base


class _RepositoryTestCase(unittest.TestCase):
    _db_manager: ProductDbManager | None = None

    def setUp(self) -> None:
        self._db_manager = None
        reset_product_db_manager()
        self._tmpdir = _REPO_ROOT / "temp" / "phase15b_repo_tests"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._tmpdir / "product_gate_repo_test.db"
        if self._db_path.exists():
            self._db_path.unlink()
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_PERSISTENCE_ENABLED",
            "PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY",
            "PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED",
            "PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG",
            "PRODUCT_ASSISTED_SERVICE_ENABLED",
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
        os.environ["PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY"] = "true"
        os.environ["PRODUCT_DB_URL"] = f"sqlite:///{self._db_path.as_posix()}"
        importlib.reload(importlib.import_module("product_persistence.flags"))
        reset_product_db_manager()
        self._db_manager = ProductDbManager(db_url=os.environ["PRODUCT_DB_URL"])
        self._db_manager.init_product_db()
        return self._db_manager

    def _repo(self) -> OutboundIdempotencyRepositorySQLite:
        assert self._db_manager is not None
        return OutboundIdempotencyRepositorySQLite(db_manager=self._db_manager)


class TestOutboundIdempotencyRepository(_RepositoryTestCase):
    def test_flags_off_repository_path_does_not_create_db_or_send(self) -> None:
        repo = OutboundIdempotencyRepositorySQLite(
            db_manager=ProductDbManager(db_url=f"sqlite:///{self._db_path.as_posix()}")
        )
        with self.assertRaises(NotImplementedError):
            repo.acquire(**_acquire_kwargs())
        self.assertFalse(self._db_path.exists())

    def test_acquire_new_key_success(self) -> None:
        self._enable_flags()
        repo = self._repo()
        result = repo.acquire(**_acquire_kwargs())
        self.assertTrue(result.acquired)
        self.assertEqual(result.status, "in_progress")
        self.assertIsNone(result.reason)
        record = repo.get("assisted_send:pending-b-1")
        assert record is not None
        self.assertEqual(record.status, "in_progress")
        self.assertEqual(record.attempt_count, 1)

    def test_acquire_existing_succeeded_returns_already_sent(self) -> None:
        self._enable_flags()
        repo = self._repo()
        repo.acquire(**_acquire_kwargs())
        repo.mark_succeeded(
            "assisted_send:pending-b-1",
            provider_message_id="msg-1",
            platform_status="accepted",
        )
        result = repo.acquire(**_acquire_kwargs())
        self.assertFalse(result.acquired)
        self.assertEqual(result.reason, "already_sent")
        self.assertEqual(result.existing_status, "succeeded")

    def test_acquire_existing_in_progress_returns_already_in_progress(self) -> None:
        self._enable_flags()
        repo = self._repo()
        repo.acquire(**_acquire_kwargs())
        result = repo.acquire(**_acquire_kwargs())
        self.assertFalse(result.acquired)
        self.assertEqual(result.reason, "already_in_progress")
        self.assertEqual(result.existing_status, "in_progress")

    def test_acquire_existing_failed_returns_manual_review_required(self) -> None:
        self._enable_flags()
        repo = self._repo()
        repo.acquire(**_acquire_kwargs())
        repo.mark_failed(
            "assisted_send:pending-b-1",
            error_code="platform_rejected",
            error_message="rejected",
        )
        result = repo.acquire(**_acquire_kwargs())
        self.assertFalse(result.acquired)
        self.assertEqual(result.reason, "manual_review_required")
        self.assertEqual(result.existing_status, "failed")

    def test_mark_succeeded_from_in_progress(self) -> None:
        self._enable_flags()
        repo = self._repo()
        repo.acquire(**_acquire_kwargs())
        record = repo.mark_succeeded(
            "assisted_send:pending-b-1",
            provider_message_id="msg-ok-1",
            platform_status="accepted",
        )
        self.assertEqual(record.status, "succeeded")
        self.assertEqual(record.provider_message_id, "msg-ok-1")
        self.assertIsNotNone(record.completed_at)

    def test_mark_failed_from_in_progress(self) -> None:
        self._enable_flags()
        repo = self._repo()
        repo.acquire(**_acquire_kwargs())
        record = repo.mark_failed(
            "assisted_send:pending-b-1",
            error_code="timeout",
            error_message="platform timeout",
        )
        self.assertEqual(record.status, "failed")
        self.assertEqual(record.error_code, "timeout")
        self.assertIsNotNone(record.completed_at)

    def test_cannot_mark_failed_after_succeeded(self) -> None:
        self._enable_flags()
        repo = self._repo()
        repo.acquire(**_acquire_kwargs())
        repo.mark_succeeded("assisted_send:pending-b-1")
        with self.assertRaises(ValueError):
            repo.mark_failed("assisted_send:pending-b-1", error_code="late_fail")

    def test_cannot_mark_succeeded_after_failed(self) -> None:
        self._enable_flags()
        repo = self._repo()
        repo.acquire(**_acquire_kwargs())
        repo.mark_failed("assisted_send:pending-b-1", error_code="fail")
        with self.assertRaises(ValueError):
            repo.mark_succeeded("assisted_send:pending-b-1")

    def test_metadata_json_roundtrip(self) -> None:
        self._enable_flags()
        repo = self._repo()
        meta = {"trace_id": "trace-b-1", "dry_run": True}
        repo.acquire(**_acquire_kwargs(), metadata=meta)
        record = repo.mark_succeeded(
            "assisted_send:pending-b-1",
            metadata={"provider": "pdd", "trace_id": "trace-b-1"},
        )
        assert self._db_manager is not None
        session = self._db_manager.get_product_session()
        try:
            row = session.get(OutboundIdempotencyRow, "assisted_send:pending-b-1")
            assert row is not None
            self.assertEqual(json.loads(row.metadata_json), record.metadata)
        finally:
            session.close()

    def test_duplicate_insert_race_safe(self) -> None:
        self._enable_flags()
        repo = self._repo()
        first = repo.acquire(**_acquire_kwargs())
        self.assertTrue(first.acquired)
        second = repo.acquire(**_acquire_kwargs())
        self.assertFalse(second.acquired)
        self.assertEqual(second.reason, "already_in_progress")

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
        repo.mark_succeeded("assisted_send:pending-b-1", provider_message_id="msg-1")
        send_reply_mock.assert_not_called()
        send_text_mock.assert_not_called()

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
            "database.models",
            "database.db_manager",
        ):
            self.assertNotIn(token, import_block, msg=token)


if __name__ == "__main__":
    unittest.main()

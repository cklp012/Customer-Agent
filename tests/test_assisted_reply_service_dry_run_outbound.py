"""Phase 15f: AssistedReplyService dry-run outbound wiring tests."""

from __future__ import annotations

import importlib
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from product_persistence.db_manager import ProductDbManager, reset_product_db_manager
from product_persistence.models import AuditLogRow, OutboundIdempotencyRow, PendingAssistedReplyRow
from product_persistence.repositories.sqlite_outbound_idempotency_repository import (
    OutboundIdempotencyRepositorySQLite,
)
from product_persistence.services.assisted_outbound_port import DryRunAssistedOutboundPort
from product_persistence.services.assisted_reply_service import AssistedReplyService

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SERVICE_SOURCE = (
    _REPO_ROOT / "product_persistence" / "services" / "assisted_reply_service.py"
)

_NOW = "2026-06-03T12:00:00+00:00"
_FUTURE = "2026-06-04T12:00:00+00:00"
_SHOP_ID = "shop-f-1"


def _create_kwargs(**overrides) -> dict:
    base = dict(
        reply_log_id="rl-f-1",
        workspace_id="ws-f-1",
        shop_id=_SHOP_ID,
        account_id="acc-f-1",
        platform_id="pinduoduo",
        buyer_id="buyer-f-1",
        buyer_message="这款商品还有库存吗",
        ai_suggested_reply="您好，该商品目前有货，欢迎下单。",
        intent="inventory_question",
        intent_bucket="allowed",
        risk_level="low",
        expires_at=_FUTURE,
        inbound_created_at=_NOW,
    )
    base.update(overrides)
    return base


def _approve_kwargs(**overrides) -> dict:
    base = dict(
        actor_user_id="op-f-1",
        actor_role="operator",
        final_reply="您好，该商品目前有货，欢迎下单。",
        effective_mode="assisted_only",
        inbound_created_at=_NOW,
        now=_NOW,
    )
    base.update(overrides)
    return base


class _DryRunOutboundTestCase(unittest.TestCase):
    _db_manager: ProductDbManager | None = None

    def setUp(self) -> None:
        self._db_manager = None
        reset_product_db_manager()
        self._tmpdir = _REPO_ROOT / "temp" / "phase15f_service_tests"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._tmpdir / "product_gate_assisted_dry_run.db"
        if self._db_path.exists():
            self._db_path.unlink()
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_PERSISTENCE_ENABLED",
            "PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED",
            "PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG",
            "PRODUCT_PERSISTENCE_WRITE_SEND_DECISION",
            "PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY",
            "PRODUCT_ASSISTED_SERVICE_ENABLED",
            "PRODUCT_ASSISTED_SEND_ENABLED",
            "PRODUCT_ASSISTED_SEND_DRY_RUN",
            "PRODUCT_ASSISTED_SEND_TEST_SHOP_ID",
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

    def _enable_assisted_flags(self) -> ProductDbManager:
        os.environ["PRODUCT_PERSISTENCE_ENABLED"] = "true"
        os.environ["PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED"] = "true"
        os.environ["PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG"] = "true"
        os.environ["PRODUCT_ASSISTED_SERVICE_ENABLED"] = "true"
        os.environ["PRODUCT_DB_URL"] = f"sqlite:///{self._db_path.as_posix()}"
        importlib.reload(importlib.import_module("product_persistence.flags"))
        reset_product_db_manager()
        self._db_manager = ProductDbManager(db_url=os.environ["PRODUCT_DB_URL"])
        self._db_manager.init_product_db()
        return self._db_manager

    def _enable_dry_run_flags(self) -> ProductDbManager:
        db = self._enable_assisted_flags()
        os.environ["PRODUCT_ASSISTED_SEND_ENABLED"] = "true"
        os.environ["PRODUCT_ASSISTED_SEND_DRY_RUN"] = "true"
        os.environ["PRODUCT_ASSISTED_SEND_TEST_SHOP_ID"] = _SHOP_ID
        os.environ["PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY"] = "true"
        os.environ["PRODUCT_PERSISTENCE_WRITE_SEND_DECISION"] = "true"
        importlib.reload(importlib.import_module("product_persistence.flags"))
        return db

    def _service(self) -> AssistedReplyService:
        assert self._db_manager is not None
        return AssistedReplyService(
            db_manager=self._db_manager,
            outbound_port=DryRunAssistedOutboundPort(),
        )

    def _create_pending(self, service: AssistedReplyService, **overrides) -> str:
        result = service.create_pending_from_preview(**_create_kwargs(**overrides))
        self.assertTrue(result.success, msg=result.error or result.reason)
        assert result.pending_assisted_id is not None
        return result.pending_assisted_id


class TestAssistedReplyServiceDryRunOutbound(_DryRunOutboundTestCase):
    def test_f1_flags_off_no_dry_run(self) -> None:
        service = AssistedReplyService(
            db_manager=ProductDbManager(
                db_url=f"sqlite:///{self._db_path.as_posix()}"
            )
        )
        result = service.approve_pending("missing", **_approve_kwargs())
        self.assertEqual(result.status, "disabled")

    def test_f2_send_enabled_false_no_dry_run(self) -> None:
        self._enable_assisted_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        result = service.approve_pending(pending_id, **_approve_kwargs())
        self.assertTrue(result.success)
        self.assertEqual(result.status, "guard_passed_but_send_not_implemented")

    def test_f3_dry_run_false_live_not_implemented_no_send(self) -> None:
        self._enable_assisted_flags()
        os.environ["PRODUCT_ASSISTED_SEND_ENABLED"] = "true"
        os.environ["PRODUCT_ASSISTED_SEND_DRY_RUN"] = "false"
        os.environ["PRODUCT_ASSISTED_SEND_TEST_SHOP_ID"] = _SHOP_ID
        importlib.reload(importlib.import_module("product_persistence.flags"))
        service = self._service()
        pending_id = self._create_pending(service)
        result = service.approve_pending(pending_id, **_approve_kwargs())
        self.assertFalse(result.success)
        self.assertEqual(result.status, "live_send_not_implemented")

    def test_f4_non_allowlisted_shop_no_dry_run(self) -> None:
        self._enable_dry_run_flags()
        service = self._service()
        pending_id = self._create_pending(service, shop_id="shop-other")
        result = service.approve_pending(pending_id, **_approve_kwargs())
        self.assertFalse(result.success)
        self.assertEqual(result.status, "allowlist_denied")

    def test_f5_guard_block_no_dry_run(self) -> None:
        self._enable_dry_run_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        result = service.approve_pending(
            pending_id,
            **_approve_kwargs(final_reply="好的，直接退款给您。"),
        )
        self.assertFalse(result.success)
        self.assertEqual(result.status, "guard_blocked")

    def test_f6_guard_allow_dry_run_would_send(self) -> None:
        db = self._enable_dry_run_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        result = service.approve_pending(pending_id, **_approve_kwargs())
        self.assertTrue(result.success)
        self.assertEqual(result.status, "dry_run_would_send")
        self.assertEqual(result.reason, "dry_run_would_send")
        session = db.get_product_session()
        try:
            audits = [row.action for row in session.query(AuditLogRow).all()]
            self.assertIn("assisted_dry_run_would_send", audits)
            self.assertIn("final_guard_passed", audits)
        finally:
            session.close()

    def test_f7_dry_run_does_not_mark_pending_sent(self) -> None:
        db = self._enable_dry_run_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        service.approve_pending(pending_id, **_approve_kwargs())
        session = db.get_product_session()
        try:
            row = session.get(PendingAssistedReplyRow, pending_id)
            assert row is not None
            self.assertEqual(row.status, "pending")
            self.assertNotEqual(row.status, "sent")
        finally:
            session.close()

    @patch.object(OutboundIdempotencyRepositorySQLite, "mark_succeeded")
    def test_f8_dry_run_does_not_mark_idempotency_succeeded(
        self,
        mark_succeeded_mock: MagicMock,
    ) -> None:
        self._enable_dry_run_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        service.approve_pending(pending_id, **_approve_kwargs())
        mark_succeeded_mock.assert_not_called()

    def test_f9_idempotency_existing_succeeded_no_dry_run(self) -> None:
        db = self._enable_dry_run_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        idem_repo = OutboundIdempotencyRepositorySQLite(db_manager=db)
        key = f"assisted_send:{pending_id}"
        idem_repo.acquire(
            key,
            workspace_id="ws-f-1",
            shop_id=_SHOP_ID,
            account_id="acc-f-1",
            platform_id="pinduoduo",
            pending_assisted_id=pending_id,
            reply_log_id="rl-f-1",
        )
        idem_repo.mark_succeeded(key, provider_message_id="prior-msg")
        result = service.approve_pending(pending_id, **_approve_kwargs())
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "already_sent")

    def test_f10_idempotency_existing_in_progress_no_dry_run(self) -> None:
        db = self._enable_dry_run_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        idem_repo = OutboundIdempotencyRepositorySQLite(db_manager=db)
        key = f"assisted_send:{pending_id}"
        idem_repo.acquire(
            key,
            workspace_id="ws-f-1",
            shop_id=_SHOP_ID,
            account_id="acc-f-1",
            platform_id="pinduoduo",
            pending_assisted_id=pending_id,
            reply_log_id="rl-f-1",
        )
        result = service.approve_pending(pending_id, **_approve_kwargs())
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "already_in_progress")

    def test_f11_idempotency_existing_failed_no_dry_run(self) -> None:
        db = self._enable_dry_run_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        idem_repo = OutboundIdempotencyRepositorySQLite(db_manager=db)
        key = f"assisted_send:{pending_id}"
        idem_repo.acquire(
            key,
            workspace_id="ws-f-1",
            shop_id=_SHOP_ID,
            account_id="acc-f-1",
            platform_id="pinduoduo",
            pending_assisted_id=pending_id,
            reply_log_id="rl-f-1",
        )
        idem_repo.mark_failed(key, error_code="platform_rejected")
        result = service.approve_pending(pending_id, **_approve_kwargs())
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "manual_review_required")

    def test_f12_dry_run_audit_written_with_dry_run_action(self) -> None:
        db = self._enable_dry_run_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        service.approve_pending(pending_id, **_approve_kwargs())
        session = db.get_product_session()
        try:
            actions = [row.action for row in session.query(AuditLogRow).all()]
            self.assertIn("assisted_dry_run_would_send", actions)
            self.assertNotIn("outbound_send_attempted", actions)
            self.assertNotIn("outbound_send_succeeded", actions)
        finally:
            session.close()

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    @patch("Message.handlers.ai_handler.AIReplyHandler._send_reply")
    def test_f13_no_sendmessage_called(
        self,
        send_reply_mock: MagicMock,
        send_text_mock: MagicMock,
    ) -> None:
        self._enable_dry_run_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        service.approve_pending(pending_id, **_approve_kwargs())
        send_reply_mock.assert_not_called()
        send_text_mock.assert_not_called()

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    def test_f14_no_pdd_or_doudian_outbound_called(self, send_text_mock: MagicMock) -> None:
        self._enable_dry_run_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        service.approve_pending(pending_id, **_approve_kwargs())
        send_text_mock.assert_not_called()

    def test_f15_live_send_not_implemented_when_dry_run_false(self) -> None:
        self._enable_assisted_flags()
        os.environ["PRODUCT_ASSISTED_SEND_ENABLED"] = "true"
        os.environ["PRODUCT_ASSISTED_SEND_DRY_RUN"] = "false"
        importlib.reload(importlib.import_module("product_persistence.flags"))
        service = self._service()
        pending_id = self._create_pending(service)
        result = service.approve_pending(pending_id, **_approve_kwargs())
        self.assertEqual(result.status, "live_send_not_implemented")

    def test_f16_no_handler_integration_static_check(self) -> None:
        source = _SERVICE_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("Message.handlers", source)

    def test_f17_no_outbound_resolver_import_static_check(self) -> None:
        import_lines = [
            line
            for line in _SERVICE_SOURCE.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        block = "\n".join(import_lines)
        self.assertNotIn("outbound_resolver", block)
        self.assertNotIn("SendMessage", block)

    def test_f18_pdd_queue_name_unchanged(self) -> None:
        from Message.queue_naming import pdd_queue_name

        self.assertEqual(pdd_queue_name("shop123"), "pdd_shop123")

    def test_idempotency_stays_in_progress_after_dry_run(self) -> None:
        db = self._enable_dry_run_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        service.approve_pending(pending_id, **_approve_kwargs())
        session = db.get_product_session()
        try:
            row = session.get(
                OutboundIdempotencyRow,
                f"assisted_send:{pending_id}",
            )
            assert row is not None
            self.assertEqual(row.status, "in_progress")
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()

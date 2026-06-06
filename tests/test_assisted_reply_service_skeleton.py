"""Phase 14x: AssistedReplyService skeleton tests (X1–X10)."""

from __future__ import annotations

import importlib
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from product_persistence.db_manager import ProductDbManager, reset_product_db_manager
from product_persistence.models import AuditLogRow, PendingAssistedReplyRow
from product_persistence.services.assisted_reply_service import AssistedReplyService

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_DB = _REPO_ROOT / "temp" / "product_gate.db"
_SERVICE_SOURCE = (
    _REPO_ROOT / "product_persistence" / "services" / "assisted_reply_service.py"
)

_NOW = "2026-06-03T12:00:00+00:00"
_FUTURE = "2026-06-04T12:00:00+00:00"
_PAST = "2026-06-03T10:00:00+00:00"


def _create_kwargs(**overrides) -> dict:
    base = dict(
        reply_log_id="rl-x-1",
        workspace_id="ws-x-1",
        shop_id="shop-x-1",
        account_id="acc-x-1",
        platform_id="pinduoduo",
        buyer_id="buyer-x-1",
        buyer_message="这款商品还有库存吗",
        ai_suggested_reply="您好，该商品目前有货。",
        intent="inventory_question",
        intent_bucket="allowed",
        risk_level="low",
        expires_at=_FUTURE,
        inbound_created_at=_NOW,
    )
    base.update(overrides)
    return base


class _AssistedServiceTestCase(unittest.TestCase):
    _db_manager: ProductDbManager | None = None

    def setUp(self) -> None:
        self._db_manager = None
        reset_product_db_manager()
        self._tmpdir = _REPO_ROOT / "temp" / "phase14x_service_tests"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._tmpdir / "product_gate_assisted_test.db"
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
            "PRODUCT_ASSISTED_SERVICE_ENABLED",
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

    def _enable_flags(self) -> ProductDbManager:
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

    def _service(self) -> AssistedReplyService:
        assert self._db_manager is not None
        return AssistedReplyService(db_manager=self._db_manager)

    def _create_pending(self, service: AssistedReplyService, **overrides):
        result = service.create_pending_from_preview(**_create_kwargs(**overrides))
        self.assertTrue(result.success, msg=result.error or result.reason)
        assert result.pending_assisted_id is not None
        return result.pending_assisted_id


class TestAssistedReplyServiceSkeleton(_AssistedServiceTestCase):
    def test_x1_flags_off_create_pending_disabled(self) -> None:
        service = AssistedReplyService(
            db_manager=ProductDbManager(
                db_url=f"sqlite:///{self._db_path.as_posix()}"
            )
        )
        result = service.create_pending_from_preview(**_create_kwargs())
        self.assertFalse(result.success)
        self.assertEqual(result.status, "disabled")
        self.assertEqual(result.reason, "assisted_disabled")
        self.assertFalse(self._db_path.exists())

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    @patch("Message.handlers.ai_handler.AIReplyHandler._send_reply")
    def test_x2_create_pending_success_no_send(
        self,
        send_reply_mock: MagicMock,
        send_text_mock: MagicMock,
    ) -> None:
        db = self._enable_flags()
        service = self._service()
        result = service.create_pending_from_preview(**_create_kwargs())
        self.assertTrue(result.success)
        self.assertEqual(result.status, "pending")
        session = db.get_product_session()
        try:
            pending = session.get(
                PendingAssistedReplyRow, result.pending_assisted_id
            )
            assert pending is not None
            self.assertEqual(pending.status, "pending")
            audits = session.query(AuditLogRow).all()
            self.assertTrue(
                any(row.action == "pending_assisted_created" for row in audits)
            )
        finally:
            session.close()
        send_reply_mock.assert_not_called()
        send_text_mock.assert_not_called()

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    def test_x3_viewer_cannot_approve(self, send_text_mock: MagicMock) -> None:
        self._enable_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        result = service.approve_pending(
            pending_id,
            actor_user_id="viewer-1",
            actor_role="viewer",
            effective_mode="assisted_only",
        )
        self.assertFalse(result.success)
        self.assertEqual(result.status, "permission_denied")
        send_text_mock.assert_not_called()

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    def test_x4_approve_guard_block_no_send(self, send_text_mock: MagicMock) -> None:
        self._enable_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        result = service.approve_pending(
            pending_id,
            actor_user_id="op-1",
            actor_role="operator",
            final_reply="好的，直接退款给您。",
            effective_mode="assisted_only",
            inbound_created_at=_NOW,
            now=_NOW,
        )
        self.assertFalse(result.success)
        self.assertEqual(result.status, "guard_blocked")
        self.assertEqual(result.final_guard_block_code, "forbidden_promise")
        assert self._db_manager is not None
        session = self._db_manager.get_product_session()
        try:
            row = session.get(PendingAssistedReplyRow, pending_id)
            assert row is not None
            self.assertEqual(row.status, "pending")
            audits = session.query(AuditLogRow).all()
            self.assertTrue(
                any(row.action == "final_guard_blocked" for row in audits)
            )
            self.assertFalse(
                any(row.action == "outbound_send_attempted" for row in audits)
            )
        finally:
            session.close()
        send_text_mock.assert_not_called()

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    def test_x5_approve_guard_pass_send_not_implemented(
        self,
        send_text_mock: MagicMock,
    ) -> None:
        db = self._enable_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        result = service.approve_pending(
            pending_id,
            actor_user_id="op-1",
            actor_role="operator",
            final_reply="您好，该商品目前有货，欢迎下单。",
            effective_mode="assisted_only",
            inbound_created_at=_NOW,
            now=_NOW,
        )
        self.assertTrue(result.success)
        self.assertEqual(result.status, "guard_passed_but_send_not_implemented")
        self.assertTrue(result.final_guard_allowed)
        self.assertEqual(result.reason, "send_not_implemented")
        session = db.get_product_session()
        try:
            row = session.get(PendingAssistedReplyRow, pending_id)
            assert row is not None
            self.assertNotEqual(row.status, "sent")
            audits = session.query(AuditLogRow).all()
            self.assertTrue(any(row.action == "assisted_approved" for row in audits))
            self.assertFalse(
                any(row.action == "outbound_send_attempted" for row in audits)
            )
        finally:
            session.close()
        send_text_mock.assert_not_called()

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    def test_x6_reject_pending_no_send(self, send_text_mock: MagicMock) -> None:
        db = self._enable_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        result = service.reject_pending(
            pending_id,
            actor_user_id="op-1",
            actor_role="operator",
            reason="not suitable",
        )
        self.assertTrue(result.success)
        self.assertEqual(result.status, "rejected")
        session = db.get_product_session()
        try:
            row = session.get(PendingAssistedReplyRow, pending_id)
            assert row is not None
            self.assertEqual(row.status, "rejected")
            audits = session.query(AuditLogRow).all()
            self.assertTrue(any(row.action == "assisted_rejected" for row in audits))
        finally:
            session.close()
        send_text_mock.assert_not_called()

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    def test_x7_expire_pending_no_send(self, send_text_mock: MagicMock) -> None:
        db = self._enable_flags()
        service = self._service()
        pending_id = self._create_pending(service, expires_at=_PAST)
        result = service.expire_pending(
            pending_id,
            actor_user_id="system",
            actor_role="system",
            now=_NOW,
        )
        self.assertTrue(result.success)
        self.assertEqual(result.status, "expired")
        session = db.get_product_session()
        try:
            row = session.get(PendingAssistedReplyRow, pending_id)
            assert row is not None
            self.assertEqual(row.status, "expired")
            audits = session.query(AuditLogRow).all()
            self.assertTrue(any(row.action == "assisted_expired" for row in audits))
        finally:
            session.close()
        send_text_mock.assert_not_called()

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    def test_x8_duplicate_or_terminal_state_no_send(
        self,
        send_text_mock: MagicMock,
    ) -> None:
        self._enable_flags()
        service = self._service()
        pending_id = self._create_pending(service)
        reject_result = service.reject_pending(
            pending_id,
            actor_user_id="op-1",
            actor_role="operator",
            reason="done",
        )
        self.assertTrue(reject_result.success)
        approve_result = service.approve_pending(
            pending_id,
            actor_user_id="op-1",
            actor_role="operator",
            effective_mode="assisted_only",
            inbound_created_at=_NOW,
            now=_NOW,
        )
        self.assertFalse(approve_result.success)
        self.assertEqual(approve_result.status, "terminal_state")
        send_text_mock.assert_not_called()

    def test_x9_service_no_handler_import_static_check(self) -> None:
        source = _SERVICE_SOURCE.read_text(encoding="utf-8")
        import_lines = [
            line
            for line in source.splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        import_block = "\n".join(import_lines)
        forbidden = (
            "Message.handlers",
            "SendMessage",
            "outbound_resolver",
            "unified_outbound",
            "Channel.pinduoduo",
            "Channel.doudian",
            "database.models",
            "database.db_manager",
        )
        for token in forbidden:
            self.assertNotIn(token, import_block, msg=f"unexpected import: {token}")

    def test_x10_non_test_legacy_unaffected(self) -> None:
        handler_path = _REPO_ROOT / "Message" / "handlers" / "ai_handler.py"
        source = handler_path.read_text(encoding="utf-8")
        self.assertNotIn("AssistedReplyService", source)
        self.assertNotIn("approve_pending(", source)


if __name__ == "__main__":
    unittest.main()

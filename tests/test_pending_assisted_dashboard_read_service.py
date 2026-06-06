"""Phase 15d: PendingAssisted dashboard read service tests."""

from __future__ import annotations

import importlib
import json
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from product_persistence.db_manager import ProductDbManager, reset_product_db_manager
from product_persistence.models import SendDecisionSnapshotRow
from product_persistence.repositories.sqlite_audit_log_repository import (
    AuditLogRepositorySQLite,
)
from product_persistence.repositories.sqlite_pending_assisted_repository import (
    PendingAssistedRepositorySQLite,
)
from product_persistence.services.pending_assisted_dashboard_read_service import (
    PendingAssistedDashboardReadService,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SERVICE_SOURCE = (
    _REPO_ROOT
    / "product_persistence"
    / "services"
    / "pending_assisted_dashboard_read_service.py"
)


def _pending_kwargs(**overrides) -> dict:
    base = dict(
        reply_log_id="rl-d-1",
        workspace_id="ws-d-1",
        shop_id="shop-d-1",
        account_id="acc-d-1",
        platform_id="pinduoduo",
        buyer_id="buyer-d-1",
        buyer_message="这款商品还有库存吗" + ("x" * 120),
        ai_suggested_reply="您好，该商品目前有货，欢迎下单。" + ("y" * 120),
        intent="stock_inquiry",
        intent_bucket="stock_inquiry",
        risk_level="low",
    )
    base.update(overrides)
    return base


class _ReadServiceTestCase(unittest.TestCase):
    _db_manager: ProductDbManager | None = None

    def setUp(self) -> None:
        self._db_manager = None
        reset_product_db_manager()
        self._tmpdir = _REPO_ROOT / "temp" / "phase15d_read_service_tests"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._tmpdir / "product_gate_read_test.db"
        if self._db_path.exists():
            self._db_path.unlink()
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_PERSISTENCE_ENABLED",
            "PRODUCT_PERSISTENCE_READ_DASHBOARD",
            "PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED",
            "PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG",
            "PRODUCT_PERSISTENCE_WRITE_SEND_DECISION",
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

    def _enable_read_flags(self) -> ProductDbManager:
        os.environ["PRODUCT_PERSISTENCE_ENABLED"] = "true"
        os.environ["PRODUCT_PERSISTENCE_READ_DASHBOARD"] = "true"
        os.environ["PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED"] = "true"
        os.environ["PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG"] = "true"
        os.environ["PRODUCT_PERSISTENCE_WRITE_SEND_DECISION"] = "true"
        os.environ["PRODUCT_DB_URL"] = f"sqlite:///{self._db_path.as_posix()}"
        importlib.reload(importlib.import_module("product_persistence.flags"))
        reset_product_db_manager()
        self._db_manager = ProductDbManager(db_url=os.environ["PRODUCT_DB_URL"])
        self._db_manager.init_product_db()
        return self._db_manager

    def _seed_pending_bundle(
        self,
        *,
        pending_id: str = "pending-d-1",
        workspace_id: str = "ws-d-1",
    ) -> str:
        assert self._db_manager is not None
        pending_repo = PendingAssistedRepositorySQLite(db_manager=self._db_manager)
        audit_repo = AuditLogRepositorySQLite(db_manager=self._db_manager)
        pending_repo.create_pending(
            **_pending_kwargs(
                pending_assisted_id=pending_id,
                workspace_id=workspace_id,
                reply_log_id=f"rl-{pending_id}",
            )
        )
        audit_repo.append_audit_log(
            workspace_id=workspace_id,
            shop_id="shop-d-1",
            actor_user_id="system",
            actor_role="system",
            action="pending_assisted_created",
            target_type="pending_assisted",
            target_id=pending_id,
            pending_assisted_id=pending_id,
            reply_log_id=f"rl-{pending_id}",
            created_at="2026-06-01T10:00:00+00:00",
        )
        audit_repo.append_audit_log(
            workspace_id=workspace_id,
            shop_id="shop-d-1",
            actor_user_id="operator-1",
            actor_role="operator",
            action="final_guard_blocked",
            target_type="pending_assisted",
            target_id=pending_id,
            pending_assisted_id=pending_id,
            reply_log_id=f"rl-{pending_id}",
            after_state=json.dumps({"block_code": "forbidden_promise"}),
            reason="回复含不允许的承诺用语",
            created_at="2026-06-01T10:05:00+00:00",
        )
        session = self._db_manager.get_product_session()
        try:
            session.add(
                SendDecisionSnapshotRow(
                    send_decision_id=f"sd-{pending_id}",
                    reply_log_id=f"rl-{pending_id}",
                    workspace_id=workspace_id,
                    shop_id="shop-d-1",
                    account_id="acc-d-1",
                    platform_id="pinduoduo",
                    decision_phase="ai_preview",
                    intent="stock_inquiry",
                    intent_bucket="stock_inquiry",
                    intent_confidence=0.91,
                    risk_level="low",
                    reply_mode="assisted",
                    workspace_pause=0,
                    shop_pause=0,
                    product_gate_enabled=1,
                    allowed_to_generate=1,
                    allowed_to_send=0,
                    send_mode="assisted_only",
                    blocked_reason="forbidden_promise",
                    decision_source="product_gate",
                    created_at="2026-06-01T09:55:00+00:00",
                )
            )
            session.commit()
        finally:
            session.close()
        return pending_id


class TestPendingAssistedDashboardReadService(_ReadServiceTestCase):
    def test_d1_read_dashboard_flag_off_disabled_or_warning(self) -> None:
        result = PendingAssistedDashboardReadService().list_pending_assisted()
        self.assertTrue(result.disabled)
        self.assertEqual(result.source, "disabled")
        self.assertIn("dashboard_read_disabled", result.warnings)
        detail = PendingAssistedDashboardReadService().get_pending_assisted_detail(
            "missing"
        )
        self.assertTrue(detail.disabled)

    def test_d2_list_pending_read_only(self) -> None:
        db = self._enable_read_flags()
        pending_id = self._seed_pending_bundle()
        svc = PendingAssistedDashboardReadService(
            pending_repository=PendingAssistedRepositorySQLite(db_manager=db),
            audit_repository=AuditLogRepositorySQLite(db_manager=db),
        )
        result = svc.list_pending_assisted(workspace_id="ws-d-1")
        self.assertFalse(result.disabled)
        self.assertEqual(result.source, "sqlite_shadow")
        self.assertEqual(result.pagination.total, 1)
        self.assertEqual(result.items[0].pending_assisted_id, pending_id)

    def test_d3_list_filters_by_workspace_shop_status(self) -> None:
        db = self._enable_read_flags()
        pending_repo = PendingAssistedRepositorySQLite(db_manager=db)
        self._seed_pending_bundle(pending_id="pending-a")
        pending_repo.create_pending(
            **_pending_kwargs(
                pending_assisted_id="pending-b",
                workspace_id="ws-other",
                shop_id="shop-other",
                reply_log_id="rl-b",
                status="failed",
            )
        )
        pending_repo.mark_status("pending-b", "failed")
        svc = PendingAssistedDashboardReadService(
            pending_repository=pending_repo,
            audit_repository=AuditLogRepositorySQLite(db_manager=db),
        )
        filtered = svc.list_pending_assisted(
            workspace_id="ws-d-1",
            shop_id="shop-d-1",
            status="pending",
        )
        self.assertEqual(filtered.pagination.total, 1)
        self.assertEqual(filtered.items[0].pending_assisted_id, "pending-a")

    def test_d4_list_pagination_limit_max_100(self) -> None:
        db = self._enable_read_flags()
        pending_repo = PendingAssistedRepositorySQLite(db_manager=db)
        for idx in range(105):
            pending_repo.create_pending(
                **_pending_kwargs(
                    pending_assisted_id=f"pending-page-{idx}",
                    reply_log_id=f"rl-page-{idx}",
                )
            )
        svc = PendingAssistedDashboardReadService(
            pending_repository=pending_repo,
            audit_repository=AuditLogRepositorySQLite(db_manager=db),
        )
        result = svc.list_pending_assisted(page=1, page_size=500)
        self.assertEqual(result.pagination.page_size, 100)
        self.assertEqual(len(result.items), 100)
        self.assertEqual(result.pagination.total, 105)

    def test_d5_list_preview_redacts_or_truncates_text(self) -> None:
        db = self._enable_read_flags()
        pending_id = self._seed_pending_bundle()
        svc = PendingAssistedDashboardReadService(
            pending_repository=PendingAssistedRepositorySQLite(db_manager=db),
            audit_repository=AuditLogRepositorySQLite(db_manager=db),
        )
        item = svc.list_pending_assisted(workspace_id="ws-d-1").items[0]
        self.assertEqual(item.pending_assisted_id, pending_id)
        assert item.buyer_message_preview is not None
        self.assertLessEqual(len(item.buyer_message_preview), 80)
        self.assertTrue(item.buyer_message_preview.endswith("…"))

    def test_d6_detail_returns_full_text_for_operator(self) -> None:
        db = self._enable_read_flags()
        pending_id = self._seed_pending_bundle()
        svc = PendingAssistedDashboardReadService(
            pending_repository=PendingAssistedRepositorySQLite(db_manager=db),
            audit_repository=AuditLogRepositorySQLite(db_manager=db),
        )
        result = svc.get_pending_assisted_detail(
            pending_id,
            workspace_id="ws-d-1",
            actor_role="operator",
        )
        assert result.detail is not None
        self.assertGreater(len(result.detail.buyer_message or ""), 80)
        self.assertNotEqual(result.detail.buyer_message, "[redacted]")

    def test_d7_detail_redacts_text_for_viewer(self) -> None:
        db = self._enable_read_flags()
        pending_id = self._seed_pending_bundle()
        svc = PendingAssistedDashboardReadService(
            pending_repository=PendingAssistedRepositorySQLite(db_manager=db),
            audit_repository=AuditLogRepositorySQLite(db_manager=db),
        )
        result = svc.get_pending_assisted_detail(
            pending_id,
            workspace_id="ws-d-1",
            actor_role="viewer",
        )
        assert result.detail is not None
        self.assertEqual(result.detail.buyer_message, "[redacted]")
        self.assertEqual(result.detail.ai_suggested_reply, "[redacted]")

    def test_d8_cross_workspace_forbidden(self) -> None:
        db = self._enable_read_flags()
        pending_id = self._seed_pending_bundle()
        svc = PendingAssistedDashboardReadService(
            pending_repository=PendingAssistedRepositorySQLite(db_manager=db),
            audit_repository=AuditLogRepositorySQLite(db_manager=db),
        )
        result = svc.get_pending_assisted_detail(
            pending_id,
            workspace_id="ws-other",
            actor_role="operator",
        )
        self.assertTrue(result.forbidden)
        self.assertIsNone(result.detail)

    def test_d9_audit_timeline_ordered_by_created_at(self) -> None:
        db = self._enable_read_flags()
        pending_id = self._seed_pending_bundle()
        svc = PendingAssistedDashboardReadService(
            pending_repository=PendingAssistedRepositorySQLite(db_manager=db),
            audit_repository=AuditLogRepositorySQLite(db_manager=db),
        )
        result = svc.get_pending_assisted_detail(
            pending_id,
            workspace_id="ws-d-1",
            actor_role="admin",
        )
        assert result.detail is not None
        times = [entry["created_at"] for entry in result.detail.audit_timeline]
        self.assertEqual(times, sorted(times))
        self.assertEqual(result.detail.audit_timeline[0]["action"], "pending_assisted_created")

    def test_d10_final_guard_block_reason_visible(self) -> None:
        db = self._enable_read_flags()
        pending_id = self._seed_pending_bundle()
        svc = PendingAssistedDashboardReadService(
            pending_repository=PendingAssistedRepositorySQLite(db_manager=db),
            audit_repository=AuditLogRepositorySQLite(db_manager=db),
        )
        list_item = svc.list_pending_assisted(workspace_id="ws-d-1").items[0]
        self.assertFalse(list_item.final_guard_allowed)
        self.assertEqual(list_item.final_guard_block_code, "forbidden_promise")
        detail = svc.get_pending_assisted_detail(
            pending_id,
            workspace_id="ws-d-1",
            actor_role="owner",
        )
        assert detail.detail is not None
        assert detail.detail.final_guard is not None
        self.assertEqual(detail.detail.final_guard["block_code"], "forbidden_promise")

    def test_d11_send_decision_snapshot_visible(self) -> None:
        db = self._enable_read_flags()
        pending_id = self._seed_pending_bundle()
        svc = PendingAssistedDashboardReadService(
            pending_repository=PendingAssistedRepositorySQLite(db_manager=db),
            audit_repository=AuditLogRepositorySQLite(db_manager=db),
        )
        detail = svc.get_pending_assisted_detail(
            pending_id,
            workspace_id="ws-d-1",
            actor_role="operator",
        )
        assert detail.detail is not None
        snapshot = detail.detail.send_decision_snapshot
        assert snapshot is not None
        self.assertEqual(snapshot["decision_phase"], "ai_preview")
        self.assertEqual(snapshot["blocked_reason"], "forbidden_promise")

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    @patch("Message.handlers.ai_handler.AIReplyHandler._send_reply")
    def test_d12_read_failure_no_send(
        self,
        send_reply_mock: MagicMock,
        send_text_mock: MagicMock,
    ) -> None:
        db = self._enable_read_flags()
        pending_id = self._seed_pending_bundle()
        svc = PendingAssistedDashboardReadService(
            pending_repository=PendingAssistedRepositorySQLite(db_manager=db),
            audit_repository=AuditLogRepositorySQLite(db_manager=db),
        )
        svc.list_pending_assisted(workspace_id="ws-d-1")
        svc.get_pending_assisted_detail(
            pending_id,
            workspace_id="ws-d-1",
            actor_role="operator",
        )
        send_reply_mock.assert_not_called()
        send_text_mock.assert_not_called()

    @patch(
        "product_persistence.repositories.sqlite_audit_log_repository.AuditLogRepositorySQLite.append_audit_log"
    )
    def test_d13_no_audit_write_on_read(self, append_mock: MagicMock) -> None:
        db = self._enable_read_flags()
        pending_id = self._seed_pending_bundle()
        svc = PendingAssistedDashboardReadService(
            pending_repository=PendingAssistedRepositorySQLite(db_manager=db),
            audit_repository=AuditLogRepositorySQLite(db_manager=db),
        )
        svc.list_pending_assisted(workspace_id="ws-d-1")
        svc.get_pending_assisted_detail(
            pending_id,
            workspace_id="ws-d-1",
            actor_role="operator",
        )
        append_mock.assert_not_called()

    @patch("Message.gates.final_guard.evaluate_final_guard")
    def test_d14_no_final_guard_execution_on_read(self, guard_mock: MagicMock) -> None:
        db = self._enable_read_flags()
        pending_id = self._seed_pending_bundle()
        svc = PendingAssistedDashboardReadService(
            pending_repository=PendingAssistedRepositorySQLite(db_manager=db),
            audit_repository=AuditLogRepositorySQLite(db_manager=db),
        )
        svc.list_pending_assisted(workspace_id="ws-d-1")
        svc.get_pending_assisted_detail(
            pending_id,
            workspace_id="ws-d-1",
            actor_role="operator",
        )
        guard_mock.assert_not_called()

    @patch(
        "product_persistence.services.assisted_outbound_port.DryRunAssistedOutboundPort.send"
    )
    def test_d15_no_outbound_on_read(self, outbound_mock: MagicMock) -> None:
        db = self._enable_read_flags()
        pending_id = self._seed_pending_bundle()
        svc = PendingAssistedDashboardReadService(
            pending_repository=PendingAssistedRepositorySQLite(db_manager=db),
            audit_repository=AuditLogRepositorySQLite(db_manager=db),
        )
        svc.list_pending_assisted(workspace_id="ws-d-1")
        svc.get_pending_assisted_detail(
            pending_id,
            workspace_id="ws-d-1",
            actor_role="operator",
        )
        outbound_mock.assert_not_called()

    def test_service_static_no_send_imports(self) -> None:
        import_lines = [
            line
            for line in _SERVICE_SOURCE.read_text(encoding="utf-8").splitlines()
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
            "evaluate_final_guard",
        ):
            self.assertNotIn(token, import_block, msg=token)


if __name__ == "__main__":
    unittest.main()

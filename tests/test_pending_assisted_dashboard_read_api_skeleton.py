"""Phase 15d: PendingAssisted dashboard read API skeleton tests."""

from __future__ import annotations

import importlib
import json
import os
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from product_persistence import flags
from product_persistence.db_manager import ProductDbManager, reset_product_db_manager
from product_persistence.pending_assisted_api_read_routes import (
    REGISTERED_GET_ROUTES,
    _FORBIDDEN_MUTATION_ROUTES,
    dispatch_pending_assisted_read_route,
    handle_get_pending_assisted_detail,
    handle_list_pending_assisted,
    pending_assisted_read_route_names,
    register_pending_assisted_read_routes,
)
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
_ROUTE_SOURCE = _REPO_ROOT / "product_persistence" / "pending_assisted_api_read_routes.py"
_SERVICE_SOURCE = (
    _REPO_ROOT
    / "product_persistence"
    / "services"
    / "pending_assisted_dashboard_read_service.py"
)


class _MockFlaskApp:
    def __init__(self) -> None:
        self.routes: list[tuple] = []

    def add_url_rule(self, rule, endpoint=None, view_func=None, methods=None) -> None:
        self.routes.append((rule, endpoint, view_func, methods))


def _pending_kwargs(**overrides) -> dict:
    base = dict(
        reply_log_id="rl-api-d-1",
        workspace_id="ws-api-d-1",
        shop_id="shop-api-d-1",
        account_id="acc-api-d-1",
        platform_id="pinduoduo",
        buyer_id="buyer-api-d-1",
        buyer_message="买家消息",
        ai_suggested_reply="AI 建议回复",
        intent="stock_inquiry",
        intent_bucket="stock_inquiry",
        risk_level="low",
    )
    base.update(overrides)
    return base


class TestPendingAssistedDashboardReadApiSkeleton(unittest.TestCase):
    _db_manager: ProductDbManager | None = None

    def setUp(self) -> None:
        self._db_manager = None
        reset_product_db_manager()
        self._tmpdir = _REPO_ROOT / "temp" / "phase15d_api_tests"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._tmpdir / "product_gate_api_test.db"
        if self._db_path.exists():
            self._db_path.unlink()
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_PERSISTENCE_ENABLED",
            "PRODUCT_PERSISTENCE_READ_DASHBOARD",
            "PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED",
            "PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG",
            "PRODUCT_DB_URL",
        ):
            os.environ.pop(key, None)
        importlib.reload(flags)

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
        os.environ["PRODUCT_DB_URL"] = f"sqlite:///{self._db_path.as_posix()}"
        importlib.reload(flags)
        reset_product_db_manager()
        self._db_manager = ProductDbManager(db_url=os.environ["PRODUCT_DB_URL"])
        self._db_manager.init_product_db()
        return self._db_manager

    def _service_with_seed(self) -> PendingAssistedDashboardReadService:
        db = self._enable_read_flags()
        pending_repo = PendingAssistedRepositorySQLite(db_manager=db)
        pending_id = pending_repo.create_pending(
            **_pending_kwargs(pending_assisted_id="pending-api-d-1")
        )
        AuditLogRepositorySQLite(db_manager=db).append_audit_log(
            workspace_id="ws-api-d-1",
            actor_user_id="system",
            actor_role="system",
            action="pending_assisted_created",
            target_type="pending_assisted",
            target_id=pending_id,
            pending_assisted_id=pending_id,
        )
        return PendingAssistedDashboardReadService(
            pending_repository=pending_repo,
            audit_repository=AuditLogRepositorySQLite(db_manager=db),
        )

    def test_d16_list_route_read_only_get(self) -> None:
        svc = self._service_with_seed()
        status, body = handle_list_pending_assisted(
            {"workspace_id": "ws-api-d-1"},
            service=svc,
        )
        self.assertEqual(status, 200)
        self.assertIn("items", body)
        self.assertEqual(body["source"], "sqlite_shadow")
        self.assertEqual(body["pagination"]["total"], 1)

    def test_d17_detail_route_read_only_get(self) -> None:
        svc = self._service_with_seed()
        status, body = handle_get_pending_assisted_detail(
            "pending-api-d-1",
            {"workspace_id": "ws-api-d-1", "actor_role": "operator"},
            service=svc,
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["pending_assisted_id"], "pending-api-d-1")
        self.assertEqual(body["buyer_message"], "买家消息")

    def test_d18_no_post_patch_delete_approve_reject_send_routes(self) -> None:
        methods = {method for method, _path in REGISTERED_GET_ROUTES}
        self.assertEqual(methods, {"GET"})
        self.assertEqual(
            set(pending_assisted_read_route_names()),
            {"list_pending_assisted", "get_pending_assisted_detail"},
        )
        for mutation in (
            "POST",
            "PATCH",
            "DELETE",
            "PUT",
        ):
            status, body = dispatch_pending_assisted_read_route(
                mutation,
                "/api/product/pending-assisted",
            )
            self.assertEqual(status, 405, msg=mutation)
            self.assertEqual(body["error"], "method_not_allowed")
        route_source = _ROUTE_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("def handle_approve", route_source)
        self.assertNotIn("def handle_reject", route_source)
        self.assertNotIn("def handle_send", route_source)
        self.assertTrue(_FORBIDDEN_MUTATION_ROUTES)

    def test_d19_route_does_not_import_handler_sendmessage_outbound(self) -> None:
        for path in (_ROUTE_SOURCE, _SERVICE_SOURCE):
            import_lines = [
                line
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip().startswith(("import ", "from "))
            ]
            block = "\n".join(import_lines)
            for token in (
                "SendMessage",
                "Message.handlers",
                "outbound_resolver",
                "Channel.pinduoduo",
                "Channel.doudian",
                "database.models",
                "database.db_manager",
            ):
                self.assertNotIn(token, block, msg=f"{path.name}:{token}")

    def test_d20_doudian_not_enabled(self) -> None:
        source = _ROUTE_SOURCE.read_text(encoding="utf-8") + _SERVICE_SOURCE.read_text(
            encoding="utf-8"
        )
        self.assertNotIn("doudian", source.lower())
        self.assertNotIn("USE_DOUDIAN", source)

    def test_d21_legacy_pdd_unaffected(self) -> None:
        from Message.queue_naming import pdd_queue_name

        self.assertEqual(pdd_queue_name("shop123"), "pdd_shop123")
        import app as app_module

        self.assertTrue(callable(app_module.main))

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    @patch(
        "Message.handlers.ai_handler.AIReplyHandler._send_reply",
        new_callable=AsyncMock,
    )
    def test_routes_do_not_call_send_paths(
        self,
        send_reply_mock: AsyncMock,
        send_text_mock: MagicMock,
    ) -> None:
        svc = self._service_with_seed()
        handle_list_pending_assisted({"workspace_id": "ws-api-d-1"}, service=svc)
        handle_get_pending_assisted_detail(
            "pending-api-d-1",
            {"workspace_id": "ws-api-d-1", "actor_role": "operator"},
            service=svc,
        )
        dispatch_pending_assisted_read_route(
            "GET",
            "/api/product/pending-assisted",
            query_params={"workspace_id": "ws-api-d-1"},
            service=svc,
        )
        dispatch_pending_assisted_read_route(
            "GET",
            "/api/product/pending-assisted/pending-api-d-1",
            query_params={"workspace_id": "ws-api-d-1", "actor_role": "operator"},
            service=svc,
        )
        send_reply_mock.assert_not_awaited()
        send_text_mock.assert_not_called()

    def test_register_routes_noop_without_flask_app(self) -> None:
        default_db = _REPO_ROOT / "temp" / "product_gate.db"
        if default_db.exists():
            default_db.unlink()
        register_pending_assisted_read_routes(None)
        self.assertFalse(default_db.exists())

        mock_app = _MockFlaskApp()
        register_pending_assisted_read_routes(mock_app)
        self.assertEqual(len(mock_app.routes), 2)
        rules = {route[0] for route in mock_app.routes}
        self.assertIn("/api/product/pending-assisted", rules)
        self.assertIn("/api/product/pending-assisted/<pending_assisted_id>", rules)

    def test_flag_off_list_returns_disabled(self) -> None:
        status, body = handle_list_pending_assisted({})
        self.assertEqual(status, 200)
        self.assertTrue(body["disabled"])
        self.assertIn("dashboard_read_disabled", body["warnings"])


if __name__ == "__main__":
    unittest.main()

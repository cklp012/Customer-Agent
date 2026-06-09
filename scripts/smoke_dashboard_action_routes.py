#!/usr/bin/env python3
"""
Local dashboard action route smoke test (Phase 15r).

Dry-run / no-send only. Does not start PDD, Doudian, GUI, or modify persistent env.
"""

from __future__ import annotations

import importlib
import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SMOKE_DB = _REPO_ROOT / "temp" / "product_smoke_dashboard_action.db"
_DEFAULT_GATE_DB = _REPO_ROOT / "temp" / "product_gate.db"
_SCRIPT_SOURCE = Path(__file__)

_FORBIDDEN_SCRIPT_STRINGS = (
    "SendMessage",
    "Message.handlers",
    "outbound_resolver",
    "Channel.pinduoduo",
    "Channel.doudian",
    "database.models",
    "database.db_manager",
    "AutoReplyThread",
    "LivePddAssistedOutboundPort",
)

_FLAG_KEYS = (
    "PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED",
    "PRODUCT_PERSISTENCE_ENABLED",
    "PRODUCT_ASSISTED_SERVICE_ENABLED",
    "PRODUCT_ASSISTED_SEND_ENABLED",
    "PRODUCT_ASSISTED_SEND_DRY_RUN",
    "PRODUCT_ASSISTED_SEND_TEST_SHOP_ID",
    "PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED",
    "PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG",
    "PRODUCT_PERSISTENCE_WRITE_SEND_DECISION",
    "PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY",
    "PRODUCT_PERSISTENCE_WRITE_ACTION_IDEMPOTENCY",
    "PRODUCT_DB_URL",
)


@dataclass
class SmokeCheckResult:
    name: str
    passed: bool
    detail: str = ""


class _MockFlaskApp:
    def __init__(self) -> None:
        self.routes: list[tuple] = []

    def add_url_rule(self, rule, endpoint=None, view_func=None, methods=None) -> None:
        self.routes.append((rule, endpoint, view_func, methods))


def _cleanup_smoke_db(db: Any | None = None) -> None:
    """Close product DB handles and remove temp smoke SQLite file."""
    if db is not None:
        db.close_product_db()
    from product_persistence.db_manager import reset_product_db_manager

    reset_product_db_manager()
    (_REPO_ROOT / "temp").mkdir(parents=True, exist_ok=True)
    if _SMOKE_DB.exists():
        try:
            _SMOKE_DB.unlink()
        except OSError:
            pass


def _ensure_project_root_on_path() -> Path:
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    return _REPO_ROOT


@contextmanager
def temporary_env(overrides: dict[str, Optional[str]]) -> Iterator[None]:
    """Apply env overrides for smoke checks; restore prior values in finally."""
    saved: dict[str, Optional[str]] = {}
    try:
        for key, value in overrides.items():
            saved[key] = os.environ.get(key)
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        import product_persistence.flags as flags_mod

        importlib.reload(flags_mod)
        yield
    finally:
        for key, prior in saved.items():
            if prior is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = prior
        import product_persistence.flags as flags_mod

        importlib.reload(flags_mod)


def assert_no_forbidden_imports() -> SmokeCheckResult:
    source = _SCRIPT_SOURCE.read_text(encoding="utf-8")
    import_lines = [
        line
        for line in source.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    block = "\n".join(import_lines)
    for token in _FORBIDDEN_SCRIPT_STRINGS:
        if token in block:
            return SmokeCheckResult(
                name="forbidden_imports_absent",
                passed=False,
                detail=f"script imports forbidden token: {token}",
            )
    return SmokeCheckResult(
        name="forbidden_imports_absent",
        passed=True,
        detail="script import block clean",
    )


def check_default_flags() -> SmokeCheckResult:
    from product_persistence import flags

    issues: list[str] = []
    if flags.is_dashboard_action_routes_enabled():
        issues.append("PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED should be false")
    if flags.is_assisted_send_enabled():
        issues.append("PRODUCT_ASSISTED_SEND_ENABLED should be false")
    if not flags.is_assisted_send_dry_run():
        issues.append("PRODUCT_ASSISTED_SEND_DRY_RUN should be true (default)")
    if flags.would_assisted_send_live():
        issues.append("would_assisted_send_live should be false")
    if issues:
        return SmokeCheckResult(
            name="default_flags_safe",
            passed=False,
            detail="; ".join(issues),
        )
    return SmokeCheckResult(
        name="default_flags_safe",
        passed=True,
        detail="dashboard off · send off · dry_run default",
    )


def check_pdd_queue_name() -> SmokeCheckResult:
    from Message.queue_naming import pdd_queue_name

    expected = "pdd_shop123"
    actual = pdd_queue_name("shop123")
    if actual != expected:
        return SmokeCheckResult(
            name="pdd_queue_name_unchanged",
            passed=False,
            detail=f"expected {expected!r}, got {actual!r}",
        )
    return SmokeCheckResult(
        name="pdd_queue_name_unchanged",
        passed=True,
        detail=expected,
    )


def check_import_no_registration_or_db() -> SmokeCheckResult:
    from product_persistence.db_manager import reset_product_db_manager
    from product_persistence.pending_assisted_action_routes import (
        reset_action_route_registration_state_for_tests,
    )

    reset_product_db_manager()
    reset_action_route_registration_state_for_tests()
    gate_existed = _DEFAULT_GATE_DB.exists()
    gate_mtime = _DEFAULT_GATE_DB.stat().st_mtime if gate_existed else None

    import product_persistence.pending_assisted_action_routes  # noqa: F401

    if not gate_existed and _DEFAULT_GATE_DB.exists():
        return SmokeCheckResult(
            name="import_no_db_side_effect",
            passed=False,
            detail=f"import created {_DEFAULT_GATE_DB}",
        )
    if gate_existed and _DEFAULT_GATE_DB.exists():
        if _DEFAULT_GATE_DB.stat().st_mtime != gate_mtime:
            return SmokeCheckResult(
                name="import_no_db_side_effect",
                passed=False,
                detail="import modified existing product_gate.db",
            )
    return SmokeCheckResult(
        name="import_no_db_side_effect",
        passed=True,
        detail="pending_assisted_action_routes import safe",
    )


def build_local_test_app() -> _MockFlaskApp:
    return _MockFlaskApp()


def check_route_registration() -> SmokeCheckResult:
    from product_persistence.pending_assisted_action_routes import (
        apply_dashboard_action_route_bootstrap,
        reset_action_route_registration_state_for_tests,
    )

    cleared = {key: None for key in _FLAG_KEYS}
    with temporary_env(cleared):
        reset_action_route_registration_state_for_tests()
        app_off = build_local_test_app()
        if apply_dashboard_action_route_bootstrap(app_off):
            return SmokeCheckResult(
                name="route_registration_flag_off",
                passed=False,
                detail="bootstrap should return False when flag off",
            )
        if app_off.routes:
            return SmokeCheckResult(
                name="route_registration_flag_off",
                passed=False,
                detail="routes registered with flag off",
            )

    with temporary_env({"PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED": "true"}):
        reset_action_route_registration_state_for_tests()
        app_on = build_local_test_app()
        if not apply_dashboard_action_route_bootstrap(app_on):
            return SmokeCheckResult(
                name="route_registration_flag_on",
                passed=False,
                detail="bootstrap should register when flag on",
            )
        if len(app_on.routes) != 2:
            return SmokeCheckResult(
                name="route_registration_flag_on",
                passed=False,
                detail=f"expected 2 routes, got {len(app_on.routes)}",
            )
    return SmokeCheckResult(
        name="route_registration",
        passed=True,
        detail="off=0 routes · on=2 POST routes",
    )


def _approve_body(**overrides: Any) -> dict:
    base = dict(
        workspace_id="ws-smoke-script-1",
        shop_id="shop-smoke-script-1",
        actor_user_id="op-smoke-script-1",
        actor_role="operator",
        client_request_id="req-smoke-script-approve",
        expected_pending_status="pending",
        dry_run_expected=True,
        csrf_token="csrf-smoke-script",
        confirm_checkbox=True,
    )
    base.update(overrides)
    return base


def _reject_body(**overrides: Any) -> dict:
    base = dict(
        workspace_id="ws-smoke-script-1",
        shop_id="shop-smoke-script-1",
        actor_user_id="op-smoke-script-1",
        actor_role="operator",
        client_request_id="req-smoke-script-reject",
        expected_pending_status="pending",
        reject_reason="smoke test",
        csrf_token="csrf-smoke-script",
        confirm_checkbox=True,
    )
    base.update(overrides)
    return base


def check_dry_run_requests() -> SmokeCheckResult:
    from product_persistence.pending_assisted_action_routes import (
        handle_approve_pending_assisted,
        handle_reject_pending_assisted,
    )

    status, body = handle_approve_pending_assisted(
        "pending-smoke-script-1",
        _approve_body(csrf_token=""),
    )
    if status != 403 or body.get("status") != "csrf_failed":
        return SmokeCheckResult(
            name="approve_csrf_required",
            passed=False,
            detail=f"expected 403 csrf_failed, got {status} {body.get('status')}",
        )

    status, body = handle_approve_pending_assisted(
        "pending-smoke-script-1",
        _approve_body(dry_run_expected=False),
    )
    if status != 422 or body.get("status") != "dry_run_required":
        return SmokeCheckResult(
            name="approve_dry_run_required",
            passed=False,
            detail=f"expected 422 dry_run_required, got {status} {body.get('status')}",
        )

    status, body = handle_reject_pending_assisted(
        "pending-smoke-script-1",
        _reject_body(csrf_token=""),
    )
    if status != 403 or body.get("status") != "csrf_failed":
        return SmokeCheckResult(
            name="reject_csrf_required",
            passed=False,
            detail=f"expected 403 csrf_failed, got {status} {body.get('status')}",
        )

    return SmokeCheckResult(
        name="dry_run_request_guards",
        passed=True,
        detail="csrf enforced · live_send_not_implemented path for dry_run_expected=false",
    )


def check_dry_run_response_shape() -> SmokeCheckResult:
    from datetime import datetime, timedelta, timezone

    from product_persistence.db_manager import ProductDbManager, reset_product_db_manager
    from product_persistence.pending_assisted_action_routes import (
        handle_approve_pending_assisted,
    )
    from product_persistence.services.assisted_outbound_port import (
        DryRunAssistedOutboundPort,
    )
    from product_persistence.services.assisted_reply_service import AssistedReplyService

    _cleanup_smoke_db()

    overrides = {
        key: None for key in _FLAG_KEYS
    }
    overrides.update(
        {
            "PRODUCT_PERSISTENCE_ENABLED": "true",
            "PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED": "true",
            "PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG": "true",
            "PRODUCT_PERSISTENCE_WRITE_SEND_DECISION": "true",
            "PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY": "true",
            "PRODUCT_PERSISTENCE_WRITE_ACTION_IDEMPOTENCY": "true",
            "PRODUCT_ASSISTED_SERVICE_ENABLED": "true",
            "PRODUCT_ASSISTED_SEND_ENABLED": "true",
            "PRODUCT_ASSISTED_SEND_DRY_RUN": "true",
            "PRODUCT_ASSISTED_SEND_TEST_SHOP_ID": "shop-smoke-script-1",
            "PRODUCT_DB_URL": f"sqlite:///{_SMOKE_DB.as_posix()}",
        }
    )

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(days=7)).replace(
        microsecond=0
    ).isoformat()

    db: ProductDbManager | None = None
    try:
        with temporary_env(overrides):
            reset_product_db_manager()
            db = ProductDbManager(db_url=os.environ["PRODUCT_DB_URL"])
            db.init_product_db()
            service = AssistedReplyService(
                db_manager=db,
                outbound_port=DryRunAssistedOutboundPort(),
            )
            created = service.create_pending_from_preview(
                reply_log_id="rl-smoke-script-1",
                workspace_id="ws-smoke-script-1",
                shop_id="shop-smoke-script-1",
                account_id="acc-smoke-script-1",
                platform_id="pinduoduo",
                buyer_id="buyer-smoke-script-1",
                buyer_message="smoke test message",
                ai_suggested_reply="smoke suggested reply",
                intent="inventory_question",
                intent_bucket="allowed",
                risk_level="low",
                expires_at=future,
                inbound_created_at=now,
            )
            if not created.success or not created.pending_assisted_id:
                return SmokeCheckResult(
                    name="dry_run_response_shape",
                    passed=False,
                    detail=created.reason or created.error or "create_pending failed",
                )
            status, body = handle_approve_pending_assisted(
                created.pending_assisted_id,
                _approve_body(
                    final_reply_override="smoke dry-run reply text",
                ),
                service=service,
            )
            if status != 200:
                return SmokeCheckResult(
                    name="dry_run_response_shape",
                    passed=False,
                    detail=f"approve failed status={status}",
                )
            if not body.get("dry_run"):
                return SmokeCheckResult(
                    name="dry_run_response_shape",
                    passed=False,
                    detail="expected dry_run=true",
                )
            if body.get("live_send_attempted"):
                return SmokeCheckResult(
                    name="dry_run_response_shape",
                    passed=False,
                    detail="live_send_attempted must be false",
                )
            if body.get("provider_message_id") is not None:
                return SmokeCheckResult(
                    name="dry_run_response_shape",
                    passed=False,
                    detail="provider_message_id must be null",
                )
            if body.get("sent_at") is not None:
                return SmokeCheckResult(
                    name="dry_run_response_shape",
                    passed=False,
                    detail="sent_at must be absent/null",
                )
    finally:
        _cleanup_smoke_db(db)

    return SmokeCheckResult(
        name="dry_run_response_shape",
        passed=True,
        detail="dry_run=true · no live_send · no provider_message_id/sent_at",
    )


def check_no_send_runtime() -> SmokeCheckResult:
    from unittest.mock import AsyncMock, MagicMock, patch

    from datetime import datetime, timedelta, timezone

    from product_persistence.db_manager import ProductDbManager, reset_product_db_manager
    from product_persistence.pending_assisted_action_routes import (
        handle_approve_pending_assisted,
    )
    from product_persistence.services.assisted_outbound_port import (
        DryRunAssistedOutboundPort,
    )
    from product_persistence.services.assisted_reply_service import AssistedReplyService

    _cleanup_smoke_db()

    overrides = {key: None for key in _FLAG_KEYS}
    overrides.update(
        {
            "PRODUCT_PERSISTENCE_ENABLED": "true",
            "PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED": "true",
            "PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG": "true",
            "PRODUCT_ASSISTED_SERVICE_ENABLED": "true",
            "PRODUCT_ASSISTED_SEND_ENABLED": "true",
            "PRODUCT_ASSISTED_SEND_DRY_RUN": "true",
            "PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY": "true",
            "PRODUCT_PERSISTENCE_WRITE_SEND_DECISION": "true",
            "PRODUCT_DB_URL": f"sqlite:///{_SMOKE_DB.as_posix()}",
            "PRODUCT_ASSISTED_SEND_TEST_SHOP_ID": "shop-smoke-script-1",
        }
    )

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(days=7)).replace(
        microsecond=0
    ).isoformat()

    send_text_mock = MagicMock()
    send_reply_mock = AsyncMock()
    db: ProductDbManager | None = None

    try:
        with patch(
            "Channel.pinduoduo.utils.API.send_message.SendMessage.send_text",
            send_text_mock,
        ), patch(
            "Message.handlers.ai_handler.AIReplyHandler._send_reply",
            send_reply_mock,
        ):
            with temporary_env(overrides):
                reset_product_db_manager()
                db = ProductDbManager(db_url=os.environ["PRODUCT_DB_URL"])
                db.init_product_db()
                service = AssistedReplyService(
                    db_manager=db,
                    outbound_port=DryRunAssistedOutboundPort(),
                )
                created = service.create_pending_from_preview(
                    reply_log_id="rl-smoke-runtime-1",
                    workspace_id="ws-smoke-script-1",
                    shop_id="shop-smoke-script-1",
                    account_id="acc-smoke-script-1",
                    platform_id="pinduoduo",
                    buyer_id="buyer-smoke-script-1",
                    buyer_message="runtime no-send check",
                    ai_suggested_reply="runtime reply",
                    intent="inventory_question",
                    intent_bucket="allowed",
                    risk_level="low",
                    expires_at=future,
                    inbound_created_at=now,
                )
                if not created.pending_assisted_id:
                    return SmokeCheckResult(
                        name="no_send_runtime",
                        passed=False,
                        detail="create_pending failed",
                    )
                handle_approve_pending_assisted(
                    created.pending_assisted_id,
                    _approve_body(final_reply_override="runtime dry-run text"),
                    service=service,
                )
        if send_text_mock.called:
            return SmokeCheckResult(
                name="no_send_runtime",
                passed=False,
                detail="SendMessage.send_text was called",
            )
        if send_reply_mock.await_count:
            return SmokeCheckResult(
                name="no_send_runtime",
                passed=False,
                detail="AIReplyHandler._send_reply was called",
            )
    finally:
        _cleanup_smoke_db(db)

    return SmokeCheckResult(
        name="no_send_runtime",
        passed=True,
        detail="SendMessage and handler send not invoked",
    )


def run_smoke_checks(
    extra_checks: Optional[List[Callable[[], SmokeCheckResult]]] = None,
) -> List[SmokeCheckResult]:
    _ensure_project_root_on_path()
    checks: List[Callable[[], SmokeCheckResult]] = [
        assert_no_forbidden_imports,
        check_default_flags,
        check_pdd_queue_name,
        check_import_no_registration_or_db,
        check_route_registration,
        check_dry_run_requests,
        check_dry_run_response_shape,
        check_no_send_runtime,
    ]
    if extra_checks:
        checks.extend(extra_checks)
    return [check() for check in checks]


def print_summary(results: List[SmokeCheckResult]) -> None:
    print("=" * 60)
    print("Dashboard Action Routes Smoke Test (Phase 15r)")
    print("Dry-run / no-send only · no PDD · no live send")
    print("=" * 60)
    print()
    for result in results:
        mark = "PASS" if result.passed else "FAIL"
        line = f"  [{mark}] {result.name}"
        if result.detail:
            line += f" — {result.detail}"
        print(line)
    print()
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    if passed == total:
        print(f"SUMMARY: PASS ({passed}/{total}) · no-send boundaries OK")
    else:
        failed = total - passed
        print(f"SUMMARY: FAIL ({failed} failed, {passed}/{total} passed)")
    print()


def main() -> int:
    results = run_smoke_checks()
    print_summary(results)
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

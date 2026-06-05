"""Dashboard read-only API skeleton (Phase 14o).

No Flask dependency required. Routes register only when the host app exposes
Flask-style ``add_url_rule`` or ``route``. PyQt ``app.py`` startup is unaffected.

Auth: placeholder only — future workspace-scoped auth required before production.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Tuple

from product_persistence.services.dashboard_read_service import (
    DashboardDetailResult,
    DashboardListResult,
    DashboardReadService,
)

READ_ONLY_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

REGISTERED_GET_ROUTES: Tuple[Tuple[str, str], ...] = (
    ("GET", "/api/product/reply-logs"),
    ("GET", "/api/product/reply-logs/<reply_log_id>"),
)


def _parse_query_params(params: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not params:
        return {}
    return {str(key): value for key, value in params.items()}


def _optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _optional_int(value: Any, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _list_result_to_json(result: DashboardListResult) -> Dict[str, Any]:
    return {
        "items": list(result.items),
        "page": result.page,
        "page_size": result.page_size,
        "total": result.total,
        "source": result.source,
        "warnings": list(result.warnings),
        "auth": "placeholder_future_auth_required",
    }


def _detail_result_to_json(result: DashboardDetailResult) -> Dict[str, Any]:
    return {
        "reply_log": result.reply_log,
        "send_decision_snapshots": list(result.send_decision_snapshots),
        "audit_logs": list(result.audit_logs),
        "pending_assisted_reply": result.pending_assisted_reply,
        "source": result.source,
        "warnings": list(result.warnings),
        "auth": "placeholder_future_auth_required",
    }


def handle_list_reply_logs(
    query_params: Mapping[str, Any] | None = None,
    *,
    service: DashboardReadService | None = None,
) -> Tuple[int, Dict[str, Any]]:
    params = _parse_query_params(query_params)
    svc = service or DashboardReadService()
    result = svc.list_reply_logs(
        workspace_id=_optional_str(params.get("workspace_id")),
        shop_id=_optional_str(params.get("shop_id")),
        account_id=_optional_str(params.get("account_id")),
        platform_id=_optional_str(params.get("platform_id")),
        buyer_id=_optional_str(params.get("buyer_id")),
        send_status=_optional_str(params.get("send_status")),
        intent_bucket=_optional_str(params.get("intent_bucket")),
        risk_level=_optional_str(params.get("risk_level")),
        page=_optional_int(params.get("page"), 1),
        page_size=_optional_int(params.get("page_size"), 50),
    )
    return 200, _list_result_to_json(result)


def handle_get_reply_log_detail(
    reply_log_id: str,
    query_params: Mapping[str, Any] | None = None,
    *,
    service: DashboardReadService | None = None,
) -> Tuple[int, Dict[str, Any]]:
    _ = _parse_query_params(query_params)
    svc = service or DashboardReadService()
    result = svc.get_reply_log_detail(reply_log_id)
    if result.not_found:
        body = _detail_result_to_json(result)
        body["error"] = "not_found"
        body["reply_log_id"] = reply_log_id
        return 404, body
    return 200, _detail_result_to_json(result)


def dashboard_read_route_names() -> Iterable[str]:
    return ("list_reply_logs", "get_reply_log_detail")


def register_dashboard_read_routes(app: Any) -> None:
    """Register GET routes when supported; otherwise no-op (safe for PyQt app)."""
    if app is None:
        return

    add_url_rule = getattr(app, "add_url_rule", None)
    if callable(add_url_rule):
        add_url_rule(
            "/api/product/reply-logs",
            endpoint="product_list_reply_logs",
            view_func=_flask_list_view,
            methods=["GET"],
        )
        add_url_rule(
            "/api/product/reply-logs/<reply_log_id>",
            endpoint="product_get_reply_log_detail",
            view_func=_flask_detail_view,
            methods=["GET"],
        )
        return

    route_decorator = getattr(app, "route", None)
    if callable(route_decorator):
        route_decorator("/api/product/reply-logs", methods=["GET"])(_flask_list_view)
        route_decorator(
            "/api/product/reply-logs/<reply_log_id>",
            methods=["GET"],
        )(_flask_detail_view)


def _flask_list_view() -> Any:
    try:
        from flask import jsonify, request
    except ImportError as exc:
        raise RuntimeError("Flask is required for HTTP view dispatch") from exc

    status, body = handle_list_reply_logs(request.args)
    return jsonify(body), status


def _flask_detail_view(reply_log_id: str) -> Any:
    try:
        from flask import jsonify, request
    except ImportError as exc:
        raise RuntimeError("Flask is required for HTTP view dispatch") from exc

    status, body = handle_get_reply_log_detail(reply_log_id, request.args)
    return jsonify(body), status


def dispatch_dashboard_read_route(
    method: str,
    path: str,
    *,
    query_params: Mapping[str, Any] | None = None,
    service: DashboardReadService | None = None,
) -> Tuple[int, Dict[str, Any]]:
    """Lightweight dispatcher for tests without Flask."""
    method_upper = method.upper()
    if method_upper not in READ_ONLY_METHODS:
        return 405, {"error": "method_not_allowed", "method": method_upper}

    if path == "/api/product/reply-logs":
        return handle_list_reply_logs(query_params, service=service)

    prefix = "/api/product/reply-logs/"
    if path.startswith(prefix):
        reply_log_id = path[len(prefix) :].strip("/")
        if reply_log_id:
            return handle_get_reply_log_detail(
                reply_log_id,
                query_params,
                service=service,
            )

    return 404, {"error": "not_found", "path": path}


def serialize_dashboard_response(status: int, body: Mapping[str, Any]) -> str:
    return json.dumps({"status": status, "body": dict(body)}, ensure_ascii=False)

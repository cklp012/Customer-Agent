"""PendingAssisted dashboard read-only API skeleton (Phase 15d).

Not registered in app.py. Safe to import without Flask or DB side effects when flags off.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Tuple

from product_persistence.services.pending_assisted_dashboard_read_service import (
    PendingAssistedDashboardReadService,
    PendingAssistedDetailResult,
    PendingAssistedListResult,
)

READ_ONLY_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

REGISTERED_GET_ROUTES: Tuple[Tuple[str, str], ...] = (
    ("GET", "/api/product/pending-assisted"),
    ("GET", "/api/product/pending-assisted/<pending_assisted_id>"),
)

_FORBIDDEN_MUTATION_ROUTES = frozenset(
    {
        "POST /api/product/pending-assisted",
        "PATCH /api/product/pending-assisted",
        "DELETE /api/product/pending-assisted",
        "POST /api/product/pending-assisted/<id>/approve",
        "POST /api/product/pending-assisted/<id>/reject",
        "POST /api/product/pending-assisted/<id>/send",
    }
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


def _list_result_to_json(result: PendingAssistedListResult) -> Dict[str, Any]:
    return {
        "items": [
            PendingAssistedDashboardReadService.list_item_to_dict(item)
            for item in result.items
        ],
        "pagination": asdict(result.pagination),
        "source": result.source,
        "warnings": list(result.warnings),
        "disabled": result.disabled,
        "auth": "placeholder_future_auth_required",
    }


def _detail_result_to_json(result: PendingAssistedDetailResult) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "source": result.source,
        "warnings": list(result.warnings),
        "disabled": result.disabled,
        "auth": "placeholder_future_auth_required",
    }
    if result.detail is not None:
        body.update(PendingAssistedDashboardReadService.detail_to_dict(result.detail))
    else:
        body["detail"] = None
    return body


def handle_list_pending_assisted(
    query_params: Mapping[str, Any] | None = None,
    *,
    service: PendingAssistedDashboardReadService | None = None,
) -> Tuple[int, Dict[str, Any]]:
    params = _parse_query_params(query_params)
    svc = service or PendingAssistedDashboardReadService()
    result = svc.list_pending_assisted(
        workspace_id=_optional_str(params.get("workspace_id")),
        shop_id=_optional_str(params.get("shop_id")),
        account_id=_optional_str(params.get("account_id")),
        platform_id=_optional_str(params.get("platform_id")),
        status=_optional_str(params.get("status")),
        buyer_id=_optional_str(params.get("buyer_id")),
        intent_category=_optional_str(params.get("intent_category")),
        risk_level=_optional_str(params.get("risk_level")),
        created_after=_optional_str(params.get("created_after")),
        created_before=_optional_str(params.get("created_before")),
        updated_after=_optional_str(params.get("updated_after")),
        updated_before=_optional_str(params.get("updated_before")),
        page=_optional_int(params.get("page"), 1),
        page_size=_optional_int(params.get("page_size"), 50),
        sort_by=_optional_str(params.get("sort_by")) or "created_at",
        sort_order=_optional_str(params.get("sort_order")) or "desc",
    )
    return 200, _list_result_to_json(result)


def handle_get_pending_assisted_detail(
    pending_assisted_id: str,
    query_params: Mapping[str, Any] | None = None,
    *,
    service: PendingAssistedDashboardReadService | None = None,
) -> Tuple[int, Dict[str, Any]]:
    params = _parse_query_params(query_params)
    svc = service or PendingAssistedDashboardReadService()
    result = svc.get_pending_assisted_detail(
        pending_assisted_id,
        workspace_id=_optional_str(params.get("workspace_id")),
        actor_role=_optional_str(params.get("actor_role")),
    )
    body = _detail_result_to_json(result)
    if result.forbidden:
        body["error"] = "forbidden"
        return 403, body
    if result.not_found:
        body["error"] = "not_found"
        body["pending_assisted_id"] = pending_assisted_id
        return 404, body
    return 200, body


def pending_assisted_read_route_names() -> Iterable[str]:
    return ("list_pending_assisted", "get_pending_assisted_detail")


def register_pending_assisted_read_routes(app: Any) -> None:
    """Register GET routes when supported; otherwise no-op."""
    if app is None:
        return

    add_url_rule = getattr(app, "add_url_rule", None)
    if callable(add_url_rule):
        add_url_rule(
            "/api/product/pending-assisted",
            endpoint="product_list_pending_assisted",
            view_func=_flask_list_view,
            methods=["GET"],
        )
        add_url_rule(
            "/api/product/pending-assisted/<pending_assisted_id>",
            endpoint="product_get_pending_assisted_detail",
            view_func=_flask_detail_view,
            methods=["GET"],
        )
        return

    route_decorator = getattr(app, "route", None)
    if callable(route_decorator):
        route_decorator("/api/product/pending-assisted", methods=["GET"])(_flask_list_view)
        route_decorator(
            "/api/product/pending-assisted/<pending_assisted_id>",
            methods=["GET"],
        )(_flask_detail_view)


def _flask_list_view() -> Any:
    try:
        from flask import jsonify, request
    except ImportError as exc:
        raise RuntimeError("Flask is required for HTTP view dispatch") from exc

    status, body = handle_list_pending_assisted(request.args)
    return jsonify(body), status


def _flask_detail_view(pending_assisted_id: str) -> Any:
    try:
        from flask import jsonify, request
    except ImportError as exc:
        raise RuntimeError("Flask is required for HTTP view dispatch") from exc

    status, body = handle_get_pending_assisted_detail(
        pending_assisted_id,
        request.args,
    )
    return jsonify(body), status


def dispatch_pending_assisted_read_route(
    method: str,
    path: str,
    *,
    query_params: Mapping[str, Any] | None = None,
    service: PendingAssistedDashboardReadService | None = None,
) -> Tuple[int, Dict[str, Any]]:
    """Lightweight dispatcher for tests without Flask."""
    method_upper = method.upper()
    if method_upper not in READ_ONLY_METHODS:
        return 405, {"error": "method_not_allowed", "method": method_upper}

    if path == "/api/product/pending-assisted":
        return handle_list_pending_assisted(query_params, service=service)

    prefix = "/api/product/pending-assisted/"
    if path.startswith(prefix):
        pending_id = path[len(prefix) :].strip("/")
        if pending_id and "/" not in pending_id:
            return handle_get_pending_assisted_detail(
                pending_id,
                query_params,
                service=service,
            )

    return 404, {"error": "not_found", "path": path}


def serialize_pending_assisted_response(
    status: int,
    body: Mapping[str, Any],
) -> str:
    return json.dumps({"status": status, "body": dict(body)}, ensure_ascii=False)

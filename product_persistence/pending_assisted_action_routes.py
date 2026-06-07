"""PendingAssisted dashboard action API skeleton (Phase 15i).

Dry-run approve/reject only. Not registered in app.py.
Routes call AssistedReplyService only — no SendMessage, outbound, or handler integration.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from product_persistence.services.assisted_reply_service import (
    AssistedReplyService,
    AssistedServiceResult,
)

ACTION_METHODS = frozenset({"POST"})

REGISTERED_POST_ROUTES: Tuple[Tuple[str, str], ...] = (
    ("POST", "/api/product/pending-assisted/<pending_assisted_id>/approve"),
    ("POST", "/api/product/pending-assisted/<pending_assisted_id>/reject"),
)

_FORBIDDEN_EXTRA_ROUTES = frozenset(
    {
        "GET /api/product/pending-assisted/<id>/approve",
        "PATCH /api/product/pending-assisted/<id>/approve",
        "DELETE /api/product/pending-assisted/<id>/approve",
        "PUT /api/product/pending-assisted/<id>/approve",
        "GET /api/product/pending-assisted/<id>/reject",
        "PATCH /api/product/pending-assisted/<id>/reject",
        "DELETE /api/product/pending-assisted/<id>/reject",
        "PUT /api/product/pending-assisted/<id>/reject",
        "POST /api/product/pending-assisted/<id>/send",
        "PATCH /api/product/pending-assisted/<id>",
        "DELETE /api/product/pending-assisted/<id>",
    }
)

_ACTION_ROLES = frozenset({"operator", "admin", "owner"})
_FORBIDDEN_OVERRIDE_FIELDS = frozenset(
    {
        "buyer_id",
        "account_id",
        "platform_id",
        "inbound_message_id",
        "conversation_id",
    }
)
_IDEMPOTENCY_KEY_PREFIX = "assisted_send:"


def _optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _parse_body(body: Mapping[str, Any] | str | None) -> Dict[str, Any]:
    if body is None:
        return {}
    if isinstance(body, str):
        text = body.strip()
        if not text:
            return {}
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("request_body_must_be_object")
        return parsed
    return {str(key): value for key, value in body.items()}


def _confirm_checkbox_true(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str) and value.strip().lower() in {"true", "1", "yes"}:
        return True
    return False


def _dry_run_expected_true(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str) and value.strip().lower() in {"true", "1", "yes"}:
        return True
    return False


def _idempotency_key(pending_assisted_id: str) -> str:
    return f"{_IDEMPOTENCY_KEY_PREFIX}{pending_assisted_id}"


def _error_response(
    *,
    action: str,
    status: str,
    reason: str,
    pending_assisted_id: Optional[str] = None,
    warnings: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    return {
        "success": False,
        "status": status,
        "action": action,
        "pending_assisted_id": pending_assisted_id,
        "reason": reason,
        "warnings": list(warnings or ()),
        "auth": "placeholder_future_auth_required",
    }


def _validate_common_action_fields(
    body: Mapping[str, Any],
    *,
    action: str,
    pending_assisted_id: str,
) -> Tuple[Optional[int], Optional[Dict[str, Any]], Optional[Dict[str, str]]]:
    for forbidden in _FORBIDDEN_OVERRIDE_FIELDS:
        if forbidden in body and body[forbidden] not in (None, ""):
            return (
                400,
                _error_response(
                    action=action,
                    status="invalid_request",
                    reason=f"forbidden_field_override:{forbidden}",
                    pending_assisted_id=pending_assisted_id,
                ),
                None,
            )

    csrf_token = _optional_str(body.get("csrf_token"))
    if not csrf_token:
        return (
            403,
            _error_response(
                action=action,
                status="csrf_failed",
                reason="csrf_token_required",
                pending_assisted_id=pending_assisted_id,
            ),
            None,
        )

    if not _confirm_checkbox_true(body.get("confirm_checkbox")):
        return (
            400,
            _error_response(
                action=action,
                status="invalid_request",
                reason="confirm_checkbox_required",
                pending_assisted_id=pending_assisted_id,
            ),
            None,
        )

    actor_role = (_optional_str(body.get("actor_role")) or "").lower()
    if actor_role == "viewer":
        return (
            403,
            _error_response(
                action=action,
                status="forbidden",
                reason="viewer_cannot_action",
                pending_assisted_id=pending_assisted_id,
            ),
            None,
        )

    actor_user_id = _optional_str(body.get("actor_user_id"))
    if not actor_user_id:
        return (
            400,
            _error_response(
                action=action,
                status="invalid_request",
                reason="actor_user_id_required",
                pending_assisted_id=pending_assisted_id,
            ),
            None,
        )

    workspace_id = _optional_str(body.get("workspace_id"))
    shop_id = _optional_str(body.get("shop_id"))
    if not workspace_id or not shop_id:
        return (
            400,
            _error_response(
                action=action,
                status="invalid_request",
                reason="workspace_id_and_shop_id_required",
                pending_assisted_id=pending_assisted_id,
            ),
            None,
        )

    client_request_id = _optional_str(body.get("client_request_id"))
    if not client_request_id:
        return (
            400,
            _error_response(
                action=action,
                status="invalid_request",
                reason="client_request_id_required",
                pending_assisted_id=pending_assisted_id,
            ),
            None,
        )

    expected_pending_status = _optional_str(body.get("expected_pending_status"))
    if not expected_pending_status:
        return (
            400,
            _error_response(
                action=action,
                status="invalid_request",
                reason="expected_pending_status_required",
                pending_assisted_id=pending_assisted_id,
            ),
            None,
        )

    return (
        None,
        None,
        {
            "actor_user_id": actor_user_id,
            "actor_role": actor_role or "operator",
            "workspace_id": workspace_id,
            "shop_id": shop_id,
            "client_request_id": client_request_id,
            "expected_pending_status": expected_pending_status,
        },
    )


def _load_pending_for_route_checks(
    service: AssistedReplyService,
    pending_assisted_id: str,
) -> Any:
    return service._pending_repository().get_pending(pending_assisted_id)


def _validate_pending_scope_and_status(
    pending: Any,
    *,
    action: str,
    pending_assisted_id: str,
    workspace_id: str,
    shop_id: str,
    expected_pending_status: str,
) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    if pending is None:
        return (
            404,
            _error_response(
                action=action,
                status="not_found",
                reason="pending_not_found",
                pending_assisted_id=pending_assisted_id,
            ),
        )

    if pending.workspace_id != workspace_id:
        return (
            403,
            _error_response(
                action=action,
                status="forbidden",
                reason="cross_workspace_forbidden",
                pending_assisted_id=pending_assisted_id,
            ),
        )

    if pending.shop_id != shop_id:
        return (
            403,
            _error_response(
                action=action,
                status="forbidden",
                reason="cross_shop_forbidden",
                pending_assisted_id=pending_assisted_id,
            ),
        )

    if pending.status != expected_pending_status:
        return (
            409,
            _error_response(
                action=action,
                status="conflict",
                reason="stale_expected_pending_status",
                pending_assisted_id=pending_assisted_id,
            ),
        )

    return None, None


def _approve_service_result_to_response(
    result: AssistedServiceResult,
) -> Tuple[int, Dict[str, Any]]:
    would_send = result.status == "dry_run_would_send"
    dry_run = would_send
    body: Dict[str, Any] = {
        "success": result.success,
        "status": result.status,
        "action": "approve",
        "pending_assisted_id": result.pending_assisted_id,
        "reply_log_id": result.reply_log_id,
        "final_guard_allowed": result.final_guard_allowed,
        "final_guard_block_code": result.final_guard_block_code,
        "dry_run": dry_run,
        "would_send": would_send,
        "live_send_attempted": False,
        "provider_message_id": None,
        "audit_log_id": result.audit_log_id,
        "idempotency_key": (
            _idempotency_key(result.pending_assisted_id)
            if result.pending_assisted_id
            else None
        ),
        "reason": result.reason,
        "warnings": [],
        "auth": "placeholder_future_auth_required",
    }

    if result.status == "not_found":
        return 404, body
    if result.status in {"permission_denied", "allowlist_denied", "disabled"}:
        return 403, body
    if result.status == "terminal_state":
        return 409, body
    if result.status == "guard_blocked":
        body["success"] = False
        return 422, body
    if result.status in {"live_send_not_implemented", "dry_run_required"}:
        body["success"] = False
        return 422, body
    if result.success:
        return 200, body
    return 422, body


def _reject_service_result_to_response(
    result: AssistedServiceResult,
) -> Tuple[int, Dict[str, Any]]:
    body: Dict[str, Any] = {
        "success": result.success,
        "status": result.status,
        "action": "reject",
        "pending_assisted_id": result.pending_assisted_id,
        "reply_log_id": result.reply_log_id,
        "audit_log_id": result.audit_log_id,
        "reason": result.reason,
        "warnings": [],
        "auth": "placeholder_future_auth_required",
    }

    if result.status == "not_found":
        return 404, body
    if result.status == "permission_denied":
        return 403, body
    if result.status == "terminal_state":
        return 409, body
    if result.success:
        return 200, body
    return 422, body


def handle_approve_pending_assisted(
    pending_assisted_id: str,
    body: Mapping[str, Any] | str | None = None,
    *,
    service: AssistedReplyService | None = None,
) -> Tuple[int, Dict[str, Any]]:
    pending_assisted_id = (pending_assisted_id or "").strip()
    if not pending_assisted_id:
        return 400, _error_response(
            action="approve",
            status="invalid_request",
            reason="pending_assisted_id_required",
        )

    try:
        parsed_body = _parse_body(body)
    except (json.JSONDecodeError, ValueError):
        return 400, _error_response(
            action="approve",
            status="invalid_request",
            reason="invalid_json_body",
            pending_assisted_id=pending_assisted_id,
        )

    status_code, error_body, fields = _validate_common_action_fields(
        parsed_body,
        action="approve",
        pending_assisted_id=pending_assisted_id,
    )
    if status_code is not None:
        assert error_body is not None
        return status_code, error_body
    assert fields is not None

    if not _dry_run_expected_true(parsed_body.get("dry_run_expected")):
        return 422, _error_response(
            action="approve",
            status="dry_run_required",
            reason="live_send_not_implemented",
            pending_assisted_id=pending_assisted_id,
            warnings=["first_implementation_dry_run_only"],
        )

    svc = service or AssistedReplyService()
    pending = _load_pending_for_route_checks(svc, pending_assisted_id)
    scope_status, scope_body = _validate_pending_scope_and_status(
        pending,
        action="approve",
        pending_assisted_id=pending_assisted_id,
        workspace_id=fields["workspace_id"],
        shop_id=fields["shop_id"],
        expected_pending_status=fields["expected_pending_status"],
    )
    if scope_status is not None:
        assert scope_body is not None
        return scope_status, scope_body

    final_reply_override = _optional_str(parsed_body.get("final_reply_override"))
    result = svc.approve_pending(
        pending_assisted_id,
        actor_user_id=fields["actor_user_id"],
        actor_role=fields["actor_role"],
        final_reply=final_reply_override,
        client_request_id=fields["client_request_id"],
        dry_run_expected=True,
    )
    return _approve_service_result_to_response(result)


def handle_reject_pending_assisted(
    pending_assisted_id: str,
    body: Mapping[str, Any] | str | None = None,
    *,
    service: AssistedReplyService | None = None,
) -> Tuple[int, Dict[str, Any]]:
    pending_assisted_id = (pending_assisted_id or "").strip()
    if not pending_assisted_id:
        return 400, _error_response(
            action="reject",
            status="invalid_request",
            reason="pending_assisted_id_required",
        )

    try:
        parsed_body = _parse_body(body)
    except (json.JSONDecodeError, ValueError):
        return 400, _error_response(
            action="reject",
            status="invalid_request",
            reason="invalid_json_body",
            pending_assisted_id=pending_assisted_id,
        )

    status_code, error_body, fields = _validate_common_action_fields(
        parsed_body,
        action="reject",
        pending_assisted_id=pending_assisted_id,
    )
    if status_code is not None:
        assert error_body is not None
        return status_code, error_body
    assert fields is not None

    svc = service or AssistedReplyService()
    pending = _load_pending_for_route_checks(svc, pending_assisted_id)
    scope_status, scope_body = _validate_pending_scope_and_status(
        pending,
        action="reject",
        pending_assisted_id=pending_assisted_id,
        workspace_id=fields["workspace_id"],
        shop_id=fields["shop_id"],
        expected_pending_status=fields["expected_pending_status"],
    )
    if scope_status is not None:
        assert scope_body is not None
        return scope_status, scope_body

    reject_reason = _optional_str(parsed_body.get("reject_reason"))
    result = svc.reject_pending(
        pending_assisted_id,
        actor_user_id=fields["actor_user_id"],
        actor_role=fields["actor_role"],
        reason=reject_reason,
        client_request_id=fields["client_request_id"],
    )
    return _reject_service_result_to_response(result)


def pending_assisted_action_route_names() -> Iterable[str]:
    return ("approve_pending_assisted", "reject_pending_assisted")


def register_pending_assisted_action_routes(app: Any) -> None:
    """Register POST approve/reject routes when supported; otherwise no-op."""
    if app is None:
        return

    add_url_rule = getattr(app, "add_url_rule", None)
    if callable(add_url_rule):
        add_url_rule(
            "/api/product/pending-assisted/<pending_assisted_id>/approve",
            endpoint="product_approve_pending_assisted",
            view_func=_flask_approve_view,
            methods=["POST"],
        )
        add_url_rule(
            "/api/product/pending-assisted/<pending_assisted_id>/reject",
            endpoint="product_reject_pending_assisted",
            view_func=_flask_reject_view,
            methods=["POST"],
        )
        return

    route_decorator = getattr(app, "route", None)
    if callable(route_decorator):
        route_decorator(
            "/api/product/pending-assisted/<pending_assisted_id>/approve",
            methods=["POST"],
        )(_flask_approve_view)
        route_decorator(
            "/api/product/pending-assisted/<pending_assisted_id>/reject",
            methods=["POST"],
        )(_flask_reject_view)


def _flask_approve_view(pending_assisted_id: str) -> Any:
    try:
        from flask import jsonify, request
    except ImportError as exc:
        raise RuntimeError("Flask is required for HTTP view dispatch") from exc

    body = request.get_json(silent=True) or {}
    status, response_body = handle_approve_pending_assisted(
        pending_assisted_id,
        body,
    )
    return jsonify(response_body), status


def _flask_reject_view(pending_assisted_id: str) -> Any:
    try:
        from flask import jsonify, request
    except ImportError as exc:
        raise RuntimeError("Flask is required for HTTP view dispatch") from exc

    body = request.get_json(silent=True) or {}
    status, response_body = handle_reject_pending_assisted(
        pending_assisted_id,
        body,
    )
    return jsonify(response_body), status


def dispatch_pending_assisted_action_route(
    method: str,
    path: str,
    *,
    body: Mapping[str, Any] | str | None = None,
    service: AssistedReplyService | None = None,
) -> Tuple[int, Dict[str, Any]]:
    """Lightweight dispatcher for tests without Flask."""
    method_upper = method.upper()
    if method_upper not in ACTION_METHODS:
        return 405, {"error": "method_not_allowed", "method": method_upper}

    prefix = "/api/product/pending-assisted/"
    if not path.startswith(prefix):
        return 404, {"error": "not_found", "path": path}

    remainder = path[len(prefix) :].strip("/")
    parts = remainder.split("/")
    if len(parts) != 2:
        return 404, {"error": "not_found", "path": path}

    pending_id, action_suffix = parts
    if not pending_id:
        return 404, {"error": "not_found", "path": path}

    if action_suffix == "approve":
        return handle_approve_pending_assisted(
            pending_id,
            body,
            service=service,
        )
    if action_suffix == "reject":
        return handle_reject_pending_assisted(
            pending_id,
            body,
            service=service,
        )

    return 404, {"error": "not_found", "path": path}


def serialize_pending_assisted_action_response(
    status: int,
    body: Mapping[str, Any],
) -> str:
    return json.dumps({"status": status, "body": dict(body)}, ensure_ascii=False)

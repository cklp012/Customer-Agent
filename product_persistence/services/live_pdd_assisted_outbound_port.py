"""Live PDD assisted outbound port skeleton (Phase 15m) — validation + safety gates only."""

from __future__ import annotations

from product_persistence import flags
from product_persistence.services.assisted_outbound_port import (
    AssistedOutboundPort,
    AssistedOutboundRequest,
    AssistedOutboundResult,
)

_PDD_PLATFORM = "pinduoduo"

_FORBIDDEN_ERROR_TOKENS = frozenset(
    {
        "cookie",
        "token",
        "credential",
        "password",
        "secret",
        "api_key",
        "session",
    }
)


def _safe_error_message(message: str) -> str:
    lower = message.lower()
    for token in _FORBIDDEN_ERROR_TOKENS:
        if token in lower:
            return "request validation or send gate failed"
    return message


def _validation_failed(
    error_code: str,
    error_message: str,
    *,
    trace_id: str | None = None,
) -> AssistedOutboundResult:
    return AssistedOutboundResult(
        success=False,
        dry_run=False,
        would_send=False,
        provider_message_id=None,
        platform_status="validation_failed",
        error_code=error_code,
        error_message=_safe_error_message(error_message),
        sent_at=None,
        trace_id=trace_id,
    )


def _unavailable(
    error_code: str,
    error_message: str,
    *,
    trace_id: str | None = None,
) -> AssistedOutboundResult:
    return AssistedOutboundResult(
        success=False,
        dry_run=False,
        would_send=False,
        provider_message_id=None,
        platform_status="unavailable",
        error_code=error_code,
        error_message=_safe_error_message(error_message),
        sent_at=None,
        trace_id=trace_id,
    )


def _live_not_implemented(
    error_code: str,
    error_message: str,
    *,
    trace_id: str | None = None,
) -> AssistedOutboundResult:
    return AssistedOutboundResult(
        success=False,
        dry_run=False,
        would_send=False,
        provider_message_id=None,
        platform_status="live_send_not_implemented",
        error_code=error_code,
        error_message=_safe_error_message(error_message),
        sent_at=None,
        trace_id=trace_id,
    )


def _non_empty(value: str | None) -> bool:
    return bool((value or "").strip())


def _validate_request(request: AssistedOutboundRequest) -> AssistedOutboundResult | None:
    trace_id = request.trace_id

    platform = (request.platform_id or "").strip().lower()
    if platform != _PDD_PLATFORM:
        return _validation_failed(
            "unsupported_platform",
            "platform_id must be pinduoduo",
            trace_id=trace_id,
        )

    if not _non_empty(request.shop_id):
        return _validation_failed(
            "missing_shop_id",
            "shop_id is required",
            trace_id=trace_id,
        )

    if not _non_empty(request.buyer_id):
        return _validation_failed(
            "missing_buyer_id",
            "buyer_id is required",
            trace_id=trace_id,
        )

    if not _non_empty(request.final_reply):
        return _validation_failed(
            "empty_final_reply",
            "final_reply is required",
            trace_id=trace_id,
        )

    if not _non_empty(request.pending_assisted_id):
        return _validation_failed(
            "missing_pending_assisted_id",
            "pending_assisted_id is required",
            trace_id=trace_id,
        )

    if not _non_empty(request.reply_log_id):
        return _validation_failed(
            "missing_reply_log_id",
            "reply_log_id is required",
            trace_id=trace_id,
        )

    if not _non_empty(request.idempotency_key):
        return _validation_failed(
            "missing_idempotency_key",
            "idempotency_key is required",
            trace_id=trace_id,
        )

    return None


def _apply_safety_gates(request: AssistedOutboundRequest) -> AssistedOutboundResult:
    trace_id = request.trace_id
    shop_id = (request.shop_id or "").strip()

    if not flags.is_assisted_send_enabled():
        return _unavailable(
            "live_send_disabled",
            "assisted live send is disabled",
            trace_id=trace_id,
        )

    if flags.is_assisted_send_dry_run() or request.dry_run:
        return _live_not_implemented(
            "dry_run_required",
            "assisted send dry-run mode is active",
            trace_id=trace_id,
        )

    if not flags.is_assisted_send_test_shop_allowlisted(shop_id):
        return _unavailable(
            "shop_not_allowlisted",
            "shop_id is not allowlisted for assisted live send",
            trace_id=trace_id,
        )

    return _live_not_implemented(
        "live_send_not_implemented",
        "live PDD assisted outbound send is not implemented",
        trace_id=trace_id,
    )


class LivePddAssistedOutboundPort(AssistedOutboundPort):
    """PDD live outbound skeleton — validates and gates only; no real send in Phase 15m."""

    def send(self, request: AssistedOutboundRequest) -> AssistedOutboundResult:
        validation = _validate_request(request)
        if validation is not None:
            return validation
        return _apply_safety_gates(request)

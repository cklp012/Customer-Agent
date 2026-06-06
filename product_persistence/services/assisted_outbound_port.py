"""Assisted outbound port (Phase 15c) — dry-run skeleton only."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AssistedOutboundRequest:
    workspace_id: Optional[str] = None
    shop_id: Optional[str] = None
    account_id: Optional[str] = None
    platform_id: Optional[str] = None
    buyer_id: Optional[str] = None
    pending_assisted_id: Optional[str] = None
    reply_log_id: Optional[str] = None
    final_reply: Optional[str] = None
    idempotency_key: Optional[str] = None
    trace_id: Optional[str] = None
    dry_run: bool = True


@dataclass(frozen=True)
class AssistedOutboundResult:
    success: bool
    dry_run: bool
    would_send: bool
    provider_message_id: Optional[str] = None
    platform_status: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[str] = None
    trace_id: Optional[str] = None


class AssistedOutboundPort(ABC):
    """Outbound port contract — implementations must not call legacy send paths directly."""

    @abstractmethod
    def send(self, request: AssistedOutboundRequest) -> AssistedOutboundResult:
        """Send or dry-run an assisted outbound message."""


class DryRunAssistedOutboundPort(AssistedOutboundPort):
    """Dry-run only — records would_send without calling real outbound paths."""

    def send(self, request: AssistedOutboundRequest) -> AssistedOutboundResult:
        trace_id = request.trace_id
        if not (request.final_reply or "").strip():
            return AssistedOutboundResult(
                success=False,
                dry_run=True,
                would_send=False,
                error_code="empty_reply",
                error_message="final_reply is empty",
                trace_id=trace_id,
            )
        if not (request.buyer_id or "").strip():
            return AssistedOutboundResult(
                success=False,
                dry_run=True,
                would_send=False,
                error_code="missing_buyer_id",
                error_message="buyer_id is required",
                trace_id=trace_id,
            )
        return AssistedOutboundResult(
            success=True,
            dry_run=True,
            would_send=True,
            provider_message_id=None,
            platform_status="dry_run_would_send",
            sent_at=None,
            trace_id=trace_id,
        )


def build_assisted_outbound_request(
    *,
    workspace_id: Optional[str] = None,
    shop_id: Optional[str] = None,
    account_id: Optional[str] = None,
    platform_id: Optional[str] = None,
    buyer_id: Optional[str] = None,
    pending_assisted_id: Optional[str] = None,
    reply_log_id: Optional[str] = None,
    final_reply: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    trace_id: Optional[str] = None,
    dry_run: bool = True,
) -> AssistedOutboundRequest:
    """Build an outbound request; defaults to dry_run=True."""
    return AssistedOutboundRequest(
        workspace_id=workspace_id,
        shop_id=shop_id,
        account_id=account_id,
        platform_id=platform_id,
        buyer_id=buyer_id,
        pending_assisted_id=pending_assisted_id,
        reply_log_id=reply_log_id,
        final_reply=final_reply,
        idempotency_key=idempotency_key,
        trace_id=trace_id,
        dry_run=dry_run,
    )

"""PendingAssisted dashboard read-only service (Phase 15d) — no writes, no guard, no send."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from product_persistence import flags
from product_persistence.models import AuditLogDTO, PendingAssistedReplyDTO

_MAX_PAGE_SIZE = 100
_PREVIEW_MAX_LEN = 80
_SORT_ALLOWLIST = frozenset(
    {"created_at", "updated_at", "expires_at", "risk_level", "status"}
)
_FULL_TEXT_ROLES = frozenset({"operator", "admin", "owner"})
_REDACTED = "[redacted]"


@dataclass(frozen=True)
class PendingAssistedListItem:
    pending_assisted_id: str
    reply_log_id: str
    workspace_id: str
    shop_id: str
    account_id: str
    platform_id: str
    buyer_id: str
    buyer_message_preview: Optional[str]
    ai_suggested_reply_preview: Optional[str]
    merchant_edited_reply_preview: Optional[str]
    intent_category: str
    risk_level: str
    status: str
    final_guard_allowed: Optional[bool]
    final_guard_block_code: Optional[str]
    expires_at: str
    created_at: str
    updated_at: str
    latest_audit_action: Optional[str]


@dataclass(frozen=True)
class PendingAssistedDetail:
    pending_assisted_id: str
    reply_log_id: str
    workspace_id: str
    shop_id: str
    account_id: str
    platform_id: str
    buyer_id: str
    inbound_message_id: Optional[str]
    buyer_message: Optional[str]
    ai_suggested_reply: Optional[str]
    merchant_edited_reply: Optional[str]
    final_reply_candidate: Optional[str]
    intent: str
    intent_category: str
    intent_confidence: Optional[float]
    risk_level: str
    status: str
    expires_at: str
    created_at: str
    updated_at: str
    policy_snapshot: Optional[Dict[str, Any]]
    template_snapshot: Optional[Dict[str, Any]]
    final_guard: Optional[Dict[str, Any]]
    send_decision_snapshot: Optional[Dict[str, Any]]
    audit_timeline: Tuple[Dict[str, Any], ...]
    warnings: Tuple[str, ...]


@dataclass(frozen=True)
class PendingAssistedPagination:
    page: int
    page_size: int
    total: int
    sort_by: str
    sort_order: str


@dataclass(frozen=True)
class PendingAssistedListResult:
    items: Tuple[PendingAssistedListItem, ...]
    pagination: PendingAssistedPagination
    source: str
    warnings: Tuple[str, ...]
    disabled: bool = False


@dataclass(frozen=True)
class PendingAssistedDetailResult:
    detail: Optional[PendingAssistedDetail]
    source: str
    warnings: Tuple[str, ...]
    not_found: bool = False
    forbidden: bool = False
    disabled: bool = False


def _clamp_page(page: int) -> int:
    return max(1, int(page or 1))


def _clamp_page_size(page_size: int) -> int:
    size = int(page_size or 50)
    return min(max(1, size), _MAX_PAGE_SIZE)


def _preview_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    stripped = text.strip()
    if not stripped:
        return None
    if len(stripped) <= _PREVIEW_MAX_LEN:
        return stripped
    return stripped[: _PREVIEW_MAX_LEN - 1] + "…"


def _parse_json_state(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _intent_category(pending: PendingAssistedReplyDTO) -> str:
    return pending.intent_bucket or pending.intent or ""


def _final_reply_candidate(pending: PendingAssistedReplyDTO) -> str:
    return (
        pending.final_reply
        or pending.merchant_edited_reply
        or pending.ai_suggested_reply
        or ""
    )


def _role_allows_full_text(actor_role: Optional[str]) -> bool:
    if not actor_role:
        return False
    return actor_role.strip().lower() in _FULL_TEXT_ROLES


def _maybe_redact(text: Optional[str], *, actor_role: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    if _role_allows_full_text(actor_role):
        return text
    return _REDACTED if text.strip() else text


def _final_guard_from_audits(
    audits: Sequence[AuditLogDTO],
) -> Tuple[Optional[bool], Optional[str], Optional[Dict[str, Any]]]:
    for audit in reversed(audits):
        if audit.action == "final_guard_blocked":
            after = _parse_json_state(audit.after_state)
            guard = {
                "allowed_to_send": False,
                "decision": "block",
                "block_code": after.get("block_code"),
                "block_reason": audit.reason,
                "created_at": audit.created_at,
            }
            block_code = after.get("block_code")
            return False, str(block_code) if block_code else None, guard
        if audit.action == "assisted_approved":
            guard = {
                "allowed_to_send": True,
                "decision": "allow",
                "block_code": None,
                "block_reason": None,
                "created_at": audit.created_at,
            }
            return True, None, guard
    return None, None, None


def _audit_timeline_entry(audit: AuditLogDTO) -> Dict[str, Any]:
    return {
        "audit_log_id": audit.audit_log_id,
        "action": audit.action,
        "actor_user_id": audit.actor_user_id,
        "actor_role": audit.actor_role,
        "reason": audit.reason,
        "before_state": _parse_json_state(audit.before_state),
        "after_state": _parse_json_state(audit.after_state),
        "created_at": audit.created_at,
    }


def _policy_template_from_audits(
    audits: Sequence[AuditLogDTO],
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    policy: Optional[Dict[str, Any]] = None
    template: Optional[Dict[str, Any]] = None
    for audit in reversed(audits):
        after = _parse_json_state(audit.after_state)
        if policy is None and after.get("policy_snapshot"):
            policy = dict(after["policy_snapshot"])
        if template is None and after.get("template_snapshot"):
            template = dict(after["template_snapshot"])
        if policy is not None and template is not None:
            break
    return policy, template


class PendingAssistedDashboardReadService:
    """Read-only PendingAssisted dashboard boundary — no guard execution, no audit writes."""

    def __init__(
        self,
        *,
        pending_repository: Any = None,
        audit_repository: Any = None,
        snapshot_repository: Any = None,
    ) -> None:
        self._pending_repository = pending_repository
        self._audit_repository = audit_repository
        self._snapshot_repository = snapshot_repository

    def _pending_repo(self) -> Any:
        if self._pending_repository is not None:
            return self._pending_repository
        from product_persistence.repositories.sqlite_pending_assisted_repository import (
            PendingAssistedRepositorySQLite,
        )

        return PendingAssistedRepositorySQLite()

    def _audit_repo(self) -> Any:
        if self._audit_repository is not None:
            return self._audit_repository
        from product_persistence.repositories.sqlite_audit_log_repository import (
            AuditLogRepositorySQLite,
        )

        return AuditLogRepositorySQLite()

    def _snapshot_repo(self) -> Any:
        if self._snapshot_repository is not None:
            return self._snapshot_repository
        from product_persistence.repositories.sqlite_send_decision_repository import (
            SendDecisionRepositorySQLite,
        )

        return SendDecisionRepositorySQLite()

    def _disabled_list(self, *, page: int, page_size: int) -> PendingAssistedListResult:
        return PendingAssistedListResult(
            items=(),
            pagination=PendingAssistedPagination(
                page=page,
                page_size=page_size,
                total=0,
                sort_by="created_at",
                sort_order="desc",
            ),
            source="disabled",
            warnings=("dashboard_read_disabled",),
            disabled=True,
        )

    def list_pending_assisted(
        self,
        *,
        workspace_id: Optional[str] = None,
        shop_id: Optional[str] = None,
        account_id: Optional[str] = None,
        platform_id: Optional[str] = None,
        status: Optional[str] = None,
        buyer_id: Optional[str] = None,
        intent_category: Optional[str] = None,
        risk_level: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        updated_after: Optional[str] = None,
        updated_before: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> PendingAssistedListResult:
        page = _clamp_page(page)
        page_size = _clamp_page_size(page_size)
        safe_sort = sort_by if sort_by in _SORT_ALLOWLIST else "created_at"
        safe_order = "asc" if sort_order.lower() == "asc" else "desc"

        if not flags.should_read_dashboard_from_product_db():
            return self._disabled_list(page=page, page_size=page_size)

        offset = (page - 1) * page_size
        pending_repo = self._pending_repo()
        audit_repo = self._audit_repo()
        rows, total = pending_repo.list_pending(
            workspace_id=workspace_id,
            shop_id=shop_id,
            account_id=account_id,
            platform_id=platform_id,
            status=status,
            buyer_id=buyer_id,
            intent_category=intent_category,
            risk_level=risk_level,
            created_after=created_after,
            created_before=created_before,
            updated_after=updated_after,
            updated_before=updated_before,
            sort_by=safe_sort,
            sort_order=safe_order,
            offset=offset,
            limit=page_size,
        )

        items: List[PendingAssistedListItem] = []
        for pending in rows:
            audits = audit_repo.list_for_pending_assisted(
                pending.pending_assisted_id,
                ascending=True,
            )
            guard_allowed, guard_block_code, _guard = _final_guard_from_audits(audits)
            latest_action = audits[-1].action if audits else None
            items.append(
                PendingAssistedListItem(
                    pending_assisted_id=pending.pending_assisted_id,
                    reply_log_id=pending.reply_log_id,
                    workspace_id=pending.workspace_id,
                    shop_id=pending.shop_id,
                    account_id=pending.account_id,
                    platform_id=pending.platform_id,
                    buyer_id=pending.buyer_id,
                    buyer_message_preview=_preview_text(pending.buyer_message),
                    ai_suggested_reply_preview=_preview_text(pending.ai_suggested_reply),
                    merchant_edited_reply_preview=_preview_text(
                        pending.merchant_edited_reply
                    ),
                    intent_category=_intent_category(pending),
                    risk_level=pending.risk_level or "",
                    status=pending.status,
                    final_guard_allowed=guard_allowed,
                    final_guard_block_code=guard_block_code,
                    expires_at=pending.expires_at,
                    created_at=pending.created_at,
                    updated_at=pending.updated_at,
                    latest_audit_action=latest_action,
                )
            )

        return PendingAssistedListResult(
            items=tuple(items),
            pagination=PendingAssistedPagination(
                page=page,
                page_size=page_size,
                total=total,
                sort_by=safe_sort,
                sort_order=safe_order,
            ),
            source="sqlite_shadow",
            warnings=(),
        )

    def get_pending_assisted_detail(
        self,
        pending_assisted_id: str,
        *,
        workspace_id: Optional[str] = None,
        actor_role: Optional[str] = None,
    ) -> PendingAssistedDetailResult:
        if not flags.should_read_dashboard_from_product_db():
            return PendingAssistedDetailResult(
                detail=None,
                source="disabled",
                warnings=("dashboard_read_disabled",),
                disabled=True,
            )

        pending = self._pending_repo().get_pending(pending_assisted_id)
        if pending is None:
            return PendingAssistedDetailResult(
                detail=None,
                source="sqlite_shadow",
                warnings=(),
                not_found=True,
            )

        if workspace_id and pending.workspace_id != workspace_id:
            return PendingAssistedDetailResult(
                detail=None,
                source="sqlite_shadow",
                warnings=("cross_workspace_forbidden",),
                forbidden=True,
            )

        audits = self._audit_repo().list_for_pending_assisted(
            pending_assisted_id,
            ascending=True,
        )
        guard_allowed, _guard_block_code, final_guard = _final_guard_from_audits(audits)
        policy_snapshot, template_snapshot = _policy_template_from_audits(audits)
        send_decision = self._snapshot_repo().latest_for_reply_log(pending.reply_log_id)
        intent_confidence = None
        if send_decision is not None:
            raw_confidence = send_decision.get("intent_confidence")
            if raw_confidence is not None:
                intent_confidence = float(raw_confidence)

        candidate = _final_reply_candidate(pending)
        detail = PendingAssistedDetail(
            pending_assisted_id=pending.pending_assisted_id,
            reply_log_id=pending.reply_log_id,
            workspace_id=pending.workspace_id,
            shop_id=pending.shop_id,
            account_id=pending.account_id,
            platform_id=pending.platform_id,
            buyer_id=pending.buyer_id,
            inbound_message_id=pending.inbound_message_id,
            buyer_message=_maybe_redact(pending.buyer_message, actor_role=actor_role),
            ai_suggested_reply=_maybe_redact(
                pending.ai_suggested_reply,
                actor_role=actor_role,
            ),
            merchant_edited_reply=_maybe_redact(
                pending.merchant_edited_reply,
                actor_role=actor_role,
            ),
            final_reply_candidate=_maybe_redact(candidate, actor_role=actor_role),
            intent=pending.intent or "",
            intent_category=_intent_category(pending),
            intent_confidence=intent_confidence,
            risk_level=pending.risk_level or "",
            status=pending.status,
            expires_at=pending.expires_at,
            created_at=pending.created_at,
            updated_at=pending.updated_at,
            policy_snapshot=policy_snapshot,
            template_snapshot=template_snapshot,
            final_guard=final_guard,
            send_decision_snapshot=send_decision,
            audit_timeline=tuple(_audit_timeline_entry(a) for a in audits),
            warnings=(),
        )
        _ = guard_allowed
        return PendingAssistedDetailResult(
            detail=detail,
            source="sqlite_shadow",
            warnings=(),
        )

    @staticmethod
    def list_item_to_dict(item: PendingAssistedListItem) -> Dict[str, Any]:
        return {
            "pending_assisted_id": item.pending_assisted_id,
            "reply_log_id": item.reply_log_id,
            "workspace_id": item.workspace_id,
            "shop_id": item.shop_id,
            "account_id": item.account_id,
            "platform_id": item.platform_id,
            "buyer_id": item.buyer_id,
            "buyer_message_preview": item.buyer_message_preview,
            "ai_suggested_reply_preview": item.ai_suggested_reply_preview,
            "merchant_edited_reply_preview": item.merchant_edited_reply_preview,
            "intent_category": item.intent_category,
            "risk_level": item.risk_level,
            "status": item.status,
            "final_guard_allowed": item.final_guard_allowed,
            "final_guard_block_code": item.final_guard_block_code,
            "expires_at": item.expires_at,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "latest_audit_action": item.latest_audit_action,
        }

    @staticmethod
    def detail_to_dict(detail: PendingAssistedDetail) -> Dict[str, Any]:
        return {
            "pending_assisted_id": detail.pending_assisted_id,
            "reply_log_id": detail.reply_log_id,
            "workspace_id": detail.workspace_id,
            "shop_id": detail.shop_id,
            "account_id": detail.account_id,
            "platform_id": detail.platform_id,
            "buyer_id": detail.buyer_id,
            "inbound_message_id": detail.inbound_message_id,
            "buyer_message": detail.buyer_message,
            "ai_suggested_reply": detail.ai_suggested_reply,
            "merchant_edited_reply": detail.merchant_edited_reply,
            "final_reply_candidate": detail.final_reply_candidate,
            "intent": detail.intent,
            "intent_category": detail.intent_category,
            "intent_confidence": detail.intent_confidence,
            "risk_level": detail.risk_level,
            "status": detail.status,
            "expires_at": detail.expires_at,
            "created_at": detail.created_at,
            "updated_at": detail.updated_at,
            "policy_snapshot": detail.policy_snapshot,
            "template_snapshot": detail.template_snapshot,
            "final_guard": detail.final_guard,
            "send_decision_snapshot": detail.send_decision_snapshot,
            "audit_timeline": list(detail.audit_timeline),
            "warnings": list(detail.warnings),
        }

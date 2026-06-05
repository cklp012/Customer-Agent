"""Dashboard read-only service (Phase 14o) — no send, no state mutation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from product_persistence import flags

_MAX_PAGE_SIZE = 100
_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "secret",
        "authorization",
        "cookie",
        "session_id",
    }
)


@dataclass(frozen=True)
class DashboardListResult:
    items: Tuple[Dict[str, Any], ...]
    page: int
    page_size: int
    total: int
    source: str
    warnings: Tuple[str, ...]


@dataclass(frozen=True)
class DashboardDetailResult:
    reply_log: Optional[Dict[str, Any]]
    send_decision_snapshots: Tuple[Dict[str, Any], ...]
    audit_logs: Tuple[Any, ...]
    pending_assisted_reply: None
    source: str
    warnings: Tuple[str, ...]
    not_found: bool = False


def _clamp_page(page: int) -> int:
    return max(1, int(page or 1))


def _clamp_page_size(page_size: int) -> int:
    size = int(page_size or 50)
    return min(max(1, size), _MAX_PAGE_SIZE)


def _sanitize_mapping(data: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        key: value
        for key, value in data.items()
        if key.lower() not in _SENSITIVE_KEYS
    }


def _item_to_dict(item: Any) -> Dict[str, Any]:
    if is_dataclass(item):
        data = asdict(item)
    elif isinstance(item, Mapping):
        data = dict(item)
    else:
        data = {
            key: getattr(item, key)
            for key in (
                "reply_log_id",
                "workspace_id",
                "platform_id",
                "shop_id",
                "account_id",
                "buyer_id",
                "buyer_message",
                "ai_suggested_reply",
                "final_reply",
                "send_status",
                "send_mode",
                "intent",
                "intent_bucket",
                "intent_confidence",
                "risk_level",
                "blocked_reason",
                "human_takeover_reason",
                "not_sent_explanation",
                "created_at",
            )
            if hasattr(item, key)
        }
    if "metadata" in data and isinstance(data["metadata"], dict):
        data["metadata"] = _sanitize_mapping(data["metadata"])
    return _sanitize_mapping(data)


def _snapshot_to_dict(snapshot: Any) -> Dict[str, Any]:
    if is_dataclass(snapshot):
        return _sanitize_mapping(asdict(snapshot))
    if isinstance(snapshot, Mapping):
        return _sanitize_mapping(dict(snapshot))
    return _sanitize_mapping(
        {
            "send_decision_id": getattr(snapshot, "send_decision_id", None),
            "reply_log_id": getattr(snapshot, "reply_log_id", None),
            "decision_phase": getattr(snapshot, "decision_phase", None),
            "intent": getattr(snapshot, "intent", None),
            "send_mode": getattr(snapshot, "send_mode", None),
            "intent_bucket": getattr(snapshot, "intent_bucket", None),
            "risk_level": getattr(snapshot, "risk_level", None),
            "allowed_to_send": getattr(snapshot, "allowed_to_send", None),
            "allowed_to_generate": getattr(snapshot, "allowed_to_generate", None),
            "decision_source": getattr(snapshot, "decision_source", None),
            "created_at": getattr(snapshot, "created_at", None),
        }
    )


def _apply_list_filters(
    items: Sequence[Any],
    *,
    workspace_id: Optional[str],
    shop_id: Optional[str],
    account_id: Optional[str],
    platform_id: Optional[str],
    buyer_id: Optional[str],
    send_status: Optional[str],
    intent_bucket: Optional[str],
    risk_level: Optional[str],
) -> List[Any]:
    filtered = list(items)
    filters = (
        ("workspace_id", workspace_id),
        ("shop_id", shop_id),
        ("account_id", account_id),
        ("platform_id", platform_id),
        ("buyer_id", buyer_id),
        ("send_status", send_status),
        ("intent_bucket", intent_bucket),
        ("risk_level", risk_level),
    )
    for field, expected in filters:
        if expected is None:
            continue
        filtered = [
            item
            for item in filtered
            if _item_to_dict(item).get(field) == expected
        ]
    return filtered


def _paginate(
    items: Sequence[Any],
    *,
    page: int,
    page_size: int,
) -> Tuple[List[Any], int]:
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return list(items[start:end]), total


class DashboardReadService:
    """Read-only dashboard boundary — no SendMessage, no writes, no flag mutation."""

    def __init__(
        self,
        preview_service: Any = None,
        reply_log_repository: Any = None,
        snapshot_repository: Any = None,
    ) -> None:
        self._preview_service = preview_service
        self._reply_log_repository = reply_log_repository
        self._snapshot_repository = snapshot_repository

    def _preview_service_instance(self) -> Any:
        if self._preview_service is not None:
            return self._preview_service
        from product_persistence.services.preview_reply_log_service import (
            PreviewReplyLogService,
        )

        return PreviewReplyLogService()

    def _reply_log_repository_instance(self) -> Any:
        if self._reply_log_repository is not None:
            return self._reply_log_repository
        from product_persistence.repositories.sqlite_reply_log_repository import (
            ReplyLogRepositorySQLite,
        )

        return ReplyLogRepositorySQLite()

    def _snapshot_repository_instance(self) -> Any:
        if self._snapshot_repository is not None:
            return self._snapshot_repository
        from product_persistence.repositories.sqlite_send_decision_repository import (
            SendDecisionRepositorySQLite,
        )

        return SendDecisionRepositorySQLite()

    def list_reply_logs(
        self,
        *,
        workspace_id: str | None = None,
        shop_id: str | None = None,
        account_id: str | None = None,
        platform_id: str | None = None,
        buyer_id: str | None = None,
        send_status: str | None = None,
        intent_bucket: str | None = None,
        risk_level: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> DashboardListResult:
        page = _clamp_page(page)
        page_size = _clamp_page_size(page_size)
        filter_kwargs = dict(
            workspace_id=workspace_id,
            shop_id=shop_id,
            account_id=account_id,
            platform_id=platform_id,
            buyer_id=buyer_id,
            send_status=send_status,
            intent_bucket=intent_bucket,
            risk_level=risk_level,
        )

        if flags.should_read_dashboard_from_product_db():
            try:
                repo = self._reply_log_repository_instance()
                rows = repo.list_reply_logs(
                    workspace_id=workspace_id,
                    shop_id=shop_id,
                    account_id=account_id,
                    platform_id=platform_id,
                    buyer_id=buyer_id,
                    send_status=send_status,
                    intent_bucket=intent_bucket,
                    risk_level=risk_level,
                    limit=10_000,
                )
                filtered = _apply_list_filters(rows, **filter_kwargs)
                page_items, total = _paginate(filtered, page=page, page_size=page_size)
                return DashboardListResult(
                    items=tuple(_item_to_dict(item) for item in page_items),
                    page=page,
                    page_size=page_size,
                    total=total,
                    source="sqlite_shadow",
                    warnings=(),
                )
            except Exception as exc:
                memory_result = self._list_from_in_memory(
                    page=page,
                    page_size=page_size,
                    **filter_kwargs,
                )
                warning = f"sqlite_read_failed_fallback_in_memory: {exc}"
                return DashboardListResult(
                    items=memory_result.items,
                    page=memory_result.page,
                    page_size=memory_result.page_size,
                    total=memory_result.total,
                    source="in_memory",
                    warnings=(warning,),
                )

        return self._list_from_in_memory(
            page=page,
            page_size=page_size,
            **filter_kwargs,
        )

    def _list_from_in_memory(
        self,
        *,
        workspace_id: Optional[str],
        shop_id: Optional[str],
        account_id: Optional[str],
        platform_id: Optional[str],
        buyer_id: Optional[str],
        send_status: Optional[str],
        intent_bucket: Optional[str],
        risk_level: Optional[str],
        page: int,
        page_size: int,
    ) -> DashboardListResult:
        preview = self._preview_service_instance()
        result = preview.list_reply_logs(
            workspace_id=workspace_id,
            shop_id=shop_id,
            buyer_id=buyer_id,
            send_status=send_status,
        )
        records = list(result.records) if result.success else []
        filtered = _apply_list_filters(
            records,
            workspace_id=workspace_id,
            shop_id=shop_id,
            account_id=account_id,
            platform_id=platform_id,
            buyer_id=buyer_id,
            send_status=send_status,
            intent_bucket=intent_bucket,
            risk_level=risk_level,
        )
        page_items, total = _paginate(filtered, page=page, page_size=page_size)
        return DashboardListResult(
            items=tuple(_item_to_dict(item) for item in page_items),
            page=page,
            page_size=page_size,
            total=total,
            source="in_memory",
            warnings=(),
        )

    def get_reply_log_detail(self, reply_log_id: str) -> DashboardDetailResult:
        if flags.should_read_dashboard_from_product_db():
            try:
                repo = self._reply_log_repository_instance()
                detail = repo.get_reply_log_detail(reply_log_id)
                if detail is None:
                    return DashboardDetailResult(
                        reply_log=None,
                        send_decision_snapshots=(),
                        audit_logs=(),
                        pending_assisted_reply=None,
                        source="sqlite_shadow",
                        warnings=(),
                        not_found=True,
                    )
                snapshots = self._snapshot_repository_instance().list_snapshots_by_reply_log(
                    reply_log_id
                )
                return DashboardDetailResult(
                    reply_log=_sanitize_mapping(detail),
                    send_decision_snapshots=tuple(
                        _snapshot_to_dict(item) for item in snapshots
                    ),
                    audit_logs=(),
                    pending_assisted_reply=None,
                    source="sqlite_shadow",
                    warnings=(),
                )
            except Exception as exc:
                memory_detail = self._detail_from_in_memory(reply_log_id)
                warning = f"sqlite_read_failed_fallback_in_memory: {exc}"
                if memory_detail.not_found:
                    return DashboardDetailResult(
                        reply_log=None,
                        send_decision_snapshots=(),
                        audit_logs=(),
                        pending_assisted_reply=None,
                        source="in_memory",
                        warnings=(warning,),
                        not_found=True,
                    )
                return DashboardDetailResult(
                    reply_log=memory_detail.reply_log,
                    send_decision_snapshots=(),
                    audit_logs=(),
                    pending_assisted_reply=None,
                    source="in_memory",
                    warnings=(warning,),
                )

        return self._detail_from_in_memory(reply_log_id)

    def _detail_from_in_memory(self, reply_log_id: str) -> DashboardDetailResult:
        item = self._preview_service_instance().get_reply_log(reply_log_id)
        if item is None:
            return DashboardDetailResult(
                reply_log=None,
                send_decision_snapshots=(),
                audit_logs=(),
                pending_assisted_reply=None,
                source="in_memory",
                warnings=(),
                not_found=True,
            )
        return DashboardDetailResult(
            reply_log=_item_to_dict(item),
            send_decision_snapshots=(),
            audit_logs=(),
            pending_assisted_reply=None,
            source="in_memory",
            warnings=(),
        )

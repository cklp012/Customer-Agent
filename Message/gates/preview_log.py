"""
In-memory preview ReplyLog (Phase 13d/13e) — test shop only, no DB or send APIs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from Message.gates.consultation_intent_classifier import IntentClassification
from Message.gates.guarded_send import GuardedSendResult
from Message.gates.intent_types import SendMode
from Message.gates.send_decision import SendDecision


def _snapshot_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not metadata:
        return {}
    safe: Dict[str, Any] = {}
    for key in (
        "message_id",
        "shop_id",
        "account_id",
        "user_id",
        "from_uid",
        "buyer_id",
        "platform",
        "platform_id",
        "workspace_id",
    ):
        if key in metadata:
            safe[key] = metadata[key]
    return safe


def _metadata_str(metadata: Dict[str, Any], key: str) -> Optional[str]:
    value = metadata.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _resolve_buyer_id(
    metadata: Dict[str, Any],
    buyer_id: Optional[str],
) -> Optional[str]:
    if buyer_id:
        return buyer_id
    return (
        _metadata_str(metadata, "from_uid")
        or _metadata_str(metadata, "buyer_id")
        or _metadata_str(metadata, "user_id")
    )


def _resolve_platform_id(
    metadata: Dict[str, Any],
    platform_id: Optional[str],
) -> Optional[str]:
    if platform_id:
        return platform_id
    return _metadata_str(metadata, "platform_id") or _metadata_str(metadata, "platform")


@dataclass
class PreviewLogRecord:
    message_text: str
    reply_text: str
    classification: IntentClassification
    send_decision: SendDecision
    guarded_result: GuardedSendResult
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    reply_log_id: str = ""
    workspace_id: Optional[str] = None
    platform_id: Optional[str] = None
    shop_id: Optional[str] = None
    account_id: Optional[str] = None
    buyer_id: Optional[str] = None
    send_status: str = ""
    send_mode: str = ""
    blocked_reason: Optional[str] = None
    human_takeover_reason: Optional[str] = None


class InMemoryPreviewLog:
    def __init__(self) -> None:
        self._records: List[PreviewLogRecord] = []

    def append(self, record: PreviewLogRecord) -> None:
        self._records.append(record)

    def all(self) -> List[PreviewLogRecord]:
        return list(self._records)

    def clear(self) -> None:
        self._records.clear()

    def __len__(self) -> int:
        return len(self._records)


preview_log = InMemoryPreviewLog()


def append_preview_log(
    *,
    message_text: str,
    reply_text: str,
    classification: IntentClassification,
    send_decision: SendDecision,
    guarded_result: GuardedSendResult,
    metadata: Optional[Dict[str, Any]] = None,
    logger: Optional[InMemoryPreviewLog] = None,
    buyer_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    platform_id: Optional[str] = None,
    shop_id: Optional[str] = None,
    account_id: Optional[str] = None,
) -> PreviewLogRecord:
    meta = _snapshot_metadata(metadata)
    send_mode_val = send_decision.send_mode
    if isinstance(send_mode_val, SendMode):
        send_mode_str = send_mode_val.value
    else:
        send_mode_str = str(send_mode_val)

    record = PreviewLogRecord(
        message_text=message_text or "",
        reply_text=reply_text or "",
        classification=classification,
        send_decision=send_decision,
        guarded_result=guarded_result,
        metadata=meta,
        created_at=datetime.now(timezone.utc).isoformat(),
        reply_log_id=str(uuid4()),
        workspace_id=workspace_id or _metadata_str(meta, "workspace_id"),
        platform_id=_resolve_platform_id(meta, platform_id),
        shop_id=shop_id or _metadata_str(meta, "shop_id"),
        account_id=account_id or _metadata_str(meta, "account_id"),
        buyer_id=_resolve_buyer_id(meta, buyer_id),
        send_status=guarded_result.send_status,
        send_mode=send_mode_str,
        blocked_reason=send_decision.blocked_reason,
        human_takeover_reason=send_decision.human_takeover_reason,
    )
    target = logger if logger is not None else preview_log
    target.append(record)
    return record

"""
In-memory preview ReplyLog (Phase 13d) — test shop only, no DB or send APIs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from Message.gates.consultation_intent_classifier import IntentClassification
from Message.gates.guarded_send import GuardedSendResult
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
        "platform",
        "platform_id",
        "workspace_id",
    ):
        if key in metadata:
            safe[key] = metadata[key]
    return safe


@dataclass
class PreviewLogRecord:
    message_text: str
    reply_text: str
    classification: IntentClassification
    send_decision: SendDecision
    guarded_result: GuardedSendResult
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""


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
) -> PreviewLogRecord:
    record = PreviewLogRecord(
        message_text=message_text or "",
        reply_text=reply_text or "",
        classification=classification,
        send_decision=send_decision,
        guarded_result=guarded_result,
        metadata=_snapshot_metadata(metadata),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    target = logger if logger is not None else preview_log
    target.append(record)
    return record

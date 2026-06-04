"""
Shadow SendDecision logging (Phase 13b).

Observe-only: product_gate_enabled=False, no send interception, no DB.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from Message.gates.consultation_intent_classifier import (
    IntentClassification,
    classify_consultation_intent,
)
from Message.gates.intent_types import ReplyMode, SendMode
from Message.gates.send_decision import SendDecision, build_send_decision


def _coerce_message_text(message_text: Optional[Union[str, Any]]) -> str:
    if message_text is None:
        return ""
    if isinstance(message_text, str):
        return message_text
    return str(message_text)


def _snapshot_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not metadata:
        return {}
    safe: Dict[str, Any] = {}
    for key in ("message_id", "shop_id", "user_id", "from_uid", "platform"):
        if key in metadata:
            safe[key] = metadata[key]
    return safe


@dataclass
class ShadowDecisionRecord:
    message_text: str
    classification: IntentClassification
    send_decision: SendDecision
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""


class InMemoryShadowDecisionLogger:
    """Lightweight in-process collector for tests and local observation."""

    def __init__(self) -> None:
        self._records: List[ShadowDecisionRecord] = []

    def append(self, record: ShadowDecisionRecord) -> None:
        self._records.append(record)

    def all(self) -> List[ShadowDecisionRecord]:
        return list(self._records)

    def clear(self) -> None:
        self._records.clear()

    def __len__(self) -> int:
        return len(self._records)


shadow_decision_logger = InMemoryShadowDecisionLogger()


def build_shadow_decision_record(
    message_text: Optional[Union[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    reply_mode: Union[ReplyMode, str] = ReplyMode.PREVIEW,
) -> ShadowDecisionRecord:
    """
    Build a shadow record without side effects (no SendMessage, outbound, or DB).
    """
    text = _coerce_message_text(message_text)
    classification = classify_consultation_intent(text)
    decision = build_send_decision(
        classification,
        reply_mode=reply_mode,
        product_gate_enabled=False,
        workspace_pause=False,
        shop_pause=False,
    )
    return ShadowDecisionRecord(
        message_text=text,
        classification=classification,
        send_decision=decision,
        metadata=_snapshot_metadata(metadata),
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def append_shadow_decision_from_handler(
    message_text: Optional[Union[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
    *,
    logger: Optional[InMemoryShadowDecisionLogger] = None,
    reply_mode: Union[ReplyMode, str] = ReplyMode.PREVIEW,
) -> Optional[ShadowDecisionRecord]:
    """
    Classify, build gate-disabled SendDecision, append to shadow logger.

    Safe to call from handler; callers must wrap in try/except (fail-open).
    """
    record = build_shadow_decision_record(
        message_text=message_text,
        metadata=metadata,
        reply_mode=reply_mode,
    )
    target = logger if logger is not None else shadow_decision_logger
    target.append(record)
    return record

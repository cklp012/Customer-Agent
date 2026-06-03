"""
INFO 级日志脱敏 helper（Phase 7i）。

复用 metadata_observability.redact_uid；不输出用户正文或完整 UID。
"""

from __future__ import annotations

from typing import Any, Optional

from bridge.context import Context
from Message.metadata_observability import redact_uid

__all__ = [
    "redact_uid",
    "content_length",
    "reply_length",
    "format_user_ref",
    "format_message_type",
]


def content_length(value: Any) -> int:
    if value is None:
        return 0
    return len(str(value))


def reply_length(text: Optional[str]) -> int:
    return content_length(text)


def format_user_ref(context: Context) -> str:
    """buyer=***suffix 或 buyer=unknown；不含 username 全文。"""
    try:
        kwargs = getattr(context, "kwargs", None)
        if kwargs is not None:
            from_uid = getattr(kwargs, "from_uid", None)
            if from_uid is None and isinstance(kwargs, dict):
                from_uid = kwargs.get("from_uid")
            redacted = redact_uid(str(from_uid) if from_uid is not None else None)
            if redacted is not None:
                return f"buyer={redacted}"
    except Exception:
        pass
    return "buyer=unknown"


def format_message_type(context: Context) -> str:
    msg_type = getattr(context, "type", None)
    if msg_type is None:
        return "unknown"
    return str(getattr(msg_type, "value", msg_type))

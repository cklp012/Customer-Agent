"""
INFO / WARNING / DEBUG 日志脱敏 helper（Phase 7i–7j）。

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
    "format_account_ref",
    "format_buyer_ref",
    "format_cs_ref",
    "format_send_context_log",
]


def _ref_label(prefix: str, uid: Optional[str]) -> str:
    if uid is None:
        return f"{prefix}=missing"
    redacted = redact_uid(str(uid))
    if redacted is None:
        return f"{prefix}=missing"
    return f"{prefix}={redacted}"


def format_account_ref(user_id: Optional[str]) -> str:
    """account=***suffix 或 account=missing。"""
    return _ref_label("account", user_id)


def format_buyer_ref(from_uid: Optional[str]) -> str:
    """buyer=***suffix 或 buyer=missing。"""
    return _ref_label("buyer", from_uid)


def format_cs_ref(cs_uid: Optional[str]) -> str:
    """cs=***suffix 或 cs=missing。"""
    return _ref_label("cs", cs_uid)


def format_send_context_log(
    shop_id: Optional[str],
    user_id: Optional[str],
    from_uid: Optional[str],
) -> str:
    """shop_id 明文；account/buyer 脱敏。"""
    shop_part = f"shop_id={shop_id}" if shop_id is not None else "shop_id=missing"
    return f"{shop_part} {format_account_ref(user_id)} {format_buyer_ref(from_uid)}"


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

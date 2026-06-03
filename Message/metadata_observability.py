"""
Handler 用 metadata 安全观测摘要（Phase 7g）。

只读 metadata_adapter 与 metadata 队列字段；不读 context.content，不输出完整 UID 或敏感正文。
本模块不接入 handler 运行时；Phase 7h 再用于 logger.debug。
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

from bridge.context import Context
from Message.metadata_adapter import (
    get_account_id,
    get_buyer_uid,
    get_content_type,
    get_platform,
    get_routing,
    has_unified_metadata,
)

ObservationValue = Union[str, bool, int, None]

OBSERVATION_KEYS = frozenset(
    {
        "handler",
        "platform",
        "content_type",
        "routing",
        "has_unified",
        "message_id",
        "unified_message_id",
        "shop_id",
        "account_id_suffix",
        "conversation_suffix",
        "retry_count",
    }
)

_FORBIDDEN_SNAPSHOT_KEYS = frozenset(
    {
        "content",
        "raw",
        "body",
        "cookie",
        "token",
        "password",
        "reply",
    }
)


def redact_uid(uid: Optional[str], visible_suffix: int = 4) -> Optional[str]:
    """脱敏 UID：仅保留末 visible_suffix 位，前缀以 *** 代替。"""
    if uid is None:
        return None
    text = str(uid).strip()
    if not text:
        return None
    if visible_suffix <= 0:
        return "***"
    if len(text) <= visible_suffix:
        return f"***{text}"
    return f"***{text[-visible_suffix:]}"


def _as_optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _as_optional_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_handler_observation(
    metadata: Dict[str, Any],
    context: Context,
    *,
    handler_name: Optional[str] = None,
) -> Dict[str, ObservationValue]:
    """
    从 (metadata, context) 构建安全观测摘要。

    不读取 context.content；conversation / buyer 标识仅输出脱敏 suffix。
    """
    buyer_uid = get_buyer_uid(metadata, context)
    conversation_raw = metadata.get("conversation_id")
    if conversation_raw is None:
        conversation_raw = buyer_uid

    obs: Dict[str, ObservationValue] = {
        "platform": get_platform(metadata, context),
        "content_type": get_content_type(metadata, context),
        "routing": get_routing(metadata, context),
        "has_unified": has_unified_metadata(metadata),
        "message_id": _as_optional_str(metadata.get("message_id")),
        "unified_message_id": (
            _as_optional_str(metadata.get("unified_message_id"))
            if has_unified_metadata(metadata)
            else None
        ),
        "shop_id": _as_optional_str(metadata.get("shop_id")),
        "account_id_suffix": redact_uid(get_account_id(metadata, context)),
        "conversation_suffix": redact_uid(
            _as_optional_str(conversation_raw) if conversation_raw is not None else None
        ),
        "retry_count": _as_optional_int(metadata.get("retry_count")),
    }

    if handler_name is not None:
        obs["handler"] = str(handler_name)

    assert obs.keys() <= OBSERVATION_KEYS
    assert not (obs.keys() & _FORBIDDEN_SNAPSHOT_KEYS)

    return obs


def format_observation_for_log(obs: Dict[str, ObservationValue]) -> str:
    """紧凑 key=value 串，供 logger.debug 使用；无换行、无 JSON。"""
    parts: list[str] = []
    for key in sorted(obs.keys()):
        if key not in OBSERVATION_KEYS:
            continue
        value = obs[key]
        if value is None:
            continue
        text = str(value)
        if any(forbidden in key.lower() for forbidden in _FORBIDDEN_SNAPSHOT_KEYS):
            continue
        parts.append(f"{key}={text}")
    return " ".join(parts)

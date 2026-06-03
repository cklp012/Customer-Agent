"""
Handler 用 metadata 读取适配层（Phase 7e）。

仅从 (metadata, context) 读取字段；handler 仍接收 Context，不接收 UnifiedMessage。
发送关键字段 legacy 优先；观测字段在 has_unified 时优先 unified metadata。
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from bridge.context import Context, ContextType

def _read_kwarg(kwargs: Any, key: str) -> Any:
    if kwargs is None:
        return None
    value = getattr(kwargs, key, None)
    if value is not None:
        return value
    if isinstance(kwargs, dict):
        return kwargs.get(key)
    return None


def _normalize_optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def has_unified_metadata(metadata: Dict[str, Any]) -> bool:
    """metadata 是否包含 Phase 7d 双轨 enrich 标记。"""
    return bool(metadata.get("has_unified"))


def get_platform(metadata: Dict[str, Any], context: Context) -> str:
    if has_unified_metadata(metadata):
        platform = metadata.get("platform")
        if platform is not None:
            return str(platform)
    channel = getattr(context, "channel_type", None)
    if channel is not None:
        return str(getattr(channel, "value", channel))
    return "pinduoduo"


def _get_send_field(
    metadata: Dict[str, Any],
    context: Context,
    *,
    legacy_meta_key: str,
    kwargs_key: str,
    unified_meta_key: Optional[str] = None,
) -> Optional[str]:
    """
    发送相关字段：metadata legacy 键 → kwargs → unified 键（仅在前两者皆空时）。
    """
    value = _normalize_optional_str(metadata.get(legacy_meta_key))
    if value is not None:
        return value

    kwargs = getattr(context, "kwargs", None)
    value = _normalize_optional_str(_read_kwarg(kwargs, kwargs_key))
    if value is not None:
        return value

    if has_unified_metadata(metadata) and unified_meta_key:
        value = _normalize_optional_str(metadata.get(unified_meta_key))
        if value is not None:
            return value

    return None


def get_shop_id(metadata: Dict[str, Any], context: Context) -> Optional[str]:
    return _get_send_field(
        metadata,
        context,
        legacy_meta_key="shop_id",
        kwargs_key="shop_id",
        unified_meta_key="shop_id",
    )


def get_account_id(metadata: Dict[str, Any], context: Context) -> Optional[str]:
    """PDD 下为卖家子账号 ID，等价于 legacy user_id。"""
    return _get_send_field(
        metadata,
        context,
        legacy_meta_key="user_id",
        kwargs_key="user_id",
        unified_meta_key="account_id",
    )


def get_buyer_uid(metadata: Dict[str, Any], context: Context) -> Optional[str]:
    return _get_send_field(
        metadata,
        context,
        legacy_meta_key="from_uid",
        kwargs_key="from_uid",
        unified_meta_key="buyer_uid",
    )


def get_content_type(metadata: Dict[str, Any], context: Context) -> str:
    if has_unified_metadata(metadata):
        ct = metadata.get("content_type")
        if ct is not None:
            return str(ct)
    msg_type = getattr(context, "type", None)
    if msg_type is not None:
        return str(getattr(msg_type, "value", msg_type))
    return "text"


def get_routing(metadata: Dict[str, Any], context: Context) -> str:
    if has_unified_metadata(metadata):
        routing = metadata.get("routing")
        if routing is not None:
            return str(routing)
    from Channel.pinduoduo.mappers.pdd_to_unified import compute_pdd_routing

    msg_type = getattr(context, "type", None)
    if isinstance(msg_type, ContextType):
        return compute_pdd_routing(msg_type)
    return "drop"


def get_send_context(
    metadata: Dict[str, Any],
    context: Context,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    发送上下文三元组 (shop_id, user_id, from_uid)。

    语义与 Message.handlers.outbound_resolver.extract_pdd_send_context 对齐：
    legacy metadata / kwargs 优先；仅缺失时 fallback unified 键。
    """
    shop_id = get_shop_id(metadata, context)
    user_id = get_account_id(metadata, context)
    from_uid = get_buyer_uid(metadata, context)
    return shop_id, user_id, from_uid

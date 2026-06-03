"""
平台无关出站解析（Phase 8b）。

Handler 生产路径仍使用 resolve_pinduoduo_outbound；本模块供测试与未来 8c 接入。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from bridge.context import Context
from Message.handlers import channel_outbound_registry
from Message.handlers.outbound_resolver import (
    _is_usable_pinduoduo_outbound,
    resolve_pinduoduo_outbound,
)
from Message.log_sanitizer import format_account_ref, format_send_context_log
from Message.metadata_adapter import get_send_context_for_extract
from utils.logger_loguru import get_logger

logger = get_logger("UnifiedOutboundResolver")


def infer_platform(metadata: Dict[str, Any], context: Optional[Context] = None) -> str:
    """平台推断：metadata.platform → kwargs.channel_type → pinduoduo。"""
    platform = metadata.get("platform")
    if platform is not None:
        return str(platform).strip().lower()

    if context is not None:
        kwargs = getattr(context, "kwargs", None)
        channel_type = getattr(kwargs, "channel_type", None) if kwargs is not None else None
        if channel_type is not None:
            return str(getattr(channel_type, "value", channel_type)).strip().lower()

    return "pinduoduo"


def _is_usable_channel_outbound(
    outbound: Any,
    shop_id: str,
    user_id: str,
) -> bool:
    """校验出站是否可用于当前账号（平台无关 duck type）。"""
    if outbound is None:
        return False
    if not callable(getattr(outbound, "send_text", None)):
        logger.debug("channel outbound 缺少 send_text，不可用")
        return False

    ob_shop = getattr(outbound, "shop_id", None)
    ob_user = getattr(outbound, "user_id", None)
    ob_account = getattr(outbound, "account_id", None)

    if ob_shop is not None and str(ob_shop) != str(shop_id):
        logger.debug(
            "channel outbound shop_id 不匹配: outbound=%s expected=%s",
            ob_shop,
            shop_id,
        )
        return False
    if ob_user is not None and str(ob_user) != str(user_id):
        logger.debug(
            "channel outbound user_id 不匹配: outbound=%s expected=%s",
            format_account_ref(str(ob_user)),
            format_account_ref(user_id),
        )
        return False
    if ob_account is not None and str(ob_account) != str(user_id):
        logger.debug(
            "channel outbound account_id 不匹配: outbound=%s expected=%s",
            format_account_ref(str(ob_account)),
            format_account_ref(user_id),
        )
        return False
    return True


def _is_usable_for_resolution(
    outbound: Any,
    shop_id: str,
    user_id: str,
    platform: str,
) -> bool:
    """PDD 平台沿用旧校验；其它平台用 channel duck type 校验。"""
    if platform == "pinduoduo":
        return _is_usable_pinduoduo_outbound(outbound, shop_id, user_id)
    return _is_usable_channel_outbound(outbound, shop_id, user_id)


def resolve_outbound(
    metadata: Dict[str, Any],
    context: Optional[Context] = None,
) -> Optional[Any]:
    """
    解析出站实例（平台无关入口）。

    顺序：metadata outbound → channel_outbound_registry →
    platform==pinduoduo 时委托 resolve_pinduoduo_outbound；其它平台 None。
    """
    shop_id, user_id, from_uid = get_send_context_for_extract(metadata, context)
    if not all([shop_id, user_id, from_uid]):
        logger.debug(
            "无法解析 unified outbound，缺少字段: %s",
            format_send_context_log(shop_id, user_id, from_uid),
        )
        return None

    assert shop_id is not None and user_id is not None
    platform = infer_platform(metadata, context)

    metadata_outbound = metadata.get("outbound")
    if _is_usable_for_resolution(metadata_outbound, shop_id, user_id, platform):
        return metadata_outbound

    registered = channel_outbound_registry.get(platform, shop_id, user_id)
    if _is_usable_for_resolution(registered, shop_id, user_id, platform):
        return registered

    if platform == "pinduoduo":
        return resolve_pinduoduo_outbound(metadata, context)

    return None

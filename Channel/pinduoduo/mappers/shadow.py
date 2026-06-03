"""
UnifiedMessage shadow 旁路（Phase 7c）。

flag on 时在 WS 处理路径旁路调用 mapper 并打日志；不改变 Context 主路径、不入队。
"""

from __future__ import annotations

from typing import Any

from bridge.context import Context
from Channel.pinduoduo.mappers.pdd_to_unified import compute_pdd_routing, pdd_message_to_unified
from Channel.pinduoduo.mappers.shadow_flags import use_unified_message_shadow
from Channel.pinduoduo.pdd_message import PDDChatMessage
from utils.logger_loguru import get_logger

logger = get_logger("UnifiedShadow")


def _shop_name_from_context(context: Context) -> str:
    kwargs = context.kwargs
    if kwargs is None:
        return ""
    name = getattr(kwargs, "shop_name", None)
    return str(name) if name is not None else ""


def _context_routing(context: Context) -> str:
    return compute_pdd_routing(context.type)


def _log_shadow_ok(unified: Any) -> None:
    conv = unified.conversation
    logger.debug(
        "unified_shadow ok message_id={} content_type={} routing={} "
        "shop_id={} account_id={} buyer_uid={} conversation_id={} mapper=success",
        unified.message_id,
        unified.content_type,
        conv.extra.get("routing", ""),
        conv.shop_id,
        conv.account_id,
        conv.buyer_uid,
        conv.conversation_id,
    )


def _log_shadow_mismatch(
    message_id: str,
    context_type: str,
    unified_type: str,
    context_route: str,
    unified_route: str,
) -> None:
    logger.warning(
        "unified_shadow mismatch message_id={} context_type={} unified_type={} "
        "context_route={} unified_route={}",
        message_id,
        context_type,
        unified_type,
        context_route,
        unified_route,
    )


def maybe_shadow_unified_message(
    pdd: PDDChatMessage,
    context: Context,
    *,
    shop_id: str,
    user_id: str,
    username: str,
) -> None:
    """
    Shadow 旁路：将 PDD 消息映射为 UnifiedMessage 并记录摘要日志。

    flag off 时为 no-op。任何异常在此函数内捕获，不向调用方抛出。
    """
    if not use_unified_message_shadow():
        return

    try:
        unified = pdd_message_to_unified(
            pdd,
            shop_id=shop_id,
            user_id=user_id,
            username=username,
            shop_name=_shop_name_from_context(context),
        )
        _log_shadow_ok(unified)

        context_type = context.type.value
        unified_type = unified.content_type
        context_route = _context_routing(context)
        unified_route = unified.conversation.extra.get("routing", "")

        if context_type != unified_type or context_route != unified_route:
            _log_shadow_mismatch(
                unified.message_id,
                context_type,
                unified_type,
                context_route,
                unified_route,
            )
    except Exception as exc:
        msg_id = getattr(pdd, "msg_id", "") or ""
        logger.warning(
            "unified_shadow failed message_id={} shop_id={} error={} mapper=failure",
            msg_id,
            shop_id,
            exc,
            exc_info=True,
        )

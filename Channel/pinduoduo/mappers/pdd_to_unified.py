"""
拼多多入站消息 → UnifiedMessage（Phase 7b）。

纯映射函数，不接入 WebSocket / put_message / handler_chain。

注意：legacy `_convert_to_context` 会把 dict content 做 json.dumps；
本 mapper 在 UnifiedMessage.content 中保留结构化 dict/list。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from bridge.context import ContextType
from Channel.base.models import UnifiedConversation, UnifiedMessage
from Channel.base.types import PlatformType
from Channel.pinduoduo.pdd_message import PDDChatMessage

# 与 Channel/pinduoduo/core/pdd_message_handler.py 中集合同构（勿改 handler，仅复制语义）
_IMMEDIATE_TYPES = frozenset(
    {
        ContextType.SYSTEM_STATUS,
        ContextType.AUTH,
        ContextType.WITHDRAW,
        ContextType.SYSTEM_HINT,
        ContextType.MALL_CS,
        ContextType.TRANSFER,
    }
)

_QUEUE_TYPES = frozenset(
    {
        ContextType.TEXT,
        ContextType.IMAGE,
        ContextType.VIDEO,
        ContextType.EMOTION,
        ContextType.GOODS_INQUIRY,
        ContextType.ORDER_INFO,
        ContextType.GOODS_CARD,
        ContextType.GOODS_SPEC,
    }
)

Routing = str  # "immediate" | "queue" | "drop"


def compute_pdd_routing(context_type: ContextType) -> Routing:
    """
    计算消息路由，与 MessageHandlerMixin._should_process_immediately /
    _should_queue_message 语义一致。
    """
    if context_type in _IMMEDIATE_TYPES:
        return "immediate"
    if context_type in _QUEUE_TYPES:
        return "queue"
    return "drop"


def _parse_timestamp(pdd: PDDChatMessage) -> Optional[datetime]:
    """从 raw / message.time 解析时间戳。"""
    raw = pdd.raw_data if isinstance(pdd.raw_data, dict) else {}
    time_val = None
    if isinstance(raw, dict):
        msg_block = raw.get("message")
        if isinstance(msg_block, dict):
            time_val = msg_block.get("time")
    if time_val is None and pdd.timestamp is not None:
        time_val = pdd.timestamp
    if time_val is None:
        return None
    if isinstance(time_val, (int, float)):
        try:
            return datetime.fromtimestamp(float(time_val), tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None
    if isinstance(time_val, str):
        try:
            return datetime.fromisoformat(time_val.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _str_or_empty(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def pdd_message_to_unified(
    pdd: PDDChatMessage,
    *,
    shop_id: str,
    user_id: str,
    username: str,
    shop_name: str = "",
) -> UnifiedMessage:
    """
    将 PDDChatMessage 转为 UnifiedMessage。

    Args:
        pdd: 已解析的拼多多消息对象
        shop_id: 店铺 ID
        user_id: 卖家子账号（客服账号）ID
        username: 卖家子账号用户名
        shop_name: 店铺名称（可选）
    """
    user_msg_type = pdd.user_msg_type
    if user_msg_type is None:
        user_msg_type = ContextType.SYSTEM_STATUS

    content_type = user_msg_type.value
    routing = compute_pdd_routing(user_msg_type)

    buyer_uid = _str_or_empty(pdd.from_uid)
    conversation = UnifiedConversation(
        platform=PlatformType.PINDUODUO,
        conversation_id=buyer_uid,
        shop_id=_str_or_empty(shop_id),
        account_id=_str_or_empty(user_id),
        buyer_uid=buyer_uid,
        buyer_nickname=pdd.nickname,
        extra={
            "username": username,
            "shop_name": shop_name,
            "from_user": pdd.from_user,
            "to_user": pdd.to_user,
            "to_uid": pdd.to_uid,
            "msg_id": pdd.msg_id,
            "routing": routing,
        },
    )

    raw: dict[str, Any] = {}
    if isinstance(pdd.raw_data, dict):
        raw = pdd.raw_data
    elif isinstance(getattr(pdd, "msg", None), dict):
        raw = pdd.msg

    return UnifiedMessage(
        platform=PlatformType.PINDUODUO,
        message_id=_str_or_empty(pdd.msg_id),
        conversation=conversation,
        direction="inbound",
        content_type=content_type,
        content=pdd.content,
        timestamp=_parse_timestamp(pdd),
        raw=raw,
    )

"""
Handler 出站解析：从 metadata / context 创建 PinduoduoOutbound（Phase 2b）。

仅负责解析与工厂创建，不发送消息、不转人工。
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from bridge.context import Context
from Channel.pinduoduo.outbound_factory import create_pinduoduo_outbound
from Channel.pinduoduo.outbound_flags import use_pinduoduo_outbound
from Channel.pinduoduo.pinduoduo_outbound import PinduoduoOutbound
from utils.logger_loguru import get_logger

logger = get_logger("OutboundResolver")


def _read_kwarg(kwargs: Any, key: str) -> Any:
    if kwargs is None:
        return None
    value = getattr(kwargs, key, None)
    if value is not None:
        return value
    if isinstance(kwargs, dict):
        return kwargs.get(key)
    return None


def extract_pdd_send_context(
    metadata: Dict[str, Any],
    context: Optional[Context] = None,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """从 metadata 优先、context.kwargs 补充，返回 (shop_id, user_id, from_uid)。"""
    shop_id = metadata.get("shop_id")
    user_id = metadata.get("user_id")
    from_uid = metadata.get("from_uid")

    if context is not None:
        kwargs = getattr(context, "kwargs", None)
        if shop_id is None:
            shop_id = _read_kwarg(kwargs, "shop_id")
        if user_id is None:
            user_id = _read_kwarg(kwargs, "user_id")
        if from_uid is None:
            from_uid = _read_kwarg(kwargs, "from_uid")

    if shop_id is not None:
        shop_id = str(shop_id)
    if user_id is not None:
        user_id = str(user_id)
    if from_uid is not None:
        from_uid = str(from_uid)

    return shop_id, user_id, from_uid


def resolve_pinduoduo_outbound(
    metadata: Dict[str, Any],
    context: Optional[Context] = None,
) -> Optional[PinduoduoOutbound]:
    """开关开启且三元组齐全时创建 outbound；否则返回 None。"""
    if not use_pinduoduo_outbound():
        return None

    shop_id, user_id, from_uid = extract_pdd_send_context(metadata, context)
    if not all([shop_id, user_id, from_uid]):
        logger.debug(
            f"无法创建 outbound，缺少字段: shop_id={shop_id}, user_id={user_id}, from_uid={from_uid}"
        )
        return None

    try:
        return create_pinduoduo_outbound(shop_id, user_id)
    except ValueError as e:
        logger.warning(f"创建 PinduoduoOutbound 失败 (ValueError): {e}")
        return None
    except Exception as e:
        logger.warning(f"创建 PinduoduoOutbound 失败: {e}")
        return None

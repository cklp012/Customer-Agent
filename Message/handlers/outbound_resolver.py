"""
Handler 出站解析：从 metadata / registry / factory 获取 PinduoduoOutbound（Phase 2b+）。

仅负责解析，不发送消息、不转人工。
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from bridge.context import Context
from Channel.pinduoduo.outbound_factory import create_pinduoduo_outbound
from Channel.pinduoduo.outbound_flags import use_pinduoduo_outbound
from Channel.pinduoduo.pinduoduo_outbound import PinduoduoOutbound
from Message.handlers.account_outbound_registry import get as get_registered_outbound
from Message.metadata_adapter import get_send_context_for_extract
from utils.logger_loguru import get_logger

logger = get_logger("OutboundResolver")


def extract_pdd_send_context(
    metadata: Dict[str, Any],
    context: Optional[Context] = None,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """从 metadata 优先、context.kwargs 补充，返回 (shop_id, user_id, from_uid)。"""
    return get_send_context_for_extract(metadata, context)


def _is_usable_pinduoduo_outbound(
    outbound: Any,
    shop_id: str,
    user_id: str,
) -> bool:
    """校验 outbound 是否可用于当前账号。"""
    if outbound is None:
        return False
    if not callable(getattr(outbound, "send_text", None)):
        logger.debug("outbound 缺少 send_text，不可用")
        return False
    if not callable(getattr(outbound, "transfer_to_human", None)):
        logger.debug("outbound 缺少 transfer_to_human，不可用")
        return False
    ob_shop = getattr(outbound, "shop_id", None)
    ob_user = getattr(outbound, "user_id", None)
    if ob_shop is None or ob_user is None:
        logger.debug("outbound 缺少 shop_id/user_id 属性，不可用")
        return False
    if str(ob_shop) != str(shop_id) or str(ob_user) != str(user_id):
        logger.debug(
            f"outbound 账号不匹配: outbound=({ob_shop},{ob_user}) "
            f"expected=({shop_id},{user_id})"
        )
        return False
    return True


def resolve_pinduoduo_outbound(
    metadata: Dict[str, Any],
    context: Optional[Context] = None,
) -> Optional[PinduoduoOutbound]:
    """
    解析出站实例。

    flag off → None。
    flag on → metadata outbound → registry → create_pinduoduo_outbound。
    """
    if not use_pinduoduo_outbound():
        return None

    shop_id, user_id, from_uid = extract_pdd_send_context(metadata, context)
    if not all([shop_id, user_id, from_uid]):
        logger.debug(
            f"无法解析 outbound，缺少字段: shop_id={shop_id}, user_id={user_id}, from_uid={from_uid}"
        )
        return None

    assert shop_id is not None and user_id is not None

    metadata_outbound = metadata.get("outbound")
    if _is_usable_pinduoduo_outbound(metadata_outbound, shop_id, user_id):
        return metadata_outbound

    registered = get_registered_outbound(shop_id, user_id)
    if _is_usable_pinduoduo_outbound(registered, shop_id, user_id):
        return registered

    try:
        return create_pinduoduo_outbound(shop_id, user_id)
    except ValueError as e:
        logger.warning(f"创建 PinduoduoOutbound 失败 (ValueError): {e}")
        return None
    except Exception as e:
        logger.warning(f"创建 PinduoduoOutbound 失败: {e}")
        return None

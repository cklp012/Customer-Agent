"""
统一入站入队 helper（Phase 8a）。

封装 put_message + USE_UNIFIED_MESSAGE_DUAL_TRACK；PDD 调用点不在此模块修改。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from bridge.context import Context
from Channel.pinduoduo.mappers.dual_track_flags import use_unified_message_dual_track

if TYPE_CHECKING:
    from Channel.base.models import UnifiedMessage

_INBOUND_EXTRA_METADATA_ATTR = "_inbound_extra_metadata"


async def enqueue_inbound_message(
    queue_name: str,
    context: Context,
    *,
    unified_message: Optional["UnifiedMessage"] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    将 Context（及可选 UnifiedMessage）放入指定队列。

    仅当 USE_UNIFIED_MESSAGE_DUAL_TRACK 为真且 unified_message 非空时附带双轨副本。

    extra_metadata：测试或调用方注入（如 metadata[\"outbound\"]），由 MessageWrapper.to_metadata 合并。
    """
    from Message import put_message

    if extra_metadata:
        setattr(context, _INBOUND_EXTRA_METADATA_ATTR, dict(extra_metadata))

    track_unified = None
    if use_unified_message_dual_track() and unified_message is not None:
        track_unified = unified_message
    return await put_message(queue_name, context, unified_message=track_unified)

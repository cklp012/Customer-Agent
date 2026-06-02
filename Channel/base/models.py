"""
跨平台统一消息模型（Phase 1 骨架）。

不与现有 Context 互转；转换逻辑在 Phase 2 Pinduoduo mapper 中实现。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from Channel.base.types import PlatformType


@dataclass
class UnifiedConversation:
    """统一会话标识"""

    platform: PlatformType
    conversation_id: str
    shop_id: str
    account_id: str
    buyer_uid: str
    buyer_nickname: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedMessage:
    """平台入站消息（Adapter 产出）"""

    platform: PlatformType
    message_id: str
    conversation: UnifiedConversation
    direction: str  # "inbound" | "outbound"
    content_type: str
    content: Any
    timestamp: Optional[datetime] = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedReply:
    """平台出站回复（Handler / Agent 产出，由 Outbound 发送）"""

    content_type: str
    content: Any
    goods_id: Optional[int] = None
    transfer_to_human: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

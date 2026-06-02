"""
多平台 Channel 抽象层（Phase 1）。

现有业务代码不应 import 本包，直至 Phase 2 接入。
"""

from Channel.base.channel import BaseChannel
from Channel.base.models import UnifiedConversation, UnifiedMessage, UnifiedReply
from Channel.base.outbound import ChannelOutbound
from Channel.base.registry import ChannelRegistry
from Channel.base.types import ChannelStatus, PlatformType

__all__ = [
    "BaseChannel",
    "ChannelOutbound",
    "ChannelRegistry",
    "ChannelStatus",
    "PlatformType",
    "UnifiedConversation",
    "UnifiedMessage",
    "UnifiedReply",
]

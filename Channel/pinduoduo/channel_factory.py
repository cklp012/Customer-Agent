"""PinduoduoChannel 工厂与 AutoReply 运行时切换（Phase 3a/3b）。"""

from __future__ import annotations

from typing import Any, Union

from Channel.base.channel import OnFailureCallback, OnSuccessCallback
from Channel.base.registry import ChannelRegistry
from Channel.base.types import PlatformType
from Channel.pinduoduo.channel_flags import use_pinduoduo_channel_wrapper
from Channel.pinduoduo.pdd_channel import PDDChannel
from Channel.pinduoduo.pinduoduo_channel import PinduoduoChannel

AutoReplyRuntimeChannel = Union[PinduoduoChannel, PDDChannel]


def _noop_on_message(*_args: Any, **_kwargs: Any) -> None:
    """PDD 为推送型；on_message 占位，供 Phase 4+ UnifiedMessage 使用。"""
    return None


def create_pinduoduo_channel(**kwargs: Any) -> PinduoduoChannel:
    """创建 PinduoduoChannel 实例。"""
    return PinduoduoChannel(**kwargs)


def create_auto_reply_runtime_channel(**kwargs: Any) -> AutoReplyRuntimeChannel:
    """按 USE_PINDUODUO_CHANNEL_WRAPPER 创建 AutoReply 运行时 Channel。"""
    if use_pinduoduo_channel_wrapper():
        return create_pinduoduo_channel(**kwargs)
    return PDDChannel(**kwargs)


async def start_auto_reply_account(
    channel: AutoReplyRuntimeChannel,
    shop_id: str,
    user_id: str,
    on_success: OnSuccessCallback,
    on_failure: OnFailureCallback,
) -> None:
    """统一启动签名：wrapper 传 noop on_message，legacy 保持原参数。"""
    if isinstance(channel, PinduoduoChannel):
        await channel.start_account(
            shop_id,
            user_id,
            _noop_on_message,
            on_success,
            on_failure,
        )
    else:
        await channel.start_account(shop_id, user_id, on_success, on_failure)


def register_pinduoduo_channel() -> None:
    """向 ChannelRegistry 注册拼多多工厂（由测试或显式 bootstrap 调用）。"""
    ChannelRegistry.register(PlatformType.PINDUODUO, create_pinduoduo_channel)

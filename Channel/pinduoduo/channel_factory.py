"""PinduoduoChannel 工厂与 AutoReply 运行时切换（Phase 3a/3b，9a Registry 门控）。"""

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


def _create_auto_reply_legacy(**kwargs: Any) -> AutoReplyRuntimeChannel:
    """按 USE_PINDUODUO_CHANNEL_WRAPPER 创建（Phase 3b 原逻辑）。"""
    if use_pinduoduo_channel_wrapper():
        return create_pinduoduo_channel(**kwargs)
    return PDDChannel(**kwargs)


def _warn_registry_fallback(reason: str, *, exc: BaseException | None = None) -> None:
    from utils.logger_loguru import get_logger

    logger = get_logger("AutoReplyChannelFactory")
    if exc is not None:
        logger.warning(
            "ChannelRegistry.create fallback for AutoReply: %s",
            reason,
            exc_info=True,
        )
    else:
        logger.warning("ChannelRegistry.create fallback for AutoReply: %s", reason)


def create_auto_reply_runtime_channel(**kwargs: Any) -> AutoReplyRuntimeChannel:
    """
    创建 AutoReply 运行时 Channel。

    USE_CHANNEL_REGISTRY_FOR_AUTOREPLY 默认 false；为 true 且 wrapper 为 true 且
    PINDUODUO 已注册时尝试 ChannelRegistry.create，失败则 fallback 旧 wrapper 路径。
    """
    from Message.autoreply_registry_flags import use_channel_registry_for_autoreply

    if not use_channel_registry_for_autoreply():
        return _create_auto_reply_legacy(**kwargs)

    if not use_pinduoduo_channel_wrapper():
        return PDDChannel(**kwargs)

    if not ChannelRegistry.is_registered(PlatformType.PINDUODUO):
        _warn_registry_fallback("PlatformType.PINDUODUO not registered")
        return create_pinduoduo_channel(**kwargs)

    try:
        channel = ChannelRegistry.create(PlatformType.PINDUODUO, **kwargs)
    except Exception as exc:
        _warn_registry_fallback("ChannelRegistry.create raised", exc=exc)
        return create_pinduoduo_channel(**kwargs)

    if not isinstance(channel, PinduoduoChannel):
        _warn_registry_fallback(
            f"unexpected channel type {type(channel)!r}, expected PinduoduoChannel"
        )
        return create_pinduoduo_channel(**kwargs)

    return channel


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

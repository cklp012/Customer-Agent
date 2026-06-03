"""PinduoduoChannel 工厂与 AutoReply 运行时切换（Phase 3a/3b，9a/9b Registry）。"""

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
    """创建 PinduoduoChannel 实例（wrapper-only，不经 wrapper flag）。"""
    return PinduoduoChannel(**kwargs)


def _create_auto_reply_legacy(**kwargs: Any) -> AutoReplyRuntimeChannel:
    """按 USE_PINDUODUO_CHANNEL_WRAPPER 创建（Phase 3b 原逻辑）。"""
    if use_pinduoduo_channel_wrapper():
        return create_pinduoduo_channel(**kwargs)
    return PDDChannel(**kwargs)


def create_pinduoduo_registry_channel(**kwargs: Any) -> AutoReplyRuntimeChannel:
    """
    ChannelRegistry 注册工厂（Phase 9b parity）。

    只调用 _create_auto_reply_legacy；禁止再入 create_auto_reply_runtime_channel
    或 ChannelRegistry.create。
    """
    return _create_auto_reply_legacy(**kwargs)


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

    USE_CHANNEL_REGISTRY_FOR_AUTOREPLY 默认 false；为 true 且 PINDUODUO 已注册时
    尝试 ChannelRegistry.create，失败则 fallback _create_auto_reply_legacy。
    """
    from Message.autoreply_registry_flags import use_channel_registry_for_autoreply

    if not use_channel_registry_for_autoreply():
        return _create_auto_reply_legacy(**kwargs)

    if not ChannelRegistry.is_registered(PlatformType.PINDUODUO):
        _warn_registry_fallback("PlatformType.PINDUODUO not registered")
        return _create_auto_reply_legacy(**kwargs)

    try:
        channel = ChannelRegistry.create(PlatformType.PINDUODUO, **kwargs)
    except Exception as exc:
        _warn_registry_fallback("ChannelRegistry.create raised", exc=exc)
        return _create_auto_reply_legacy(**kwargs)

    if channel is None:
        _warn_registry_fallback("ChannelRegistry.create returned None")
        return _create_auto_reply_legacy(**kwargs)

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
    """向 ChannelRegistry 注册拼多多 parity 工厂（Phase 9b）。"""
    ChannelRegistry.register(PlatformType.PINDUODUO, create_pinduoduo_registry_channel)

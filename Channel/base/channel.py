"""
多平台 Channel 抽象基类（Phase 1 骨架）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from Channel.base.outbound import ChannelOutbound
from Channel.base.types import ChannelStatus, PlatformType

# 入站消息回调：Adapter 收到消息后交给上层（Message 队列等）
OnMessageCallback = Callable[..., Any]
OnSuccessCallback = Callable[[], None]
OnFailureCallback = Callable[[str], None]


class BaseChannel(ABC):
    """
    电商平台客服 Channel 抽象。

    子类负责 login、连接、收消息；出站统一通过 outbound。
    """

    platform: PlatformType

    @property
    @abstractmethod
    def outbound(self) -> ChannelOutbound:
        """平台出站能力实现"""
        ...

    @abstractmethod
    async def login(
        self,
        shop_id: str,
        account_id: str,
        credentials: dict[str, Any],
    ) -> bool:
        """登录并持久化会话（如 cookies）。"""
        ...

    @abstractmethod
    async def logout(self, shop_id: str, account_id: str) -> None:
        """登出并清理会话。"""
        ...

    @abstractmethod
    def get_status(self, shop_id: str, account_id: str) -> ChannelStatus:
        """当前连接/登录状态。"""
        ...

    @abstractmethod
    async def start_account(
        self,
        shop_id: str,
        account_id: str,
        on_message: OnMessageCallback,
        on_success: OnSuccessCallback,
        on_failure: OnFailureCallback,
    ) -> None:
        """启动指定店铺账号的消息监听（WebSocket / 轮询等）。"""
        ...

    @abstractmethod
    async def stop_account(self, shop_id: str, account_id: str) -> None:
        """停止指定店铺账号。"""
        ...

    @abstractmethod
    async def reconnect(self, shop_id: str, account_id: str) -> None:
        """主动触发重连。"""
        ...

    async def receive_message(self) -> Optional[Any]:
        """
        拉取单条消息（可选）。

        推送型平台（如 PDD WebSocket）可返回 None，由内部回调驱动。
        """
        return None

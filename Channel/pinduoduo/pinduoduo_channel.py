"""
拼多多 Channel — BaseChannel 包装层（Phase 3a Strangler）。

内部委托 legacy PDDChannel，不重写 WebSocket / 队列 / 消息解析。
"""

from __future__ import annotations

from typing import Any, Optional

from Channel.base.channel import (
    BaseChannel,
    OnFailureCallback,
    OnMessageCallback,
    OnSuccessCallback,
)
from Channel.base.types import ChannelStatus, PlatformType
from Channel.pinduoduo.outbound_factory import create_pinduoduo_outbound
from Channel.pinduoduo.pdd_channel import PDDChannel
from Channel.pinduoduo.pinduoduo_outbound import PinduoduoOutbound
from core.connection_status import ConnectionState
from utils.logger_loguru import get_logger

logger = get_logger("PinduoduoChannel")

_CONNECTION_STATE_TO_CHANNEL_STATUS: dict[ConnectionState, ChannelStatus] = {
    ConnectionState.DISCONNECTED: ChannelStatus.DISCONNECTED,
    ConnectionState.CONNECTING: ChannelStatus.CONNECTING,
    ConnectionState.CONNECTED: ChannelStatus.CONNECTED,
    ConnectionState.RECONNECTING: ChannelStatus.RECONNECTING,
    ConnectionState.ERROR: ChannelStatus.ERROR,
}


class PinduoduoChannel(BaseChannel):
    """拼多多 BaseChannel 实现，委托 legacy PDDChannel。"""

    platform = PlatformType.PINDUODUO

    def __init__(self, legacy: Optional[PDDChannel] = None, **legacy_kwargs: Any) -> None:
        self._legacy = legacy if legacy is not None else PDDChannel(**legacy_kwargs)
        self._shop_id: Optional[str] = None
        self._account_id: Optional[str] = None
        self._outbound: Optional[PinduoduoOutbound] = None
        self._on_message: Optional[OnMessageCallback] = None
        self._on_success: Optional[OnSuccessCallback] = None
        self._on_failure: Optional[OnFailureCallback] = None

    @property
    def legacy(self) -> PDDChannel:
        """底层 PDDChannel（WebSocket / 队列 / 生命周期）。"""
        return self._legacy

    @property
    def outbound(self) -> PinduoduoOutbound:
        """当前账号出站适配器；须先 start_account。"""
        if self._shop_id is None or self._account_id is None:
            raise RuntimeError(
                "outbound 在 start_account 之前不可用；请先调用 start_account(shop_id, account_id, ...)"
            )
        if self._outbound is None:
            self._outbound = create_pinduoduo_outbound(self._shop_id, self._account_id)
        return self._outbound

    def request_stop(self) -> None:
        """请求停止 WebSocket（透传 legacy）。"""
        self._legacy.request_stop()

    async def login(
        self,
        shop_id: str,
        account_id: str,
        credentials: dict[str, Any],
    ) -> bool:
        """登录（薄封装 pdd_login.login_pdd，不修改 pdd_login.py）。"""
        del shop_id, account_id
        username = credentials.get("username") or credentials.get("name")
        password = credentials.get("password")
        if not username or not password:
            logger.warning("login 缺少 username/password")
            return False

        headless = bool(credentials.get("headless", False))
        try:
            from Channel.pinduoduo.pdd_login import login_pdd

            result = await login_pdd(username, password, headless=headless)
            if result and isinstance(result, dict):
                return True
            return False
        except Exception as e:
            logger.error(f"login 失败: {e}")
            return False

    async def logout(self, shop_id: str, account_id: str) -> None:
        """登出：停止账号连接（无平台登出 API）。"""
        await self.stop_account(shop_id, account_id)

    def get_status(self, shop_id: str, account_id: str) -> ChannelStatus:
        """查询连接状态（ConnectionState → ChannelStatus）。"""
        status = self._legacy.status_manager.get_status(shop_id, account_id)
        if status is None:
            return ChannelStatus.DISCONNECTED
        return _CONNECTION_STATE_TO_CHANNEL_STATUS.get(
            status.state,
            ChannelStatus.DISCONNECTED,
        )

    async def start_account(
        self,
        shop_id: str,
        account_id: str,
        on_message: OnMessageCallback,
        on_success: OnSuccessCallback,
        on_failure: OnFailureCallback,
    ) -> None:
        """启动账号监听（委托 legacy；on_message Phase 3a 仅保存）。"""
        self._shop_id = str(shop_id)
        self._account_id = str(account_id)
        self._on_message = on_message
        self._on_success = on_success
        self._on_failure = on_failure
        self._outbound = None

        await self._legacy.start_account(
            self._shop_id,
            self._account_id,
            on_success,
            on_failure,
        )

    async def stop_account(self, shop_id: str, account_id: str) -> None:
        """停止账号（委托 legacy）。"""
        await self._legacy.stop_account(shop_id, account_id)
        if str(shop_id) == self._shop_id and str(account_id) == self._account_id:
            self._outbound = None

    async def reconnect(self, shop_id: str, account_id: str) -> None:
        """主动重连：stop 后使用已保存回调再 start。"""
        if self._on_success is None or self._on_failure is None:
            raise RuntimeError("reconnect 需要先成功调用过 start_account")

        on_message = self._on_message
        if on_message is None:
            raise RuntimeError("reconnect 缺少 on_message 回调")

        await self.stop_account(shop_id, account_id)
        await self.start_account(
            shop_id,
            account_id,
            on_message,
            self._on_success,
            self._on_failure,
        )

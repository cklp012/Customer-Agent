"""
抖店 mock Channel（Phase 11b）。

BaseChannel 内存实现；不联网、不启动线程、不调真实 API。
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
from Channel.doudian.doudian_outbound import DoudianMockOutbound


class DoudianMockChannel(BaseChannel):
    """抖店 mock Channel，仅内存状态机（非 production）。"""

    platform = PlatformType.DOUDIAN

    def __init__(self, **kwargs: Any) -> None:
        del kwargs
        self._shop_id: Optional[str] = None
        self._account_id: Optional[str] = None
        self._status: ChannelStatus = ChannelStatus.DISCONNECTED
        self._outbound: Optional[DoudianMockOutbound] = None
        self._on_message: Optional[OnMessageCallback] = None
        self._on_success: Optional[OnSuccessCallback] = None
        self._on_failure: Optional[OnFailureCallback] = None

    @property
    def outbound(self) -> DoudianMockOutbound:
        if self._shop_id is None or self._account_id is None:
            raise RuntimeError(
                "outbound 在 start_account 之前不可用；请先调用 start_account(shop_id, account_id, ...)"
            )
        if self._outbound is None:
            self._outbound = DoudianMockOutbound(self._shop_id, self._account_id)
        return self._outbound

    async def login(
        self,
        shop_id: str,
        account_id: str,
        credentials: dict[str, Any],
    ) -> bool:
        del shop_id, account_id, credentials
        return True

    async def logout(self, shop_id: str, account_id: str) -> None:
        await self.stop_account(shop_id, account_id)

    def get_status(self, shop_id: str, account_id: str) -> ChannelStatus:
        if (
            self._shop_id is not None
            and self._account_id is not None
            and str(shop_id) == self._shop_id
            and str(account_id) == self._account_id
        ):
            return self._status
        return ChannelStatus.DISCONNECTED

    async def start_account(
        self,
        shop_id: str,
        account_id: str,
        on_message: OnMessageCallback,
        on_success: OnSuccessCallback,
        on_failure: OnFailureCallback,
    ) -> None:
        del on_failure, on_message
        self._shop_id = str(shop_id)
        self._account_id = str(account_id)
        self._on_success = on_success
        self._outbound = None
        self._status = ChannelStatus.CONNECTING

        self._outbound = DoudianMockOutbound(self._shop_id, self._account_id)
        self._status = ChannelStatus.CONNECTED
        on_success()

    async def stop_account(self, shop_id: str, account_id: str) -> None:
        if (
            self._shop_id is not None
            and self._account_id is not None
            and str(shop_id) == self._shop_id
            and str(account_id) == self._account_id
        ):
            self._status = ChannelStatus.DISCONNECTED
            self._outbound = None

    async def reconnect(self, shop_id: str, account_id: str) -> None:
        if self._on_success is None:
            raise RuntimeError("reconnect 需要先成功调用过 start_account")
        on_message = self._on_message
        if on_message is None:
            on_message = lambda *_a, **_k: None
        await self.stop_account(shop_id, account_id)
        await self.start_account(
            shop_id,
            account_id,
            on_message,
            self._on_success,
            lambda _msg: None,
        )


__all__ = ["DoudianMockChannel"]

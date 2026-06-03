"""
Demo 平台 Channel（Phase 6b）。

BaseChannel 内存实现，用于多平台 Registry / 契约验证；不联网、不登录真实平台。
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
from Channel.demo.demo_outbound import DemoOutbound

_SYNTHETIC_INBOUND: dict[str, Any] = {
    "platform": "demo",
    "message_id": "demo-msg-1",
    "content_type": "text",
    "content": "synthetic inbound (test only)",
}


class DemoChannel(BaseChannel):
    """假电商平台 Channel，仅内存状态机。"""

    platform = PlatformType.DEMO

    def __init__(
        self,
        *,
        inject_synthetic_message_on_start: bool = False,
        inject_runtime_flow: bool = False,
        runtime_queue_name: Optional[str] = None,
    ) -> None:
        self._inject_synthetic_message_on_start = inject_synthetic_message_on_start
        self._inject_runtime_flow = inject_runtime_flow
        self._runtime_queue_name = runtime_queue_name
        self._shop_id: Optional[str] = None
        self._account_id: Optional[str] = None
        self._status: ChannelStatus = ChannelStatus.DISCONNECTED
        self._outbound: Optional[DemoOutbound] = None
        self._on_message: Optional[OnMessageCallback] = None
        self._on_success: Optional[OnSuccessCallback] = None
        self._on_failure: Optional[OnFailureCallback] = None

    @property
    def outbound(self) -> DemoOutbound:
        if self._shop_id is None or self._account_id is None:
            raise RuntimeError(
                "outbound 在 start_account 之前不可用；请先调用 start_account(shop_id, account_id, ...)"
            )
        if self._outbound is None:
            self._outbound = DemoOutbound(self._shop_id, self._account_id)
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
        self._shop_id = str(shop_id)
        self._account_id = str(account_id)
        self._on_message = on_message
        self._on_success = on_success
        self._on_failure = on_failure
        self._outbound = None
        self._status = ChannelStatus.CONNECTING

        self._outbound = DemoOutbound(self._shop_id, self._account_id)
        self._status = ChannelStatus.CONNECTED

        on_success()

        if self._inject_runtime_flow:
            if not self._runtime_queue_name:
                raise RuntimeError(
                    "inject_runtime_flow=True 需要 runtime_queue_name（仅测试用）"
                )
            from Channel.demo.demo_inbound import enqueue_demo_message

            await enqueue_demo_message(
                _SYNTHETIC_INBOUND,
                self._shop_id,
                self._account_id,
                self._runtime_queue_name,
            )
        elif self._inject_synthetic_message_on_start and self._on_message is not None:
            self._on_message(_SYNTHETIC_INBOUND)

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

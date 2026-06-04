"""Phase 11e：DoudianMockChannel outbound 生命周期 + channel_outbound_registry。"""

from __future__ import annotations

import asyncio
import os
import unittest
from unittest.mock import patch

from Channel.base.types import ChannelStatus, PlatformType
from Channel.doudian.doudian_channel import DoudianMockChannel
from Message.handlers import channel_outbound_registry
from Message.handlers.unified_outbound_resolver import resolve_outbound

_SHOP = "DD_SHOP_001"
_ACCOUNT = "DD_ACC_001"
_BUYER = "DD_BUYER_001"


def _doudian_meta(**extra: object) -> dict:
    base = {
        "platform": "doudian",
        "shop_id": _SHOP,
        "user_id": _ACCOUNT,
        "from_uid": _BUYER,
    }
    base.update(extra)
    return base


def _noop_success() -> None:
    return None


class _LifecycleTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self._unified_flag_backup = os.environ.get("USE_UNIFIED_OUTBOUND_RESOLVER")

    def tearDown(self) -> None:
        channel_outbound_registry.clear()
        if self._unified_flag_backup is None:
            os.environ.pop("USE_UNIFIED_OUTBOUND_RESOLVER", None)
        else:
            os.environ["USE_UNIFIED_OUTBOUND_RESOLVER"] = self._unified_flag_backup

    @staticmethod
    async def _start(channel: DoudianMockChannel) -> None:
        await channel.start_account(
            _SHOP,
            _ACCOUNT,
            lambda *_a, **_k: None,
            _noop_success,
            lambda _msg: None,
        )

    @staticmethod
    async def _stop(channel: DoudianMockChannel) -> None:
        await channel.stop_account(_SHOP, _ACCOUNT)


class TestDoudianChannelOutboundLifecycle(_LifecycleTestBase):
    def test_l1_start_registers_outbound(self) -> None:
        channel = DoudianMockChannel()

        asyncio.run(self._start(channel))

        registered = channel_outbound_registry.get(
            PlatformType.DOUDIAN,
            _SHOP,
            _ACCOUNT,
        )
        self.assertIs(registered, channel.outbound)
        self.assertEqual(channel.get_status(_SHOP, _ACCOUNT), ChannelStatus.CONNECTED)

    def test_l2_stop_unregisters_outbound(self) -> None:
        channel = DoudianMockChannel()

        async def run() -> None:
            await self._start(channel)
            await self._stop(channel)

        asyncio.run(run())

        self.assertIsNone(
            channel_outbound_registry.get(PlatformType.DOUDIAN, _SHOP, _ACCOUNT)
        )
        self.assertIsNone(channel._outbound)
        self.assertEqual(channel.get_status(_SHOP, _ACCOUNT), ChannelStatus.DISCONNECTED)

    def test_l3_stop_start_reregisters_outbound(self) -> None:
        channel = DoudianMockChannel()
        first_outbound: object | None = None

        async def run() -> None:
            nonlocal first_outbound
            await self._start(channel)
            first_outbound = channel.outbound
            await self._stop(channel)
            self.assertIsNone(
                channel_outbound_registry.get(PlatformType.DOUDIAN, _SHOP, _ACCOUNT)
            )
            await self._start(channel)

        asyncio.run(run())

        second = channel_outbound_registry.get(PlatformType.DOUDIAN, _SHOP, _ACCOUNT)
        self.assertIsNotNone(second)
        self.assertIs(second, channel.outbound)
        self.assertIsNot(first_outbound, second)
        self.assertEqual(channel.get_status(_SHOP, _ACCOUNT), ChannelStatus.CONNECTED)

    def test_l4_resolve_outbound_hits_after_start_without_manual_register(self) -> None:
        channel = DoudianMockChannel()
        asyncio.run(self._start(channel))

        resolved = resolve_outbound(_doudian_meta())
        self.assertIs(resolved, channel.outbound)

    def test_l5_resolve_outbound_misses_after_stop(self) -> None:
        channel = DoudianMockChannel()

        async def run() -> None:
            await self._start(channel)
            await self._stop(channel)

        asyncio.run(run())

        self.assertIsNone(resolve_outbound(_doudian_meta()))

    def test_l6_pdd_paths_unaffected(self) -> None:
        os.environ.pop("USE_UNIFIED_OUTBOUND_RESOLVER", None)
        channel = DoudianMockChannel()
        asyncio.run(self._start(channel))

        self.assertIsNone(
            channel_outbound_registry.get(PlatformType.PINDUODUO, _SHOP, _ACCOUNT)
        )
        self.assertIsNone(
            channel_outbound_registry.get("pinduoduo", _SHOP, _ACCOUNT)
        )

        with patch(
            "Message.handlers.unified_outbound_resolver.resolve_pinduoduo_outbound"
        ) as pdd_mock:
            resolved = resolve_outbound(_doudian_meta())
            pdd_mock.assert_not_called()

        self.assertIs(resolved, channel.outbound)


class TestDoudianChannelStopUnregisterSemantics(_LifecycleTestBase):
    def test_stop_always_unregisters_passed_key_even_if_channel_mismatch(self) -> None:
        """对齐 PDD：stop 对传入 shop/account 始终 unregister；内部状态仅匹配时清理。"""
        channel = DoudianMockChannel()
        other_shop = "DD_SHOP_OTHER"
        other_account = "DD_ACC_OTHER"

        async def run() -> None:
            await channel.start_account(
                other_shop,
                other_account,
                lambda *_a, **_k: None,
                _noop_success,
                lambda _msg: None,
            )
            self.assertIsNotNone(
                channel_outbound_registry.get(
                    PlatformType.DOUDIAN,
                    other_shop,
                    other_account,
                )
            )
            await channel.stop_account(_SHOP, _ACCOUNT)

        asyncio.run(run())

        self.assertIsNotNone(
            channel_outbound_registry.get(
                PlatformType.DOUDIAN,
                other_shop,
                other_account,
            )
        )
        await_stop_clears_wrong_key = channel_outbound_registry.get(
            PlatformType.DOUDIAN,
            _SHOP,
            _ACCOUNT,
        )
        self.assertIsNone(await_stop_clears_wrong_key)

    def test_reconnect_reregisters_outbound(self) -> None:
        channel = DoudianMockChannel()
        first: object | None = None

        async def run() -> None:
            nonlocal first
            await self._start(channel)
            first = channel.outbound
            await channel.reconnect(_SHOP, _ACCOUNT)

        asyncio.run(run())

        second = channel_outbound_registry.get(PlatformType.DOUDIAN, _SHOP, _ACCOUNT)
        self.assertIsNotNone(second)
        self.assertIs(second, channel.outbound)
        self.assertIsNot(first, second)
        self.assertEqual(channel.get_status(_SHOP, _ACCOUNT), ChannelStatus.CONNECTED)


if __name__ == "__main__":
    unittest.main()

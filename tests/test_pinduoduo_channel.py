"""Phase 3a：PinduoduoChannel 包装层单元测试（mock legacy PDDChannel）。"""

from __future__ import annotations

import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from Channel.base import BaseChannel, ChannelRegistry, ChannelStatus, PlatformType
from Channel.pinduoduo.channel_factory import (
    create_pinduoduo_channel,
    register_pinduoduo_channel,
)
from Channel.pinduoduo.pinduoduo_channel import PinduoduoChannel
from core.connection_status import ConnectionState, ConnectionStatus


class TestPinduoduoChannel(unittest.TestCase):
    def _make_legacy(self) -> MagicMock:
        legacy = MagicMock()
        legacy.start_account = AsyncMock()
        legacy.stop_account = AsyncMock()
        legacy.request_stop = MagicMock()
        legacy.status_manager = MagicMock()
        legacy.status_manager.get_status.return_value = None
        return legacy

    def test_is_base_channel(self) -> None:
        channel = PinduoduoChannel(legacy=self._make_legacy())
        self.assertIsInstance(channel, BaseChannel)
        self.assertEqual(channel.platform, PlatformType.PINDUODUO)

    def test_outbound_before_start_raises(self) -> None:
        channel = PinduoduoChannel(legacy=self._make_legacy())
        with self.assertRaises(RuntimeError):
            _ = channel.outbound

    def test_start_account_delegates_and_sets_ids(self) -> None:
        legacy = self._make_legacy()
        channel = PinduoduoChannel(legacy=legacy)
        on_message = MagicMock()
        on_success = MagicMock()
        on_failure = MagicMock()

        asyncio.run(
            channel.start_account("s1", "u1", on_message, on_success, on_failure)
        )

        legacy.start_account.assert_awaited_once_with("s1", "u1", on_success, on_failure)
        self.assertEqual(channel._shop_id, "s1")
        self.assertEqual(channel._account_id, "u1")
        self.assertIs(channel._on_message, on_message)

    @patch("Channel.pinduoduo.pinduoduo_channel.create_pinduoduo_outbound")
    def test_outbound_lazy_after_start(self, create_mock: MagicMock) -> None:
        sentinel = MagicMock()
        create_mock.return_value = sentinel
        legacy = self._make_legacy()
        channel = PinduoduoChannel(legacy=legacy)

        asyncio.run(
            channel.start_account("s2", "u2", MagicMock(), MagicMock(), MagicMock())
        )

        self.assertIs(channel.outbound, sentinel)
        create_mock.assert_called_once_with("s2", "u2")
        self.assertIs(channel.outbound, sentinel)
        create_mock.assert_called_once()

    def test_stop_account_delegates_and_clears_outbound(self) -> None:
        legacy = self._make_legacy()
        channel = PinduoduoChannel(legacy=legacy)
        channel._shop_id = "s3"
        channel._account_id = "u3"
        channel._outbound = MagicMock()

        asyncio.run(channel.stop_account("s3", "u3"))

        legacy.stop_account.assert_awaited_once_with("s3", "u3")
        self.assertIsNone(channel._outbound)

    def test_get_status_mapping(self) -> None:
        legacy = self._make_legacy()
        legacy.status_manager.get_status.return_value = ConnectionStatus(
            shop_id="s",
            user_id="u",
            username="n",
            state=ConnectionState.CONNECTED,
        )
        channel = PinduoduoChannel(legacy=legacy)
        self.assertEqual(channel.get_status("s", "u"), ChannelStatus.CONNECTED)

        legacy.status_manager.get_status.return_value = ConnectionStatus(
            shop_id="s",
            user_id="u",
            username="n",
            state=ConnectionState.ERROR,
        )
        self.assertEqual(channel.get_status("s", "u"), ChannelStatus.ERROR)

        legacy.status_manager.get_status.return_value = None
        self.assertEqual(channel.get_status("s", "u"), ChannelStatus.DISCONNECTED)

    def test_reconnect_stop_then_start(self) -> None:
        legacy = self._make_legacy()
        channel = PinduoduoChannel(legacy=legacy)
        on_message = MagicMock()
        on_success = MagicMock()
        on_failure = MagicMock()

        async def run() -> None:
            await channel.start_account("s4", "u4", on_message, on_success, on_failure)
            legacy.start_account.reset_mock()
            legacy.stop_account.reset_mock()
            await channel.reconnect("s4", "u4")

        asyncio.run(run())

        legacy.stop_account.assert_awaited_once_with("s4", "u4")
        self.assertEqual(legacy.start_account.await_count, 1)
        legacy.start_account.assert_awaited_with("s4", "u4", on_success, on_failure)

    def test_request_stop_forwards(self) -> None:
        legacy = self._make_legacy()
        channel = PinduoduoChannel(legacy=legacy)
        channel.request_stop()
        legacy.request_stop.assert_called_once()

    @patch("Channel.pinduoduo.pdd_login.login_pdd", new_callable=AsyncMock)
    def test_login_success(self, login_mock: AsyncMock) -> None:
        login_mock.return_value = {"cookies": {}}
        legacy = self._make_legacy()
        channel = PinduoduoChannel(legacy=legacy)
        ok = asyncio.run(
            channel.login(
                "s",
                "u",
                {"username": "a", "password": "p"},
            )
        )
        self.assertTrue(ok)
        login_mock.assert_awaited_once()

    @patch("Channel.pinduoduo.pdd_login.login_pdd", new_callable=AsyncMock)
    def test_login_failure(self, login_mock: AsyncMock) -> None:
        login_mock.return_value = False
        legacy = self._make_legacy()
        channel = PinduoduoChannel(legacy=legacy)
        ok = asyncio.run(
            channel.login("s", "u", {"username": "a", "password": "p"})
        )
        self.assertFalse(ok)

    def test_logout_calls_stop(self) -> None:
        legacy = self._make_legacy()
        channel = PinduoduoChannel(legacy=legacy)
        asyncio.run(channel.logout("s5", "u5"))
        legacy.stop_account.assert_awaited_once_with("s5", "u5")


class TestChannelFactory(unittest.TestCase):
    def setUp(self) -> None:
        self._wrapper_backup = os.environ.get("USE_PINDUODUO_CHANNEL_WRAPPER")

    def tearDown(self) -> None:
        ChannelRegistry.unregister(PlatformType.PINDUODUO)
        if self._wrapper_backup is None:
            os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        else:
            os.environ["USE_PINDUODUO_CHANNEL_WRAPPER"] = self._wrapper_backup

    @patch("Channel.pinduoduo.channel_factory.create_pinduoduo_channel")
    def test_register_and_create_wrapper_on(self, create_mock: MagicMock) -> None:
        os.environ["USE_PINDUODUO_CHANNEL_WRAPPER"] = "true"
        register_pinduoduo_channel()
        self.assertTrue(ChannelRegistry.is_registered(PlatformType.PINDUODUO))
        wrapper = MagicMock(spec=PinduoduoChannel)
        create_mock.return_value = wrapper
        channel = ChannelRegistry.create(PlatformType.PINDUODUO, legacy=MagicMock())
        self.assertIs(channel, wrapper)
        create_mock.assert_called_once()

    @patch("Channel.pinduoduo.channel_factory.PDDChannel")
    def test_register_and_create_wrapper_off(self, pdd_cls: MagicMock) -> None:
        os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        register_pinduoduo_channel()
        legacy = MagicMock()
        pdd_cls.return_value = legacy
        channel = ChannelRegistry.create(PlatformType.PINDUODUO)
        self.assertIs(channel, legacy)
        pdd_cls.assert_called_once()

    def test_create_factory_function(self) -> None:
        legacy = MagicMock()
        channel = create_pinduoduo_channel(legacy=legacy)
        self.assertIs(channel.legacy, legacy)


if __name__ == "__main__":
    unittest.main()

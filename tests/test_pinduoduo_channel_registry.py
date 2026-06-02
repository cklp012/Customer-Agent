"""Phase 4b：PinduoduoChannel AccountOutboundRegistry 生命周期测试。"""

from __future__ import annotations

import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from Message.handlers.account_outbound_registry import clear, get
from Message.handlers.outbound_resolver import resolve_pinduoduo_outbound
from Channel.pinduoduo.pinduoduo_channel import PinduoduoChannel


class TestPinduoduoChannelRegistry(unittest.TestCase):
    def setUp(self) -> None:
        clear()
        self._env_backup = os.environ.get("USE_PINDUODUO_OUTBOUND")

    def tearDown(self) -> None:
        clear()
        if self._env_backup is None:
            os.environ.pop("USE_PINDUODUO_OUTBOUND", None)
        else:
            os.environ["USE_PINDUODUO_OUTBOUND"] = self._env_backup

    def _make_legacy(self) -> MagicMock:
        legacy = MagicMock()
        legacy.start_account = AsyncMock()
        legacy.stop_account = AsyncMock()
        legacy.request_stop = MagicMock()
        return legacy

    @patch("Channel.pinduoduo.pinduoduo_channel.create_pinduoduo_outbound")
    def test_start_account_registers_outbound(self, create_mock: MagicMock) -> None:
        outbound = MagicMock()
        outbound.shop_id = "s1"
        outbound.user_id = "u1"
        create_mock.return_value = outbound
        channel = PinduoduoChannel(legacy=self._make_legacy())

        asyncio.run(
            channel.start_account("s1", "u1", MagicMock(), MagicMock(), MagicMock())
        )

        self.assertIs(get("s1", "u1"), outbound)
        self.assertIs(channel.outbound, outbound)

    @patch("Channel.pinduoduo.pinduoduo_channel.create_pinduoduo_outbound")
    def test_stop_account_unregisters(self, create_mock: MagicMock) -> None:
        outbound = MagicMock()
        outbound.shop_id = "s2"
        outbound.user_id = "u2"
        create_mock.return_value = outbound
        channel = PinduoduoChannel(legacy=self._make_legacy())

        async def run() -> None:
            await channel.start_account("s2", "u2", MagicMock(), MagicMock(), MagicMock())
            await channel.stop_account("s2", "u2")

        asyncio.run(run())

        self.assertIsNone(get("s2", "u2"))
        self.assertIsNone(channel._outbound)

    def test_start_account_failure_does_not_register(self) -> None:
        legacy = self._make_legacy()
        legacy.start_account = AsyncMock(side_effect=RuntimeError("connect failed"))
        channel = PinduoduoChannel(legacy=legacy)

        with self.assertRaises(RuntimeError):
            asyncio.run(
                channel.start_account("s3", "u3", MagicMock(), MagicMock(), MagicMock())
            )

        self.assertIsNone(get("s3", "u3"))

    @patch("Channel.pinduoduo.pinduoduo_channel.unregister_outbound")
    @patch("Channel.pinduoduo.pinduoduo_channel.create_pinduoduo_outbound")
    def test_request_stop_does_not_unregister(
        self, create_mock: MagicMock, unregister_mock: MagicMock
    ) -> None:
        outbound = MagicMock()
        outbound.shop_id = "s4"
        outbound.user_id = "u4"
        create_mock.return_value = outbound
        legacy = self._make_legacy()
        channel = PinduoduoChannel(legacy=legacy)

        asyncio.run(
            channel.start_account("s4", "u4", MagicMock(), MagicMock(), MagicMock())
        )
        channel.request_stop()

        legacy.request_stop.assert_called_once()
        unregister_mock.assert_not_called()
        self.assertIs(get("s4", "u4"), outbound)

    @patch("Channel.pinduoduo.pinduoduo_channel.create_pinduoduo_outbound")
    def test_resolver_uses_registered_outbound(self, create_mock: MagicMock) -> None:
        os.environ["USE_PINDUODUO_OUTBOUND"] = "true"
        outbound = MagicMock()
        outbound.shop_id = "s5"
        outbound.user_id = "u5"
        outbound.send_text = MagicMock()
        outbound.transfer_to_human = MagicMock()
        create_mock.return_value = outbound
        channel = PinduoduoChannel(legacy=self._make_legacy())

        asyncio.run(
            channel.start_account("s5", "u5", MagicMock(), MagicMock(), MagicMock())
        )

        meta = {"shop_id": "s5", "user_id": "u5", "from_uid": "buyer1"}
        resolved = resolve_pinduoduo_outbound(meta)
        self.assertIs(resolved, outbound)
        self.assertEqual(create_mock.call_count, 1)


if __name__ == "__main__":
    unittest.main()

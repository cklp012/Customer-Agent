"""Phase 3b：AutoReply 运行时 Channel 切换测试。"""

from __future__ import annotations

import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from Channel.pinduoduo.channel_factory import (
    create_auto_reply_runtime_channel,
    start_auto_reply_account,
)
from Channel.pinduoduo.pinduoduo_channel import PinduoduoChannel


class TestAutoReplyChannelSwitch(unittest.TestCase):
    def setUp(self) -> None:
        self._env_backup = os.environ.get("USE_PINDUODUO_CHANNEL_WRAPPER")

    def tearDown(self) -> None:
        if self._env_backup is None:
            os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        else:
            os.environ["USE_PINDUODUO_CHANNEL_WRAPPER"] = self._env_backup

    @patch("Channel.pinduoduo.channel_factory.PDDChannel")
    def test_flag_off_creates_legacy(self, pdd_cls: MagicMock) -> None:
        os.environ.pop("USE_PINDUODUO_CHANNEL_WRAPPER", None)
        legacy = MagicMock()
        pdd_cls.return_value = legacy
        channel = create_auto_reply_runtime_channel()
        self.assertIs(channel, legacy)
        pdd_cls.assert_called_once()

    @patch("Channel.pinduoduo.channel_factory.create_pinduoduo_channel")
    def test_flag_on_creates_wrapper(self, create_mock: MagicMock) -> None:
        os.environ["USE_PINDUODUO_CHANNEL_WRAPPER"] = "true"
        wrapper = MagicMock(spec=PinduoduoChannel)
        create_mock.return_value = wrapper
        channel = create_auto_reply_runtime_channel()
        self.assertIs(channel, wrapper)
        create_mock.assert_called_once()

    def test_start_wrapper_passes_on_message(self) -> None:
        channel = MagicMock(spec=PinduoduoChannel)
        channel.start_account = AsyncMock()
        on_success = MagicMock()
        on_failure = MagicMock()

        asyncio.run(
            start_auto_reply_account(channel, "s1", "u1", on_success, on_failure)
        )

        channel.start_account.assert_awaited_once()
        args = channel.start_account.await_args.args
        self.assertEqual(args[0], "s1")
        self.assertEqual(args[1], "u1")
        self.assertTrue(callable(args[2]))
        self.assertIs(args[3], on_success)
        self.assertIs(args[4], on_failure)
        args[2]()
        self.assertIsNone(args[2]())

    def test_start_legacy_without_on_message(self) -> None:
        channel = MagicMock()
        channel.start_account = AsyncMock()
        on_success = MagicMock()
        on_failure = MagicMock()

        asyncio.run(
            start_auto_reply_account(channel, "s2", "u2", on_success, on_failure)
        )

        channel.start_account.assert_awaited_once_with(
            "s2", "u2", on_success, on_failure
        )

    def test_wrapper_request_stop_delegates(self) -> None:
        legacy = MagicMock()
        legacy.request_stop = MagicMock()
        channel = PinduoduoChannel(legacy=legacy)
        channel.request_stop()
        legacy.request_stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()

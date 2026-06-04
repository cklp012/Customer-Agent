"""Phase 10h：pdd_lifecycle lifecycle-safe queue name（mock，无真实 WS/Consumer）。"""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from Channel.pinduoduo.core.pdd_config import HeartbeatConfig
from Channel.pinduoduo.core.pdd_lifecycle import _lifecycle_pdd_queue_name
from Channel.pinduoduo.pdd_channel import PDDChannel


class TestLifecyclePddQueueNameHelper(unittest.TestCase):
    def test_normal_shop_ids(self) -> None:
        self.assertEqual(_lifecycle_pdd_queue_name("S1"), "pdd_S1")
        self.assertEqual(_lifecycle_pdd_queue_name(123), "pdd_123")
        self.assertEqual(_lifecycle_pdd_queue_name("S1"), f"pdd_{'S1'}")

    def test_legacy_edge_cases_match_fstring(self) -> None:
        self.assertEqual(_lifecycle_pdd_queue_name(None), "pdd_None")
        self.assertEqual(_lifecycle_pdd_queue_name(""), "pdd_")
        self.assertEqual(_lifecycle_pdd_queue_name(" "), "pdd_ ")


class _FakeWsConnect:
    """websockets.connect 返回的 async context manager（非 coroutine）。"""

    def __init__(self, websocket: MagicMock) -> None:
        self._websocket = websocket

    async def __aenter__(self) -> MagicMock:
        return self._websocket

    async def __aexit__(self, *args: object) -> None:
        return None


def _make_channel() -> PDDChannel:
    channel = PDDChannel(status_manager=MagicMock())
    channel.heartbeat_config = HeartbeatConfig(
        enable_heartbeat=False,
        enable_cookie_health_check=False,
    )
    channel.reconnect_config.enable_auto_reconnect = False
    channel.resource_manager = MagicMock()
    channel.resource_manager.register_websocket = MagicMock()
    channel.cleanup_processing_tasks = AsyncMock()
    channel._cleanup_reconnect_tasks = AsyncMock()
    channel._cleanup_heartbeat_tasks = AsyncMock()
    channel._cleanup_health_tasks = AsyncMock()
    channel._is_ws_closed = MagicMock(return_value=False)
    return channel


class TestPddLifecycleInitQueueName(unittest.IsolatedAsyncioTestCase):
    async def test_init_setup_and_message_loop_same_queue_name(self) -> None:
        shop_id = "shop_init_01"
        expected = f"pdd_{shop_id}"
        channel = _make_channel()
        captured: dict = {}

        async def record_loop(ws, sid, uid, uname, queue_name: str) -> None:
            captured["loop"] = queue_name
            channel._stop_event.set()

        mock_ws = MagicMock()
        mock_ws.closed = False

        with (
            patch("Channel.pinduoduo.core.pdd_lifecycle.GetToken") as mock_token,
            patch("Channel.pinduoduo.core.pdd_lifecycle.websockets.connect") as mock_connect,
            patch.object(channel, "_setup_message_consumer", new_callable=AsyncMock) as mock_setup,
            patch.object(channel, "_message_loop", side_effect=record_loop),
            patch.object(channel, "_cleanup_resources", new_callable=AsyncMock) as mock_cleanup,
        ):
            mock_token.return_value.get_token.return_value = "token"
            mock_connect.return_value = _FakeWsConnect(mock_ws)

            on_success = MagicMock()
            on_failure = MagicMock()
            await channel.init(shop_id, "uid1", "user1", on_success, on_failure)

        mock_setup.assert_awaited_once_with(expected)
        self.assertEqual(captured["loop"], expected)
        mock_cleanup.assert_awaited()
        self.assertEqual(mock_cleanup.await_args.args[0], expected)
        on_success.assert_called_once()

    async def test_init_exception_cleanup_uses_same_queue_name(self) -> None:
        shop_id = "shop_exc_01"
        expected = f"pdd_{shop_id}"
        channel = _make_channel()

        class _FailingConnect:
            async def __aenter__(self) -> MagicMock:
                raise RuntimeError("ws failed")

            async def __aexit__(self, *args: object) -> None:
                return None

        with (
            patch("Channel.pinduoduo.core.pdd_lifecycle.GetToken") as mock_token,
            patch("Channel.pinduoduo.core.pdd_lifecycle.websockets.connect") as mock_connect,
            patch.object(channel, "_setup_message_consumer", new_callable=AsyncMock),
            patch.object(channel, "_cleanup_resources", new_callable=AsyncMock) as mock_cleanup,
        ):
            mock_connect.return_value = _FailingConnect()
            mock_token.return_value.get_token.return_value = "token"
            on_success = MagicMock()
            on_failure = MagicMock()
            await channel.init(shop_id, "uid1", "user1", on_success, on_failure)

        mock_cleanup.assert_awaited_once_with(expected)
        on_failure.assert_called_once()


class TestPddLifecycleStopAccountQueueName(unittest.IsolatedAsyncioTestCase):
    async def test_stop_account_cleanup_when_account_exists(self) -> None:
        shop_id = "shop_stop_01"
        expected = f"pdd_{shop_id}"
        channel = _make_channel()

        with (
            patch(
                "Channel.pinduoduo.core.pdd_lifecycle.db_manager"
            ) as mock_db,
            patch.object(channel, "_cleanup_resources", new_callable=AsyncMock) as mock_cleanup,
        ):
            mock_db.get_account.return_value = {"username": "testuser"}
            await channel.stop_account(shop_id, "uid1")

        mock_cleanup.assert_awaited_once_with(expected)

    async def test_stop_account_skips_cleanup_when_no_account(self) -> None:
        channel = _make_channel()

        with (
            patch(
                "Channel.pinduoduo.core.pdd_lifecycle.db_manager"
            ) as mock_db,
            patch.object(channel, "_cleanup_resources", new_callable=AsyncMock) as mock_cleanup,
        ):
            mock_db.get_account.return_value = None
            await channel.stop_account("shop_x", "uid_x")

        mock_cleanup.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()

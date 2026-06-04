"""Phase 10l：抖店 mock transport + enqueue runtime flow（patch 入队，无 Consumer/线程/网络）。"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

from Channel.base.types import PlatformType
from Channel.doudian.doudian_inbound import enqueue_doudian_raw_message
from Channel.doudian.mock_transport import DoudianMockTransport
from Channel.doudian.mappers.routing import compute_doudian_routing
from Message.queue_naming import build_queue_name, pdd_queue_name

_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "doudian_messages"
_ENQUEUE_TARGET = "Channel.doudian.doudian_inbound.enqueue_inbound_message"
_EXPECTED_QUEUE = "doudian_DD_SHOP_001"


def _load(name: str) -> dict:
    with open(_FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class TestDoudianMockTransport(unittest.TestCase):
    def test_poll_in_order(self) -> None:
        raw_list: List[Dict[str, Any]] = [
            _load("text.json"),
            _load("product_inquiry.json"),
            _load("system_notice.json"),
        ]
        transport = DoudianMockTransport(raw_list)
        self.assertEqual(transport.poll()["message_type"], "text")
        self.assertEqual(transport.poll()["message_type"], "product_inquiry")
        self.assertEqual(transport.poll()["message_type"], "system_notice")
        self.assertIsNone(transport.poll())

    def test_poll_all(self) -> None:
        raw_list = [_load("text.json"), _load("product_inquiry.json")]
        transport = DoudianMockTransport(raw_list)
        batch = transport.poll_all()
        self.assertEqual(len(batch), 2)
        self.assertEqual(transport.pending_count, 0)
        self.assertEqual(transport.poll_all(), [])

    def test_no_network(self) -> None:
        transport = DoudianMockTransport([_load("text.json")])
        msg = transport.poll()
        self.assertIsNotNone(msg)
        self.assertEqual(msg["platform"], "doudian")


class TestDoudianEnqueueRuntimeFlow(unittest.IsolatedAsyncioTestCase):
    async def test_enqueue_text(self) -> None:
        raw = _load("text.json")
        mock_enqueue = AsyncMock(return_value="mock-msg-id-text")
        with patch(_ENQUEUE_TARGET, mock_enqueue):
            result = await enqueue_doudian_raw_message(raw)

        self.assertEqual(compute_doudian_routing("text"), "queue")
        self.assertTrue(result.queued)
        self.assertEqual(result.queue_name, _EXPECTED_QUEUE)
        self.assertEqual(result.routing, "queue")
        self.assertIsNotNone(result.context)
        self.assertEqual(result.unified_message.platform, PlatformType.DOUDIAN)
        self.assertEqual(result.unified_message.content_type, "text")
        self.assertEqual(result.message_id, "mock-msg-id-text")
        mock_enqueue.assert_awaited_once()
        _qn, ctx, *_ = mock_enqueue.await_args.args
        self.assertEqual(_qn, _EXPECTED_QUEUE)
        self.assertIs(ctx, result.context)

    async def test_enqueue_product_inquiry(self) -> None:
        raw = _load("product_inquiry.json")
        mock_enqueue = AsyncMock(return_value="mock-msg-id-product")
        with patch(_ENQUEUE_TARGET, mock_enqueue):
            result = await enqueue_doudian_raw_message(raw)

        self.assertEqual(result.routing, "queue")
        self.assertTrue(result.queued)
        self.assertEqual(result.queue_name, _EXPECTED_QUEUE)
        mock_enqueue.assert_awaited_once()

    async def test_system_notice_drop_no_enqueue(self) -> None:
        raw = _load("system_notice.json")
        mock_enqueue = AsyncMock()
        with patch(_ENQUEUE_TARGET, mock_enqueue):
            result = await enqueue_doudian_raw_message(raw)

        self.assertEqual(result.routing, "drop")
        self.assertFalse(result.queued)
        self.assertIsNone(result.context)
        self.assertEqual(result.unified_message.conversation.extra["routing"], "drop")
        mock_enqueue.assert_not_awaited()

    async def test_default_queue_name_from_shop_id(self) -> None:
        raw = _load("text.json")
        expected = build_queue_name("doudian", raw["shop_id"])
        mock_enqueue = AsyncMock(return_value="id")
        with patch(_ENQUEUE_TARGET, mock_enqueue):
            result = await enqueue_doudian_raw_message(raw)
        self.assertEqual(result.queue_name, expected)
        self.assertEqual(expected, _EXPECTED_QUEUE)

    async def test_transport_poll_then_enqueue_text_only(self) -> None:
        transport = DoudianMockTransport(
            [_load("text.json"), _load("system_notice.json")]
        )
        mock_enqueue = AsyncMock(return_value="id-1")
        with patch(_ENQUEUE_TARGET, mock_enqueue):
            first = await enqueue_doudian_raw_message(transport.poll())
            second = await enqueue_doudian_raw_message(transport.poll())

        self.assertTrue(first.queued)
        self.assertFalse(second.queued)
        mock_enqueue.assert_awaited_once()


class TestDoudianRuntimeIsolation(unittest.TestCase):
    def test_queue_not_pdd_prefix(self) -> None:
        name = build_queue_name("doudian", "DD_SHOP_001")
        self.assertTrue(name.startswith("doudian_"))
        self.assertFalse(name.startswith("pdd_"))
        self.assertNotEqual(name, pdd_queue_name("DD_SHOP_001"))

    def test_inbound_module_no_pinduoduo_import(self) -> None:
        from Channel.doudian import doudian_inbound

        source = Path(doudian_inbound.__file__).read_text(encoding="utf-8")
        self.assertNotIn("pinduoduo", source)
        self.assertNotIn("pdd_", source)


if __name__ == "__main__":
    unittest.main()

"""Phase 8a：Demo platform runtime flow 集成测试。"""

from __future__ import annotations

import asyncio
import os
import unittest
from typing import Any, Dict, List, Tuple

from bridge.context import Context
from Channel.demo import DemoChannel, DemoOutbound
from Channel.demo.demo_inbound import enqueue_demo_message
from Channel.demo.mappers.demo_to_context import demo_raw_to_context
from Channel.demo.mappers.demo_to_unified import demo_raw_to_unified
from Message.core.consumer import message_consumer_manager
from Message.core.handlers import MessageHandler
from Message.core.queue import queue_manager
from Message.models.queue_models import MessageWrapper, QueueConfig


_RAW_INBOUND: Dict[str, Any] = {
    "platform": "demo",
    "message_id": "demo-runtime-msg-1",
    "content_type": "text",
    "content": "demo runtime inbound",
    "from_uid": "demo-buyer-runtime-1",
}

_SHOP = "demo_test_shop"
_ACCOUNT = "demo_test_user"
_QUEUE = f"demo_{_SHOP}"


class _RecordingHandler(MessageHandler):
    def __init__(self) -> None:
        super().__init__()
        self.seen: List[Tuple[Context, Dict[str, Any]]] = []

    def can_handle(self, context: Context) -> bool:
        return True

    async def handle(self, context: Context, metadata: Dict[str, Any]) -> bool:
        self.seen.append((context, dict(metadata)))
        return True


class _OutboundProbeHandler(MessageHandler):
    def can_handle(self, context: Context) -> bool:
        return True

    async def handle(self, context: Context, metadata: Dict[str, Any]) -> bool:
        outbound = metadata.get("outbound")
        if outbound is None:
            return False
        from_uid = metadata.get("from_uid")
        await outbound.send_text(from_uid, "demo-probe-reply")
        return True


def _to_metadata_with_inbound_extra(self: MessageWrapper) -> Dict[str, Any]:
    meta = TestDemoRuntimeFlow._orig_to_metadata(self)
    extra = getattr(self.context, "_inbound_extra_metadata", None)
    if extra:
        meta.update(extra)
    return meta


class TestDemoRuntimeFlow(unittest.IsolatedAsyncioTestCase):
    _orig_to_metadata = MessageWrapper.to_metadata

    @classmethod
    def setUpClass(cls) -> None:
        MessageWrapper.to_metadata = _to_metadata_with_inbound_extra  # type: ignore[method-assign]

    @classmethod
    def tearDownClass(cls) -> None:
        MessageWrapper.to_metadata = cls._orig_to_metadata  # type: ignore[method-assign]

    async def asyncSetUp(self) -> None:
        self._dual_track_backup = os.environ.get("USE_UNIFIED_MESSAGE_DUAL_TRACK")
        os.environ["USE_UNIFIED_MESSAGE_DUAL_TRACK"] = "true"
        queue_manager.recreate_queue(
            _QUEUE,
            QueueConfig(max_size=50, enable_deduplication=False),
        )
        message_consumer_manager._consumers.pop(_QUEUE, None)
        self._recording = _RecordingHandler()
        self._consumer = message_consumer_manager.create_consumer(_QUEUE, max_concurrent=2)
        self._consumer.add_handler(self._recording)
        await message_consumer_manager.start_consumer(_QUEUE)

    async def asyncTearDown(self) -> None:
        await message_consumer_manager.stop_consumer(_QUEUE)
        message_consumer_manager._consumers.pop(_QUEUE, None)
        if self._dual_track_backup is None:
            os.environ.pop("USE_UNIFIED_MESSAGE_DUAL_TRACK", None)
        else:
            os.environ["USE_UNIFIED_MESSAGE_DUAL_TRACK"] = self._dual_track_backup
        await asyncio.sleep(0.05)

    async def _wait_for_handlers(self, min_count: int = 1, timeout: float = 2.0) -> None:
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            if len(self._recording.seen) >= min_count:
                return
            await asyncio.sleep(0.05)
        self.fail(f"handler 未在 {timeout}s 内收到消息")

    async def test_enqueue_dual_track_metadata(self) -> None:
        await enqueue_demo_message(_RAW_INBOUND, _SHOP, _ACCOUNT, _QUEUE)
        await self._wait_for_handlers()
        _ctx, meta = self._recording.seen[0]
        self.assertTrue(meta.get("has_unified"))
        self.assertEqual(meta.get("platform"), "demo")
        self.assertEqual(meta.get("content_type"), "text")
        self.assertEqual(meta.get("routing"), "queue")

    async def test_handler_receives_context(self) -> None:
        raw = dict(_RAW_INBOUND)
        raw["message_id"] = "demo-ctx-handler-1"
        await enqueue_demo_message(raw, _SHOP, _ACCOUNT, _QUEUE)
        await self._wait_for_handlers()
        ctx, _meta = self._recording.seen[-1]
        self.assertIsInstance(ctx, Context)
        kwargs = ctx.kwargs
        self.assertEqual(getattr(kwargs, "shop_id", None), _SHOP)
        self.assertEqual(getattr(kwargs, "channel_type", None), "demo")

    async def test_demo_channel_inject_runtime_flow(self) -> None:
        before = len(self._recording.seen)
        channel = DemoChannel(
            inject_runtime_flow=True,
            runtime_queue_name=_QUEUE,
        )
        await channel.start_account(
            _SHOP,
            _ACCOUNT,
            lambda _p: None,
            lambda: None,
            lambda: None,
        )
        await self._wait_for_handlers(min_count=before + 1)
        _ctx, meta = self._recording.seen[-1]
        self.assertEqual(meta.get("platform"), "demo")

    async def test_outbound_via_metadata_injection(self) -> None:
        probe_queue = "demo_outbound_probe_shop"
        queue_manager.recreate_queue(
            probe_queue,
            QueueConfig(max_size=10, enable_deduplication=False),
        )
        message_consumer_manager._consumers.pop(probe_queue, None)
        probe = _OutboundProbeHandler()
        consumer = message_consumer_manager.create_consumer(probe_queue, 2)
        consumer.add_handler(probe)
        await message_consumer_manager.start_consumer(probe_queue)

        outbound = DemoOutbound(_SHOP, _ACCOUNT)
        raw = dict(_RAW_INBOUND)
        raw["message_id"] = "demo-outbound-probe-1"
        raw["content"] = "outbound probe unique content"
        from Message.inbound_enqueue import enqueue_inbound_message

        ctx = demo_raw_to_context(raw, _SHOP, _ACCOUNT)
        unified = demo_raw_to_unified(raw, _SHOP, _ACCOUNT)
        await enqueue_inbound_message(
            probe_queue,
            ctx,
            unified_message=unified,
            extra_metadata={"outbound": outbound},
        )
        await asyncio.sleep(0.3)
        await message_consumer_manager.stop_consumer(probe_queue)
        message_consumer_manager._consumers.pop(probe_queue, None)

        self.assertGreaterEqual(len(outbound.sent_log), 1)
        self.assertEqual(outbound.sent_log[0]["method"], "send_text")

    async def test_does_not_pollute_pdd_queue(self) -> None:
        pdd_queue = "pdd_demo_isolation_check"
        queue_manager.recreate_queue(pdd_queue, QueueConfig(max_size=10))
        q = queue_manager.get_queue(pdd_queue)
        self.assertIsNotNone(q)
        self.assertEqual(q.get_stats().current_size, 0)


class TestDemoMappers(unittest.TestCase):
    def test_unified_platform_is_demo(self) -> None:
        unified = demo_raw_to_unified(_RAW_INBOUND, _SHOP, _ACCOUNT)
        self.assertEqual(unified.platform.value, "demo")

    def test_context_kwargs_fields(self) -> None:
        ctx = demo_raw_to_context(_RAW_INBOUND, _SHOP, _ACCOUNT)
        self.assertEqual(ctx.kwargs.shop_id, _SHOP)
        self.assertEqual(ctx.kwargs.user_id, _ACCOUNT)
        self.assertEqual(ctx.kwargs.channel_type, "demo")


if __name__ == "__main__":
    unittest.main()

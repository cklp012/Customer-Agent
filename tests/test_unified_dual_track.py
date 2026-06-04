"""Phase 7d：UnifiedMessage / Context 双轨入队测试。"""

from __future__ import annotations

import asyncio
import json
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from bridge.context import Context, ContextType, ChannelType
from Channel.base.models import UnifiedConversation, UnifiedMessage
from Channel.base.types import PlatformType
from Channel.pinduoduo.mappers.dual_track_flags import use_unified_message_dual_track
from Channel.pinduoduo.pdd_message import PDDChatMessage
from Message.core.consumer import enrich_metadata_from_unified
from Message.core.queue import SimpleMessageQueue
from Message.models.queue_models import MessageWrapper, QueueConfig
from Message import put_message

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "pdd_messages" / "text.json"


def _make_context() -> Context:
    return Context.create_pinduoduo_context(
        content="hello",
        msg_id="demo-msg-text-001",
        from_uid="demo_buyer_uid_001",
        user_msg_type=ContextType.TEXT,
        shop_id="demo_shop_001",
        user_id="demo_cs_uid_001",
        username="demo_cs_user",
        shop_name="Demo Shop",
        channel_type=ChannelType.PINDUODUO,
    )


def _make_unified() -> UnifiedMessage:
    return UnifiedMessage(
        platform=PlatformType.PINDUODUO,
        message_id="demo-msg-text-001",
        conversation=UnifiedConversation(
            platform=PlatformType.PINDUODUO,
            conversation_id="demo_buyer_uid_001",
            shop_id="demo_shop_001",
            account_id="demo_cs_uid_001",
            buyer_uid="demo_buyer_uid_001",
            extra={"routing": "queue"},
        ),
        direction="inbound",
        content_type="text",
        content="hello",
    )


class TestDualTrackFlags(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("USE_UNIFIED_MESSAGE_DUAL_TRACK", None)

    def test_default_false(self) -> None:
        os.environ.pop("USE_UNIFIED_MESSAGE_DUAL_TRACK", None)
        self.assertFalse(use_unified_message_dual_track())


class TestQueueDualTrack(unittest.IsolatedAsyncioTestCase):
    async def test_put_without_unified(self) -> None:
        queue = SimpleMessageQueue("test_dual_off", QueueConfig(max_size=10))
        ctx = _make_context()
        msg_id = await queue.put(ctx)
        wrapper = await queue.get(timeout=1.0)
        assert wrapper is not None
        self.assertEqual(wrapper.message_id, msg_id)
        self.assertIsNone(wrapper.unified_message)

    async def test_put_with_unified(self) -> None:
        queue = SimpleMessageQueue("test_dual_on", QueueConfig(max_size=10))
        ctx = _make_context()
        unified = _make_unified()
        await queue.put(ctx, unified_message=unified)
        wrapper = await queue.get(timeout=1.0)
        assert wrapper is not None
        self.assertIsNotNone(wrapper.unified_message)
        self.assertEqual(wrapper.unified_message.message_id, "demo-msg-text-001")
        self.assertEqual(wrapper.context.type, ContextType.TEXT)


class TestPutMessageCompat(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        from Message.core.queue import queue_manager

        self._queue_name = "test_put_message_compat"
        queue_manager.get_or_create_queue(self._queue_name, QueueConfig(max_size=10))

    async def test_legacy_put_message_signature(self) -> None:
        ctx = _make_context()
        msg_id = await put_message(self._queue_name, ctx)
        self.assertTrue(msg_id)


class TestMetadataEnrichment(unittest.TestCase):
    def test_enrich_from_unified(self) -> None:
        wrapper = MessageWrapper(
            message_id="w1",
            context=_make_context(),
            timestamp=1.0,
            unified_message=_make_unified(),
        )
        meta = enrich_metadata_from_unified(wrapper)
        self.assertTrue(meta["has_unified"])
        self.assertEqual(meta["platform"], "pinduoduo")
        self.assertEqual(meta["routing"], "queue")
        self.assertEqual(meta["unified_message_id"], "demo-msg-text-001")

    def test_enrich_empty_without_unified(self) -> None:
        wrapper = MessageWrapper(
            message_id="w2",
            context=_make_context(),
            timestamp=1.0,
        )
        self.assertEqual(enrich_metadata_from_unified(wrapper), {})


class TestHandlerStillContext(unittest.TestCase):
    def test_handler_receives_context_type(self) -> None:
        ctx = _make_context()
        handler = MagicMock()
        handler.can_handle = lambda c: isinstance(c, Context)
        self.assertTrue(handler.can_handle(ctx))
        self.assertFalse(handler.can_handle(_make_unified()))


class TestDualTrackMapperFailure(unittest.TestCase):
    def test_pdd_to_unified_from_fixture(self) -> None:
        with open(_FIXTURE, encoding="utf-8") as f:
            pdd = PDDChatMessage(json.load(f))
        from Channel.pinduoduo.mappers.pdd_to_unified import pdd_message_to_unified

        unified = pdd_message_to_unified(
            pdd,
            shop_id="s",
            user_id="u",
            username="n",
        )
        self.assertEqual(unified.content_type, "text")


class TestFixtureMapperEnrichChain(unittest.TestCase):
    """Phase 10d：fixture → mapper → enrich（不启 WS / Consumer 线程）。"""

    def tearDown(self) -> None:
        os.environ.pop("USE_UNIFIED_MESSAGE_DUAL_TRACK", None)

    def test_fixture_to_enriched_metadata(self) -> None:
        from Channel.pinduoduo.mappers.pdd_to_unified import pdd_message_to_unified

        with open(_FIXTURE, encoding="utf-8") as f:
            pdd = PDDChatMessage(json.load(f))
        ctx = _make_context()
        unified = pdd_message_to_unified(
            pdd,
            shop_id="demo_shop_001",
            user_id="demo_cs_uid_001",
            username="demo_cs_user",
            shop_name="Demo Shop",
        )
        wrapper = MessageWrapper(
            message_id="10d-chain",
            context=ctx,
            timestamp=1.0,
            unified_message=unified,
        )
        meta = enrich_metadata_from_unified(wrapper)

        self.assertTrue(meta["has_unified"])
        self.assertEqual(meta["platform"], "pinduoduo")
        self.assertEqual(meta["routing"], "queue")
        self.assertEqual(meta["content_type"], "text")
        self.assertEqual(meta["routing"], unified.conversation.extra["routing"])

    def test_dual_track_flag_only_when_set_in_test(self) -> None:
        os.environ.pop("USE_UNIFIED_MESSAGE_DUAL_TRACK", None)
        self.assertFalse(use_unified_message_dual_track())
        os.environ["USE_UNIFIED_MESSAGE_DUAL_TRACK"] = "true"
        try:
            self.assertTrue(use_unified_message_dual_track())
        finally:
            os.environ.pop("USE_UNIFIED_MESSAGE_DUAL_TRACK", None)
        self.assertFalse(use_unified_message_dual_track())


if __name__ == "__main__":
    unittest.main()

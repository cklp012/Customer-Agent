"""Phase 10d：platform / routing / content_type 跨层契约（account → Unified → Context → metadata）。"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from bridge.context import Context, ContextType, ChannelType
from Channel.base.types import PlatformType
from Channel.pinduoduo.mappers.pdd_to_unified import compute_pdd_routing, pdd_message_to_unified
from Channel.pinduoduo.pdd_message import PDDChatMessage
from Message.core.consumer import enrich_metadata_from_unified
from Message.metadata_adapter import get_content_type, get_platform, get_routing
from Message.models.queue_models import MessageWrapper
from ui.auto_reply.platform_ui import (
    is_autoreply_supported,
    normalize_channel_name,
    PRODUCTION_AUTOREPLY_PLATFORM,
)

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "pdd_messages" / "text.json"
_SHOP_ID = "contract_shop"
_USER_ID = "contract_user"
_USERNAME = "contract_cs"


def _account_pinduoduo() -> dict:
    return {
        "channel_name": "pinduoduo",
        "shop_id": _SHOP_ID,
        "user_id": _USER_ID,
        "username": _USERNAME,
        "status": 1,
    }


def _legacy_context() -> Context:
    return Context.create_pinduoduo_context(
        content="hello",
        msg_id="demo-msg-text-001",
        from_uid="demo_buyer_uid_001",
        user_msg_type=ContextType.TEXT,
        shop_id=_SHOP_ID,
        user_id=_USER_ID,
        username=_USERNAME,
        shop_name="Shop",
        channel_type=ChannelType.PINDUODUO,
    )


class TestAccountChannelName(unittest.TestCase):
    def test_pinduoduo_channel_name(self) -> None:
        acc = _account_pinduoduo()
        self.assertEqual(normalize_channel_name(acc["channel_name"]), PRODUCTION_AUTOREPLY_PLATFORM)
        self.assertTrue(is_autoreply_supported(acc["channel_name"]))

    def test_missing_channel_name_defaults_pinduoduo(self) -> None:
        self.assertEqual(normalize_channel_name(None), PRODUCTION_AUTOREPLY_PLATFORM)
        self.assertEqual(normalize_channel_name(""), PRODUCTION_AUTOREPLY_PLATFORM)
        self.assertTrue(is_autoreply_supported(None))


class TestUnifiedAndContextPlatform(unittest.TestCase):
    def test_fixture_unified_platform(self) -> None:
        with open(_FIXTURE, encoding="utf-8") as f:
            pdd = PDDChatMessage(json.load(f))
        unified = pdd_message_to_unified(
            pdd,
            shop_id=_SHOP_ID,
            user_id=_USER_ID,
            username=_USERNAME,
        )
        self.assertEqual(unified.platform, PlatformType.PINDUODUO)
        self.assertEqual(unified.platform.value, "pinduoduo")

    def test_context_channel_type(self) -> None:
        ctx = _legacy_context()
        self.assertEqual(ctx.channel_type, ChannelType.PINDUODUO)
        self.assertEqual(ctx.channel_type.value, "pinduoduo")


class TestEnrichedMetadataContract(unittest.TestCase):
    def _wrapper_from_fixture(self) -> MessageWrapper:
        with open(_FIXTURE, encoding="utf-8") as f:
            pdd = PDDChatMessage(json.load(f))
        ctx = _legacy_context()
        unified = pdd_message_to_unified(
            pdd,
            shop_id=_SHOP_ID,
            user_id=_USER_ID,
            username=_USERNAME,
            shop_name="Shop",
        )
        return MessageWrapper(
            message_id="contract-w1",
            context=ctx,
            timestamp=1.0,
            unified_message=unified,
        )

    def test_enrich_metadata_fields(self) -> None:
        wrapper = self._wrapper_from_fixture()
        unified = wrapper.unified_message
        assert unified is not None
        meta = enrich_metadata_from_unified(wrapper)

        self.assertTrue(meta["has_unified"])
        self.assertEqual(meta["platform"], "pinduoduo")
        self.assertEqual(meta["routing"], unified.conversation.extra["routing"])
        self.assertEqual(meta["content_type"], unified.content_type)
        self.assertEqual(meta["routing"], compute_pdd_routing(ContextType.TEXT))

    def test_metadata_adapter_platform_and_routing(self) -> None:
        wrapper = self._wrapper_from_fixture()
        meta = enrich_metadata_from_unified(wrapper)
        ctx = wrapper.context

        self.assertEqual(get_platform(meta, ctx), "pinduoduo")
        self.assertEqual(get_routing(meta, ctx), meta["routing"])
        self.assertEqual(get_content_type(meta, ctx), meta["content_type"])

    def test_platform_layers_aligned(self) -> None:
        acc = _account_pinduoduo()
        wrapper = self._wrapper_from_fixture()
        unified = wrapper.unified_message
        assert unified is not None
        meta = enrich_metadata_from_unified(wrapper)
        ctx = wrapper.context

        platform_id = normalize_channel_name(acc["channel_name"])
        self.assertEqual(platform_id, unified.platform.value)
        self.assertEqual(platform_id, ctx.channel_type.value)
        self.assertEqual(platform_id, meta["platform"])


if __name__ == "__main__":
    unittest.main()

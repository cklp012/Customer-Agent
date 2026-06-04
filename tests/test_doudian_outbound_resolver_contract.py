"""Phase 11c Route B：抖店 outbound 经 unified_outbound_resolver 契约测试（仅测试，无生产变更）。"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from bridge.context import Context, ContextType
from Channel.base.types import PlatformType
from Channel.doudian.doudian_outbound import DoudianMockOutbound
from Channel.doudian.mappers.doudian_to_context import doudian_raw_to_context
from Message.handlers import channel_outbound_registry
from Message.handlers.unified_outbound_resolver import infer_platform, resolve_outbound

_SHOP = "DD_SHOP_001"
_ACCOUNT = "DD_ACC_001"
_BUYER = "DD_BUYER_001"

_FIXTURE_TEXT = (
    Path(__file__).resolve().parent / "fixtures" / "doudian_messages" / "text.json"
)


class _Kwargs:
    def __init__(self, **fields: object) -> None:
        for key, value in fields.items():
            setattr(self, key, value)


def _doudian_meta(**extra: object) -> dict:
    base = {
        "platform": "doudian",
        "shop_id": _SHOP,
        "user_id": _ACCOUNT,
        "from_uid": _BUYER,
    }
    base.update(extra)
    return base


class TestDoudianInferPlatform(unittest.TestCase):
    """R1: infer_platform resolves doudian from metadata or Context channel_type."""

    def test_metadata_platform_doudian(self) -> None:
        self.assertEqual(infer_platform({"platform": "doudian"}), "doudian")

    def test_kwargs_channel_type_doudian(self) -> None:
        ctx = Context(
            type=ContextType.TEXT,
            kwargs=_Kwargs(channel_type="doudian"),
        )
        self.assertEqual(infer_platform({}, ctx), "doudian")

    def test_kwargs_channel_type_platform_enum(self) -> None:
        ctx = Context(
            type=ContextType.TEXT,
            kwargs=_Kwargs(channel_type=PlatformType.DOUDIAN),
        )
        self.assertEqual(infer_platform({}, ctx), "doudian")


class TestDoudianResolveOutboundContract(unittest.TestCase):
    def tearDown(self) -> None:
        channel_outbound_registry.clear()

    def test_r2_registry_resolves_same_instance(self) -> None:
        outbound = DoudianMockOutbound(_SHOP, _ACCOUNT)
        channel_outbound_registry.register("doudian", _SHOP, _ACCOUNT, outbound)
        meta = _doudian_meta()
        self.assertIs(resolve_outbound(meta), outbound)

    def test_r3_metadata_outbound_priority_over_registry(self) -> None:
        registry_outbound = DoudianMockOutbound(_SHOP, _ACCOUNT)
        metadata_outbound = DoudianMockOutbound(_SHOP, _ACCOUNT)
        channel_outbound_registry.register("doudian", _SHOP, _ACCOUNT, registry_outbound)
        meta = _doudian_meta(outbound=metadata_outbound)
        self.assertIs(resolve_outbound(meta), metadata_outbound)
        self.assertIsNot(resolve_outbound(meta), registry_outbound)

    def test_r4_shop_account_mismatch_returns_none(self) -> None:
        outbound = DoudianMockOutbound(_SHOP, _ACCOUNT)
        channel_outbound_registry.register("doudian", _SHOP, _ACCOUNT, outbound)
        meta_wrong_shop = _doudian_meta(shop_id="OTHER_SHOP")
        meta_wrong_user = _doudian_meta(user_id="OTHER_ACC")
        self.assertIsNone(resolve_outbound(meta_wrong_shop))
        self.assertIsNone(resolve_outbound(meta_wrong_user))

    @patch("Message.handlers.unified_outbound_resolver.resolve_pinduoduo_outbound")
    def test_r5_unregistered_doudian_no_pdd_fallback(
        self, legacy_mock: MagicMock
    ) -> None:
        meta = _doudian_meta()
        self.assertIsNone(resolve_outbound(meta))
        legacy_mock.assert_not_called()

    @patch("Message.handlers.unified_outbound_resolver.resolve_pinduoduo_outbound")
    def test_r6_pinduoduo_still_delegates_to_legacy_resolver(
        self, legacy_mock: MagicMock
    ) -> None:
        sentinel = object()
        legacy_mock.return_value = sentinel
        meta = {
            "platform": "pinduoduo",
            "shop_id": "PDD_SHOP",
            "user_id": "PDD_ACC",
            "from_uid": "PDD_BUYER",
        }
        self.assertIs(resolve_outbound(meta), sentinel)
        legacy_mock.assert_called_once()
        call_meta, call_ctx = legacy_mock.call_args[0]
        self.assertEqual(call_meta, meta)
        self.assertIsNone(call_ctx)

    def test_r7_no_registry_does_not_auto_create_doudian_outbound(self) -> None:
        raw = json.loads(_FIXTURE_TEXT.read_text(encoding="utf-8"))
        ctx = doudian_raw_to_context(raw)
        self.assertIsNotNone(ctx)
        meta = _doudian_meta()
        self.assertIsNone(resolve_outbound(meta, ctx))


if __name__ == "__main__":
    unittest.main()

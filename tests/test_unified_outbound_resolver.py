"""Phase 8b：unified_outbound_resolver 单元测试。"""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from bridge.context import Context, ContextType
from Channel.demo.demo_outbound import DemoOutbound
from Channel.demo.mappers.demo_to_context import demo_raw_to_context
from Message.handlers import channel_outbound_registry
from Message.handlers.unified_outbound_resolver import (
    infer_platform,
    resolve_outbound,
)


class _Kwargs:
    def __init__(self, **fields: object) -> None:
        for key, value in fields.items():
            setattr(self, key, value)


class TestInferPlatform(unittest.TestCase):
    def test_metadata_platform_first(self) -> None:
        ctx = Context(type=ContextType.TEXT, kwargs=_Kwargs(channel_type="demo"))
        self.assertEqual(infer_platform({"platform": "demo"}, ctx), "demo")

    def test_kwargs_channel_type_second(self) -> None:
        ctx = Context(type=ContextType.TEXT, kwargs=_Kwargs(channel_type="demo"))
        self.assertEqual(infer_platform({}, ctx), "demo")

    def test_default_pinduoduo(self) -> None:
        ctx = Context(type=ContextType.TEXT, kwargs=_Kwargs(shop_id="s"))
        self.assertEqual(infer_platform({}, ctx), "pinduoduo")


class TestResolveOutbound(unittest.TestCase):
    def tearDown(self) -> None:
        channel_outbound_registry.clear()
        backup = getattr(self, "_pdd_flag_backup", None)
        if backup is None:
            os.environ.pop("USE_PINDUODUO_OUTBOUND", None)
        else:
            os.environ["USE_PINDUODUO_OUTBOUND"] = backup

    def _meta(
        self,
        shop: str = "s1",
        user: str = "u1",
        buyer: str = "b1",
        **extra: object,
    ) -> dict:
        base = {"shop_id": shop, "user_id": user, "from_uid": buyer}
        base.update(extra)
        return base

    def test_incomplete_context_returns_none(self) -> None:
        self.assertIsNone(resolve_outbound({"shop_id": "s"}))

    def test_metadata_outbound_priority(self) -> None:
        outbound = DemoOutbound("s1", "u1")
        meta = self._meta(outbound=outbound, platform="demo")
        self.assertIs(resolve_outbound(meta), outbound)

    def test_demo_registry_resolves(self) -> None:
        outbound = DemoOutbound("s2", "u2")
        channel_outbound_registry.register("demo", "s2", "u2", outbound)
        meta = self._meta(shop="s2", user="u2", buyer="b2", platform="demo")
        self.assertIs(resolve_outbound(meta), outbound)

    def test_account_mismatch_skips_metadata(self) -> None:
        outbound = DemoOutbound("other-shop", "other-user")
        meta = self._meta(outbound=outbound, platform="demo")
        self.assertIsNone(resolve_outbound(meta))

    @patch("Message.handlers.unified_outbound_resolver.resolve_pinduoduo_outbound")
    def test_pinduoduo_delegates_to_legacy_resolver(self, legacy_mock: MagicMock) -> None:
        sentinel = object()
        legacy_mock.return_value = sentinel
        meta = self._meta(platform="pinduoduo")
        self.assertIs(resolve_outbound(meta), sentinel)
        legacy_mock.assert_called_once()
        call_meta, call_ctx = legacy_mock.call_args[0]
        self.assertEqual(call_meta, meta)
        self.assertIsNone(call_ctx)

    @patch("Message.handlers.outbound_resolver.create_pinduoduo_outbound")
    def test_pinduoduo_delegate_parity(self, create_mock: MagicMock) -> None:
        from Message.handlers.outbound_resolver import resolve_pinduoduo_outbound

        self._pdd_flag_backup = os.environ.get("USE_PINDUODUO_OUTBOUND")
        os.environ["USE_PINDUODUO_OUTBOUND"] = "true"
        sentinel = object()
        create_mock.return_value = sentinel

        meta = self._meta(platform="pinduoduo")
        unified = resolve_outbound(meta)
        legacy = resolve_pinduoduo_outbound(meta)
        self.assertIs(unified, legacy)
        self.assertIs(unified, sentinel)

    def test_demo_does_not_auto_create(self) -> None:
        raw = {
            "platform": "demo",
            "message_id": "m1",
            "content": "hi",
            "from_uid": "buyer-1",
        }
        ctx = demo_raw_to_context(raw, "s3", "u3")
        meta = {"platform": "demo", "shop_id": "s3", "user_id": "u3", "from_uid": "buyer-1"}
        self.assertIsNone(resolve_outbound(meta, ctx))


if __name__ == "__main__":
    unittest.main()

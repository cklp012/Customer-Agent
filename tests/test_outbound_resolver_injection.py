"""Phase 4a：outbound_resolver metadata / registry 复用测试。"""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from Message.handlers.account_outbound_registry import clear, get, register, unregister
from Message.handlers.outbound_resolver import resolve_pinduoduo_outbound
class _StubOutbound:
    """最小 outbound 桩，满足 resolver 校验。"""

    def __init__(self, shop_id: str, user_id: str) -> None:
        self.shop_id = shop_id
        self.user_id = user_id

    async def send_text(self, *_args: object, **_kwargs: object) -> bool:
        return True

    async def transfer_to_human(self, *_args: object, **_kwargs: object) -> bool:
        return True


def _make_outbound(shop_id: str = "s1", user_id: str = "u1") -> _StubOutbound:
    return _StubOutbound(shop_id, user_id)


class TestOutboundResolverInjection(unittest.TestCase):
    def setUp(self) -> None:
        self._env_backup = os.environ.get("USE_PINDUODUO_OUTBOUND")
        clear()

    def tearDown(self) -> None:
        clear()
        if self._env_backup is None:
            os.environ.pop("USE_PINDUODUO_OUTBOUND", None)
        else:
            os.environ["USE_PINDUODUO_OUTBOUND"] = self._env_backup

    def test_flag_off_ignores_metadata_outbound(self) -> None:
        os.environ.pop("USE_PINDUODUO_OUTBOUND", None)
        outbound = _make_outbound()
        meta = {
            "shop_id": "s1",
            "user_id": "u1",
            "from_uid": "b1",
            "outbound": outbound,
        }
        self.assertIsNone(resolve_pinduoduo_outbound(meta))

    @patch("Message.handlers.outbound_resolver.create_pinduoduo_outbound")
    def test_flag_on_metadata_outbound_reused(self, create_mock: MagicMock) -> None:
        os.environ["USE_PINDUODUO_OUTBOUND"] = "true"
        outbound = _make_outbound()
        meta = {
            "shop_id": "s1",
            "user_id": "u1",
            "from_uid": "b1",
            "outbound": outbound,
        }
        result = resolve_pinduoduo_outbound(meta)
        self.assertIs(result, outbound)
        create_mock.assert_not_called()

    @patch("Message.handlers.outbound_resolver.create_pinduoduo_outbound")
    def test_flag_on_metadata_mismatch_falls_back_create(self, create_mock: MagicMock) -> None:
        os.environ["USE_PINDUODUO_OUTBOUND"] = "true"
        outbound = _make_outbound(shop_id="other", user_id="u1")
        sentinel = MagicMock()
        create_mock.return_value = sentinel
        meta = {
            "shop_id": "s1",
            "user_id": "u1",
            "from_uid": "b1",
            "outbound": outbound,
        }
        result = resolve_pinduoduo_outbound(meta)
        self.assertIs(result, sentinel)
        create_mock.assert_called_once_with("s1", "u1")

    @patch("Message.handlers.outbound_resolver.create_pinduoduo_outbound")
    def test_flag_on_registry_hit(self, create_mock: MagicMock) -> None:
        os.environ["USE_PINDUODUO_OUTBOUND"] = "true"
        outbound = _make_outbound("s2", "u2")
        register("s2", "u2", outbound)
        meta = {"shop_id": "s2", "user_id": "u2", "from_uid": "b2"}
        result = resolve_pinduoduo_outbound(meta)
        self.assertIs(result, outbound)
        create_mock.assert_not_called()

    @patch("Message.handlers.outbound_resolver.create_pinduoduo_outbound")
    def test_flag_on_no_source_calls_create(self, create_mock: MagicMock) -> None:
        os.environ["USE_PINDUODUO_OUTBOUND"] = "true"
        sentinel = MagicMock()
        create_mock.return_value = sentinel
        meta = {"shop_id": "s3", "user_id": "u3", "from_uid": "b3"}
        result = resolve_pinduoduo_outbound(meta)
        self.assertIs(result, sentinel)
        create_mock.assert_called_once_with("s3", "u3")

    @patch("Message.handlers.outbound_resolver.create_pinduoduo_outbound")
    def test_invalid_metadata_object_falls_back_create(self, create_mock: MagicMock) -> None:
        os.environ["USE_PINDUODUO_OUTBOUND"] = "true"
        sentinel = MagicMock()
        create_mock.return_value = sentinel
        meta = {
            "shop_id": "s4",
            "user_id": "u4",
            "from_uid": "b4",
            "outbound": object(),
        }
        result = resolve_pinduoduo_outbound(meta)
        self.assertIs(result, sentinel)
        create_mock.assert_called_once_with("s4", "u4")

    def test_registry_clear_and_unregister(self) -> None:
        outbound = _make_outbound("s5", "u5")
        register("s5", "u5", outbound)
        self.assertIs(get("s5", "u5"), outbound)
        unregister("s5", "u5")
        self.assertIsNone(get("s5", "u5"))
        register("s6", "u6", outbound)
        clear()
        self.assertIsNone(get("s6", "u6"))


if __name__ == "__main__":
    unittest.main()

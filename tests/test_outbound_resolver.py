"""Phase 2b：outbound_resolver 单元测试。"""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from bridge.context import Context, ContextType, PinduoduoKwargs
from Message.handlers.outbound_resolver import (
    extract_pdd_send_context,
    resolve_pinduoduo_outbound,
)


class TestExtractPddSendContext(unittest.TestCase):
    def test_from_metadata(self) -> None:
        meta = {"shop_id": "s1", "user_id": "u1", "from_uid": "b1"}
        shop_id, user_id, from_uid = extract_pdd_send_context(meta)
        self.assertEqual((shop_id, user_id, from_uid), ("s1", "u1", "b1"))

    def test_from_kwargs_attr(self) -> None:
        ctx = Context(
            type=ContextType.TEXT,
            kwargs=PinduoduoKwargs(shop_id="s2", user_id="u2", from_uid="b2"),
        )
        shop_id, user_id, from_uid = extract_pdd_send_context({}, ctx)
        self.assertEqual((shop_id, user_id, from_uid), ("s2", "u2", "b2"))

    def test_from_kwargs_dict(self) -> None:
        ctx = Context(
            type=ContextType.TEXT,
            kwargs={"shop_id": "s3", "user_id": "u3", "from_uid": "b3"},
        )
        shop_id, user_id, from_uid = extract_pdd_send_context({}, ctx)
        self.assertEqual((shop_id, user_id, from_uid), ("s3", "u3", "b3"))

    def test_metadata_and_kwargs_mixed(self) -> None:
        ctx = Context(
            type=ContextType.TEXT,
            kwargs=PinduoduoKwargs(user_id="u4", from_uid="b4"),
        )
        meta = {"shop_id": "s4"}
        shop_id, user_id, from_uid = extract_pdd_send_context(meta, ctx)
        self.assertEqual((shop_id, user_id, from_uid), ("s4", "u4", "b4"))


class TestResolvePinduoduoOutbound(unittest.TestCase):
    def setUp(self) -> None:
        self._env_backup = os.environ.get("USE_PINDUODUO_OUTBOUND")

    def tearDown(self) -> None:
        if self._env_backup is None:
            os.environ.pop("USE_PINDUODUO_OUTBOUND", None)
        else:
            os.environ["USE_PINDUODUO_OUTBOUND"] = self._env_backup

    def test_flag_off_returns_none(self) -> None:
        os.environ.pop("USE_PINDUODUO_OUTBOUND", None)
        meta = {"shop_id": "s", "user_id": "u", "from_uid": "f"}
        self.assertIsNone(resolve_pinduoduo_outbound(meta))

    @patch("Message.handlers.outbound_resolver.create_pinduoduo_outbound")
    def test_flag_on_returns_outbound(self, create_mock) -> None:
        os.environ["USE_PINDUODUO_OUTBOUND"] = "true"
        sentinel = object()
        create_mock.return_value = sentinel
        meta = {"shop_id": "s", "user_id": "u", "from_uid": "f"}
        self.assertIs(resolve_pinduoduo_outbound(meta), sentinel)
        create_mock.assert_called_once_with("s", "u")

    @patch("Message.handlers.outbound_resolver.create_pinduoduo_outbound")
    def test_create_value_error_returns_none(self, create_mock) -> None:
        os.environ["USE_PINDUODUO_OUTBOUND"] = "1"
        create_mock.side_effect = ValueError("no account")
        meta = {"shop_id": "s", "user_id": "u", "from_uid": "f"}
        self.assertIsNone(resolve_pinduoduo_outbound(meta))

    def test_incomplete_context_returns_none(self) -> None:
        os.environ["USE_PINDUODUO_OUTBOUND"] = "true"
        self.assertIsNone(resolve_pinduoduo_outbound({"shop_id": "s"}))


if __name__ == "__main__":
    unittest.main()

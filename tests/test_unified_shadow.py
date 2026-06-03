"""Phase 7c：UnifiedMessage shadow 旁路测试。"""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from bridge.context import Context, ContextType, ChannelType
from Channel.pinduoduo.mappers.shadow import maybe_shadow_unified_message
from Channel.pinduoduo.mappers.shadow_flags import use_unified_message_shadow
from Channel.pinduoduo.pdd_message import PDDChatMessage

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


def _make_pdd() -> PDDChatMessage:
    with open(_FIXTURE, encoding="utf-8") as f:
        return PDDChatMessage(json.load(f))


class TestShadowFlags(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("USE_UNIFIED_MESSAGE_SHADOW", None)

    def test_default_false(self) -> None:
        os.environ.pop("USE_UNIFIED_MESSAGE_SHADOW", None)
        self.assertFalse(use_unified_message_shadow())

    def test_true_values(self) -> None:
        for val in ("1", "true", "TRUE", "on", "yes"):
            os.environ["USE_UNIFIED_MESSAGE_SHADOW"] = val
            self.assertTrue(use_unified_message_shadow(), msg=val)


class TestMaybeShadowUnifiedMessage(unittest.TestCase):
    def setUp(self) -> None:
        self._env_backup = os.environ.get("USE_UNIFIED_MESSAGE_SHADOW")
        os.environ.pop("USE_UNIFIED_MESSAGE_SHADOW", None)

    def tearDown(self) -> None:
        if self._env_backup is None:
            os.environ.pop("USE_UNIFIED_MESSAGE_SHADOW", None)
        else:
            os.environ["USE_UNIFIED_MESSAGE_SHADOW"] = self._env_backup

    @patch("Channel.pinduoduo.mappers.shadow.pdd_message_to_unified")
    def test_flag_off_does_not_call_mapper(self, mapper_mock: MagicMock) -> None:
        maybe_shadow_unified_message(
            _make_pdd(),
            _make_context(),
            shop_id="s",
            user_id="u",
            username="n",
        )
        mapper_mock.assert_not_called()

    @patch("Channel.pinduoduo.mappers.shadow.logger")
    @patch("Channel.pinduoduo.mappers.shadow.pdd_message_to_unified")
    def test_flag_on_calls_mapper(
        self, mapper_mock: MagicMock, logger_mock: MagicMock
    ) -> None:
        os.environ["USE_UNIFIED_MESSAGE_SHADOW"] = "true"
        unified = MagicMock()
        unified.message_id = "demo-msg-text-001"
        unified.content_type = "text"
        unified.conversation.extra = {"routing": "queue"}
        unified.conversation.shop_id = "demo_shop_001"
        unified.conversation.account_id = "demo_cs_uid_001"
        unified.conversation.buyer_uid = "demo_buyer_uid_001"
        unified.conversation.conversation_id = "demo_buyer_uid_001"
        mapper_mock.return_value = unified

        maybe_shadow_unified_message(
            _make_pdd(),
            _make_context(),
            shop_id="demo_shop_001",
            user_id="demo_cs_uid_001",
            username="demo_cs_user",
        )

        mapper_mock.assert_called_once()
        logger_mock.debug.assert_called()

    @patch("Channel.pinduoduo.mappers.shadow.logger")
    @patch("Channel.pinduoduo.mappers.shadow.pdd_message_to_unified")
    def test_mapper_exception_swallowed(
        self, mapper_mock: MagicMock, logger_mock: MagicMock
    ) -> None:
        os.environ["USE_UNIFIED_MESSAGE_SHADOW"] = "true"
        mapper_mock.side_effect = RuntimeError("mapper boom")

        maybe_shadow_unified_message(
            _make_pdd(),
            _make_context(),
            shop_id="s",
            user_id="u",
            username="n",
        )

        logger_mock.warning.assert_called()

    @patch("Channel.pinduoduo.mappers.shadow.logger")
    @patch("Channel.pinduoduo.mappers.shadow.pdd_message_to_unified")
    def test_mismatch_logs_warning(
        self, mapper_mock: MagicMock, logger_mock: MagicMock
    ) -> None:
        os.environ["USE_UNIFIED_MESSAGE_SHADOW"] = "true"
        unified = MagicMock()
        unified.message_id = "demo-msg-text-001"
        unified.content_type = "withdraw"
        unified.conversation.extra = {"routing": "immediate"}
        unified.conversation.shop_id = "s"
        unified.conversation.account_id = "u"
        unified.conversation.buyer_uid = "b"
        unified.conversation.conversation_id = "b"
        mapper_mock.return_value = unified

        maybe_shadow_unified_message(
            _make_pdd(),
            _make_context(),
            shop_id="demo_shop_001",
            user_id="demo_cs_uid_001",
            username="demo_cs_user",
        )

        warning_calls = [str(c) for c in logger_mock.warning.call_args_list]
        self.assertTrue(
            any("unified_shadow mismatch" in c for c in warning_calls),
            msg=f"expected mismatch warning, got {warning_calls}",
        )


if __name__ == "__main__":
    unittest.main()

"""Phase 7g：metadata_observability 单元测试。"""

from __future__ import annotations

import unittest

from bridge.context import Context, ContextType, ChannelType
from Message.metadata_adapter import get_content_type, get_platform, get_routing
from Message.metadata_observability import (
    OBSERVATION_KEYS,
    build_handler_observation,
    format_observation_for_log,
    redact_uid,
)


def _legacy_context() -> Context:
    return Context.create_pinduoduo_context(
        content="secret user message should never appear",
        msg_id="m1",
        from_uid="buyer_legacy_uid_12345678",
        user_msg_type=ContextType.TEXT,
        shop_id="shop_legacy",
        user_id="user_legacy_account_99",
        username="cs_user",
        shop_name="Shop",
        channel_type=ChannelType.PINDUODUO,
    )


def _legacy_metadata() -> dict:
    return {
        "message_id": "w1",
        "timestamp": 1.0,
        "retry_count": 0,
        "shop_id": "shop_legacy",
        "user_id": "user_legacy",
        "from_uid": "buyer_legacy_uid_12345678",
    }


def _unified_enrich_metadata() -> dict:
    base = _legacy_metadata()
    base.update(
        {
            "has_unified": True,
            "platform": "pinduoduo",
            "account_id": "user_legacy",
            "buyer_uid": "buyer_legacy_uid_12345678",
            "conversation_id": "buyer_legacy_uid_12345678",
            "content_type": "text",
            "routing": "queue",
            "unified_message_id": "m1",
        }
    )
    return base


_SENSITIVE_KEYS = frozenset(
    {"content", "raw", "body", "cookie", "token", "password", "reply"}
)

_FULL_BUYER_UID = "buyer_legacy_uid_12345678"


class TestRedactUid(unittest.TestCase):
    def test_redact_keeps_suffix(self) -> None:
        self.assertEqual(redact_uid("buyer_legacy_uid_12345678"), "***5678")

    def test_redact_none(self) -> None:
        self.assertIsNone(redact_uid(None))


class TestLegacyOnlyObservation(unittest.TestCase):
    def test_has_unified_false(self) -> None:
        meta = _legacy_metadata()
        ctx = _legacy_context()
        obs = build_handler_observation(meta, ctx)
        self.assertFalse(obs["has_unified"])
        self.assertEqual(obs["platform"], "pinduoduo")
        self.assertEqual(obs["content_type"], "text")
        self.assertEqual(obs["routing"], "queue")
        self.assertEqual(obs["message_id"], "w1")
        self.assertIsNone(obs["unified_message_id"])

    def test_matches_metadata_adapter(self) -> None:
        meta = _legacy_metadata()
        ctx = _legacy_context()
        obs = build_handler_observation(meta, ctx)
        self.assertEqual(obs["platform"], get_platform(meta, ctx))
        self.assertEqual(obs["content_type"], get_content_type(meta, ctx))
        self.assertEqual(obs["routing"], get_routing(meta, ctx))


class TestUnifiedEnrichObservation(unittest.TestCase):
    def test_has_unified_true(self) -> None:
        meta = _unified_enrich_metadata()
        ctx = _legacy_context()
        obs = build_handler_observation(meta, ctx)
        self.assertTrue(obs["has_unified"])
        self.assertEqual(obs["platform"], "pinduoduo")
        self.assertEqual(obs["content_type"], "text")
        self.assertEqual(obs["routing"], "queue")
        self.assertEqual(obs["unified_message_id"], "m1")

    def test_matches_metadata_adapter(self) -> None:
        meta = _unified_enrich_metadata()
        ctx = _legacy_context()
        obs = build_handler_observation(meta, ctx)
        self.assertEqual(obs["platform"], get_platform(meta, ctx))
        self.assertEqual(obs["content_type"], get_content_type(meta, ctx))
        self.assertEqual(obs["routing"], get_routing(meta, ctx))


class TestPrivacyBoundaries(unittest.TestCase):
    def test_snapshot_keys_are_safe(self) -> None:
        meta = _unified_enrich_metadata()
        ctx = _legacy_context()
        obs = build_handler_observation(meta, ctx, handler_name="AIReplyHandler")
        self.assertTrue(obs.keys() <= OBSERVATION_KEYS)
        self.assertFalse(obs.keys() & _SENSITIVE_KEYS)

    def test_full_buyer_uid_not_in_snapshot(self) -> None:
        meta = _unified_enrich_metadata()
        ctx = _legacy_context()
        obs = build_handler_observation(meta, ctx)
        snapshot_text = " ".join(str(v) for v in obs.values() if v is not None)
        self.assertNotIn(_FULL_BUYER_UID, snapshot_text)
        self.assertEqual(obs["conversation_suffix"], "***5678")

    def test_full_buyer_uid_not_in_log_format(self) -> None:
        meta = _unified_enrich_metadata()
        ctx = _legacy_context()
        obs = build_handler_observation(meta, ctx, handler_name="KeywordDetectionHandler")
        log_line = format_observation_for_log(obs)
        self.assertNotIn(_FULL_BUYER_UID, log_line)
        self.assertNotIn("secret user message", log_line)
        self.assertNotIn("\n", log_line)
        self.assertNotIn("{", log_line)
        self.assertNotIn("}", log_line)

    def test_forbidden_substrings_not_in_log(self) -> None:
        meta = _legacy_metadata()
        ctx = _legacy_context()
        log_line = format_observation_for_log(build_handler_observation(meta, ctx))
        for forbidden in _SENSITIVE_KEYS:
            self.assertNotIn(f"{forbidden}=", log_line)


class TestHandlerNameOptional(unittest.TestCase):
    def test_handler_name_included_when_provided(self) -> None:
        meta = _legacy_metadata()
        ctx = _legacy_context()
        obs = build_handler_observation(meta, ctx, handler_name="AIReplyHandler")
        self.assertEqual(obs["handler"], "AIReplyHandler")

    def test_handler_name_omitted_when_not_provided(self) -> None:
        meta = _legacy_metadata()
        ctx = _legacy_context()
        obs = build_handler_observation(meta, ctx)
        self.assertNotIn("handler", obs)


if __name__ == "__main__":
    unittest.main()

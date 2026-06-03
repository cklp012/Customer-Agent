"""Phase 7i：log_sanitizer 单元测试。"""

from __future__ import annotations

import unittest

from bridge.context import Context, ContextType, ChannelType
from Message.log_sanitizer import (
    content_length,
    format_account_ref,
    format_buyer_ref,
    format_cs_ref,
    format_message_type,
    format_send_context_log,
    format_user_ref,
    redact_uid,
)
from Message.metadata_observability import redact_uid as obs_redact_uid


_FULL_UID = "buyer_uid_12345678"
_ACCOUNT = "user_account_999"
_CS = "cs_staff_uid_abcdef12"
_USERNAME = "nickname_secret"


def _context(*, content: str | None = "hello") -> Context:
    return Context.create_pinduoduo_context(
        content=content or "",
        from_uid=_FULL_UID,
        username=_USERNAME,
        user_msg_type=ContextType.TEXT,
        shop_id="s1",
        user_id="u1",
        channel_type=ChannelType.PINDUODUO,
    )


class TestRedactUidReexport(unittest.TestCase):
    def test_matches_observability(self) -> None:
        self.assertEqual(redact_uid(_FULL_UID), obs_redact_uid(_FULL_UID))


class TestContentLength(unittest.TestCase):
    def test_none_is_zero(self) -> None:
        self.assertEqual(content_length(None), 0)

    def test_string_length(self) -> None:
        self.assertEqual(content_length("abcd"), 4)


class TestFormatUserRef(unittest.TestCase):
    def test_no_full_uid(self) -> None:
        ref = format_user_ref(_context())
        self.assertNotIn(_FULL_UID, ref)
        self.assertIn("buyer=", ref)
        self.assertIn("***5678", ref)

    def test_no_username(self) -> None:
        ref = format_user_ref(_context())
        self.assertNotIn(_USERNAME, ref)


class TestFormatMessageType(unittest.TestCase):
    def test_text_type(self) -> None:
        self.assertEqual(format_message_type(_context()), "text")


class TestFormatUidRefs(unittest.TestCase):
    def test_format_account_ref(self) -> None:
        self.assertEqual(format_account_ref(_ACCOUNT), "account=***_999")
        self.assertEqual(format_account_ref(None), "account=missing")

    def test_format_buyer_ref(self) -> None:
        self.assertEqual(format_buyer_ref(_FULL_UID), "buyer=***5678")
        self.assertEqual(format_buyer_ref(None), "buyer=missing")

    def test_format_cs_ref(self) -> None:
        self.assertNotIn(_CS, format_cs_ref(_CS))
        self.assertIn("cs=***", format_cs_ref(_CS))

    def test_format_send_context_log(self) -> None:
        line = format_send_context_log("shop1", _ACCOUNT, _FULL_UID)
        self.assertIn("shop_id=shop1", line)
        self.assertNotIn(_ACCOUNT, line)
        self.assertNotIn(_FULL_UID, line)
        self.assertIn("account=***", line)
        self.assertIn("buyer=***", line)

    def test_format_send_context_log_missing(self) -> None:
        line = format_send_context_log("s1", None, _FULL_UID)
        self.assertIn("account=missing", line)
        self.assertNotIn(_FULL_UID, line)


if __name__ == "__main__":
    unittest.main()

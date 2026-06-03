"""Phase 7i：log_sanitizer 单元测试。"""

from __future__ import annotations

import unittest

from bridge.context import Context, ContextType, ChannelType
from Message.log_sanitizer import (
    content_length,
    format_message_type,
    format_user_ref,
    redact_uid,
)
from Message.metadata_observability import redact_uid as obs_redact_uid


_FULL_UID = "buyer_uid_12345678"
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


if __name__ == "__main__":
    unittest.main()

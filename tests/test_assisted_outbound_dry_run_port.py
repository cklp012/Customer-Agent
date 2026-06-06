"""Phase 15c: Assisted outbound dry-run port tests."""

from __future__ import annotations

import importlib
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from product_persistence.services.assisted_outbound_port import (
    AssistedOutboundRequest,
    DryRunAssistedOutboundPort,
    build_assisted_outbound_request,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PORT_SOURCE = _REPO_ROOT / "product_persistence" / "services" / "assisted_outbound_port.py"
_HANDLER_SOURCES = tuple(
    (_REPO_ROOT / "Message" / "handlers").glob("**/*.py")
)


def _safe_request(**overrides) -> AssistedOutboundRequest:
    base = dict(
        workspace_id="ws-c-1",
        shop_id="shop-c-1",
        account_id="acc-c-1",
        platform_id="pinduoduo",
        buyer_id="buyer-c-1",
        pending_assisted_id="pending-c-1",
        reply_log_id="rl-c-1",
        final_reply="您好，该商品目前有货。",
        idempotency_key="assisted_send:pending-c-1",
        trace_id="trace-c-1",
        dry_run=True,
    )
    base.update(overrides)
    return AssistedOutboundRequest(**base)


class TestDryRunAssistedOutboundPort(unittest.TestCase):
    def setUp(self) -> None:
        self.port = DryRunAssistedOutboundPort()

    def test_c1_dry_run_port_would_send_safe_request(self) -> None:
        result = self.port.send(_safe_request())
        self.assertTrue(result.success)
        self.assertTrue(result.dry_run)
        self.assertTrue(result.would_send)
        self.assertEqual(result.platform_status, "dry_run_would_send")
        self.assertEqual(result.trace_id, "trace-c-1")

    def test_c2_dry_run_port_empty_reply_rejected(self) -> None:
        for empty in ("", "   ", None):
            with self.subTest(empty=empty):
                result = self.port.send(_safe_request(final_reply=empty))
                self.assertFalse(result.success)
                self.assertFalse(result.would_send)
                self.assertEqual(result.error_code, "empty_reply")

    def test_c3_dry_run_port_missing_buyer_rejected(self) -> None:
        for missing in ("", "   ", None):
            with self.subTest(missing=missing):
                result = self.port.send(_safe_request(buyer_id=missing))
                self.assertFalse(result.success)
                self.assertFalse(result.would_send)
                self.assertEqual(result.error_code, "missing_buyer_id")

    def test_c4_dry_run_result_has_no_provider_message_id(self) -> None:
        result = self.port.send(_safe_request())
        self.assertIsNone(result.provider_message_id)

    def test_c5_dry_run_result_sent_at_none(self) -> None:
        result = self.port.send(_safe_request())
        self.assertIsNone(result.sent_at)

    def test_build_assisted_outbound_request_defaults_dry_run(self) -> None:
        request = build_assisted_outbound_request(
            shop_id="shop-c-1",
            buyer_id="buyer-c-1",
            final_reply="hello",
        )
        self.assertTrue(request.dry_run)

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    @patch("Message.handlers.ai_handler.AIReplyHandler._send_reply")
    def test_no_send_side_effect(
        self,
        send_reply_mock: MagicMock,
        send_text_mock: MagicMock,
    ) -> None:
        self.port.send(_safe_request())
        send_reply_mock.assert_not_called()
        send_text_mock.assert_not_called()


class TestAssistedOutboundPortStaticChecks(unittest.TestCase):
    def _import_block(self, path: Path) -> str:
        import_lines = [
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        return "\n".join(import_lines)

    def test_c6_dry_run_port_does_not_import_SendMessage(self) -> None:
        block = self._import_block(_PORT_SOURCE)
        self.assertNotIn("SendMessage", block)

    def test_c7_dry_run_port_does_not_import_outbound_resolver(self) -> None:
        block = self._import_block(_PORT_SOURCE)
        self.assertNotIn("outbound_resolver", block)

    def test_c8_dry_run_port_does_not_import_Channel_pinduoduo_or_doudian(
        self,
    ) -> None:
        block = self._import_block(_PORT_SOURCE)
        self.assertNotIn("Channel.pinduoduo", block)
        self.assertNotIn("Channel.doudian", block)

    def test_c9_dry_run_port_does_not_import_legacy_database(self) -> None:
        block = self._import_block(_PORT_SOURCE)
        self.assertNotIn("database.models", block)
        self.assertNotIn("database.db_manager", block)

    def test_c11_no_handler_integration_static_check(self) -> None:
        source = _PORT_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("Message.handlers", source)
        self.assertNotIn("AssistedReplyService", source)
        assisted_source = (
            _REPO_ROOT / "product_persistence" / "services" / "assisted_reply_service.py"
        ).read_text(encoding="utf-8")
        self.assertIn("DryRunAssistedOutboundPort", assisted_source)
        self.assertNotIn("Message.handlers", assisted_source)


class TestAssistedSendFlags(unittest.TestCase):
    def setUp(self) -> None:
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_ASSISTED_SEND_ENABLED",
            "PRODUCT_ASSISTED_SEND_DRY_RUN",
            "PRODUCT_ASSISTED_SEND_TEST_SHOP_ID",
        ):
            os.environ.pop(key, None)
        importlib.reload(importlib.import_module("product_persistence.flags"))

    def tearDown(self) -> None:
        self._env_patch.stop()

    def test_c10_flags_default_enabled_false_dry_run_true(self) -> None:
        from product_persistence import flags

        self.assertFalse(flags.is_assisted_send_enabled())
        self.assertTrue(flags.is_assisted_send_dry_run())
        self.assertEqual(flags.get_assisted_send_test_shop_id(), "")
        self.assertFalse(flags.would_assisted_send_live())


if __name__ == "__main__":
    unittest.main()

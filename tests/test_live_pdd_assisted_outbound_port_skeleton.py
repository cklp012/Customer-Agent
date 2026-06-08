"""Phase 15m: LivePddAssistedOutboundPort skeleton tests."""

from __future__ import annotations

import importlib
import os
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from product_persistence import flags
from product_persistence.services.assisted_outbound_port import (
    AssistedOutboundPort,
    AssistedOutboundRequest,
    AssistedOutboundResult,
)
from product_persistence.services.live_pdd_assisted_outbound_port import (
    LivePddAssistedOutboundPort,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PORT_SOURCE = (
    _REPO_ROOT / "product_persistence" / "services" / "live_pdd_assisted_outbound_port.py"
)
_ASSISTED_SERVICE_SOURCE = (
    _REPO_ROOT / "product_persistence" / "services" / "assisted_reply_service.py"
)
_TEST_SHOP_ID = "shop-m-1"


def _live_request(**overrides) -> AssistedOutboundRequest:
    base = dict(
        workspace_id="ws-m-1",
        shop_id=_TEST_SHOP_ID,
        account_id="acc-m-1",
        platform_id="pinduoduo",
        buyer_id="buyer-m-1",
        pending_assisted_id="pending-m-1",
        reply_log_id="rl-m-1",
        final_reply="您好，该商品目前有货。",
        idempotency_key="assisted_send:pending-m-1",
        trace_id="trace-m-1",
        dry_run=False,
    )
    base.update(overrides)
    return AssistedOutboundRequest(**base)


def _enable_live_flags(*, shop_id: str = _TEST_SHOP_ID) -> None:
    os.environ["PRODUCT_ASSISTED_SEND_ENABLED"] = "true"
    os.environ["PRODUCT_ASSISTED_SEND_DRY_RUN"] = "false"
    os.environ["PRODUCT_ASSISTED_SEND_TEST_SHOP_ID"] = shop_id
    importlib.reload(flags)


class TestLivePddAssistedOutboundPortSkeleton(unittest.TestCase):
    def setUp(self) -> None:
        self._env_patch = patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for key in (
            "PRODUCT_ASSISTED_SEND_ENABLED",
            "PRODUCT_ASSISTED_SEND_DRY_RUN",
            "PRODUCT_ASSISTED_SEND_TEST_SHOP_ID",
        ):
            os.environ.pop(key, None)
        importlib.reload(flags)
        self.port = LivePddAssistedOutboundPort()

    def tearDown(self) -> None:
        self._env_patch.stop()

    def test_m1_live_pdd_port_class_exists(self) -> None:
        self.assertTrue(hasattr(LivePddAssistedOutboundPort, "send"))

    def test_m2_implements_assisted_outbound_port(self) -> None:
        self.assertTrue(issubclass(LivePddAssistedOutboundPort, AssistedOutboundPort))

    def test_m3_uses_assisted_outbound_request_and_result(self) -> None:
        result = self.port.send(_live_request())
        self.assertIsInstance(result, AssistedOutboundResult)

    def test_m4_rejects_non_pdd_platform(self) -> None:
        result = self.port.send(_live_request(platform_id="doudian"))
        self.assertFalse(result.success)
        self.assertFalse(result.would_send)
        self.assertEqual(result.platform_status, "validation_failed")
        self.assertEqual(result.error_code, "unsupported_platform")

    def test_m5_rejects_missing_shop_id(self) -> None:
        for missing in ("", "   ", None):
            with self.subTest(missing=missing):
                result = self.port.send(_live_request(shop_id=missing))
                self.assertEqual(result.error_code, "missing_shop_id")
                self.assertEqual(result.platform_status, "validation_failed")

    def test_m6_rejects_missing_buyer_id(self) -> None:
        for missing in ("", "   ", None):
            with self.subTest(missing=missing):
                result = self.port.send(_live_request(buyer_id=missing))
                self.assertEqual(result.error_code, "missing_buyer_id")
                self.assertEqual(result.platform_status, "validation_failed")

    def test_m7_rejects_empty_final_reply(self) -> None:
        for empty in ("", "   ", None):
            with self.subTest(empty=empty):
                result = self.port.send(_live_request(final_reply=empty))
                self.assertEqual(result.error_code, "empty_final_reply")
                self.assertEqual(result.platform_status, "validation_failed")

    def test_m8_rejects_missing_pending_assisted_id(self) -> None:
        for missing in ("", "   ", None):
            with self.subTest(missing=missing):
                result = self.port.send(_live_request(pending_assisted_id=missing))
                self.assertEqual(result.error_code, "missing_pending_assisted_id")

    def test_m9_rejects_missing_reply_log_id(self) -> None:
        for missing in ("", "   ", None):
            with self.subTest(missing=missing):
                result = self.port.send(_live_request(reply_log_id=missing))
                self.assertEqual(result.error_code, "missing_reply_log_id")

    def test_m10_rejects_missing_idempotency_key(self) -> None:
        for missing in ("", "   ", None):
            with self.subTest(missing=missing):
                result = self.port.send(_live_request(idempotency_key=missing))
                self.assertEqual(result.error_code, "missing_idempotency_key")

    def test_m11_default_flags_live_send_disabled_no_send(self) -> None:
        result = self.port.send(_live_request())
        self.assertFalse(result.success)
        self.assertFalse(result.would_send)
        self.assertEqual(result.platform_status, "unavailable")
        self.assertEqual(result.error_code, "live_send_disabled")

    def test_m12_dry_run_true_no_live_send(self) -> None:
        os.environ["PRODUCT_ASSISTED_SEND_ENABLED"] = "true"
        importlib.reload(flags)
        result = self.port.send(_live_request(dry_run=True))
        self.assertFalse(result.success)
        self.assertEqual(result.platform_status, "live_send_not_implemented")
        self.assertEqual(result.error_code, "dry_run_required")

        os.environ["PRODUCT_ASSISTED_SEND_DRY_RUN"] = "true"
        importlib.reload(flags)
        result = self.port.send(_live_request(dry_run=False))
        self.assertEqual(result.error_code, "dry_run_required")

    def test_m13_non_allowlisted_shop_no_send(self) -> None:
        _enable_live_flags(shop_id="other-shop")
        result = self.port.send(_live_request(shop_id=_TEST_SHOP_ID))
        self.assertFalse(result.success)
        self.assertEqual(result.platform_status, "unavailable")
        self.assertEqual(result.error_code, "shop_not_allowlisted")

    def test_m14_all_live_flags_enabled_still_live_send_not_implemented(self) -> None:
        _enable_live_flags()
        result = self.port.send(_live_request())
        self.assertFalse(result.success)
        self.assertFalse(result.dry_run)
        self.assertFalse(result.would_send)
        self.assertEqual(result.platform_status, "live_send_not_implemented")
        self.assertEqual(result.error_code, "live_send_not_implemented")
        self.assertEqual(result.trace_id, "trace-m-1")

    def test_m15_provider_message_id_not_faked(self) -> None:
        _enable_live_flags()
        result = self.port.send(_live_request())
        self.assertIsNone(result.provider_message_id)

    def test_m16_sent_at_none_when_not_sent(self) -> None:
        _enable_live_flags()
        result = self.port.send(_live_request())
        self.assertIsNone(result.sent_at)

    def test_m17_no_cookie_token_credential_in_error(self) -> None:
        forbidden = ("cookie", "token", "credential", "password", "secret", "session")
        cases = (
            _live_request(platform_id="doudian"),
            _live_request(buyer_id=""),
            _live_request(),
            _live_request(dry_run=True),
        )
        _enable_live_flags()
        cases = cases + (_live_request(),)
        for request in cases:
            result = self.port.send(request)
            message = (result.error_message or "").lower()
            for token in forbidden:
                self.assertNotIn(token, message, msg=result.error_code)

    @patch("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text")
    @patch(
        "Message.handlers.ai_handler.AIReplyHandler._send_reply",
        new_callable=AsyncMock,
    )
    def test_m23_no_real_send_called_runtime(
        self,
        send_reply_mock: AsyncMock,
        send_text_mock: MagicMock,
    ) -> None:
        _enable_live_flags()
        self.port.send(_live_request())
        send_reply_mock.assert_not_awaited()
        send_text_mock.assert_not_called()

    def test_m24_pdd_queue_name_unchanged(self) -> None:
        from Message.queue_naming import pdd_queue_name

        self.assertEqual(pdd_queue_name("shop123"), "pdd_shop123")

    def test_m25_no_auto_send(self) -> None:
        service_source = _ASSISTED_SERVICE_SOURCE.read_text(encoding="utf-8")
        self.assertIn("DryRunAssistedOutboundPort", service_source)
        self.assertNotIn("LivePddAssistedOutboundPort", service_source)


class TestLivePddAssistedOutboundPortStaticChecks(unittest.TestCase):
    def _import_block(self) -> str:
        import_lines = [
            line
            for line in _PORT_SOURCE.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        return "\n".join(import_lines)

    def _full_source(self) -> str:
        return _PORT_SOURCE.read_text(encoding="utf-8")

    def test_m18_no_sendmessage_import(self) -> None:
        self.assertNotIn("SendMessage", self._import_block())

    def test_m19_no_handler_import(self) -> None:
        self.assertNotIn("Message.handlers", self._full_source())

    def test_m20_no_pdd_doudian_import(self) -> None:
        block = self._import_block()
        self.assertNotIn("Channel.pinduoduo", block)
        self.assertNotIn("Channel.doudian", block)

    def test_m21_no_legacy_database_import(self) -> None:
        block = self._import_block()
        self.assertNotIn("database.models", block)
        self.assertNotIn("database.db_manager", block)

    def test_m22_no_outbound_resolver_import(self) -> None:
        self.assertNotIn("outbound_resolver", self._full_source())

    def test_no_autoreplythread_import(self) -> None:
        self.assertNotIn("AutoReplyThread", self._full_source())


class TestLivePddPortPackageExport(unittest.TestCase):
    def test_live_port_exportable_without_db_or_send(self) -> None:
        from product_persistence.services import LivePddAssistedOutboundPort as exported

        self.assertIs(exported, LivePddAssistedOutboundPort)


if __name__ == "__main__":
    unittest.main()

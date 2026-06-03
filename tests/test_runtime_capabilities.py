"""Phase 8d：runtime_capabilities 单元测试。"""

from __future__ import annotations

import os
import unittest

from Message.runtime_capabilities import (
    build_runtime_capability_report,
    format_capability_report_for_console,
    get_channel_registry_status,
    infer_autoreply_channel_source,
    read_all_runtime_flags,
)


class TestReadAllRuntimeFlags(unittest.TestCase):
    def tearDown(self) -> None:
        for key in (
            "USE_PINDUODUO_CHANNEL_WRAPPER",
            "USE_PINDUODUO_OUTBOUND",
            "USE_UNIFIED_MESSAGE_SHADOW",
            "USE_UNIFIED_MESSAGE_DUAL_TRACK",
            "USE_UNIFIED_OUTBOUND_RESOLVER",
            "USE_CHANNEL_REGISTRY_FOR_AUTOREPLY",
        ):
            os.environ.pop(key, None)

    def test_defaults_all_false(self) -> None:
        for key in (
            "USE_PINDUODUO_CHANNEL_WRAPPER",
            "USE_PINDUODUO_OUTBOUND",
            "USE_UNIFIED_MESSAGE_SHADOW",
            "USE_UNIFIED_MESSAGE_DUAL_TRACK",
            "USE_UNIFIED_OUTBOUND_RESOLVER",
            "USE_CHANNEL_REGISTRY_FOR_AUTOREPLY",
        ):
            os.environ.pop(key, None)
        flags = read_all_runtime_flags()
        self.assertFalse(flags["USE_PINDUODUO_CHANNEL_WRAPPER"])
        self.assertFalse(flags["USE_PINDUODUO_OUTBOUND"])
        self.assertFalse(flags["USE_UNIFIED_OUTBOUND_RESOLVER"])
        self.assertFalse(flags["USE_UNIFIED_MESSAGE_DUAL_TRACK"])
        self.assertFalse(flags["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"])

    def test_infer_autoreply_source_defaults(self) -> None:
        flags = read_all_runtime_flags()
        self.assertEqual(
            infer_autoreply_channel_source(flags=flags, registry_platforms=[]),
            "legacy_factory",
        )

    def test_infer_autoreply_source_registry_on_registered(self) -> None:
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = "true"
        flags = read_all_runtime_flags()
        self.assertEqual(
            infer_autoreply_channel_source(
                flags=flags,
                registry_platforms=["pinduoduo"],
            ),
            "registry",
        )

    def test_infer_autoreply_source_registry_on_missing(self) -> None:
        os.environ["USE_CHANNEL_REGISTRY_FOR_AUTOREPLY"] = "true"
        flags = read_all_runtime_flags()
        self.assertEqual(
            infer_autoreply_channel_source(flags=flags, registry_platforms=[]),
            "registry_fallback",
        )

    def test_unified_outbound_flag(self) -> None:
        os.environ["USE_UNIFIED_OUTBOUND_RESOLVER"] = "true"
        flags = read_all_runtime_flags()
        report = build_runtime_capability_report(flags=flags)
        self.assertTrue(flags["USE_UNIFIED_OUTBOUND_RESOLVER"])
        self.assertTrue(report.handler_unified_outbound_enabled)
        self.assertIn("resolve_outbound", report.handler_outbound_resolver)

    def test_dual_track_flag(self) -> None:
        os.environ["USE_UNIFIED_MESSAGE_DUAL_TRACK"] = "on"
        flags = read_all_runtime_flags()
        report = build_runtime_capability_report(flags=flags)
        self.assertTrue(report.unified_inbound_dual_track_enabled)


class TestRuntimeCapabilityReport(unittest.TestCase):
    def test_channel_registry_empty_is_valid(self) -> None:
        platforms = get_channel_registry_status()
        self.assertIsInstance(platforms, list)

    def test_import_checks_present(self) -> None:
        from Message.runtime_capabilities import check_module_imports

        imports = check_module_imports()
        self.assertTrue(imports["pdd_core"]["PinduoduoChannel"])
        self.assertTrue(imports["demo_8a"]["demo_raw_to_context"])
        self.assertTrue(imports["outbound_8b_8c"]["resolve_outbound"])

    def test_format_contains_key_fields(self) -> None:
        report = build_runtime_capability_report()
        text = format_capability_report_for_console(report)
        for token in (
            "Active PDD send path",
            "Handler outbound resolver",
            "pdd_message_handler",
            "Demo test runtime",
            "ChannelRegistry platforms",
            "Bootstrap status",
            "Default registration plan",
            "AutoReply channel source",
        ):
            self.assertIn(token, text, msg=f"missing {token}")


if __name__ == "__main__":
    unittest.main()

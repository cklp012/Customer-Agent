"""Phase 15r: Local dashboard action smoke script skeleton tests."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "smoke_dashboard_action_routes.py"
_APP_PATH = _REPO_ROOT / "app.py"
_SMOKE_DB = _REPO_ROOT / "temp" / "product_smoke_dashboard_action.db"

_FORBIDDEN_SCRIPT_STRINGS = (
    "SendMessage",
    "Message.handlers",
    "outbound_resolver",
    "Channel.pinduoduo",
    "Channel.doudian",
    "database.models",
    "database.db_manager",
    "AutoReplyThread",
    "LivePddAssistedOutboundPort",
)

_FLAG_KEYS = (
    "PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED",
    "PRODUCT_ASSISTED_SEND_ENABLED",
    "PRODUCT_ASSISTED_SEND_DRY_RUN",
    "PRODUCT_ASSISTED_SEND_TEST_SHOP_ID",
)


def _load_smoke_module():
    module_name = "smoke_dashboard_action_routes_phase15r"
    spec = importlib.util.spec_from_file_location(module_name, _SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    spec.loader.exec_module(module)
    return module


class TestPhase15rSmokeScriptSkeleton(unittest.TestCase):
    def test_r1_script_exists(self) -> None:
        self.assertTrue(_SCRIPT_PATH.is_file())

    def test_r2_script_has_main(self) -> None:
        source = _SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertIn("def main(", source)
        self.assertIn('if __name__ == "__main__":', source)

    def test_r3_script_import_safe_no_side_effect(self) -> None:
        mod = _load_smoke_module()
        result = mod.check_import_no_registration_or_db()
        self.assertTrue(result.passed, msg=result.detail)

    def test_r4_script_default_does_not_create_db(self) -> None:
        mod = _load_smoke_module()
        result = mod.check_import_no_registration_or_db()
        self.assertTrue(result.passed, msg=result.detail)

    def test_r5_script_does_not_modify_env_after_run(self) -> None:
        before = {key: os.environ.get(key) for key in _FLAG_KEYS}
        proc = subprocess.run(
            [sys.executable, str(_SCRIPT_PATH)],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        after = {key: os.environ.get(key) for key in _FLAG_KEYS}
        self.assertEqual(before, after, msg="parent process env changed")
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)

    def test_r6_script_forbidden_imports_absent(self) -> None:
        import_lines = [
            line
            for line in _SCRIPT_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        block = "\n".join(import_lines)
        for token in _FORBIDDEN_SCRIPT_STRINGS:
            self.assertNotIn(token, block, msg=token)

    def test_r7_script_checks_pdd_queue_name(self) -> None:
        mod = _load_smoke_module()
        result = mod.check_pdd_queue_name()
        self.assertTrue(result.passed)
        self.assertEqual(result.detail, "pdd_shop123")

    def test_r8_script_returns_zero_on_safe_smoke(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(_SCRIPT_PATH)],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        self.assertIn("SUMMARY: PASS", proc.stdout)

    def test_r9_script_pass_summary_contains_no_send(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(_SCRIPT_PATH)],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        combined = proc.stdout.lower()
        self.assertIn("no-send", combined)
        self.assertIn("no_send_runtime", proc.stdout)

    def test_r10_script_fail_returns_nonzero_when_check_fails(self) -> None:
        mod = _load_smoke_module()

        def _fail() -> mod.SmokeCheckResult:
            return mod.SmokeCheckResult(
                name="injected_fail",
                passed=False,
                detail="unittest injected failure",
            )

        results = mod.run_smoke_checks(extra_checks=[_fail])
        exit_code = 0 if all(r.passed for r in results) else 1
        self.assertEqual(exit_code, 1)

    def test_r11_no_sendmessage_called_runtime(self) -> None:
        mod = _load_smoke_module()
        result = mod.check_no_send_runtime()
        self.assertTrue(result.passed, msg=result.detail)

    def test_r12_no_handler_called_runtime(self) -> None:
        mod = _load_smoke_module()
        result = mod.check_no_send_runtime()
        self.assertIn("handler", result.detail.lower())

    def test_r13_no_pdd_doudian_import(self) -> None:
        mod = _load_smoke_module()
        result = mod.assert_no_forbidden_imports()
        self.assertTrue(result.passed)

    def test_r14_no_live_send_flags_enabled_by_default(self) -> None:
        mod = _load_smoke_module()
        result = mod.check_default_flags()
        self.assertTrue(result.passed, msg=result.detail)

    def test_r15_no_app_py_modified_or_required(self) -> None:
        source = _SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertNotIn("import app", source)
        self.assertNotIn("from app", source)
        self.assertTrue(_APP_PATH.is_file())

    def test_r16_smoke_uses_temp_db_only_if_needed(self) -> None:
        mod = _load_smoke_module()
        self.assertEqual(mod._SMOKE_DB.name, "product_smoke_dashboard_action.db")
        self.assertIn("temp", mod._SMOKE_DB.parts)
        mod._cleanup_smoke_db()
        result = mod.check_dry_run_response_shape()
        self.assertTrue(result.passed, msg=result.detail)
        self.assertFalse(_SMOKE_DB.exists(), msg="smoke db should be cleaned up")


if __name__ == "__main__":
    unittest.main()

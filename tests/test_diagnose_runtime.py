"""Phase 8d：diagnose_runtime.py 冒烟测试。"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


class TestDiagnoseRuntimeScript(unittest.TestCase):
    def test_subprocess_exit_zero_and_output_tokens(self) -> None:
        root = _project_root()
        script = root / "scripts" / "diagnose_runtime.py"
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=f"stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}",
        )
        out = proc.stdout
        for token in (
            "USE_UNIFIED_OUTBOUND_RESOLVER",
            "Runtime capability report",
            "Platform bootstrap",
            "Available platforms",
            "AutoReplyThread",
            "ChannelRegistry",
            "pdd_message_handler",
            "Demo test runtime",
        ):
            self.assertIn(token, out, msg=f"missing token: {token}")


if __name__ == "__main__":
    unittest.main()

"""Phase 8c：USE_UNIFIED_OUTBOUND_RESOLVER 开关测试。"""

from __future__ import annotations

import os
import unittest

from Message.handlers.unified_outbound_flags import use_unified_outbound_resolver


class TestUnifiedOutboundFlags(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("USE_UNIFIED_OUTBOUND_RESOLVER", None)

    def test_default_false(self) -> None:
        os.environ.pop("USE_UNIFIED_OUTBOUND_RESOLVER", None)
        self.assertFalse(use_unified_outbound_resolver())

    def test_true_values(self) -> None:
        for val in ("1", "true", "yes", "on", "TRUE", " On "):
            with self.subTest(val=val):
                os.environ["USE_UNIFIED_OUTBOUND_RESOLVER"] = val
                self.assertTrue(use_unified_outbound_resolver())

    def test_other_values_false(self) -> None:
        for val in ("", "0", "false", "no", "off", "maybe"):
            with self.subTest(val=val):
                os.environ["USE_UNIFIED_OUTBOUND_RESOLVER"] = val
                self.assertFalse(use_unified_outbound_resolver())


if __name__ == "__main__":
    unittest.main()

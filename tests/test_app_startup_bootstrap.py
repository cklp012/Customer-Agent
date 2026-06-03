"""Phase 8f：app 启动 ChannelRegistry bootstrap 测试。"""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from Message.runtime_bootstrap import (
    apply_app_startup_bootstrap,
    clear_channel_registry_for_tests,
    get_default_registration_plan,
)


class TestApplyAppStartupBootstrap(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("USE_DEMO_CHANNEL_REGISTRATION", None)
        clear_channel_registry_for_tests()

    @patch("Message.runtime_bootstrap.register_default_platforms")
    @patch("utils.logger_loguru.get_logger")
    def test_apply_app_startup_bootstrap_success(
        self,
        logger_mock: MagicMock,
        register_mock: MagicMock,
    ) -> None:
        register_mock.return_value = ["pinduoduo"]
        log = MagicMock()
        logger_mock.return_value = log

        apply_app_startup_bootstrap()

        register_mock.assert_called_once()
        log.info.assert_called_once()
        self.assertIn("pinduoduo", str(log.info.call_args))

    @patch("Message.runtime_bootstrap.register_default_platforms")
    @patch("utils.logger_loguru.get_logger")
    def test_apply_app_startup_bootstrap_failure_swallowed(
        self,
        logger_mock: MagicMock,
        register_mock: MagicMock,
    ) -> None:
        register_mock.side_effect = RuntimeError("bootstrap failed")
        log = MagicMock()
        logger_mock.return_value = log

        apply_app_startup_bootstrap()

        log.warning.assert_called_once()
        self.assertTrue(log.warning.call_args.kwargs.get("exc_info"))

    def test_register_still_only_pdd_by_default(self) -> None:
        os.environ.pop("USE_DEMO_CHANNEL_REGISTRATION", None)
        self.assertEqual(get_default_registration_plan(), ["pinduoduo"])


if __name__ == "__main__":
    unittest.main()

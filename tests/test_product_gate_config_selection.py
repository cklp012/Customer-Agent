"""Phase 13d: product gate config / allowlist selection."""

from __future__ import annotations

import unittest

from Message.gates.product_gate_config import (
    ProductGateConfig,
    TestShopAllowlistEntry,
    clear_test_shop_allowlist,
    select_product_gate_config,
    set_test_shop_allowlist,
)

_WS = "ws-test-0001"
_SHOP = "shop_pdd_preview_test"
_ACCOUNT = "acc_pdd_preview_test"


def _entry(**kwargs) -> TestShopAllowlistEntry:
    defaults = {
        "workspace_id": _WS,
        "shop_id": _SHOP,
        "account_id": _ACCOUNT,
    }
    defaults.update(kwargs)
    return TestShopAllowlistEntry(**defaults)


def _meta(**kwargs) -> dict:
    base = {
        "workspace_id": _WS,
        "shop_id": _SHOP,
        "account_id": _ACCOUNT,
        "platform_id": "pinduoduo",
    }
    base.update(kwargs)
    return base


class TestProductGateConfigSelection(unittest.TestCase):
    def tearDown(self) -> None:
        clear_test_shop_allowlist()

    def test_default_disabled(self) -> None:
        clear_test_shop_allowlist()
        cfg = select_product_gate_config(_meta())
        self.assertFalse(cfg.product_gate_enabled)

    def test_pinduoduo_exact_match_enabled(self) -> None:
        set_test_shop_allowlist([_entry()])
        cfg = select_product_gate_config(_meta())
        self.assertTrue(cfg.product_gate_enabled)
        self.assertEqual(cfg.reply_mode, "preview")
        self.assertTrue(cfg.consultation_only)
        self.assertEqual(cfg.shop_id, _SHOP)
        self.assertEqual(cfg.account_id, _ACCOUNT)

    def test_platform_pdd_alias(self) -> None:
        set_test_shop_allowlist([_entry()])
        cfg = select_product_gate_config(_meta(platform_id="pdd", platform="pdd"))
        self.assertTrue(cfg.product_gate_enabled)

    def test_shop_id_mismatch_disabled(self) -> None:
        set_test_shop_allowlist([_entry()])
        cfg = select_product_gate_config(_meta(shop_id="other_shop"))
        self.assertFalse(cfg.product_gate_enabled)

    def test_account_id_mismatch_disabled(self) -> None:
        set_test_shop_allowlist([_entry()])
        cfg = select_product_gate_config(_meta(account_id="other_acc"))
        self.assertFalse(cfg.product_gate_enabled)

    def test_shop_name_same_id_mismatch_disabled(self) -> None:
        set_test_shop_allowlist([_entry()])
        cfg = select_product_gate_config(
            _meta(shop_id="wrong_id", shop_name="Golden Test Shop Name")
        )
        self.assertFalse(cfg.product_gate_enabled)

    def test_doudian_disabled(self) -> None:
        set_test_shop_allowlist([_entry()])
        cfg = select_product_gate_config(_meta(platform_id="doudian", platform="doudian"))
        self.assertFalse(cfg.product_gate_enabled)

    def test_taobao_disabled(self) -> None:
        set_test_shop_allowlist([_entry()])
        cfg = select_product_gate_config(_meta(platform_id="taobao"))
        self.assertFalse(cfg.product_gate_enabled)

    def test_clear_allowlist_disabled(self) -> None:
        set_test_shop_allowlist([_entry()])
        clear_test_shop_allowlist()
        cfg = select_product_gate_config(_meta())
        self.assertFalse(cfg.product_gate_enabled)

    def test_missing_workspace_id_disabled(self) -> None:
        set_test_shop_allowlist([_entry()])
        meta = _meta()
        del meta["workspace_id"]
        cfg = select_product_gate_config(meta)
        self.assertFalse(cfg.product_gate_enabled)

    def test_missing_account_id_disabled(self) -> None:
        set_test_shop_allowlist([_entry()])
        meta = _meta()
        del meta["account_id"]
        cfg = select_product_gate_config(meta)
        self.assertFalse(cfg.product_gate_enabled)

    def test_reply_mode_not_preview_disabled(self) -> None:
        set_test_shop_allowlist([_entry(reply_mode="assisted")])
        cfg = select_product_gate_config(_meta())
        self.assertFalse(cfg.product_gate_enabled)

    def test_product_gate_enabled_false_on_entry(self) -> None:
        set_test_shop_allowlist([_entry(product_gate_enabled=False)])
        cfg = select_product_gate_config(_meta())
        self.assertFalse(cfg.product_gate_enabled)

    def test_disabled_config_is_frozen_default_shape(self) -> None:
        cfg = select_product_gate_config({})
        self.assertIsInstance(cfg, ProductGateConfig)
        self.assertFalse(cfg.product_gate_enabled)


if __name__ == "__main__":
    unittest.main()

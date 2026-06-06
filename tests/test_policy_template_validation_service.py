"""Phase 14w: Policy / Template validation service tests (W1–W15)."""

from __future__ import annotations

import unittest
from pathlib import Path

from product_persistence.services.policy_template_validation_service import (
    PolicyValidationResult,
    TemplateValidationResult,
    compute_content_hash,
    validate_policy_mode,
    validate_reply_template,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SERVICE_SOURCE = (
    _REPO_ROOT
    / "product_persistence"
    / "services"
    / "policy_template_validation_service.py"
)


class TestPolicyTemplateValidationService(unittest.TestCase):
    def test_w1_policy_allows_within_ceiling(self) -> None:
        result = validate_policy_mode(
            intent_category="product_question",
            requested_mode="assisted_only",
            platform_ceiling="auto_allowed",
        )
        self.assertIsInstance(result, PolicyValidationResult)
        self.assertTrue(result.valid)
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.effective_mode, "assisted_only")

    def test_w2_policy_rejects_above_ceiling(self) -> None:
        result = validate_policy_mode(
            intent_category="refund_request",
            requested_mode="auto_allowed",
            platform_ceiling="assisted_only",
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.status, "rejected")
        self.assertIn("超过 platform_ceiling", result.reason or "")

    def test_w3_redline_intent_forces_blocked(self) -> None:
        result = validate_policy_mode(
            intent_category="private_contact",
            requested_mode="guide_only",
            platform_ceiling="blocked",
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.effective_mode, "blocked")
        self.assertIn("红线", result.reason or "")

    def test_w4_unknown_intent_conservative_ceiling(self) -> None:
        result = validate_policy_mode(
            intent_category="unknown_future_intent",
            requested_mode="auto_allowed",
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.platform_ceiling, "assisted_only")
        self.assertEqual(result.status, "rejected")

    def test_w5_shop_reply_mode_cap_applies(self) -> None:
        result = validate_policy_mode(
            intent_category="product_question",
            requested_mode="assisted_only",
            platform_ceiling="auto_allowed",
            shop_reply_mode_cap="template_only",
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.effective_mode, "template_only")

    def test_w6_template_safe_refund_guidance_passes(self) -> None:
        result = validate_reply_template(
            "亲，请通过平台售后入口申请退款，我们会按照平台流程处理。",
            intent_category="refund_request",
        )
        self.assertIsInstance(result, TemplateValidationResult)
        self.assertEqual(result.validation_status, "passed")

    def test_w7_template_forbidden_refund_promise_rejected(self) -> None:
        result = validate_reply_template("好的，直接退款给您。")
        self.assertEqual(result.validation_status, "rejected")
        self.assertEqual(result.forbidden_category, "forbidden_promise")
        self.assertEqual(result.forbidden_keyword, "直接退款")

    def test_w8_template_off_platform_rejected(self) -> None:
        result = validate_reply_template("请加微信联系我。")
        self.assertEqual(result.validation_status, "rejected")
        self.assertEqual(result.forbidden_category, "off_platform_risk")
        self.assertEqual(result.forbidden_keyword, "加微信")

    def test_w9_template_review_manipulation_rejected(self) -> None:
        result = validate_reply_template("好评返现哦。")
        self.assertEqual(result.validation_status, "rejected")
        self.assertEqual(result.forbidden_category, "review_manipulation")

    def test_w10_template_empty_rejected(self) -> None:
        result = validate_reply_template("   ")
        self.assertEqual(result.validation_status, "rejected")
        self.assertIn("为空", result.reason or "")

    def test_w11_template_unknown_variable_rejected(self) -> None:
        result = validate_reply_template(
            "您好 {{buyer_nick}}",
            variables={"buyer_nick": "小明", "secret_phone": "123"},
        )
        self.assertEqual(result.validation_status, "rejected")
        self.assertIn("secret_phone", result.reason or "")

    def test_w12_template_allowed_variables_pass(self) -> None:
        result = validate_reply_template(
            "您好 {{buyer_nick}}，商品 {{product_name}} 目前有货。",
            variables={
                "buyer_nick": "小明",
                "product_name": "示例商品",
                "shop_name": "示例店",
            },
        )
        self.assertEqual(result.validation_status, "passed")

    def test_w13_template_content_hash_stable(self) -> None:
        content = "赠品以活动页面显示为准。"
        expected = compute_content_hash(content)
        result = validate_reply_template(content)
        self.assertEqual(result.content_hash, expected)
        self.assertEqual(compute_content_hash(content), expected)

    def test_w14_validation_service_no_send_side_effect_static_import_check(self) -> None:
        source = _SERVICE_SOURCE.read_text(encoding="utf-8")
        import_lines = [
            line
            for line in source.splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        import_block = "\n".join(import_lines)
        forbidden = (
            "SendMessage",
            "Message.handlers",
            "outbound_resolver",
            "unified_outbound",
            "Channel.pinduoduo",
            "Channel.doudian",
            "database.models",
            "database.db_manager",
        )
        for token in forbidden:
            self.assertNotIn(token, import_block, msg=f"unexpected import: {token}")

    def test_w15_service_does_not_import_repositories_or_db(self) -> None:
        source = _SERVICE_SOURCE.read_text(encoding="utf-8")
        import_lines = [
            line
            for line in source.splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        import_block = "\n".join(import_lines)
        self.assertNotIn("product_persistence.repositories", import_block)
        self.assertNotIn("product_persistence.db_manager", import_block)
        self.assertNotIn("sqlite3", import_block)


if __name__ == "__main__":
    unittest.main()

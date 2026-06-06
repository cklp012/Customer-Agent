"""Phase 14v: Final Guard pure function tests (T1–T25)."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from Message.gates.final_guard import (
    FinalGuardInput,
    evaluate_final_guard,
    scan_forbidden_promise,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FINAL_GUARD_SOURCE = _REPO_ROOT / "Message" / "gates" / "final_guard.py"

_NOW = "2026-06-03T12:00:00+00:00"
_FUTURE = "2026-06-04T12:00:00+00:00"
_STALE_INBOUND = "2026-06-03T10:00:00+00:00"


def _assisted_base(**overrides) -> FinalGuardInput:
    ctx = FinalGuardInput(
        product_gate_enabled=True,
        workspace_pause=False,
        shop_pause=False,
        workspace_id="ws-v-1",
        shop_id="shop-v-1",
        account_id="acc-v-1",
        platform_id="pinduoduo",
        actor_user_id="op-1",
        actor_role="operator",
        reply_log_id="rl-v-1",
        pending_assisted_id="pending-v-1",
        buyer_id="buyer-v-1",
        inbound_message_id="in-v-1",
        buyer_message="这款还有货吗",
        final_reply="您好，该商品目前有货，欢迎下单。",
        intent_category="inventory_question",
        intent="inventory_question",
        intent_bucket="allowed",
        risk_level="low",
        policy_id="policy-v-1",
        policy_version=1,
        ai_intervention_mode="template_only",
        effective_mode="template_only",
        platform_mode_ceiling="assisted_only",
        template_id="tpl-v-1",
        template_version=1,
        template_validation_status="passed",
        reply_mode="assisted",
        pending_status="approved",
        expires_at=_FUTURE,
        inbound_created_at=_NOW,
        outbound_channel_status="available",
        idempotency_consumed=False,
        now=_NOW,
    )
    for key, value in overrides.items():
        setattr(ctx, key, value)
    return ctx


def _auto_base(**overrides) -> FinalGuardInput:
    ctx = _assisted_base(
        reply_mode="auto",
        pending_assisted_id=None,
        pending_status=None,
        expires_at=None,
        effective_mode="auto_allowed",
        ai_intervention_mode="auto_allowed",
        platform_mode_ceiling="auto_allowed",
        actor_role="system",
        actor_user_id="system",
        template_id=None,
        template_validation_status=None,
        final_reply="您好，物流时效以平台显示为准，我们会尽快安排发货。",
        intent_category="basic_shipping_question",
        intent="basic_shipping_question",
    )
    for key, value in overrides.items():
        setattr(ctx, key, value)
    return ctx


class TestFinalGuardPureFunction(unittest.TestCase):
    def test_t1_guard_allows_safe_assisted_template(self) -> None:
        result = evaluate_final_guard(_assisted_base())
        self.assertTrue(result.allowed_to_send)
        self.assertEqual(result.decision, "allow")
        self.assertEqual(result.send_mode, "assisted_send")
        self.assertEqual(result.audit_action, "final_guard_passed")

    def test_t2_guard_allows_safe_platform_guidance_refund(self) -> None:
        result = evaluate_final_guard(
            _assisted_base(
                effective_mode="guide_only",
                ai_intervention_mode="guide_only",
                template_id=None,
                template_validation_status=None,
                final_reply="亲，请通过平台售后入口申请退款，我们会按照平台流程处理。",
                intent_category="refund_request",
                intent="refund_request",
            )
        )
        self.assertTrue(result.allowed_to_send)
        self.assertEqual(result.send_mode, "assisted_send")

    def test_t3_product_gate_disabled_blocks(self) -> None:
        result = evaluate_final_guard(_assisted_base(product_gate_enabled=False))
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "product_gate_disabled")

    def test_t4_merchant_policy_blocked_blocks(self) -> None:
        result = evaluate_final_guard(_assisted_base(effective_mode="blocked"))
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "policy_blocked")

    def test_t5_ceiling_violation_blocks(self) -> None:
        result = evaluate_final_guard(
            _auto_base(
                platform_mode_ceiling="assisted_only",
                effective_mode="auto_allowed",
            )
        )
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "ceiling_violation")

    def test_t6_guide_only_non_guidance_blocks(self) -> None:
        result = evaluate_final_guard(
            _assisted_base(
                effective_mode="guide_only",
                ai_intervention_mode="guide_only",
                template_id=None,
                template_validation_status=None,
                final_reply="我马上给你退款。",
            )
        )
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "mode_violation")

    def test_t7_template_only_without_template_blocks(self) -> None:
        result = evaluate_final_guard(
            _assisted_base(template_id=None, template_validation_status=None)
        )
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "template_required")

    def test_t8_template_validation_rejected_blocks(self) -> None:
        result = evaluate_final_guard(
            _assisted_base(template_validation_status="rejected")
        )
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "template_not_validated")

    def test_t9_assisted_without_pending_blocks(self) -> None:
        result = evaluate_final_guard(_assisted_base(pending_assisted_id=None))
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "pending_not_found")

    def test_t10_viewer_permission_denied(self) -> None:
        result = evaluate_final_guard(_assisted_base(actor_role="viewer"))
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "permission_denied")

    def test_t11_pending_expired_blocks(self) -> None:
        result = evaluate_final_guard(
            _assisted_base(expires_at="2026-06-03T11:00:00+00:00")
        )
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "pending_expired")

    def test_t12_duplicate_idempotency_blocks(self) -> None:
        result = evaluate_final_guard(_assisted_base(idempotency_consumed=True))
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "duplicate_send_attempt")

    def test_t13_forbidden_promise_blocks(self) -> None:
        result = evaluate_final_guard(_assisted_base(final_reply="好的，直接退款给您。"))
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "forbidden_promise")

    def test_t14_off_platform_risk_blocks(self) -> None:
        result = evaluate_final_guard(_assisted_base(final_reply="请加微信联系我处理。"))
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "off_platform_risk")

    def test_t15_review_manipulation_blocks(self) -> None:
        result = evaluate_final_guard(_assisted_base(final_reply="好评返现哦亲。"))
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "review_manipulation")

    def test_t16_stale_message_blocks(self) -> None:
        result = evaluate_final_guard(
            _assisted_base(inbound_created_at=_STALE_INBOUND)
        )
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "stale_message")

    def test_t17_outbound_unavailable_blocks(self) -> None:
        result = evaluate_final_guard(
            _assisted_base(outbound_channel_status="unavailable")
        )
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "outbound_unavailable")

    def test_t18_guard_exception_no_send(self) -> None:
        ctx = _assisted_base()
        with patch(
            "Message.gates.final_guard._parse_iso",
            side_effect=RuntimeError("parse failed"),
        ):
            result = evaluate_final_guard(ctx)
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "guard_exception")
        self.assertIn("G27", result.checked_rules)

    def test_t19_blocked_reason_blocks(self) -> None:
        result = evaluate_final_guard(
            _assisted_base(blocked_reason="intent requires human review")
        )
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "blocked_intent")

    def test_t20_human_takeover_reason_blocks(self) -> None:
        result = evaluate_final_guard(
            _assisted_base(human_takeover_reason="complaint escalation")
        )
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "human_takeover_required")

    def test_t21_high_risk_blocks(self) -> None:
        result = evaluate_final_guard(_assisted_base(risk_level="high"))
        self.assertFalse(result.allowed_to_send)
        self.assertEqual(result.block_code, "high_risk")

    def test_t22_auto_allowed_safe_case_allows_auto_send(self) -> None:
        result = evaluate_final_guard(_auto_base())
        self.assertTrue(result.allowed_to_send)
        self.assertEqual(result.send_mode, "auto_send")
        self.assertEqual(result.audit_action, "final_guard_passed")

    def test_t23_policy_snapshot_in_decision(self) -> None:
        result = evaluate_final_guard(_assisted_base())
        self.assertEqual(result.policy_snapshot["policy_id"], "policy-v-1")
        self.assertEqual(result.policy_snapshot["policy_version"], 1)
        self.assertEqual(result.policy_snapshot["effective_mode"], "template_only")
        self.assertEqual(result.policy_snapshot["platform_mode_ceiling"], "assisted_only")

    def test_t24_template_snapshot_in_decision(self) -> None:
        result = evaluate_final_guard(_assisted_base())
        self.assertEqual(result.template_snapshot["template_id"], "tpl-v-1")
        self.assertEqual(result.template_snapshot["template_version"], 1)
        self.assertEqual(result.template_snapshot["validation_status"], "passed")

    def test_t25_no_send_side_effect_static_import_check(self) -> None:
        source = _FINAL_GUARD_SOURCE.read_text(encoding="utf-8")
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
            "product_persistence",
        )
        for token in forbidden:
            self.assertNotIn(
                token,
                import_block,
                msg=f"unexpected import: {token}",
            )


class TestForbiddenScan(unittest.TestCase):
    def test_safe_platform_guidance_not_blocked(self) -> None:
        text = "亲，请通过平台售后入口申请退款，我们会按照平台流程处理。"
        scan = scan_forbidden_promise(text)
        self.assertFalse(scan.blocked)

    def test_forbidden_promise_detected(self) -> None:
        scan = scan_forbidden_promise("好的，马上退款。")
        self.assertTrue(scan.blocked)
        self.assertEqual(scan.block_code, "forbidden_promise")


if __name__ == "__main__":
    unittest.main()

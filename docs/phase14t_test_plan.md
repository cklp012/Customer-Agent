# Phase 14t — Test Plan (Future Implementation)

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 测试未编写** |
| 前置 | 14v pure function · 14u policy schema · 14w validation |

---

## 1. 测试原则

| # | 原则 |
|---|------|
| T1 | 14t **不编写**测试 |
| T2 | `evaluate_final_guard` **无** SendMessage import |
| T3 | `allowed_to_send=false` → caller mock 验证 no outbound |
| T4 | merchant policy **不能** override guard in tests |
| T5 | non-test legacy / Doudian unchanged tests remain |

---

## 2. T1–T25

| ID | 名称 | 要点 |
|----|------|------|
| **T1** | `guard_allows_safe_assisted_template` | passed template + approved → allow |
| **T2** | `guard_allows_safe_platform_guidance_refund` | guide 话术 allow |
| **T3** | `product_gate_disabled_blocks` | G1 |
| **T4** | `merchant_policy_blocked_blocks` | G7 |
| **T5** | `ceiling_violation_blocks` | G12 |
| **T6** | `guide_only_non_guidance_blocks` | G8 |
| **T7** | `template_only_without_template_blocks` | G9 |
| **T8** | `template_validation_rejected_blocks` | G10 |
| **T9** | `assisted_without_pending_blocks` | G11 |
| **T10** | `viewer_permission_denied` | G5 |
| **T11** | `pending_expired_blocks` | G15 |
| **T12** | `duplicate_idempotency_blocks` | G16 |
| **T13** | `forbidden_promise_blocks` | G22 |
| **T14** | `off_platform_risk_blocks` | G23 |
| **T15** | `review_manipulation_blocks` | G24 |
| **T16** | `stale_message_blocks` | G25 |
| **T17** | `outbound_unavailable_blocks` | G26 |
| **T18** | `guard_exception_no_send` | G27 fail-closed |
| **T19** | `audit_failure_before_send_no_send` | service integration |
| **T20** | `snapshot_failure_before_send_no_send` | service integration |
| **T21** | `policy_snapshot_in_decision` | output fields |
| **T22** | `dashboard_block_reason_available` | block_code/reason |
| **T23** | `non_test_legacy_unchanged` | no guard on legacy |
| **T24** | `doudian_not_enabled` | no production path |
| **T25** | `no_handler_sendmessage_changes` | static scan |

---

## 3. 测试分层（14v+）

| 层 | 文件（规划） |
|----|--------------|
| pure function | `test_final_guard_pure_function.py` |
| forbidden scan | `test_final_guard_forbidden_scan.py` |
| rule matrix | `test_final_guard_rule_matrix.py` |
| policy integration | `test_final_guard_with_policy.py` |
| service | `test_assisted_reply_service_guard_integration.py` |

---

## 4. 与 14s S-tests / 14r R-tests

| 已有 | 关系 |
|------|------|
| S9–S10 | guard 为 authoritative sendability |
| R5–R6 | assisted approve 须 guard pass |

---

*Phase 14t · planning only · 2026-06-03*

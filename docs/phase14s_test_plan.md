# Phase 14s — Test Plan (Future Implementation)

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 测试未编写** |
| 范围 | MerchantSafetyPolicy · MerchantReplyTemplate · pipeline · scan · snapshot |
| 前置 | 14u schema · 14v final guard pure function · 14t planning |

---

## 1. 测试原则

| # | 原则 |
|---|------|
| T1 | 14s **不编写**测试 |
| T2 | mock SendMessage / `_send_reply` 于任何 send 测试 |
| T3 | non-test legacy **unchanged** |
| T4 | Doudian **无** production policy path |
| T5 | handler **无** direct policy repository import（future） |
| T6 | merchant policy **不能** override final guard |

---

## 2. 测试用例 S1–S16

### S1 `default_policy_matrix_safe`

- 新 shop 无 custom policy → default matrix applied
- redline categories → blocked

### S2 `merchant_policy_cannot_exceed_platform_ceiling`

- merchant sets auto_allowed · ceiling=assisted_only → effective=assisted_only
- save API rejects invalid combo

### S3 `redline_intent_always_blocked`

- private_contact / review_cashback / delete_bad_review → effective blocked regardless of merchant config

### S4 `refund_guide_only_allows_platform_process_template`

- refund_request · guide_only · passed guide template → candidate text allowed path
- no result promise in text

### S5 `template_save_rejects_forbidden_promise`

- save template with「马上给你退款」→ validation_status=rejected

### S6 `template_pending_review_for_suspicious_content`

- borderline wording → pending_review · not enableable until review

### S7 `template_variables_whitelist`

- unknown variable `{hack}` → save rejected

### S8 `rendered_template_rescan`

- template passed · render injects forbidden via variable abuse → block

### S9 `merchant_policy_does_not_override_final_guard`

- auto_allowed policy · forbidden text → guard blocks · no send

### S10 `final_guard_blocks_forbidden_template_even_if_policy_allows`

- passed template later edited in approve path with forbidden → block

### S11 `policy_snapshot_written_to_send_decision_future`

- record_preview / assisted path → snapshot contains policy_id/version/effective_mode

### S12 `policy_change_audit_logged_future`

- policy update → AuditLog merchant_policy_changed append-only

### S13 `policy_read_failure_no_send_or_safe_default`

- DB read fail → default matrix or no-send · **no legacy send**

### S14 `non_test_legacy_unchanged`

- non-test shop → no policy pipeline on legacy hot path

### S15 `doudian_not_enabled`

- Doudian → no merchant policy production write/send

### S16 `no_handler_sendmessage_changes`

- static scan · handler unchanged in policy-only phases

---

## 3. 测试分层（future）

| 层 | 文件（规划名） |
|----|----------------|
| default matrix | `test_merchant_default_policy_matrix.py` |
| ceiling | `test_merchant_policy_ceiling.py` |
| template validation | `test_merchant_template_validation.py` |
| pipeline resolve | `test_merchant_policy_pipeline.py` |
| snapshot | `test_merchant_policy_snapshot_write.py` |
| guard integration | `test_final_guard_with_policy.py`（14v） |

---

## 4. 与现有测试

| 已有 | 关系 |
|------|------|
| 14l–14q tests | 保持 green |
| 14r R1–R15 | assisted 测试叠加 policy+guard 前置 |

---

*Phase 14s · planning only · 2026-06-03*

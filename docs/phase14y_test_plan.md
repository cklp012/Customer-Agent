# Phase 14y — Test Plan (Future Implementation)

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 测试未编写** |
| 前置 | 15a assisted send planning · 15b idempotency skeleton · 14x service skeleton |

---

## 1. 测试原则

| # | 原则 |
|---|------|
| Y0 | 14y **不编写**测试 |
| Y0a | mock SendMessage · 验证 caller 在 block/fail 时 **never called** |
| Y0b | merchant policy / approve **不能** override guard block |
| Y0c | non-test legacy tests **remain green** |

---

## 2. Y1–Y17

| ID | 名称 | 要点 |
|----|------|------|
| **Y1** | `approve_guard_block_no_send` | forbidden / policy block · no outbound · no attempted audit |
| **Y2** | `approve_guard_pass_audit_snapshot_then_outbound` | strict order · guard pass → snapshot → attempted → send |
| **Y3** | `audit_before_outbound_failure_no_send` | final_guard_passed or attempted audit fail · no SendMessage |
| **Y4** | `snapshot_failure_no_send` | merchant_confirm fail · no outbound |
| **Y5** | `idempotency_lock_failure_no_send` | acquire fail · no outbound · no double-send |
| **Y6** | `outbound_failure_marks_failed` | status=failed · outbound_send_failed audit |
| **Y7** | `outbound_success_marks_sent` | status=sent · outbound_send_succeeded audit |
| **Y8** | `duplicate_approve_sent_no_double_send` | already_sent · SendMessage once only |
| **Y9** | `duplicate_approve_in_progress_no_double_send` | concurrent · already_in_progress |
| **Y10** | `failed_pending_manual_review_no_auto_retry` | failed → no auto resend |
| **Y11** | `final_guard_exception_no_send` | G27 · fail-closed |
| **Y12** | `outbound_send_attempted_written_before_send` | audit timestamp/order before SendMessage mock |
| **Y13** | `outbound_success_audit_failure_recovery_no_resend` | recovery task · no second send |
| **Y14** | `non_test_legacy_unchanged` | legacy handler path untouched |
| **Y15** | `handler_no_direct_send_integration` | handler 不 import SendMessage on assisted branch |
| **Y16** | `doudian_not_enabled` | no Doudian production outbound |
| **Y17** | `no_fallback_legacy_send_on_db_failure` | product DB fail · no legacy send |

---

## 3. 测试分层（future）

| 层 | 文件（规划） |
|----|--------------|
| approve sequence integration | `test_assisted_reply_service_outbound_integration.py` |
| idempotency | `test_assisted_idempotency.py` |
| audit ordering | `test_assisted_audit_snapshot_ordering.py` |
| failure / recovery | `test_assisted_failure_recovery.py` |
| handler boundary | `test_handler_assisted_service_boundary.py` |
| legacy regression | existing `test_handler_*` · `test_non_test_*` |

---

## 4. 与 14x X-tests 关系

| 已有 | 关系 |
|------|------|
| X4 guard block no send | Y1 扩展 + outbound mock |
| X5 send_not_implemented | 15a 前 baseline · Y2 替代 |
| X8 terminal state | Y8/Y9 扩展 |
| T1–T25 final guard | guard 层 unit · Y11 重叠 |

---

*Phase 14y · planning only · 2026-06-03*

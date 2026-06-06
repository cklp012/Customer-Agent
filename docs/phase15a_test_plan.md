# Phase 15a — Test Plan (Future Implementation)

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 测试未编写** |
| 前置 | 15b idempotency · 15c dry-run port · 15e+ live send |

---

## 1. 测试原则

| # | 原则 |
|---|------|
| A0 | 15a **不编写**测试 |
| A0a | mock SendMessage / outbound port · assert call counts |
| A0b | non-test legacy tests **remain green** |
| A0c | Dashboard read tests **no send** |

---

## 2. A1–A21

| ID | 名称 | 要点 |
|----|------|------|
| **A1** | `assisted_send_flag_off_no_send` | SEND_ENABLED=false |
| **A2** | `non_allowlisted_shop_no_send` | shop mismatch |
| **A3** | `dry_run_records_would_send_no_outbound` | DRY_RUN=true · no SendMessage |
| **A4** | `guard_block_no_send` | forbidden · no attempted |
| **A5** | `audit_before_outbound_failure_no_send` | audit fail · no outbound |
| **A6** | `snapshot_failure_no_send` | merchant_confirm fail |
| **A7** | `idempotency_acquire_failure_no_send` | lock fail |
| **A8** | `outbound_unavailable_no_send` | channel down |
| **A9** | `outbound_attempted_written_before_send` | audit order |
| **A10** | `outbound_success_marks_sent` | status=sent · lock succeeded |
| **A11** | `outbound_failure_marks_failed` | status=failed |
| **A12** | `outbound_timeout_unknown_reconcile_no_auto_retry` | reconcile · no 2nd send |
| **A13** | `duplicate_sent_no_double_send` | already_sent |
| **A14** | `duplicate_in_progress_no_double_send` | concurrent |
| **A15** | `duplicate_failed_manual_review` | no auto retry |
| **A16** | `db_failure_no_legacy_fallback` | product DB fail |
| **A17** | `handler_not_modified` | no assisted send in handler |
| **A18** | `SendMessage_not_directly_imported_by_assisted_service` | static scan |
| **A19** | `PDD_queue_name_unchanged` | pdd_{shop_id} |
| **A20** | `doudian_not_enabled` | no Doudian outbound |
| **A21** | `dashboard_read_does_not_send` | GET only |

---

## 3. 测试分层（future）

| 层 | 文件（规划） |
|----|--------------|
| flags + allowlist | `test_assisted_send_flags.py` |
| dry_run port | `test_assisted_outbound_dry_run.py` |
| idempotency | `test_assisted_send_idempotency.py` |
| audit ordering | `test_assisted_send_audit_order.py` |
| live send (stage 5) | `test_assisted_send_live_test_shop.py` |
| failure / recovery | `test_assisted_send_failure_recovery.py` |
| legacy regression | existing suite |

---

## 4. 与 14x / 14y 关系

| 已有 | 关系 |
|------|------|
| X5 send_not_implemented | baseline before 15c |
| Y2–Y12 | outbound integration · A5–A12 扩展 |
| Z21 dashboard no send | A21 |

---

*Phase 15a · planning only · 2026-06-03*

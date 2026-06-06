# Phase 15e — Test Plan (Future Implementation)

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 前置实现 | 15f dry-run wire · 15h live port · 15g action endpoint |
| 本 phase | **不写测试代码** |

---

## 1. 测试分层

| 层 | 文件（future） | 范围 |
|----|----------------|------|
| Unit | `test_assisted_send_flag_gate.py` | flags · allowlist |
| Service | `test_assisted_reply_service_live_send.py` | approve_pending sequence |
| Idempotency | `test_assisted_send_idempotency_integration.py` | acquire/mark + service |
| Port | `test_live_pdd_assisted_outbound_port.py` | LivePdd mock |
| Static | existing skeleton tests | no SendMessage import |

---

## 2. 用例清单

| ID | 名称 | 断言 |
|----|------|------|
| **E1** | `flag_missing_no_send` | 任一 live gate flag off → no port call |
| **E2** | `dry_run_true_no_live_send` | DRY_RUN=true → DryRun port · SendMessage not called |
| **E3** | `non_allowlisted_shop_no_send` | shop mismatch → no outbound |
| **E4** | `allowlisted_shop_live_gate_passes` | all flags + allowlist → live port invoked (mock) |
| **E5** | `pending_invalid_status_no_send` | sent/rejected/expired → no outbound |
| **E6** | `final_guard_block_no_send` | guard block → no idempotency acquire |
| **E7** | `final_guard_allow_pre_outbound_steps_ordered` | audit/snapshot/acquire/attempted order |
| **E8** | `snapshot_failure_no_send` | snapshot raises → no port |
| **E9** | `idempotency_acquire_failure_no_send` | already_sent → no port |
| **E10** | `outbound_attempted_audit_failure_no_send` | attempted audit fails → port not called |
| **E11** | `live_outbound_success_marks_sent` | success → idempotency succeeded · pending sent |
| **E12** | `live_outbound_failure_marks_failed` | failure → idempotency failed · pending failed |
| **E13** | `live_outbound_timeout_requires_reconciliation` | timeout → no auto retry · reconcile flag |
| **E14** | `duplicate_sent_no_double_send` | second acquire → already_sent |
| **E15** | `duplicate_in_progress_no_double_send` | concurrent → already_in_progress |
| **E16** | `duplicate_failed_manual_review` | failed → manual_review_required |
| **E17** | `success_audit_failure_recovery_no_resend` | sent on platform · audit fail → recovery only |
| **E18** | `db_failure_no_legacy_fallback` | DB error → no handler SendMessage |
| **E19** | `handler_not_modified` | Message/handlers diff empty vs baseline |
| **E20** | `SendMessage_not_imported_by_assisted_service` | static import scan |
| **E21** | `PDD_queue_name_unchanged` | `pdd_{shop_id}` parity |
| **E22** | `Doudian_not_enabled` | no doudian live port in default wiring |
| **E23** | `dashboard_read_does_not_send` | 15d read routes · SendMessage not called |
| **E24** | `dry_run_port_remains_default` | no flags → DryRun or disabled · no live port |

---

## 3. Mock 要求

| Mock | 用途 |
|------|------|
| `SendMessage.send_text` | assert_not_called unless live integration test in isolated harness |
| `AIReplyHandler._send_reply` | assert_not_called |
| `LivePddAssistedOutboundPort.send` | success/failure/timeout scenarios |
| `evaluate_final_guard` | block/allow injection |
| repository failures | snapshot/audit/idempotency error paths |

---

## 4. 非目标（15e）

| 项 | 状态 |
|----|------|
| 实现 E1–E24 | ❌ future |
| CI 新增 job | ❌ |
| 修改现有 692 tests | ❌ |

---

## 5. 签收标准（future phase）

全部 E1–E24 pass · handler/PDD/Doudian unchanged · no default live send · dry_run default safe.

---

*Phase 15e · docs only · 2026-06-03*

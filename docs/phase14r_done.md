# Phase 14r 完成 — Assisted approve/reject Service Planning

| 项 | 内容 |
|----|------|
| 状态 | **docs only · 规划完成** |
| 日期 | 2026-06-03 |
| 前置 | [phase14q_done.md](phase14q_done.md) · [phase14p_done.md](phase14p_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 类型 | **仅文档** |
| Python 代码 | **未写** |
| `AssistedReplyService` 实现 | **未实现** |
| approve/reject/send | **未实现** |
| handler / SendMessage / PDD / Doudian | **未改** |
| Dashboard API（14o） | **未改** |
| 14q schema/repository | **已实现** · 本 phase 只规划 service |
| assisted / auto send | **未实现** |

---

## 新增文档

| 文档 | 内容 |
|------|------|
| [phase14r_assisted_service_plan.md](phase14r_assisted_service_plan.md) | 总体规划 · service 职责 |
| [phase14r_create_pending_flow.md](phase14r_create_pending_flow.md) | create pending |
| [phase14r_approve_reject_service_flow.md](phase14r_approve_reject_service_flow.md) | approve / reject / expire |
| [phase14r_state_machine_and_idempotency.md](phase14r_state_machine_and_idempotency.md) | 状态机 · 幂等 |
| [phase14r_audit_and_snapshot_sequence.md](phase14r_audit_and_snapshot_sequence.md) | audit + snapshot 顺序 |
| [phase14r_failure_and_rollback.md](phase14r_failure_and_rollback.md) | failure · rollback |
| [phase14r_test_plan.md](phase14r_test_plan.md) | R1–R15 |

---

## 规划结论（签收）

| # | 结论 |
|---|------|
| 1 | AssistedReplyService 编排 pending · audit · guard · snapshot · outbound |
| 2 | **merchant approve ≠ 直接发送** · final guard pass 才 outbound |
| 3 | **approve 不能绕过 final guard** |
| 4 | blocked / uncertain intent 规则与 14p 一致 |
| 5 | viewer 不能 approve/reject |
| 6 | duplicate approve **不能** double-send · `sent` 终态 |
| 7 | audit/snapshot failure before send → **no send**（strict） |
| 8 | outbound failure → `failed` · no auto retry |
| 9 | DB failure **不 fallback legacy send** |
| 10 | preview zero-send · non-test legacy **不变** |
| 11 | auto send **未实现** |

---

## 当前 runtime（unchanged）

- 14q：`PendingAssistedRepositorySQLite` · `AuditLogRepositorySQLite` skeleton
- `AssistedReplyService` stub → `NotImplementedError`
- test shop preview：**zero-send**
- non-test legacy：**unchanged**

---

## 下一步

| Phase | 内容 |
|-------|------|
| **14s** | Final guard **implementation planning** |
| **14t** | Assisted service **skeleton behind flags** |
| **14u** | PendingAssisted dashboard read planning |

---

*签收：Phase 14r · docs only · 2026-06-03*

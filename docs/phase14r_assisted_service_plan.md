# Phase 14r — AssistedReplyService Planning

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不写代码** |
| 日期 | 2026-06-03 |
| 前置 | [phase14q_done.md](phase14q_done.md) · [phase14p_done.md](phase14p_done.md) · [phase13f_done.md](phase13f_done.md) |

---

## 1. Phase 14r 定位

| 项 | 结论 |
|----|------|
| 交付 | **仅文档** |
| Python 代码 | **未写** |
| `AssistedReplyService` 实现 | **未实现** |
| approve/reject/send | **未实现** |
| handler / SendMessage / PDD / Doudian | **未改** |
| Dashboard API（14o） | **未改** |
| 14q schema/repository | **已实现** · 本 phase 只规划 service 层 |

Phase 14r 在 14q（PendingAssisted + AuditLog repository skeleton）之上，规划未来 **`AssistedReplyService`** 的职责边界、流程、状态机、audit/snapshot 顺序与失败策略。

---

## 2. AssistedReplyService 未来职责

| 方法（规划） | 职责 |
|--------------|------|
| `create_pending_from_preview(...)` | 从 assisted preview 路径创建 `PendingAssistedReply status=pending` + audit |
| `approve_pending(...)` | 权限校验 → final guard → snapshot → outbound → status 转换 |
| `reject_pending(...)` | 权限校验 → `rejected` + audit · **不发送** |
| `expire_pending(...)` | 超时检测 → `expired` + audit · **不发送** |
| `_run_final_guard(...)` | 发送前最后一道门 · **pass 才允许 outbound** |
| `_append_audit(...)` | 有序写入 AuditLog（append-only） |
| `_write_merchant_confirm_snapshot(...)` | `SendDecisionSnapshot decision_phase=merchant_confirm` |

**Service 不直接 import handler。** Handler 未来仅调用 service 公共 API，不直接写 pending/audit repository。

---

## 3. 核心原则

| # | 原则 |
|---|------|
| 1 | **Assisted ≠ Auto** — 必须 merchant approve |
| 2 | **merchant approve ≠ 直接发送** — 须 final guard pass |
| 3 | **final guard pass 才允许 outbound** |
| 4 | **blocked intent 不能**普通 approve |
| 5 | **uncertain intent** 须 edit 或 human takeover |
| 6 | **viewer 不能** approve/reject |
| 7 | **operator / admin / owner 可以** approve/reject |
| 8 | **DB/audit/snapshot failure 不 fallback legacy send** |
| 9 | **auto send 未实现** |

---

## 4. 与现有组件关系

```
Handler (future assisted branch)
    → AssistedReplyService
        → PendingAssistedRepositorySQLite (14q)
        → AuditLogRepositorySQLite (14q)
        → SendDecisionRepositorySQLite (14n)
        → FinalGuardService (14s planning)
        → OutboundResolver / SendMessage (future · assisted path only)

PreviewReplyLogService (14g–14n) — preview zero-send · 不变
Legacy _send_reply (non-test) — 不变
```

| 组件 | 14r 状态 |
|------|----------|
| `AssistedReplyService` stub | 存在 · `NotImplementedError` |
| Service 规划 | ✅ 本 phase |
| Repository (14q) | ✅ skeleton |
| Final guard impl | 📋 14s |
| Service skeleton impl | 📋 14t |

---

## 5. Flags（规划 · 默认 off）

| Flag | 用途 |
|------|------|
| `PRODUCT_PERSISTENCE_ENABLED` | 总开关 |
| `PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED` | pending shadow write |
| `PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG` | audit shadow write |
| `PRODUCT_PERSISTENCE_WRITE_SEND_DECISION` | merchant_confirm snapshot |

**不默认开启 assisted。** `reply_mode=assisted` 为 per-shop 显式配置（future）。

---

## 6. 文档索引

| 文档 | 内容 |
|------|------|
| [phase14r_create_pending_flow.md](phase14r_create_pending_flow.md) | create pending |
| [phase14r_approve_reject_service_flow.md](phase14r_approve_reject_service_flow.md) | approve / reject / expire |
| [phase14r_state_machine_and_idempotency.md](phase14r_state_machine_and_idempotency.md) | 状态机 · 幂等 |
| [phase14r_audit_and_snapshot_sequence.md](phase14r_audit_and_snapshot_sequence.md) | audit + snapshot 顺序 |
| [phase14r_failure_and_rollback.md](phase14r_failure_and_rollback.md) | failure · rollback |
| [phase14r_test_plan.md](phase14r_test_plan.md) | R1–R15 |

**对齐：** [phase14p_assisted_approve_reject_flow.md](phase14p_assisted_approve_reject_flow.md) · [phase14p_permissions_and_final_guard.md](phase14p_permissions_and_final_guard.md)

---

## 7. 非目标（14r）

- 不实现 service 代码（14t）
- 不实现 final guard 代码（14s）
- 不新增 POST approve/reject API
- 不改 handler / SendMessage / outbound resolver
- Doudian 不进入 production assisted path

---

*Phase 14r · planning only · 2026-06-03*

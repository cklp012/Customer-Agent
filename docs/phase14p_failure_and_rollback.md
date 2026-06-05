# Phase 14p — Failure and Rollback

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14p_auditlog_pending_assisted_plan.md](phase14p_auditlog_pending_assisted_plan.md) · [phase14j_flags_failure_rollback.md](phase14j_flags_failure_rollback.md) · [phase14n_done.md](phase14n_done.md) |

---

## 1. 总原则

| # | 原则 |
|---|------|
| F1 | **DB failure 不 fallback legacy send** |
| F2 | **final guard failure 不发送** |
| F3 | **audit failure 策略保守**（approve/send 路径） |
| F4 | **duplicate approve 幂等** — 不能 double-send |
| F5 | **expired pending 不可发送** |
| F6 | preview zero-send 路径不受影响 |
| F7 | auto mode **未实现** — 本 doc 不涉及 auto rollback |

---

## 2. 失败场景矩阵

| 场景 | 发送? | pending 状态 | audit | 备注 |
|------|-------|--------------|-------|------|
| Pending create failure | ❌ | 无记录 | 可选 degraded | 不创建 pending → 不 assisted send |
| AuditLog write failure **before approve** | ❌ 或 degraded | 保持 pending | 缺失 | **保守：阻止 approve API 成功** |
| AuditLog write failure **after send success** | 已发送 | sent | 补写 retry queue | 发送不可逆 · 必须 eventual audit |
| Approve DB failure | ❌ | 保持 pending | 无 assisted_approved | 不进入 final guard |
| Final guard failure | ❌ | approved 或 failed | `final_guard_blocked` | **不得 SendMessage** |
| Outbound failure | ❌ | `failed` | `outbound_send_failed` | **不重试 auto** · manual review |
| Outbound success + snapshot fail | 已发送 | `sent` | outbound_succeeded | snapshot 补写 · 不 resend |
| SQLite read failure (Dashboard) | N/A | N/A | N/A | fallback in-memory（14o 已实现） |
| Duplicate approve | ❌ 第二次 | `sent` 保持 | 幂等 skip | **不能 double-send** |
| Expired pending approve | ❌ | `expired` | `assisted_expired` | 403 |

---

## 3. Audit failure 保守策略

### 3.1 Before approve / before send（推荐 strict）

```
approve request
  → write AuditLog assisted_approved
  → if audit fail: **abort approve** · return 503 · **no final guard · no send**
```

**理由：** 无 audit 的 approve/send 无法合规复盘 — 保守阻止。

### 3.2 Degraded mode（可选 · 需 explicit flag）

```
PRODUCT_AUDIT_DEGRADED_MODE=true  (默认 false)
  → audit fail: log warning · allow approve with warnings[]
```

**14p 推荐 default：strict · 非 degraded。**

### 3.3 After send success

- outbound 已成功 → **不得** 因 audit fail 撤销发送
- 写入 retry queue / dead letter audit 补录
- Alert ops

---

## 4. Final guard failure

```
final_guard.evaluate(pending, reply_log, context)
  → blocked
  → AuditLog final_guard_blocked
  → **no SendMessage**
  → **no _send_reply**
  → pending: 保持 approved 或 → failed（14s 实现时定）
  → merchant UI: 展示 block reason
```

**明确：final guard 失败不得发送。**

---

## 5. Outbound failure

```
outbound.send_text(...)
  → failure
  → status = failed
  → AuditLog outbound_send_failed
  → **no automatic retry**（避免 duplicate send 风险）
  → route to manual review / re-create pending（新 pending_assisted_id）
```

**不重试或进入 manual review** — 与 P11 测试对齐。

---

## 6. Duplicate approve 幂等

```
approve(pending_assisted_id)
  if status == sent:
    return 200 idempotent · **no second send**
  if status == approved and send in flight:
    return 409 · in_progress
  if status == pending:
    proceed once
```

数据库层可选：`status=sent` UNIQUE constraint on transition。

---

## 7. Expired pending

```
if now > expires_at and status == pending:
  status → expired
  AuditLog assisted_expired

approve(expired_id) → 403 · **no send**
```

---

## 8. Rollback 策略

| Rollback 动作 | 行为 |
|---------------|------|
| disable assisted mode | shop `reply_mode=preview` · 新消息不走 assisted |
| keep preview mode | test shop zero-send 不变 |
| keep ReplyLog read-only | Dashboard GET 仍可用 |
| audit logs | **不 DELETE**（除非 explicit migration rollback / legal） |
| pending 未完成项 | cancel 或 expire · 不 force send |
| flags off | `WRITE_PENDING_ASSISTED=false` · `WRITE_AUDIT_LOG=false` |
| legacy send path | **不变** · non-test 仍 legacy |

**DB failure 不 fallback legacy send** — 与 14l/14n 一致。

---

## 9. auto mode

| 项 | 状态 |
|----|------|
| auto send | **未实现** |
| auto rollback | **N/A** |
| 本 doc | 不影响 auto 规划 |

---

## 10. 与已实现 phase 一致性

| Phase | failure policy |
|-------|----------------|
| 14l ReplyLog write fail | in-memory ok · no send impact |
| 14n snapshot write fail | no send · snapshot_recorded=false |
| 14o read fail | fallback in-memory + warning |
| 14p assisted (future) | 上表 · **no legacy send fallback** |

---

*Phase 14p · planning only · 2026-06-03*

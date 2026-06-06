# Phase 15a — Idempotency Lock Contract

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14y_idempotency_and_state_transition.md](phase14y_idempotency_and_state_transition.md) · [phase15a_status_transition_and_audit.md](phase15a_status_transition_and_audit.md) |

---

## 1. Idempotency key

| 规则 | 值 |
|------|-----|
| 格式 | `assisted_send:{pending_assisted_id}` |
| 唯一性 | 同一 `pending_assisted_id` **最多成功发送一次** |
| Final Guard G16 | `idempotency_consumed=true` → block |

---

## 2. Lock states

| state | 含义 |
|-------|------|
| `not_started` | 尚未 attempt |
| `in_progress` | lock acquired · outbound 进行中 |
| `succeeded` | outbound 成功 · consumed |
| `failed` | outbound 失败 · 未 consumed · manual review |

---

## 3. Operations（规划）

### 3.1 acquire

```text
acquire(idempotency_key, pending_assisted_id, actor_user_id)
  → if state=succeeded: return AlreadySent
  → if state=in_progress: return AlreadyInProgress
  → if state=failed: return ManualReviewRequired
  → if state=not_started: CAS not_started → in_progress
       success → return Acquired
       fail → return AcquireFailed
```

**必须在 `outbound_send_attempted` audit 之前 acquire 成功。**

| acquire 结果 | send? |
|--------------|-------|
| Acquired | 可继续 |
| AlreadySent | ❌ |
| AlreadyInProgress | ❌ |
| ManualReviewRequired | ❌ |
| AcquireFailed / DB error | ❌ |

---

### 3.2 mark_succeeded

- outbound platform success 后调用
- state → `succeeded` · idempotency consumed
- pending status → `sent`

### 3.3 mark_failed

- outbound platform failure 后调用
- state → `failed` · **不** consumed
- pending status → `failed`
- **no auto retry**

### 3.4 release（仅 error path）

- acquire 后、outbound 前若 audit/outbound 前置失败
- in_progress → not_started（或 failed · 实现选择）
- **不得**在 succeeded 后 release

---

## 4. Duplicate approve 行为

| lock / pending state | approve 响应 | send? |
|----------------------|--------------|-------|
| not_started | 正常流程 | 视 guard |
| in_progress | `already_in_progress` | ❌ |
| succeeded / sent | `already_sent` | ❌ **no double-send** |
| failed | `manual_review_required` | ❌ **no auto retry** |

---

## 5. 存储选项比较（future · 15b）

| 选项 | 优点 | 缺点 |
|------|------|------|
| **A. pending row + status + send_lock_at** | 无新表 · 14q schema | 并发 CAS 需 careful SQL |
| **B. 新表 `assisted_send_idempotency`** | 清晰 lock state · unique on key | 新 migration · 15a 不建表 |
| **C. audit-derived infer** | 无 extra write | 弱一致 · **不推荐生产** |

**推荐：** 15b 实现 **B 或 A+unique partial index** · **不允许内存锁作为生产唯一保证**。

---

## 6. DB failure

| 场景 | 行为 |
|------|------|
| acquire DB error | **no-send** · fail-closed |
| mark_succeeded DB error | outbound 可能已成功 → reconciliation · **no resend** |
| mark_failed DB error | reconciliation |

**DB failure acquiring lock → no-send · no fallback legacy send.**

---

*Phase 15a · planning only · 2026-06-03*

# Phase 14r — State Machine and Idempotency

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14p_pending_assisted_schema_detail.md](phase14p_pending_assisted_schema_detail.md) |

---

## 1. 状态枚举

| status | 含义 | 终态? |
|--------|------|-------|
| `pending` | 待商家确认 | ❌ |
| `approved` | 已确认 · 待/正在 send | ❌ |
| `rejected` | 商家拒绝 | ✅ |
| `expired` | 超时 | ✅ |
| `canceled` | 系统/商家取消 | ✅ |
| `sent` | outbound 成功 | ✅ |
| `failed` | outbound 失败 | ✅* |

*`failed` 可人工 reopen 为新 pending（future manual_review）· **14r 不自动 retry**

---

## 2. 合法状态转换

```
pending ──approve──► approved ──outbound ok──► sent
pending ──reject──► rejected
pending ──timeout──► expired
pending ──cancel──► canceled
approved ──outbound fail──► failed
approved ──guard block──► approved (locked) or failed  [14s 定]
```

| 转换 | 合法? |
|------|-------|
| pending → approved | ✅ |
| pending → rejected | ✅ |
| pending → expired | ✅ |
| pending → canceled | ✅ |
| approved → sent | ✅（outbound success only） |
| approved → failed | ✅（outbound failure） |
| failed → pending | 📋 future manual_review only · **14r 不 auto** |
| sent → * | ❌ |
| rejected/expired/canceled → * | ❌ |

---

## 3. 终态规则

| 终态 | 规则 |
|------|------|
| `sent` | **不可再次发送** · duplicate approve → idempotent `already_sent` |
| `rejected` | approve → `invalid_state` 409 |
| `expired` | approve → `invalid_state` 403 |
| `canceled` | approve → `invalid_state` 409 |
| `failed` | approve → 须新 pending 或 manual flow · **不 reuse 同一 outbound** |

---

## 4. Duplicate approve 防 double-send

```
approve(pending_assisted_id):
  if status == sent:
    return ApproveResult(already_sent=True, sent=False)  — HTTP 200 idempotent
  if status in (rejected, expired, canceled):
    return error invalid_state
  if status == approved and outbound_in_flight:
    return error in_progress  — 409
  if status == pending:
    CAS transition pending → approved (DB row lock)
    proceed once
```

| 机制 | 说明 |
|------|------|
| DB CAS | `UPDATE ... WHERE status='pending'` rowcount check |
| in-flight lock | optional Redis/DB flag · 14t |
| sent 终态 | 硬阻止第二次 outbound |

**duplicate approve 不能 double-send。**

---

## 5. Outbound idempotency key

| 字段 | 用途 |
|------|------|
| `pending_assisted_id` | 幂等 key 基础 |
| `outbound_attempt_id` | 每次 attempt 新 UUID · audit 链 |
| metadata | `{ "idempotency_key": pending_assisted_id }` 传给 outbound |

**规则：**

- 同一 `pending_assisted_id` 仅 **一次** successful outbound
- 每次 outbound attempt 必须 `outbound_send_attempted` audit
- retry（若 future 允许）须 **新** pending_assisted_id · 非 resend 同一 id

---

## 6. HTTP / API 响应（future）

| 场景 | 响应 |
|------|------|
| 首次 approve + send ok | 200 · `status=sent` |
| duplicate approve (sent) | 200 · `already_sent=true` |
| reject/expired approve | 403/409 · `invalid_state` |
| guard block | 200/422 · `sent=false` · `guard_blocked=true` |

---

## 7. 与 14q repository 关系

| 14q `mark_status` | 14r service |
|-------------------|-------------|
| 裸 status 更新 | 包裹在 state machine + guard + outbound 内 |
| 无 send 语义 | service 唯一 outbound 调用点 |

14q repository **不**单独用于 approve send path · 仅 service 内部调用。

---

*Phase 14r · planning only · 2026-06-03*

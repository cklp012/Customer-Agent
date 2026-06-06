# Phase 14y — Idempotency and State Transition

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14y_approve_to_outbound_sequence.md](phase14y_approve_to_outbound_sequence.md) · [phase14r_state_machine_and_idempotency.md](phase14r_state_machine_and_idempotency.md) |

---

## 1. PendingAssisted 状态

| status | 含义 | 终态? |
|--------|------|-------|
| `pending` | 待商家确认 | 否 |
| `approved` | 商家已 approve · 尚未 outbound 或 outbound 进行中 | 否 |
| `rejected` | 商家拒绝 | **是** |
| `expired` | 超时 | **是** |
| `canceled` | 商家/系统取消 | **是** |
| `sent` | outbound 成功 | **是** |
| `failed` | outbound 失败 | 否（需 manual review · 非 auto-retry 终态） |

**注：** 14x skeleton 不写入 `approved` / `sent` / `failed` · 本表为 future 15a+ 目标。

---

## 2. 合法状态转换

```text
pending ──approve intent──► approved ──outbound success──► sent
   │                          │
   │                          └──outbound failure──► failed
   │
   ├──reject──► rejected
   ├──expire──► expired
   └──cancel──► canceled

sent / rejected / expired / canceled → 终态（不可 approve outbound）
failed → manual_review_required（默认不自动 retry · 不自动 → sent）
```

| 转换 | 触发 | outbound? |
|------|------|-----------|
| pending → approved | merchant approve · pre-outbound | 尚未 |
| approved → sent | outbound success | 已完成 |
| approved → failed | outbound failure | 已 attempt |
| pending → rejected | reject_pending | ❌ |
| pending → expired | expire_pending | ❌ |
| pending → canceled | cancel API / admin | ❌ |

**非法转换（必须拒绝）：**

- sent → * （任何）
- rejected / expired / canceled → sent
- failed → sent **without** new pending row / explicit manual resend flow（future · 非 auto）

---

## 3. 幂等键设计

| 字段 | 用途 |
|------|------|
| `pending_assisted_id` | 主业务 id · idempotency 基础 |
| `idempotency_key` | 默认 `{pending_assisted_id}:assisted_send` · 可含 attempt version |
| `idempotency_consumed` | FinalGuardInput 字段 · true → guard G16 block |

**规则：**

| # | 规则 |
|---|------|
| I1 | 同一个 `pending_assisted_id` **只能成功发送一次** |
| I2 | outbound attempt 前必须 **acquire** idempotency lock |
| I3 | lock acquired → 写 `outbound_send_attempted` → 再 outbound |
| I4 | outbound success → mark idempotency **consumed** · status=sent |
| I5 | outbound failure → release or mark failed · **不** consumed · **不** auto retry |

---

## 4. Duplicate approve 行为

| 当前 pending status | duplicate approve 响应 | send? |
|---------------------|------------------------|-------|
| `pending` | 正常流程（若另一请求 in_progress → 见下） | 视 guard |
| `approved` + in_progress | `already_in_progress` | ❌ |
| `sent` | `already_sent` | ❌ **no double-send** |
| `failed` | `manual_review_required` | ❌ |
| `rejected` | `terminal_state` | ❌ |
| `expired` | `terminal_state` | ❌ |
| `canceled` | `terminal_state` | ❌ |

**并发：**

- 两线程同时 approve 同一 pending → 仅一个 acquire idempotency 成功
- 失败者 → `already_in_progress` · no-send
- **不允许 double-send**

---

## 5. 与 Final Guard G16 关系

| 场景 | idempotency_consumed | guard |
|------|----------------------|-------|
| 首次 approve | false | 可 pass |
| 已成功 sent 后再次 approve | true（或 terminal check 先于 guard） | G16 / terminal block |
| failed 后再次 approve | false（lock released）但 status=failed | terminal / manual_review · no auto send |

---

## 6. 14x skeleton 现状

| 项 | 14x |
|----|-----|
| status 转换 | reject → rejected · expire → expired · approve **不** → sent/approved |
| idempotency lock | **未实现** |
| duplicate approve on rejected | `terminal_state` ✅ |

---

*Phase 14y · planning only · 2026-06-03*

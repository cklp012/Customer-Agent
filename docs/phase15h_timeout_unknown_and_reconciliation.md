# Phase 15h — Timeout, Unknown, and Reconciliation

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15e_failure_rollback_and_reconciliation.md](phase15e_failure_rollback_and_reconciliation.md) |

---

## 1. Timeout ≠ Failed

| 场景 | 错误分类 | 行为 |
|------|----------|------|
| HTTP/MMS timeout | `timeout_unknown` | **unknown outcome** |
| Connection reset mid-send | `timeout_unknown` | **unknown outcome** |
| Platform explicit error | `failed` or `rejected_by_platform` | known failure |
| Adapter unavailable | `unavailable` | no-send · retry later |

**Outbound timeout 不能简单视为 failed** — 可能已发送但响应丢失。

---

## 2. Unknown outcome 处理

| 规则 |
|------|
| Port returns `platform_status=timeout_unknown` |
| Service **不得**自动重发 |
| Service sets pending → **unknown** (or failed_unknown · schema TBD) |
| Audit: `outbound_send_unknown` |
| Idempotency: stay **`in_progress`** or **`failed_unknown`** — **后续 phase 决定** |
| Trigger reconciliation task |

---

## 3. Reconciliation 流程（future）

```text
unknown detected
    → append audit: reconciliation_required
    → recovery task (scheduled · manual trigger)
        → query PDD message history / platform API
        → OR human confirms in dashboard
    → branch:
        A) platform actually sent
            →补 audit: outbound_send_succeeded (late)
            → pending → sent
            → idempotency → mark_succeeded
        B) platform did NOT send
            → human confirms retry or reject
            → NO automatic retry
        C) still ambiguous
            → pending stays unknown
            → manual_review_required
```

**Recovery task 只能 reconcile / append audit — 不自动重发。**

---

## 4. Idempotency 状态建议（TBD · 后续 schema planning）

| Outcome | Suggested idempotency state |
|---------|----------------------------|
| sent (confirmed) | `succeeded` |
| failed (confirmed) | `failed` |
| timeout_unknown | `in_progress` **or** `failed_unknown` |
| reconciliation → sent | `succeeded` (late mark) |
| reconciliation → not sent | `failed` · human decides retry |

**15h 只规划 · 不创建表 · 不实现 mark 逻辑。**

---

## 5. Pending 状态建议（TBD · 后续 schema planning）

| Outcome | Suggested pending status |
|---------|-------------------------|
| sent | `sent` |
| failed | `failed` |
| timeout_unknown | `unknown` or `failed` with `unknown_outcome` flag |
| reconciliation pending | `unknown` + `manual_review_required` |

---

## 6. Duplicate approve on unknown

| 场景 | 行为 |
|------|------|
| pending status = unknown | duplicate approve → **`manual_review_required`** |
| idempotency still in_progress | **no double-send** |
| new approve attempt | 409 or 422 · dashboard shows reconciliation UI |

---

## 7. Platform success + local DB failure（danger state）

| 场景 | 行为 |
|------|------|
| Port returns `sent` + `provider_message_id` | platform OK |
| Local pending/idempotency/audit write fails | **danger state** |
| Action | reconciliation · **不自动重发** |
| Audit | `outbound_send_local_persist_failed` |
| Human | verify platform message · repair local state |

---

## 8. 禁止

| 禁止 |
|------|
| Auto-retry on timeout |
| Auto-retry on unknown |
| Idempotency release + resend without human |
| Fallback legacy SendMessage on unknown |

---

*Phase 15h · docs only · 2026-06-03*

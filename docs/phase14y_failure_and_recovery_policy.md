# Phase 14y — Failure and Recovery Policy

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14y_approve_to_outbound_sequence.md](phase14y_approve_to_outbound_sequence.md) · [phase14r_failure_and_rollback.md](phase14r_failure_and_rollback.md) |

---

## 1. 总原则

| # | 原则 |
|---|------|
| F1 | **final guard block → no-send** |
| F2 | **final guard exception (G27) → no-send** · fail-closed |
| F3 | **AuditLog before outbound failure → no-send**（strict 默认） |
| F4 | **SendDecisionSnapshot failure before outbound → no-send** |
| F5 | **idempotency lock failure → no-send** |
| F6 | **outbound unavailable → no-send** |
| F7 | **outbound failure → pending status=failed · manual review · no auto retry** |
| F8 | **DB failure → no fallback legacy send** |
| F9 | **duplicate approve → no double-send** |
| F10 | **recovery task 可补 audit · 不得自动重发** |
| F11 | **non-test legacy unchanged** |

---

## 2. 失败场景矩阵

| 场景 | send? | pending status | audit | 备注 |
|------|-------|----------------|-------|------|
| final guard block | ❌ | pending（或 approved 未 outbound） | final_guard_blocked | 14x ✅ |
| final guard exception | ❌ | 不变 | guard_exception optional | fail-closed |
| AuditLog before outbound fail | ❌ | 不变/approved | 缺失 partial | strict block |
| Snapshot merchant_confirm fail | ❌ | approved | partial | no outbound |
| idempotency acquire fail | ❌ | approved | 无 attempted | no double-send |
| outbound_send_attempted audit fail | ❌ | approved | 无 attempted | **不得** outbound |
| outbound fail | attempt only | **failed** | outbound_send_failed | no auto retry |
| outbound success | ✅ | **sent** | outbound_send_succeeded | |
| success + succeeded audit fail | 已发送 | sent | recovery | **no resend** |
| duplicate approve (sent) | ❌ | sent | idempotent | already_sent |
| duplicate approve (in_progress) | ❌ | approved | — | already_in_progress |
| duplicate approve (failed) | ❌ | failed | — | manual_review_required |
| DB read/write fail mid-flow | ❌ | 不变/rollback | partial | **no legacy fallback** |

---

## 3. Recovery task（规划 · 非 auto retry）

| 场景 | recovery 动作 | 禁止 |
|------|---------------|------|
| outbound success · audit fail | 补写 `outbound_send_succeeded` · reconcile pending=sent | **重发** SendMessage |
| partial audit chain | 补缺失 audit 行 · Dashboard 标记 reconciled | 推断 success 并重发 |
| pending=failed | 人工 review UI · 新建 pending 或 human takeover | auto retry outbound |
| idempotency stuck | admin release lock · 仅 manual | auto release + send |

**Recovery worker：** 15b+ 可选 · flags off 默认 · read-only reconcile preferred。

---

## 4. Rollback 策略

| 动作 | 行为 |
|------|------|
| disable `PRODUCT_ASSISTED_SERVICE_ENABLED` | service no-op · create/approve disabled |
| disable assisted send sub-flag (15a) | approve 仅 guard skeleton / no outbound |
| keep preview mode | test shop zero-send 不变 |
| keep pending/audit/replylog tables | read-only · Dashboard 14z read |
| audit logs | **不 DELETE** |
| pending rows | cancel/expire · 不 force send |
| PDD legacy | **无影响** · queue `pdd_{shop_id}` 不变 |
| non-test `_send_reply` | **无影响** |
| Doudian | production **not enabled** |

---

## 5. Service 结果 status（future 扩展）

| status | 含义 | send occurred? |
|--------|------|----------------|
| `guard_blocked` | final guard block | ❌ |
| `guard_passed_but_send_not_implemented` | 14x skeleton | ❌ |
| `outbound_succeeded` | future success | ✅ |
| `outbound_failed` | future platform fail | attempt |
| `already_sent` | duplicate | ❌ |
| `already_in_progress` | concurrent | ❌ |
| `manual_review_required` | failed pending | ❌ |
| `audit_before_send_failed` | strict | ❌ |
| `snapshot_before_send_failed` | strict | ❌ |
| `idempotency_failed` | strict | ❌ |

---

## 6. 与 legacy 隔离

```text
product_gate.db failure
    → AssistedReplyService returns error
    → NO fallback to database/models.py legacy path
    → NO fallback to handler _send_reply for assisted intent
```

---

*Phase 14y · planning only · 2026-06-03*

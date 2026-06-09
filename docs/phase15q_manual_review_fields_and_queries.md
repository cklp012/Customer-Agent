# Phase 15q — Manual Review Fields and Queries

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15n_manual_review_and_operator_runbook.md](phase15n_manual_review_and_operator_runbook.md) |

---

## 1. Manual review detail 展示字段

| 字段 | 来源 |
|------|------|
| `pending_assisted_id` | `pending_assisted_replies` |
| `reply_log_id` | pending row |
| `buyer_id` / `shop_id` | pending row |
| `final_reply` | pending row（只读） |
| `current_pending_status` | pending.`status` |
| `outbound_idempotency_key` | `assisted_send:{pending_assisted_id}` |
| `outbound_status` | `outbound_idempotency_keys.status` |
| `last_platform_status` | idempotency.`platform_status` |
| `provider_message_id` | idempotency.`provider_message_id` |
| `trace_id` | audit / idempotency metadata |
| `reconciliation_attempts` | `reconciliation_attempts` list by pending |
| `audit timeline` | `audit_logs` by pending_assisted_id |
| `final guard snapshot` | `send_decisions` + guard audit |
| `last operator action` | latest audit with operator_* / reconciliation_* |

**Redact：** cookie · token · credential · session · API key

---

## 2. List filters（manual review queue）

| Filter | 列 / join |
|--------|-----------|
| `workspace_id` | pending / idempotency |
| `shop_id` | pending |
| `platform_id` | pending |
| `status` | pending.`status` IN (`send_unknown`, `manual_review_required`, ...) |
| `outbound_status` | join idempotency.`status` |
| `created_at` range | pending.`created_at` |
| `updated_at` range | pending.`updated_at` |
| `operator_user_id` | audit / reconciliation_attempts |
| `buyer_id` | pending |
| `trace_id` | audit / reconciliation |

**默认队列：** `status IN ('manual_review_required', 'send_unknown')` AND outbound `status IN ('timeout_unknown', 'sent_unconfirmed', 'manual_review_required')`

---

## 3. 建议 API（future · 15t+）

| Endpoint | 方法 | 说明 |
|----------|------|------|
| `/api/product/manual-review` | GET | list + filters |
| `/api/product/manual-review/<pending_assisted_id>` | GET | detail |
| `/api/product/manual-review/<id>/mark-sent` | POST | operator · audit |
| `/api/product/manual-review/<id>/mark-not-sent` | POST | operator · audit |

**15q 不实现** — 仅规划字段与查询。

---

## 4. 权限

| 角色 | 权限 |
|------|------|
| `viewer` | read-only list/detail |
| `operator` | read + mark actions（shop scope） |
| `admin` / `owner` | operator + create_new_pending |
| **cross-workspace** | **forbidden** — 所有查询必须 `workspace_id` 过滤 |

---

## 5. Join 查询草图（future SQL · planning）

```sql
-- conceptual only · not executed in 15q
SELECT p.*, o.status AS outbound_status, o.platform_status, o.provider_message_id
FROM pending_assisted_replies p
LEFT JOIN outbound_idempotency_keys o
  ON o.idempotency_key = 'assisted_send:' || p.pending_assisted_id
WHERE p.workspace_id = :ws AND p.shop_id = :shop
  AND p.status IN ('manual_review_required', 'send_unknown')
ORDER BY p.updated_at DESC;
```

Reconciliation attempts: separate query by `pending_assisted_id`.

---

## 6. 与 read dashboard（15d）关系

| 项 | 关系 |
|----|------|
| Pending list/detail read API | **unchanged** · 可扩展 filter 文档 |
| Manual review | **新** read surface · 不替代 15d |
| Action routes | approve on `manual_review_required` → **block** |

---

*Phase 15q · docs only · 2026-06-03*

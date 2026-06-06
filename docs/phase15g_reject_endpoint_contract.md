# Phase 15g — Reject Endpoint Contract

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不实现 endpoint** |
| 方法 | `POST /api/product/pending-assisted/<pending_assisted_id>/reject` |
| 对齐 | [phase15g_dashboard_action_endpoint_plan.md](phase15g_dashboard_action_endpoint_plan.md) · [phase14x_done.md](phase14x_done.md) |

---

## 1. 设计原则

| # | 原则 |
|---|------|
| 1 | Endpoint **只调用** `AssistedReplyService.reject_pending` |
| 2 | **不触发** final guard |
| 3 | **不 outbound** · **不 SendMessage** |
| 4 | `rejected` 是 **终态** |
| 5 | duplicate reject → `terminal_state` 或 idempotent 200 |
| 6 | **viewer 禁止** reject |

---

## 2. Request

```http
POST /api/product/pending-assisted/{pending_assisted_id}/reject
Content-Type: application/json
```

### 2.1 Body

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `workspace_id` | string | ✅ | scope |
| `shop_id` | string | ✅ | scope |
| `actor_user_id` | string | ✅ | |
| `actor_role` | string | ✅ | operator / admin / owner |
| `reject_reason` | string | 可选 | 人类可读原因 |
| `client_request_id` | string | ✅ | replay 防护 |
| `expected_pending_status` | string | ✅ | 通常 `pending` |
| `csrf_token` | string | ✅ | CSRF |
| `confirm_checkbox` | bool | ✅ | 必须 true |

---

## 3. Response（200 · success）

```json
{
  "success": true,
  "status": "rejected",
  "action": "reject",
  "pending_assisted_id": "pa-uuid",
  "reply_log_id": "rl-uuid",
  "audit_log_id": "audit-uuid",
  "reason": "not suitable",
  "warnings": []
}
```

### 3.1 Response 字段

| 字段 | 说明 |
|------|------|
| `success` | true on reject success |
| `status` | `"rejected"` |
| `action` | `"reject"` |
| `audit_log_id` | `assisted_rejected` audit |
| `reason` | reject_reason echo |

---

## 4. 行为约束

| 行为 | reject endpoint |
|------|-----------------|
| final guard | ❌ 不调用 |
| outbound / idempotency acquire | ❌ |
| SendMessage | ❌ |
| pending status | `pending` → `rejected` |
| 已 rejected / sent / expired | 409 或 200 idempotent · **no mutation** |

---

## 5. Handler 伪代码（future）

```text
validate auth + csrf + role + scope
dedupe client_request_id
if expected_pending_status != pending.status → 409
result = AssistedReplyService.reject_pending(..., reason=reject_reason)
return JSON · no SendMessage
```

---

## 6. 可选：expire/cancel（future）

| Endpoint | Service | 说明 |
|----------|---------|------|
| `POST .../expire` | `expire_pending` | system/cron 或 admin · 15g 仅规划可选 |

不在 15g 首要交付范围。

---

*Phase 15g · docs only · 2026-06-03*

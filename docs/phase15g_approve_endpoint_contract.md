# Phase 15g — Approve Endpoint Contract

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不实现 endpoint** |
| 方法 | `POST /api/product/pending-assisted/<pending_assisted_id>/approve` |
| 对齐 | [phase15g_dashboard_action_endpoint_plan.md](phase15g_dashboard_action_endpoint_plan.md) · [phase15f_done.md](phase15f_done.md) |

---

## 1. 设计原则

| # | 原则 |
|---|------|
| 1 | Endpoint **只调用** `AssistedReplyService.approve_pending` — 不 SendMessage / outbound |
| 2 | **默认 dry_run=true** — 与 env `PRODUCT_ASSISTED_SEND_DRY_RUN` 一致 |
| 3 | **dry_run=false** → service 返回 `live_send_not_implemented` · **本阶段禁止 live send** |
| 4 | **不得**用 request body 覆盖 pending 的 `buyer_id` / ownership 字段 |
| 5 | `final_reply_override` 传入 service · **重新** final guard |
| 6 | `expected_pending_status` 乐观并发 · stale → 409 |
| 7 | `client_request_id` replay 防护 |

---

## 2. Request

```http
POST /api/product/pending-assisted/{pending_assisted_id}/approve
Content-Type: application/json
```

### 2.1 Body

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `workspace_id` | string | ✅ | 须 match pending.workspace_id |
| `shop_id` | string | ✅ | 须 match pending.shop_id |
| `actor_user_id` | string | ✅ | 操作者 |
| `actor_role` | string | ✅ | operator / admin / owner · **非 viewer** |
| `final_reply_override` | string | 可选 | 覆盖 final_reply · 触发 guard |
| `client_request_id` | string | ✅ | UUID · replay 防护 |
| `expected_pending_status` | string | ✅ | 通常 `pending` · stale → 409 |
| `dry_run_expected` | bool | ✅ | **默认 true** · UI 确认 dry-run |
| `csrf_token` | string | ✅ | browser dashboard CSRF |
| `confirm_checkbox` | bool | ✅ | 必须 `true` · 人工确认 |

**禁止字段：** `buyer_id` override · `platform_id` override · arbitrary outbound flags · direct `SendMessage` params。

---

## 3. Response（200 · workflow result）

```json
{
  "success": true,
  "status": "dry_run_would_send",
  "action": "approve",
  "pending_assisted_id": "pa-uuid",
  "reply_log_id": "rl-uuid",
  "final_guard_allowed": true,
  "final_guard_block_code": null,
  "dry_run": true,
  "would_send": true,
  "live_send_attempted": false,
  "provider_message_id": null,
  "audit_log_id": "audit-uuid",
  "idempotency_key": "assisted_send:pa-uuid",
  "reason": "dry_run_would_send",
  "warnings": [],
  "auth": "placeholder_future_auth_required"
}
```

### 3.1 Response 字段

| 字段 | 说明 |
|------|------|
| `success` | workflow 是否成功（guard block → false） |
| `status` | service status · e.g. `dry_run_would_send` · `guard_blocked` · `live_send_not_implemented` |
| `action` | `"approve"` |
| `final_guard_allowed` | guard 结果 |
| `final_guard_block_code` | block 时非空 |
| `dry_run` | 是否 dry-run 路径 |
| `would_send` | dry-run port 结果 |
| `live_send_attempted` | **dry-run stage 恒 false** |
| `provider_message_id` | live only · dry-run **null** |
| `idempotency_key` | `assisted_send:{pending_assisted_id}` |
| `warnings` | 非致命提示 |

---

## 4. Handler 伪代码（future · 15i）

```text
validate auth + csrf + role + workspace/shop scope
dedupe client_request_id
if expected_pending_status != pending.status → 409
result = AssistedReplyService.approve_pending(
    pending_assisted_id,
    actor_user_id=...,
    actor_role=...,
    final_reply=final_reply_override,
)
map result.status → HTTP + JSON
never call SendMessage
```

---

## 5. Error 映射（摘要）

| 场景 | HTTP | status 字段 |
|------|------|-------------|
| guard block | **422** | `guard_blocked` |
| allowlist denied | 403 | `allowlist_denied` |
| live_send_not_implemented | 200 或 422 | `live_send_not_implemented` |
| not found | 404 | `not_found` |
| stale status | 409 | `conflict` |

详见 [action_audit_and_response_codes](phase15g_action_audit_and_response_codes.md)。

---

## 6. 明确不提供（15g）

| 项 | 状态 |
|----|------|
| Endpoint 实现 | ❌ |
| Live send | ❌ |
| pending → sent | ❌ |
| Handler 直调 | ❌ |

---

*Phase 15g · docs only · 2026-06-03*

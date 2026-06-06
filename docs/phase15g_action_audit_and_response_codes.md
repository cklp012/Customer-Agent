# Phase 15g — Action Audit and Response Codes

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15g_dashboard_action_endpoint_plan.md](phase15g_dashboard_action_endpoint_plan.md) |

---

## 1. Audit actions（规划）

### 1.1 Dashboard layer（action route）

| action | 时机 |
|--------|------|
| `dashboard_approve_requested` | POST approve 收到 · mutation 前 |
| `dashboard_reject_requested` | POST reject 收到 |
| `dashboard_action_denied` | RBAC / scope 拒绝 |
| `dashboard_action_conflict` | stale status / client_request_id conflict |
| `dashboard_action_csrf_failed` | CSRF 校验失败 |
| `dashboard_action_rate_limited` | 429 |

### 1.2 Service layer（AssistedReplyService · 已有/15f）

| action | 时机 |
|--------|------|
| `assisted_approved` | guard pass path |
| `final_guard_passed` | guard allow |
| `final_guard_blocked` | guard block |
| `assisted_dry_run_would_send` | dry-run port success |
| `assisted_rejected` | reject success |
| `live_send_not_implemented` | dry_run=false · metadata reason |

**dry-run stage 不写：** `outbound_send_attempted` · `outbound_send_succeeded`

---

## 2. HTTP response codes

| Code | 场景 |
|------|------|
| **200** | success · dry_run_would_send · rejected · idempotent replay |
| **400** | invalid body · missing confirm_checkbox |
| **401** | unauthenticated |
| **403** | forbidden · viewer · cross-workspace/shop · CSRF fail |
| **404** | pending_assisted_id not found |
| **409** | conflict · stale expected_pending_status · client_request_id payload mismatch |
| **422** | **final guard blocked** · validation failed |
| **429** | rate limited |
| **500** | internal error · **no-send** |

---

## 3. Final guard block HTTP 选择

**15g 签收：guard block → HTTP 422**

| 项 | 值 |
|----|-----|
| HTTP | **422 Unprocessable Entity** |
| body.success | `false` |
| body.status | `guard_blocked` |
| body.final_guard_block_code | e.g. `forbidden_promise` |
| pending status | **unchanged** |

理由：block 是业务校验失败 · 非 auth 问题 · dashboard 可展示 block_reason。

---

## 4. Error response 安全

| 规则 |
|------|
| **不得**暴露 token / cookie / credential / session_id |
| **不得**返回 stack trace 给 browser |
| error 字段 human-readable · 无 PII leak |
| 所有 no-send errors **dashboard-readable** |

---

## 5. Audit failure policy

| 时机 | 行为 |
|------|------|
| dashboard audit **before** mutation fails | **no mutation** where possible |
| service audit fails mid-flow | 见 [failure_rollback](phase15g_failure_rollback_policy.md) · no legacy send |

---

## 6. Response body 错误示例（422 guard block）

```json
{
  "success": false,
  "status": "guard_blocked",
  "action": "approve",
  "pending_assisted_id": "pa-uuid",
  "final_guard_allowed": false,
  "final_guard_block_code": "forbidden_promise",
  "reason": "回复含不允许的承诺用语",
  "dry_run": true,
  "would_send": false,
  "live_send_attempted": false,
  "warnings": []
}
```

---

*Phase 15g · docs only · 2026-06-03*

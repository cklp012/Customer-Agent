# Phase 15g — Permissions · CSRF · Idempotency

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14z_filters_permissions_and_pagination.md](phase14z_filters_permissions_and_pagination.md) |

---

## 1. RBAC

| Role | approve | reject | final_reply_override | cancel/expire |
|------|---------|--------|----------------------|---------------|
| **viewer** | ❌ | ❌ | ❌ | ❌ |
| **operator** | ✅ | ✅ | ✅ | ❌ |
| **admin** | ✅ | ✅ | ✅ | ✅ optional |
| **owner** | ✅ | ✅ | ✅ | ✅ optional |

**viewer 禁止一切 action endpoint。**

---

## 2. Scope 校验

| 校验 | 失败 |
|------|------|
| `workspace_id` match pending + auth context | **403** forbidden |
| `shop_id` match pending + auth context | **403** |
| cross-workspace | **403** · audit `dashboard_action_denied` |
| cross-shop | **403** |

Action route **不得**接受 body 中任意 `buyer_id` / `shop_id` 覆盖已有 pending ownership。

---

## 3. CSRF

| 项 | 规则 |
|----|------|
| browser dashboard POST | **csrf_token 必填** |
| failure | **403** · audit `dashboard_action_csrf_failed` · **no mutation** |
| API token / service account（future） | 单独规划 · 非 15g scope |

---

## 4. client_request_id（action replay）

| 场景 | 行为 |
|------|------|
| 首次 request | 正常执行 service · 缓存 `(client_request_id → response)` |
| 重复 **相同** payload | **200** · 返回缓存结果（idempotent） |
| 重复 **不同** payload | **409** conflict · audit `dashboard_action_conflict` |
| TTL | 建议 24h · 15j skeleton 规划持久化 |

存储：**15j** `client_request_id` skeleton — 15g 仅规划。

---

## 5. expected_pending_status（乐观并发）

| 场景 | 行为 |
|------|------|
| match pending.status | proceed |
| mismatch | **409** · audit `dashboard_action_conflict` · **no mutation** |
| terminal state | **409** 或 idempotent reject response |

---

## 6. Rate limit

| 维度 | 建议 |
|------|------|
| per `actor_user_id` | 60 approve/min · configurable |
| per `shop_id` | burst protection |
| exceeded | **429** · audit `dashboard_action_rate_limited` |

---

## 7. Audit every attempt

尽可能记录：

- `dashboard_approve_requested` / `dashboard_reject_requested`（mutation 前）
- `dashboard_action_denied` / `csrf_failed` / `conflict` / `rate_limited`（失败）

详见 [action_audit_and_response_codes](phase15g_action_audit_and_response_codes.md)。

---

## 8. 禁止

| 禁止 | 原因 |
|------|------|
| arbitrary SQL / bulk action | injection / scope escape |
| viewer action | RBAC |
| bypass AssistedReplyService | G1 |
| fallback legacy send on auth failure | no-send |

---

*Phase 15g · docs only · 2026-06-03*

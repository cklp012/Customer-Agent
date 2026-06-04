# Phase 12d — API Contract（Draft · SSOT）

| 项 | 值 |
|----|-----|
| 类型 | **未来 API 设计** · **本 Phase 不实现** |
| 版本 | `v1`（草案） |
| 关联 | [phase12d_dashboard_ia.md](phase12d_dashboard_ia.md) · [phase12d_connection_status_read_model.md](phase12d_connection_status_read_model.md) |

---

## 1. 通用约定

| 项 | 约定 |
|----|------|
| Base URL | `/api/v1` |
| Auth | Bearer session / workspace scoped |
| 错误 | `{ "error": { "code", "message", "details" } }` |
| 分页 | `cursor` + `limit`（max 100） |
| 时区 | 查询参数 `tz`（IANA）；默认工作区设置 |
| Idempotency | POST 变更操作建议 `Idempotency-Key` header |

**权限角色：** `owner` \| `admin` \| `agent` \| `readonly`

**审计：** 所有 **POST** 变更 **必须** 写 `AuditLog`（见各 endpoint）。

---

## 2. GET `/api/workspaces/{workspace_id}/dashboard`

| 项 | 内容 |
|----|------|
| **purpose** | 首页聚合：工作区摘要 + 店铺卡片 + 今日活动 + 告警 + 待人工数量 |
| **permission** | `readonly`+ |
| **audit** | 否 |

**Query params**

| 名 | 类型 | 说明 |
|----|------|------|
| `date` | date? | 默认 today |
| `tz` | string? | |

**Response `200`**

```json
{
  "workspace": { "WorkspaceStatusSummary" },
  "pause": { "PauseStateSummary" },
  "today_activity": { "ReplyActivitySummary" },
  "shops": [ { "ShopConnectionSummary" } ],
  "alerts": [ { "Alert" } ],
  "human_takeover_open_count": 0,
  "usage": { "plan_name", "ai_suggestions_used", "..." },
  "as_of": "ISO8601"
}
```

---

## 3. GET `/api/workspaces/{workspace_id}/shops`

| 项 | 内容 |
|----|------|
| **purpose** | 店铺列表（连接卡片数据源） |
| **permission** | `readonly`+ |
| **audit** | 否 |

**Query:** `platform_id?`, `effective_status?`, `cursor`, `limit`

**Response:** `{ "items": [ ShopConnectionSummary ], "next_cursor": "..." }`

---

## 4. GET `/api/shops/{shop_binding_id}/connection-status`

| 项 | 内容 |
|----|------|
| **purpose** | 单店连接详情 + credential 健康 |
| **permission** | `readonly`+（须属 workspace） |
| **audit** | 否 |

**Response:**

```json
{
  "shop": { "ShopConnectionSummary" },
  "credential": { "CredentialHealthSummary" },
  "alerts": [ { "Alert" } ]
}
```

---

## 5. GET `/api/shops/{shop_binding_id}/reply-activity`

| 项 | 内容 |
|----|------|
| **purpose** | 模块 C：按日统计 |
| **permission** | `readonly`+ |
| **audit** | 否 |

**Query:** `date` (required), `tz?`

**Response:** `{ "summary": ReplyActivitySummary, "risk_summary": { refund_request_count, ... } }`

---

## 6. GET `/api/shops/{shop_binding_id}/reply-logs`

| 项 | 内容 |
|----|------|
| **purpose** | 回复日志列表（preview / sent / blocked） |
| **permission** | `readonly`+ |
| **audit** | 否 |

**Query:** `date?`, `intent?`, `send_status?`, `blocked_reason?`, `cursor`, `limit`

**Response:** `{ "items": [ ReplyLogListItem ], "next_cursor" }`

---

## 7. GET `/api/workspaces/{workspace_id}/human-takeover-queue`

| 项 | 内容 |
|----|------|
| **purpose** | 模块 D：待人工队列 |
| **permission** | `agent`+ |
| **audit** | 否 |

**Query:** `status=open|claimed|resolved`, `shop_binding_id?`, `priority?`, `cursor`, `limit`

**Response:** `{ "items": [ HumanTakeoverQueueItem ], "next_cursor" }`

---

## 8. POST `/api/workspaces/{workspace_id}/pause`

| 项 | 内容 |
|----|------|
| **purpose** | 工作区一键暂停（模块 H） |
| **permission** | `admin`+ |
| **audit** | **必须** `workspace.pause` |

**Body**

```json
{
  "reason": "string (optional)",
  "confirm": true
}
```

**Response `200`:** `{ "workspace_pause": true, "paused_at", "paused_by", "audit_id" }`

---

## 9. POST `/api/shops/{shop_binding_id}/pause`

| 项 | 内容 |
|----|------|
| **purpose** | 单店暂停 |
| **permission** | `admin`+ |
| **audit** | **必须** `shop.pause` |

**Body:** `{ "reason?", "confirm": true }`

**Response:** `{ "shop_pause": true, "audit_id" }`

---

## 10. POST `/api/workspaces/{workspace_id}/resume`

| 项 | 内容 |
|----|------|
| **purpose** | 恢复工作区（清除 workspace_pause） |
| **permission** | `admin`+ |
| **audit** | **必须** `workspace.resume` |

**Body:** `{ "confirm": true }`

**Response:** `{ "workspace_pause": false, "resumed_by", "resumed_at", "audit_id" }`

---

## 11. POST `/api/shops/{shop_binding_id}/resume`

| 项 | 内容 |
|----|------|
| **purpose** | 恢复单店 |
| **permission** | `admin`+ |
| **audit** | **必须** `shop.resume` |

**Body:** `{ "confirm": true }`

---

## 12. POST `/api/shops/{shop_binding_id}/reply-mode`

| 项 | 内容 |
|----|------|
| **purpose** | 切换 preview / assisted / auto |
| **permission** | `admin`+ |
| **audit** | **必须** `shop.reply_mode_changed` |

**Body**

```json
{
  "reply_mode": "preview | assisted | auto",
  "product_gate_enabled": true,
  "confirm_risk": false,
  "confirm_consultation_scope": false,
  "confirm_auto_enable": false
}
```

**校验规则**

| 目标 mode | 必填 confirm |
|-----------|--------------|
| `preview` | 无 |
| `assisted` | 无（Growth+） |
| `auto` | `confirm_risk=true` AND `confirm_consultation_scope=true` AND `confirm_auto_enable=true` |

**附加校验**

- `binding_status` 须 `connected`
- `auth_action_required` → **409** `AUTH_REQUIRED`
- **`preview → auto` 不能绕过 intent gate** — API 只改 `reply_mode`；运行时 SendDecision 仍拦截 blocked intent
- `auto` 写入 `auto_enabled_at`, `auto_enabled_by`

**Response `200`:**

```json
{
  "shop": { "ShopConnectionSummary" },
  "audit_id": "uuid"
}
```

**Response `409`:** 未满足确认项 / 连接未就绪

---

## 13. AuditLog 要求（变更类 SSOT）

| action | 记录字段 |
|--------|----------|
| `workspace.pause` | workspace_id, merchant_id, reason, ts |
| `workspace.resume` | workspace_id, merchant_id, ts |
| `shop.pause` | shop_binding_id, merchant_id, reason, ts |
| `shop.resume` | shop_binding_id, merchant_id, ts |
| `shop.reply_mode_changed` | from_mode, to_mode, confirms[], merchant_id, ts |

**保留：** ≥ 90 天（Growth），≥ 365 天（Pro）。

---

## 14. 未纳入 12d 的 endpoint（后续）

| endpoint | Phase |
|----------|-------|
| `POST .../reply-logs/{id}/approve` | 12c/12f assisted |
| `GET .../send-decisions/{id}` | 12e |
| `POST .../reauthorize` | binding playbook |

---

## 15. 实现声明

| 项 | 状态 |
|----|------|
| API 实现 | **未开始** |
| DB / projection | **12e** |
| UI 绑定 | **12g** wireframe |

---

*Phase 12d · API Contract · docs only*

# Phase 14z — Pending Assisted List API Contract

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不实现 endpoint** |
| 方法 | `GET /api/product/pending-assisted` |
| 对齐 | [phase14z_pending_assisted_dashboard_read_plan.md](phase14z_pending_assisted_dashboard_read_plan.md) · [phase14o_done.md](phase14o_done.md) |

---

## 1. 设计原则

| # | 原则 |
|---|------|
| 1 | **只读** — GET only · 无 POST/PUT/PATCH/DELETE |
| 2 | **不调用** SendMessage / outbound / handler |
| 3 | **列表只返回 preview** — 非完整敏感文本 |
| 4 | **不暴露** credential / token / cookie / session_id |
| 5 | **workspace / shop scope 必校验** |
| 6 | **不提供** approve / reject / send |

---

## 2. Request

### 2.1 Endpoint

```http
GET /api/product/pending-assisted
```

### 2.2 Query 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `workspace_id` | string | ✅（authenticated） | 租户 scope |
| `shop_id` | string | 可选 | 店铺 filter |
| `account_id` | string | 可选 | 账号 filter |
| `platform_id` | string | 可选 | e.g. `pinduoduo` |
| `status` | string | 可选 | pending / sent / failed / rejected / expired / canceled · 可多值 comma |
| `buyer_id` | string | 可选 | 买家 filter |
| `intent_category` | string | 可选 | policy key |
| `risk_level` | string | 可选 | low / medium / high / critical |
| `final_guard_allowed` | bool | 可选 | 最近一次 guard 结果 filter |
| `final_guard_block_code` | string | 可选 | e.g. `forbidden_promise` |
| `created_after` | ISO8601 | 可选 | |
| `created_before` | ISO8601 | 可选 | |
| `updated_after` | ISO8601 | 可选 | |
| `updated_before` | ISO8601 | 可选 | |
| `page` | int | 可选 | 默认 1 · ≥1 |
| `page_size` | int | 可选 | 默认 20 · **上限 100** |
| `sort_by` | string | 可选 | allowlist · 见 filters doc |
| `sort_order` | string | 可选 | `asc` \| `desc` · 默认 `desc` |

**非法 sort_by / 超大 page_size → 400 + error body（规划）**

---

## 3. Response

### 3.1 Success (200)

```json
{
  "items": [
    {
      "pending_assisted_id": "pa-uuid",
      "reply_log_id": "rl-uuid",
      "workspace_id": "ws-1",
      "shop_id": "shop-1",
      "account_id": "acc-1",
      "platform_id": "pinduoduo",
      "buyer_id": "buyer-1",
      "buyer_message_preview": "这款商品还有库存吗…",
      "ai_suggested_reply_preview": "您好，该商品目前有货…",
      "merchant_edited_reply_preview": null,
      "intent_category": "inventory_question",
      "risk_level": "low",
      "status": "pending",
      "final_guard_allowed": null,
      "final_guard_block_code": null,
      "expires_at": "2026-06-04T12:00:00+00:00",
      "created_at": "2026-06-03T12:00:00+00:00",
      "updated_at": "2026-06-03T12:00:00+00:00",
      "latest_audit_action": "pending_assisted_created"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 42,
    "has_next": true
  },
  "source": "sqlite_shadow",
  "warnings": []
}
```

### 3.2 Field 说明

| 字段 | 说明 |
|------|------|
| `buyer_message_preview` | 截断 preview · 默认 max 80 chars · 不含完整 PII |
| `ai_suggested_reply_preview` | 同上 |
| `merchant_edited_reply_preview` | 同上 · nullable |
| `final_guard_allowed` | 来自最近 snapshot/guard 缓存 join · 无则 null |
| `final_guard_block_code` | 最近 block · 无则 null |
| `latest_audit_action` | 最新 audit action 名 |
| `source` | `sqlite_shadow` \| `empty` |
| `warnings[]` | stale · partial · flag off · DB degraded |

### 3.3 Preview 截断规则（规划）

| 规则 | 值 |
|------|-----|
| max preview length | 80 chars（可配置） |
| suffix | `…` |
| 列表 **不返回** 完整 buyer_message / full reply |

---

## 4. Error responses（规划）

| HTTP | 场景 |
|------|------|
| 400 | invalid sort · page_size > 100 · bad date |
| 403 | cross-workspace · role denied |
| 503 | DB unavailable · optional · 或 200 + empty + warnings |

**read failure 不 fallback legacy send** — 见 failure policy doc。

---

## 5. 与 write path 隔离

| 操作 | List API |
|------|----------|
| create pending | ❌ |
| approve / reject | ❌ |
| final guard execute | ❌ |
| audit append | ❌ |
| outbound | ❌ |

---

*Phase 14z · planning only · 2026-06-03*

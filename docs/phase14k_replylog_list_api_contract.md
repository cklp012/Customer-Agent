# Phase 14k — ReplyLog List API Contract (Draft)

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不实现** |
| 日期 | 2026-06-03 |
| Endpoint | `GET /api/product/reply-logs` |
| 对齐 | `PreviewReplyLogListItem`（13e）· `reply_logs` 表（14j） |

---

## 1. Purpose

分页列出 workspace 内 preview ReplyLog 活动，供 Dashboard 活动流 / 筛选列表使用。

**只读 · 不发送 · 不修改 gate 配置。**

---

## 2. Request

### 2.1 Method & Path

```
GET /api/product/reply-logs
```

### 2.2 Headers

| Header | 必填 | 说明 |
|--------|------|------|
| `Authorization` | ✅ | Bearer session · workspace scoped |
| `X-Workspace-Id` | 推荐 | 与 query `workspace_id` 交叉校验 |

### 2.3 Query Parameters

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `workspace_id` | string | ✅ | 租户隔离 |
| `shop_id` | string | | 店铺筛选 |
| `account_id` | string | | 账号筛选 |
| `platform_id` | string | | 默认 `pinduoduo` |
| `buyer_id` | string | | 买家筛选（脱敏展示在 UI，API 可传完整 id） |
| `send_status` | string | | 如 `not_sent_preview` · `not_sent_human_takeover` |
| `intent_bucket` | string | | `allowed` · `blocked` · `uncertain` |
| `risk_level` | string | | `low` · `medium` · `high` |
| `created_after` | ISO8601 | | 时间范围起 |
| `created_before` | ISO8601 | | 时间范围止 |
| `page` | int | | 默认 `1` · ≥ 1 |
| `page_size` | int | | 默认 `20` · **max 100** |

### 2.4 排序

- 默认：`created_at DESC`
- 14k 不规划多字段排序；14m 可扩展 `sort=-created_at`

---

## 3. Response `200`

```json
{
  "items": [
    {
      "reply_log_id": "uuid",
      "workspace_id": "ws-001",
      "platform_id": "pinduoduo",
      "shop_id": "shop_pdd_preview_test",
      "account_id": "acc_pdd_preview_test",
      "buyer_id": "buyer_uid_preview_test",
      "buyer_message": "这款商品还有库存吗",
      "ai_suggested_reply": "preview suggestion text",
      "send_status": "not_sent_preview",
      "send_mode": "preview_only",
      "intent": "stock_inquiry",
      "intent_bucket": "allowed",
      "risk_level": "low",
      "not_sent_explanation": "Preview mode: suggestion recorded, not sent.",
      "created_at": "2026-06-03T12:00:00+00:00"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1,
  "source": "in_memory",
  "warnings": []
}
```

### 3.1 `source` 枚举

| 值 | 含义 |
|----|------|
| `in_memory` | 仅读 `preview_log` projection |
| `sqlite_shadow` | 仅读 `product_gate.db` |
| `mixed` | 合并/去重（未来；14k 不实现） |

### 3.2 `warnings[]`

| 示例 | 场景 |
|------|------|
| `"sqlite_read_failed_fallback_in_memory"` | SQLite 读失败 · fallback in-memory |
| `"total_approximate_in_memory"` | in-memory 模式 total 为过滤后 len |

---

## 4. 字段映射（13e → API）

| API 字段 | 来源 |
|----------|------|
| `reply_log_id` | `PreviewReplyLogListItem.reply_log_id` |
| `buyer_message` | `buyer_message` |
| `ai_suggested_reply` | `ai_suggested_reply` |
| `send_status` | `send_status` |
| `intent` / `intent_bucket` / `risk_level` | projection |
| `not_sent_explanation` | projection |

**列表不包含：** `final_reply`（preview 为 null）· SendDecision 全量 · audit

---

## 5. 分页与 total 说明

| 模式 | `total` 行为 |
|------|-------------|
| **in_memory（14k/14l 初期）** | 过滤后 `len(items)` 或全量 len · **不保证跨请求精确** |
| **sqlite_shadow（14l+）** | `COUNT(*)` 精确 |
| **mixed** | 文档化近似策略（未来） |

- `page_size` **上限 100** — 防止大 payload
- 空结果：`items=[]` · `total=0`

---

## 6. 安全与隐私

| 规则 | 说明 |
|------|------|
| 不返回 | cookie · password · MMS token · session secret |
| buyer_id | UI 可脱敏；API 内部 id 需权限校验 |
| 错误 | 403 workspace mismatch · 404 无数据（不用 404 暴露 id 存在性时可返回空列表） |

---

## 7. Errors

| HTTP | code | 说明 |
|------|------|------|
| 400 | `invalid_query` | page_size > 100 · 非法日期 |
| 403 | `forbidden` | workspace / shop 无权 |
| 500 | `read_failed` | 读源完全失败（in-memory 也失败） |

**read API 错误不得触发 SendMessage。**

---

## 8. 实现阶段

| Phase | 范围 |
|-------|------|
| **14k** | 本 contract · **不实现** |
| **14m** | route skeleton · 调 `PreviewReplyLogService` |
| **14l** | SQLite read source behind flag |

---

*Phase 14k · planning only · 2026-06-03*

# Phase 14k — ReplyLog Detail API Contract (Draft)

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不实现** |
| 日期 | 2026-06-03 |
| Endpoint | `GET /api/product/reply-logs/{reply_log_id}` |
| 对齐 | `PreviewLogRecord` · 14j `reply_logs` schema |

---

## 1. Purpose

按 `reply_log_id` 返回单条 ReplyLog 详情，含 gate 决策上下文，供 Dashboard 详情抽屉 / 审计查看。

**只读 · 不发送 · 不修改配置。**

---

## 2. Request

```
GET /api/product/reply-logs/{reply_log_id}
```

| 参数 | 位置 | 必填 | 说明 |
|------|------|------|------|
| `reply_log_id` | path | ✅ | UUID |
| `workspace_id` | query | ✅ | 租户校验 |

---

## 3. Response `200`

```json
{
  "reply_log_id": "uuid",
  "workspace_id": "ws-001",
  "platform_id": "pinduoduo",
  "shop_id": "shop_pdd_preview_test",
  "account_id": "acc_pdd_preview_test",
  "buyer_id": "buyer_uid_preview_test",
  "conversation_id": null,
  "inbound_message_id": "w-preview-1",
  "buyer_message": "我要退款",
  "ai_suggested_reply": "preview suggestion text",
  "final_reply": null,
  "reply_mode": "preview",
  "send_mode": "human_takeover",
  "send_status": "not_sent_human_takeover",
  "intent": "refund_request",
  "intent_bucket": "blocked",
  "intent_confidence": 0.95,
  "risk_level": "high",
  "blocked_reason": "intent_blocked",
  "human_takeover_reason": "keyword_rule",
  "not_sent_explanation": "Blocked intent requires human takeover; preview only, not sent.",
  "product_gate_enabled": true,
  "created_at": "2026-06-03T12:00:00+00:00",
  "updated_at": "2026-06-03T12:00:00+00:00",
  "send_decision_snapshots": [],
  "audit_logs": [],
  "pending_assisted_reply": null,
  "source": "in_memory"
}
```

---

## 4. 字段说明

| 字段 | 14k/14i 可用 | 未来 |
|------|-------------|------|
| 核心 ReplyLog 字段 | ✅ in-memory projection | ✅ SQLite |
| `send_decision_snapshots[]` | **空数组** | 14m+ shadow write |
| `audit_logs[]` | **空数组** | assisted 14n+ |
| `pending_assisted_reply` | **null** | assisted 14n+ |
| `final_reply` | preview 模式 **null** | assisted approve 后填充 |

---

## 5. 缺失 section 规则

| Section | 13e/14i 无数据时 |
|---------|-------------------|
| `send_decision_snapshots` | `[]` |
| `audit_logs` | `[]` |
| `pending_assisted_reply` | `null` |

**不得** 因缺失 section 返回 500；**不得** 省略 key（保持 contract 稳定）。

---

## 6. `send_decision_snapshots[]` 元素（未来 · 14m+）

| 字段 | 说明 |
|------|------|
| `decision_phase` | `classify` · `gate` · `guard` |
| `allowed_to_generate` | bool |
| `allowed_to_send` | bool |
| `decision_source` | string |
| `created_at` | ISO8601 |

14k **只规划结构**；不实现写入。

---

## 7. 安全

- 不返回 credential / cookie / password
- `workspace_id` 必须与 record 所属 workspace 匹配，否则 **403**
- 跨 workspace 的 `reply_log_id` → **403** 或 **404**（实现时统一策略）

---

## 8. Errors

| HTTP | 说明 |
|------|------|
| 403 | workspace 无权 |
| 404 | `reply_log_id` 不存在或不属于 workspace |
| 500 | 读源完全失败 |

---

## 9. 与 list API 关系

- list 返回摘要字段
- detail 返回完整字段 + 嵌套 arrays
- 同一 `reply_log_id` 两处 `source` 应一致

---

## 10. 实现阶段

| Phase | 范围 |
|-------|------|
| **14k** | 本 contract |
| **14m** | GET handler skeleton |
| **14l** | detail 可读 SQLite row |
| **14n** | audit / pending sections |

---

*Phase 14k · planning only · 2026-06-03*

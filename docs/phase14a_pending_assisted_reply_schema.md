# Phase 14a — PendingAssistedReply Schema

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 对齐 | [phase13f_assisted_confirmation_flow.md](phase13f_assisted_confirmation_flow.md) |
| 表名 | `pending_assisted_replies`（shadow） |

---

## 1. 职责

Assisted 模式下 **待商家确认** 的回复；**pending ≠ sent**。

---

## 2. 字段

| 列 | 类型 | 必填 | 说明 |
|----|------|------|------|
| `pending_reply_id` | UUID PK | ✅ | |
| `reply_log_id` | UUID FK → reply_logs | ✅ | 1:1 或 N:1（重试场景） |
| `workspace_id` | UUID FK | ✅ | |
| `shop_id` | string | ✅ | |
| `account_id` | string | ✅ | |
| `platform_id` | enum | ✅ | `pinduoduo` |
| `buyer_id` | string | ✅ | |
| `inbound_message_id` | string | ✅ | 原始入站 ID |
| `suggested_reply` | text | ✅ | AI 建议 |
| `edited_reply` | text? | | 商家编辑稿 |
| `status` | enum | ✅ | 见 §3 |
| `intent` | string | ✅ | snapshot |
| `intent_bucket` | enum | ✅ | |
| `risk_level` | enum | ✅ | |
| `created_by` | enum | ✅ | `ai_handler` |
| `approved_by` | UUID? | | member_id |
| `rejected_by` | UUID? | | member_id |
| `expires_at` | datetime | ✅ | 默认 +24h |
| `superseded_by_message_id` | string? | | 新买家消息 ID |
| `blocked_reason` | string? | | |
| `created_at` | datetime | ✅ | |
| `updated_at` | datetime | ✅ | |

---

## 3. `status` 枚举

| 值 | 含义 | 可 approve? |
|----|------|-------------|
| `pending` | 待确认 | ✅（guard 通过） |
| `approved` | 已确认并触发 send 流程 | ❌ 终态 |
| `rejected` | 商家拒绝 | ❌ |
| `expired` | 超过 `expires_at` | ❌ |
| `superseded` | 被新消息取代 | ❌ |
| `blocked` | blocked intent · 禁止普通 approve | ❌ |

**与 13f 映射：** `pending` ≈ awaiting_approval；`approved` 后 ReplyLog → `sent`。

---

## 4. 业务规则

| # | 规则 |
|---|------|
| R1 | **pending 不等于 sent** — 无 `approved` + SendMessage 成功前 ReplyLog 不得 `sent` |
| R2 | **approve 时重跑 final guard** — 新 `send_decision_snapshot` + `evaluate_guarded_send(merchant_approved=true)` |
| R3 | **stale / expired** — `status in (expired, superseded)` → approve API 403 |
| R4 | **blocked intent** — 创建时可为 `blocked` 或 `pending`+UI 禁用；**禁止**普通 operator 一键 approve |
| R5 | **uncertain** — 须 `edited_reply IS NOT NULL` 且 ≠ `suggested_reply` 才可提交 |
| R6 | **幂等** — 同一 `pending_reply_id` 仅一次成功 `approved` |

---

## 5. 索引

| 索引 | 用途 |
|------|------|
| `(shop_id, status, created_at DESC)` | 待处理列表 |
| `(buyer_id, shop_id, status)` | 会话去重 |
| `(reply_log_id)` UNIQUE | 1:1 约束（可选） |
| `(expires_at)` WHERE status=pending | 过期清扫 job |

---

## 6. 生命周期

```text
AI handle → insert pending(status=pending)
  → merchant approve → guard → send → status=approved + ReplyLog.sent
  → merchant reject → status=rejected
  → new buyer message → status=superseded + superseded_by_message_id
  → TTL job → status=expired
  → blocked intent → status=blocked (或 pending + 前端禁用)
```

---

*PendingAssistedReply schema · Phase 14a · 2026-06-03*

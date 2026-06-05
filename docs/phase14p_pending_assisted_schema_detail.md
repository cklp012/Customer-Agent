# Phase 14p — PendingAssistedReply Schema Detail

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不建表** |
| 表名 | `pending_assisted_replies`（`product_gate.db` shadow · future） |
| 对齐 | [phase14p_auditlog_pending_assisted_plan.md](phase14p_auditlog_pending_assisted_plan.md) · [phase14a_pending_assisted_reply_schema.md](phase14a_pending_assisted_reply_schema.md) |

---

## 1. 职责

Assisted 模式下，保存 **待商家确认** 的 AI 建议。**pending 不等于 sent**；**approved 不等于 sent**（须 final guard + outbound 成功）。

---

## 2. 字段

| 列 | 类型 | 必填 | 说明 |
|----|------|------|------|
| `pending_assisted_id` | TEXT PK | ✅ | UUID |
| `reply_log_id` | TEXT | ✅ | 弱关联 `reply_logs.reply_log_id` |
| `workspace_id` | TEXT | ✅ | 租户 |
| `shop_id` | TEXT | ✅ | 店铺 |
| `account_id` | TEXT | ✅ | 账号 |
| `platform_id` | TEXT | ✅ | 如 `pinduoduo` |
| `buyer_id` | TEXT | ✅ | 买家 |
| `conversation_id` | TEXT | | 会话 ID（可选） |
| `inbound_message_id` | TEXT | | 原始入站 message id |
| `buyer_message` | TEXT | ✅ | 买家原文 |
| `ai_suggested_reply` | TEXT | ✅ | AI 建议 |
| `merchant_edited_reply` | TEXT | | 商家编辑稿（uncertain 场景必填才 approve） |
| `final_reply` | TEXT | | 实际发送文本（send 成功后填充） |
| `status` | TEXT | ✅ | enum · 见 §3 |
| `intent` | TEXT | ✅ | 分类 intent |
| `intent_bucket` | TEXT | ✅ | `allowed` · `blocked` · `uncertain` |
| `risk_level` | TEXT | ✅ | `low` · `medium` · `high` |
| `blocked_reason` | TEXT | | gate 阻断原因 |
| `human_takeover_reason` | TEXT | | 人工接管原因 |
| `created_by` | TEXT | ✅ | 如 `ai_handler` · `system` |
| `approved_by` | TEXT | | actor_user_id |
| `rejected_by` | TEXT | | actor_user_id |
| `expires_at` | TEXT | ✅ | ISO8601 · 默认 +24h |
| `created_at` | TEXT | ✅ | ISO8601 |
| `updated_at` | TEXT | ✅ | ISO8601 |

**类型约定：**

- 所有 enum 存 **TEXT**（非 SQLite native enum）
- 所有 timestamp 存 **ISO8601 TEXT**
- **不 FK** legacy `channel_shop.db` 或 `database.models` 表
- `reply_log_id` 仅弱关联 product `reply_logs`

---

## 3. `status` 枚举

| 值 | 含义 | 可 approve? | 可 send? |
|----|------|-------------|----------|
| `pending` | 待确认 | ✅（guard + 权限） | ❌ |
| `approved` | 已确认 · 待/正在 send 流程 | ❌ 幂等锁 | 仅 final guard 通过后一次 |
| `rejected` | 商家拒绝 | ❌ | ❌ |
| `expired` | 超过 `expires_at` | ❌ | ❌ |
| `canceled` | 系统/商家取消 | ❌ | ❌ |
| `sent` | outbound 已成功 | ❌ | ❌ **不可再次发送** |
| `failed` | outbound 失败 | ❌ | ❌ 须人工 review |

**状态机要点：**

```
pending → approved → (final guard) → sent
pending → rejected
pending → expired
pending → canceled
approved → failed   (outbound failure)
```

- `approved` **不等于** `sent` — 必须 final guard pass + outbound success
- `sent` 为终态 — **禁止** duplicate send / re-approve

---

## 4. 索引

| 索引名 | 列 | 用途 |
|--------|-----|------|
| `idx_pending_workspace_status_created_at` | `workspace_id`, `status`, `created_at` | workspace 待处理列表 |
| `idx_pending_shop_status_created_at` | `shop_id`, `status`, `created_at` | 店铺待处理列表 |
| `idx_pending_reply_log_id` | `reply_log_id` | detail 关联 · 1:1 查重（可选 UNIQUE future） |
| `idx_pending_buyer_created_at` | `buyer_id`, `created_at` | 买家会话历史 |

---

## 5. 业务规则

| # | 规则 |
|---|------|
| R1 | **pending ≠ sent** — 无 outbound 成功前 ReplyLog 不得标记 sent |
| R2 | **approved ≠ sent** — approve 仅表示商家意图；final guard + SendMessage 成功后 `status=sent` |
| R3 | **sent 后不可再次发送** — 同一 `pending_assisted_id` 仅一次成功 outbound |
| R4 | **blocked intent** — 禁止普通 operator 一键 approve |
| R5 | **uncertain intent** — 须 `merchant_edited_reply` 非空且与 `ai_suggested_reply` 不同，或 human takeover |
| R6 | **expires_at** — 超时自动 `expired`；expired 不可 approve |
| R7 | **幂等** — duplicate approve 不得 double-send |
| R8 | **弱关联** — `reply_log_id` 不 CASCADE 到 legacy 表 |

---

## 6. 与 ReplyLog / Snapshot 关系

```
ReplyLog (14l)          pending_assisted_replies (14q future)
     │                              │
     └──── reply_log_id ────────────┘
     
SendDecisionSnapshot (14n)
  ai_preview      → preview / suggestion 阶段
  merchant_confirm → approve + final guard pass 后（future）
```

---

## 7. 非目标

- 14p **不创建** 此表
- 不修改 `product_persistence/models.py`
- 不实现 repository / service 代码

---

*Phase 14p · planning only · 2026-06-03*

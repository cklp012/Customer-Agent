# Phase 14a — ReplyLog Schema

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 对齐 | [phase12e_send_decision_reply_log_schema.md](phase12e_send_decision_reply_log_schema.md) · [phase13e_done.md](phase13e_done.md) |
| 表名 | `reply_logs`（shadow） |

---

## 1. 职责

记录 **生成了什么**、**实际发了什么**、**为何没发** — Dashboard 活动流主表。

---

## 2. 字段

| 列 | 类型 | 必填 | 说明 |
|----|------|------|------|
| `reply_log_id` | UUID PK | ✅ | |
| `workspace_id` | UUID FK | ✅ | |
| `shop_binding_id` | UUID FK? | 推荐 | 14b+ 外键 |
| `shop_id` | string | ✅ | 冗余查询 · PDD shop_id |
| `account_id` | string | ✅ | PDD 账号维度 |
| `platform_id` | enum | ✅ | 默认 `pinduoduo` |
| `buyer_id` | string | ✅ | 可加密存储 |
| `conversation_id` | string? | | 会话 ID |
| `inbound_message_id` | string | ✅ | 入站 message_id |
| `buyer_message` | text | ✅ | 规范化后文本 |
| `ai_suggested_reply` | text? | | AI 建议 |
| `final_reply` | text? | | 确认后/编辑后正文 |
| `reply_mode` | enum | ✅ | preview / assisted / auto / paused |
| `send_mode` | enum | ✅ | 来自 SendDecision |
| `send_status` | enum | ✅ | 见 §3 |
| `intent` | string | ✅ | |
| `intent_bucket` | enum | ✅ | allowed / blocked / uncertain |
| `intent_confidence` | float | ✅ | |
| `risk_level` | enum | ✅ | low / medium / high |
| `blocked_reason` | string? | | |
| `human_takeover_reason` | string? | | |
| `not_sent_explanation` | text? | | 13e 读模型字段 |
| `product_gate_enabled` | bool | ✅ | snapshot |
| `sent_at` | datetime? | | 仅 `sent` 时填 |
| `created_at` | datetime | ✅ | |
| `updated_at` | datetime | ✅ | |

**可选 FK：** `latest_send_decision_id` → `send_decision_snapshots`

---

## 3. `send_status` 枚举

| 值 | 含义 | 适用模式 |
|----|------|----------|
| `not_sent_preview` | Preview · **零 send** | preview |
| `not_sent_human_takeover` | blocked / 转人工 | preview / assisted |
| `not_sent_assisted_required` | 待商家确认 | assisted |
| `not_sent_paused` | 暂停 | 全部 |
| `sent` | 成功发出 | assisted（将来 auto） |
| `failed` | 尝试发送失败 | assisted |
| `skipped_gate_disabled` | gate off · legacy 旁路记录 | shadow only |

**14a 新增（相对 12e）：** `skipped_gate_disabled` — 可选记录 legacy 店 shadow 对比；**不** 表示 shadow 路径已 send。

---

## 4. 写入规则

| 模式 | `ai_suggested_reply` | `final_reply` | `send_status` |
|------|----------------------|---------------|---------------|
| **preview** | ✅ 写入 | ❌ NULL | `not_sent_preview` |
| **assisted（AI 阶段）** | ✅ 写入 | ❌ NULL | `not_sent_assisted_required` |
| **assisted（approve 后）** | 保留 | ✅ 写入编辑后文本 | `sent` / `failed` |
| **auto（将来）** | ✅ | 可能=建议 | `sent` 仅 gate 允许 |
| **blocked** | 可选建议 | ❌ | `not_sent_human_takeover` — **不允许 `sent`** |

**约束（应用层 + 可选 CHECK）：**

- `send_status=not_sent_preview` → `sent_at IS NULL` · `final_reply IS NULL`
- `intent_bucket=blocked` → `send_status != sent`（无 elevated override 时）

---

## 5. 索引

| 索引 | 用途 |
|------|------|
| `(shop_id, created_at DESC)` | 店维度时间线 |
| `(workspace_id, created_at DESC)` | Dashboard 聚合 |
| `(buyer_id, shop_id, created_at DESC)` | 会话历史 |
| `(send_status, created_at)` | 待处理队列 |
| `(inbound_message_id)` | 幂等 / 去重 |

---

## 6. 与 13e 投影映射

| PreviewReplyLogListItem | reply_logs 列 |
|-------------------------|---------------|
| `reply_log_id` | `reply_log_id` |
| `buyer_message` | `buyer_message` |
| `ai_suggested_reply` | `ai_suggested_reply` |
| `send_status` | `send_status` |
| `not_sent_explanation` | `not_sent_explanation` |
| `final_reply` | `final_reply`（preview 为 NULL） |

---

*ReplyLog schema · Phase 14a · 2026-06-03*

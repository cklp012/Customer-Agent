# Phase 12d — Reply Activity Read Model（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 关联 | [phase12c_send_decision_model.md](phase12c_send_decision_model.md) · [phase12d_dashboard_ia.md](phase12d_dashboard_ia.md) |

---

## 1. ReplyActivitySummary

**粒度：** `(workspace_id, shop_binding_id?, date)` — `shop_binding_id` null 表示工作区聚合。

| 字段 | 类型 | 说明 |
|------|------|------|
| `workspace_id` | UUID | ✅ |
| `shop_binding_id` | UUID? | 可选筛选 |
| `date` | date | 自然日（工作区时区） |
| `inbound_messages_count` | int | 入站 |
| `ai_suggestions_count` | int | 生成建议次数 |
| `preview_only_count` | int | `outcome=preview_only` |
| `assisted_required_count` | int | `send_mode=assisted_required` 且未发送 |
| `auto_sent_count` | int | `outcome=sent` + `reply_mode=auto` |
| `blocked_count` | int | `allowed_to_send=false` 且已生成或尝试 |
| `human_takeover_count` | int | transfer / human_takeover |
| `failed_send_count` | int | send API 失败 |
| `average_response_latency_ms` | int? | 入站到首条建议/发送 |
| `intent_breakdown` | map<string,int>? | 可选 · 按 intent 计数 |
| `blocked_reason_breakdown` | map<string,int>? | 可选 |
| `as_of` | datetime | |

**聚合来源：** `SendDecision` + `ReplyLog`（12e 表）。

---

## 2. SendDecisionSummary

列表/详情用；字段对齐 [phase12c_send_decision_model.md](phase12c_send_decision_model.md)。

| 字段 | 类型 |
|------|------|
| `decision_id` | UUID |
| `workspace_id` | UUID |
| `shop_binding_id` | UUID |
| `message_id` | string |
| `buyer_id` | string |
| `normalized_text` | string? · 列表可截断 |
| `intent` | string |
| `intent_bucket` | enum |
| `intent_confidence` | float |
| `risk_level` | enum |
| `reply_mode` | enum |
| `workspace_pause` | bool |
| `shop_pause` | bool |
| `allowed_to_generate` | bool |
| `allowed_to_send` | bool |
| `send_mode` | enum |
| `blocked_reason` | string? |
| `human_takeover_reason` | string? |
| `decision_source` | enum |
| `created_at` | datetime |

**Dashboard「为何没发」解释矩阵：**

| blocked_reason | 商家文案 |
|----------------|----------|
| `preview_mode` | 预览模式，未发送 |
| `workspace_paused` | 工作区已暂停 |
| `shop_paused` | 本店已暂停 |
| `intent_blocked` | 非售前咨询，已转人工 |
| `uncertain_intent` | 不确定，需人工确认 |
| `low_confidence` | 置信度低，未自动发送 |
| `awaiting_approval` | 等待您确认 |
| `commitment_guard` | 含禁止承诺用语，已拦截 |

---

## 3. HumanTakeoverQueueItem

| 字段 | 类型 | 说明 |
|------|------|------|
| `queue_item_id` | UUID | PK |
| `workspace_id` | UUID | |
| `shop_binding_id` | UUID | |
| `shop_name` | string | 冗余 |
| `buyer_id` | string | 脱敏 |
| `conversation_id` | string? | |
| `latest_message` | string | 买家最近一条 |
| `intent` | string | |
| `intent_bucket` | enum | 通常 blocked |
| `risk_level` | enum | |
| `reason` | string | = human_takeover_reason 或 blocked_reason |
| `blocked_reason` | string? | |
| `human_takeover_reason` | string? | |
| `priority` | enum | `high` \| `medium` \| `low` |
| `status` | enum | `open` \| `claimed` \| `resolved` |
| `created_at` | datetime | |
| `updated_at` | datetime? | |

**priority 规则：**

| 条件 | priority |
|------|----------|
| `complaint`, `bad_review_threat`, `compensation_request` | high |
| `refund_request`, `after_sales_dispute` | high |
| `order_change`, `address_change` | medium |
| `uncertain` + assisted 超时 | medium |
| 其他 blocked | low |

---

## 4. ReplyLogListItem

| 字段 | 类型 | 说明 |
|------|------|------|
| `reply_log_id` | UUID | |
| `decision_id` | UUID? | FK |
| `workspace_id` | UUID | |
| `shop_binding_id` | UUID | |
| `buyer_id` | string | |
| `buyer_message` | string | |
| `ai_suggested_reply` | string? | |
| `final_reply` | string? | 实际发送或商家编辑后 |
| `send_status` | enum | `not_sent` \| `sent` \| `failed` \| `preview_only` |
| `send_mode` | enum | 来自 SendDecision |
| `intent` | string | |
| `intent_bucket` | enum? | |
| `blocked_reason` | string? | |
| `human_takeover_reason` | string? | |
| `would_send_if_auto` | bool? | dry-run 教育字段 |
| `created_at` | datetime | |

---

## 5. 关系图

```text
Inbound Message
  → SendDecision (1)
  → ReplyLog (0..1)
  → HumanTakeoverQueueItem (0..1, if takeover)

ReplyActivitySummary = aggregate(SendDecision, ReplyLog) by day
```

---

## 6. 查询模式（供 API）

| 查询 | 输入 | 输出 |
|------|------|------|
| 今日概览 | workspace_id, date | ReplyActivitySummary |
| 店今日 | shop_binding_id, date | ReplyActivitySummary |
| 决策详情 | decision_id | SendDecisionSummary + ReplyLogListItem |
| 待人工队列 | workspace_id, status=open | HumanTakeoverQueueItem[] |
| 回复日志页 | shop_binding_id, cursor | ReplyLogListItem[] |

---

## 7. 「没发」原因合成（商家可读）

对单条 `SendDecisionSummary`，UI 合成 **`not_sent_explanation`**（派生字段，非 DB）：

```text
if shop_pause or workspace_pause → "已暂停"
elif send_mode == preview_only → "预览模式"
elif intent_bucket == blocked → "售后/纠纷类，已转人工"
elif blocked_reason == low_confidence → "置信度不足"
elif send_mode == assisted_required → "等待您确认"
elif allowed_to_send == false → blocked_reason 映射文案
else → null (已发送或通过)
```

---

*Phase 12d · Reply Activity Read Model · docs only*

# Phase 12e — SendDecision / ReplyLog / Queue Schema（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 对齐 | [phase12c_send_decision_model.md](phase12c_send_decision_model.md) · [phase12d_reply_activity_read_model.md](phase12d_reply_activity_read_model.md) |

---

## 1. 职责分离

| 实体 | 回答的问题 |
|------|------------|
| **SendDecision** | **为什么** 能/不能生成？能/不能发送？ |
| **ReplyLog** | **生成了什么**？**实际发了什么**？ |
| **HumanTakeoverQueue** | 谁要人工处理？优先级？ |
| **AuditLog** | 谁改了 pause / reply-mode？ |

```text
Inbound → SendDecision (1) → ReplyLog (0..1)
              └────────────→ HumanTakeoverQueue (0..1, if blocked/takeover)
```

---

## 2. `send_decisions`

| 列 | 类型 | 必填 |
|----|------|------|
| `decision_id` | UUID PK | ✅ |
| `workspace_id` | UUID FK | ✅ |
| `shop_binding_id` | UUID FK | ✅ |
| `platform_id` | enum | ✅ |
| `shop_id` | string | ✅ 冗余查询 |
| `buyer_id` | string | ✅ 存储可加密 |
| `message_id` | string | ✅ |
| `conversation_id` | string? | |
| `normalized_text` | text | ✅ |
| `intent` | string | ✅ |
| `intent_bucket` | enum | allowed / blocked / uncertain |
| `intent_confidence` | float | ✅ |
| `risk_level` | enum | low / medium / high |
| `reply_mode` | enum | 决策时刻 snapshot |
| `workspace_pause` | bool | snapshot |
| `shop_pause` | bool | snapshot |
| `allowed_to_generate` | bool | ✅ |
| `allowed_to_send` | bool | ✅ |
| `send_mode` | enum | none / preview_only / assisted_required / auto_send / human_takeover |
| `blocked_reason` | string? | |
| `human_takeover_reason` | string? | |
| `decision_source` | enum | keyword_rule / ai_classifier / combined / manual_override |
| `product_gate_enabled` | bool | snapshot |
| `created_at` | datetime | ✅ |

| 索引 | 说明 |
|------|------|
| `(shop_binding_id, created_at DESC)` | 店维度时间线 |
| `(workspace_id, created_at DESC)` | Dashboard 聚合 |
| `(buyer_id, shop_binding_id, created_at DESC)` | 会话历史 |
| `(intent_bucket, created_at)` | 风险报表 |

| 约束 | |
|------|--|
| `intent_bucket=blocked` → `allowed_to_send=false`（应用层 + CHECK 可选） |
| `reply_mode=preview` snapshot → `allowed_to_send=false` |

---

## 3. `reply_logs`

| 列 | 类型 | 必填 |
|----|------|------|
| `reply_log_id` | UUID PK | ✅ |
| `decision_id` | UUID FK → send_decisions | ✅ |
| `workspace_id` | UUID FK | ✅ |
| `shop_binding_id` | UUID FK | ✅ |
| `buyer_id` | string | ✅ |
| `buyer_message` | text | ✅ |
| `ai_suggested_reply` | text? | |
| `final_reply` | text? | 发送或商家编辑后 |
| `send_status` | enum | ✅ 见 §4 |
| `send_mode` | enum | 来自 decision |
| `intent` | string? | 冗余 |
| `intent_bucket` | enum? | |
| `blocked_reason` | string? | |
| `human_takeover_reason` | string? | |
| `would_send_if_auto` | bool? | dry-run 教育 |
| `send_result_code` | string? | 平台 API |
| `send_error_message` | string? | |
| `sent_at` | datetime? | |
| `created_at` | datetime | ✅ |

### 4. `send_status` 枚举

| 值 | 含义 |
|----|------|
| `not_sent_preview` | Preview 模式 · **零 send** |
| `not_sent_blocked` | gate 拦截 |
| `not_sent_paused` | 暂停 |
| `not_sent_awaiting_approval` | assisted 待确认 |
| `sent` | 成功发出 |
| `failed` | 尝试发送失败 |
| `not_sent_takeover` | 已转人工，未发 AI 正文 |

**Preview 必须：** `send_status=not_sent_preview` 且 `sent_at IS NULL` 且 **无** 关联 outbound 成功记录。

---

## 5. `human_takeover_queue`

| 列 | 类型 |
|----|------|
| `queue_item_id` | UUID PK |
| `workspace_id` | UUID FK |
| `shop_binding_id` | UUID FK |
| `decision_id` | UUID FK? |
| `buyer_id` | string |
| `conversation_id` | string? |
| `latest_message` | text |
| `intent` | string |
| `intent_bucket` | enum |
| `risk_level` | enum |
| `reason` | string |
| `blocked_reason` | string? |
| `human_takeover_reason` | string? |
| `priority` | enum high / medium / low |
| `status` | enum open / claimed / resolved |
| `assigned_to` | UUID FK merchant? |
| `created_at` | datetime |
| `resolved_at` | datetime? |

| 索引 | `(workspace_id, status, priority, created_at)` |
| 入队 | `send_mode=human_takeover` OR `intent_bucket=blocked` |

---

## 6. `usage_meters`（周期聚合）

| 列 | 类型 |
|----|------|
| `usage_meter_id` | UUID PK |
| `workspace_id` | UUID FK |
| `shop_binding_id` | UUID FK nullable |
| `period_start` | date |
| `period_end` | date |
| `inbound_messages_count` | int default 0 |
| `ai_suggestions_count` | int |
| `preview_only_count` | int |
| `assisted_sent_count` | int |
| `auto_sent_count` | int |
| `blocked_count` | int |
| `human_takeover_count` | int |
| `failed_send_count` | int |
| `updated_at` | datetime |

| 更新 | 自 `send_decisions` / `reply_logs` 异步 roll-up（M8） |

---

## 7. 写入规则（product gate）

| 场景 | SendDecision | ReplyLog | Queue |
|------|--------------|----------|-------|
| Preview + allowed | allowed_to_send=false | not_sent_preview + suggested | — |
| blocked refund | allowed_to_send=false | optional 无 suggested 外发 | open |
| auto + allowed + sent | allowed_to_send=true | sent | — |
| paused | allowed_to_send=false | not_sent_paused | — |
| gate **off** (M4 shadow) | 仍写 decision 标注 `product_gate_enabled=false` | 可选不写 | — |

**M4：** `product_gate_enabled=false` 时 SendDecision 可 **仅影子** 记录（`decision_source=combined`），发送仍 legacy，ReplyLog `send_status=sent` 与 today 统计 **分离** 标注 `shadow=false`。

---

## 8. AuditLog 动作（与 gate 相关）

| action | 触发 |
|--------|------|
| `workspace.pause` / `workspace.resume` | POST pause API |
| `shop.pause` / `shop.resume` | |
| `shop.reply_mode_changed` | preview ↔ assisted ↔ auto |
| `shop.auto_enabled` | 二次确认开启 auto |
| `shop.product_gate_enabled` | 内部/支持操作 |

---

## 9. 保留策略

| 表 | Starter | Growth | Pro |
|----|---------|--------|-----|
| send_decisions | 7d | 30d | 365d |
| reply_logs | 7d | 30d | 365d |
| audit_logs | 30d | 90d | 365d |

---

## 10. Dashboard 读路径

| Dashboard 模块 | 主表 |
|----------------|------|
| C 今日活动 | `usage_meters` 或 aggregate `reply_logs` |
| D 待人工 | `human_takeover_queue` |
| E 风险摘要 | aggregate `send_decisions` by intent |
| 单条「为何没发」 | `send_decisions` + `reply_logs` |

---

*Phase 12e · SendDecision / ReplyLog Schema · docs only*

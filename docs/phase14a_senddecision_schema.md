# Phase 14a — SendDecision Snapshot Schema

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 对齐 | [phase12e_send_decision_reply_log_schema.md](phase12e_send_decision_reply_log_schema.md) · `Message/gates/send_decision.py` |
| 表名 | `send_decision_snapshots`（shadow） |

---

## 1. 职责

不可变 **决策快照** — 解释「为何允许/拒绝生成与发送」；支持 Dashboard 与风控复盘。

**与 ReplyLog：** 一次 inbound 可有多条 snapshot（AI 阶段 + approve 重检阶段）。

---

## 2. 字段

| 列 | 类型 | 必填 | 说明 |
|----|------|------|------|
| `send_decision_id` | UUID PK | ✅ | |
| `reply_log_id` | UUID FK? | | 关联 ReplyLog |
| `workspace_id` | UUID FK | ✅ | |
| `shop_id` | string | ✅ | |
| `account_id` | string | ✅ | |
| `platform_id` | enum | ✅ | |
| `inbound_message_id` | string | ✅ | |
| `intent` | string | ✅ | |
| `intent_bucket` | enum | ✅ | |
| `intent_confidence` | float | ✅ | |
| `risk_level` | enum | ✅ | |
| `reply_mode` | enum | ✅ | 决策时刻 |
| `workspace_pause` | bool | ✅ | snapshot |
| `shop_pause` | bool | ✅ | snapshot |
| `product_gate_enabled` | bool | ✅ | snapshot |
| `allowed_to_generate` | bool | ✅ | |
| `allowed_to_send` | bool | ✅ | |
| `send_mode` | enum | ✅ | |
| `blocked_reason` | string? | | |
| `human_takeover_reason` | string? | | |
| `decision_source` | enum | ✅ | keyword_rule / ai_classifier / combined / gate_disabled / confirm_recheck |
| `decision_phase` | enum | ✅ | `ai_generate` / `merchant_confirm` / `shadow_only` |
| `merchant_approved` | bool | ✅ | default false |
| `created_at` | datetime | ✅ | |

---

## 3. 写入时机

| 阶段 | `decision_phase` | 说明 |
|------|------------------|------|
| 13b shadow | `shadow_only` | gate off；可选写 shadow 表（M4+） |
| 13d preview AI | `ai_generate` | gate on + preview |
| 14c assisted AI | `ai_generate` | `merchant_approved=false` |
| assisted approve | `merchant_confirm` | **新一行** · re-classify + final guard |
| legacy 旁路 | — | 可不写（或 `skipped_gate_disabled` ReplyLog only） |

---

## 4. 与纯函数映射

`build_send_decision()` + `evaluate_guarded_send()` 输出 → 行字段 1:1 映射。

| SendDecision 字段 | DB 列 |
|-------------------|-------|
| `intent` | `intent` |
| `send_mode` | `send_mode` |
| `allowed_to_send` | `allowed_to_send` |
| `product_gate_enabled` | `product_gate_enabled` |

---

## 5. 索引

| 索引 | 用途 |
|------|------|
| `(reply_log_id, created_at)` | 决策链 |
| `(shop_id, created_at DESC)` | 店维度 |
| `(inbound_message_id)` | 入站关联 |
| `(intent_bucket, created_at)` | 风控报表 |

---

## 6. 约束

- `reply_mode=preview` snapshot → `allowed_to_send=false`
- `intent_bucket=blocked` → `allowed_to_send=false`（confirm 阶段无 elevated 时）
- append-only：不 UPDATE 历史 snapshot

---

*SendDecision snapshot schema · Phase 14a · 2026-06-03*

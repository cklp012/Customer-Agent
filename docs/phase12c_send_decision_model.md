# Phase 12c — SendDecision Model（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only · **产品级 gate**，非 env flag |
| 关联 | [phase12c_intent_gate_design.md](phase12c_intent_gate_design.md) · [phase12b1_send_gate_requirements.md](phase12b1_send_gate_requirements.md) |

---

## 1. 定位

**SendDecision** 是每条入站消息在「是否生成 / 是否发送」上的 **唯一裁决快照**。

| 是 | 不是 |
|----|------|
| 店铺级 / 工作区级 `reply_mode` + intent + pause 的求值结果 | `USE_UNIFIED_OUTBOUND_RESOLVER` |
| 写入 ReplyLog / SendDecision 表（12e） | 全局 Python env 默认行为 |
| final send guard 的输入 SSOT | 仅靠 prompt 约束 |

---

## 2. 字段定义

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `decision_id` | UUID | ✅ | 主键 |
| `workspace_id` | UUID | ✅ | 租户 |
| `shop_binding_id` | UUID | ✅ | 店铺绑定 |
| `platform_id` | enum | ✅ | 如 `pinduoduo` |
| `shop_id` | string | ✅ | 平台店 ID |
| `buyer_id` | string | ✅ | 买家 UID（存储可加密） |
| `message_id` | string | ✅ | 入站消息 ID / wrapper id |
| `normalized_text` | text | ✅ | normalize 后文本 |
| `intent` | string | ✅ | 如 `product_question` |
| `intent_bucket` | enum | ✅ | `allowed` \| `blocked` \| `uncertain` |
| `intent_confidence` | float | ✅ | 0.0–1.0 |
| `risk_level` | enum | ✅ | `low` \| `medium` \| `high` |
| `reply_mode` | enum | ✅ | `preview` \| `assisted` \| `auto` |
| `workspace_pause` | bool | ✅ | 工作区暂停 |
| `shop_pause` | bool | ✅ | 单店暂停 |
| `allowed_to_generate` | bool | ✅ | 是否调用 AI 生成 |
| `allowed_to_send` | bool | ✅ | 是否允许平台 send API |
| `send_mode` | enum | ✅ | 见 §3 |
| `blocked_reason` | string? | | 如 `intent_blocked`, `preview_mode`, `workspace_paused` |
| `human_takeover_reason` | string? | | `keyword_rule`, `blocked_intent`, `manual`, … |
| `decision_source` | enum | ✅ | `keyword_rule` \| `ai_classifier` \| `combined` \| `manual_override` |
| `created_at` | datetime | ✅ | UTC |

**可选扩展（12e）：** `conversation_id`, `commitment_rule_ids[]`, `merchant_approve_id`, `would_send_if_auto`, `suggested_reply_id`.

---

## 3. `send_mode` 枚举

| 值 | 含义 |
|----|------|
| `none` | 不生成、不发送（严格 paused 或配置跳过） |
| `preview_only` | 可生成；**永不** send |
| `assisted_required` | 可生成；send 须审批 |
| `auto_send` | 允许在 final guard 后 send |
| `human_takeover` | 转人工路径；**不** auto 发 AI 回复 |

---

## 4. 决策优先级（SSOT）

**从高到低：**

```text
paused
  > human_takeover
  > blocked_intent
  > uncertain_intent
  > reply_mode
  > send
```

### 4.1 求值表

| 顺序 | 条件 | `allowed_to_send` | `send_mode` | `blocked_reason` |
|------|------|-------------------|-------------|------------------|
| 1 | `workspace_pause=true` | false | `none` 或 `preview_only`* | `workspace_paused` |
| 2 | `shop_pause=true` | false | 同上 | `shop_paused` |
| 3 | 会话 `human_takeover` 活跃 | false | `human_takeover` | — |
| 4 | `intent_bucket=blocked` | false | `human_takeover` | `intent_blocked` |
| 5 | `intent_bucket=uncertain` AND `reply_mode=auto` | false | `preview_only` 或 `assisted_required` | `uncertain_intent` |
| 6 | `intent_confidence < threshold` AND `auto` | false | `assisted_required` | `low_confidence` |
| 7 | `reply_mode=preview` | false | `preview_only` | `preview_mode` |
| 8 | `reply_mode=assisted` | false† | `assisted_required` | `awaiting_approval` |
| 9 | `allowed` + `auto` + high conf + `risk_level=low` | **true** | `auto_send` | — |

\* paused 时 `allowed_to_generate` 可配置为 true（12a：推荐 Preview 仍生成建议）。  
† assisted 在 `merchant_approve` 后为 true。

### 4.2 不变量

| # | 规则 |
|---|------|
| I1 | `workspace_pause=true` → `allowed_to_send=false` |
| I2 | `shop_pause=true` → `allowed_to_send=false` |
| I3 | `reply_mode=preview` → `allowed_to_send=false` |
| I4 | `intent_bucket=blocked` → `allowed_to_send=false` |
| I5 | `intent_bucket=uncertain` + `auto` → `allowed_to_send=false` |
| I6 | `allowed` + `auto` + high confidence + `risk_level=low` → `allowed_to_send=true`（仍须 final commitment guard） |
| I7 | `reply_mode=auto` **不能**覆盖 I4–I5 |

---

## 5. `allowed_to_generate` 规则

| 场景 | 默认 |
|------|------|
| `preview` + allowed/uncertain | true |
| `preview` + blocked | false 或 true（仅内部备注，产品配置） |
| `paused` + 推荐策略 | true（继续生成建议供观察） |
| `paused` + 严格策略 | false |
| `human_takeover` | false（推荐） |

---

## 6. `decision_source`

| 值 | 何时 |
|----|------|
| `keyword_rule` | 仅关键词决定 bucket |
| `ai_classifier` | 仅模型分类 |
| `combined` | 关键词与分类器合并（**默认**） |
| `manual_override` | 商家强制人工/强制发送（审计） |

---

## 7. 与 ReplyLog 关系

```text
SendDecision (1) ──► ReplyLog (0..1)
  - ReplyLog 引用 decision_id
  - 字段冗余：intent, outcome, blocked_reason 便于列表查询
```

**`would_send_if_auto`（ReplyLog / dry-run）：** 若当前为 preview，记录「若 reply_mode=auto 且 gate 通过是否会 send」— 用于商家教育与测试断言。

---

## 8. 配置来源（非 env）

| 配置 | 来源 |
|------|------|
| `reply_mode` | `ShopBinding` |
| `workspace_pause` | `Workspace` |
| `shop_pause` | `ShopBinding` |
| `consultation_only` | `ShopBinding`（默认 true） |
| 阈值 / 词表 | `SafetySettings` |
| **product gate enabled** | `ShopBinding.product_gate_enabled` 或 workspace feature flag（**12f**，默认 false） |

---

## 9. API 形状（概念，供 12d/12e）

```text
POST /internal/v1/send-decisions/evaluate
  in:  normalized_text, shop_binding_id, message_id, conversation_id?
  out: SendDecision (full)

GET /v1/shops/{id}/reply-logs?decision_id=...
```

---

*Phase 12c · SendDecision Model · docs only*

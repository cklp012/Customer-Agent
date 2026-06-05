# Phase 14t — Final Guard Input / Output Contract

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不写代码** |
| 函数名（规划） | `evaluate_final_guard(context) -> FinalGuardResult` |

---

## 1. 设计原则

| # | 原则 |
|---|------|
| 1 | **Pure function** · 无 I/O · 无 SendMessage |
| 2 | Input 由 **AssistedReplyService / send orchestrator** 组装 |
| 3 | Output 供 caller 决定是否 outbound · 写 audit/snapshot |
| 4 | `allowed_to_send=false` → caller **不得** SendMessage |
| 5 | Output **本身**不发送、不写 DB |

---

## 2. Input（FinalGuardContext）

### 2.1 租户 / 店铺 / 平台

| 字段 | 类型 | 说明 |
|------|------|------|
| `workspace_id` | string | |
| `shop_id` | string | |
| `account_id` | string | |
| `platform_id` | string | e.g. `pinduoduo` |

### 2.2 Actor / 权限

| 字段 | 类型 | 说明 |
|------|------|------|
| `actor_user_id` | string | approve 时必填 · preview 可 `system` |
| `actor_role` | string | owner / admin / operator / viewer / system |

### 2.3 消息 / 回复文本

| 字段 | 类型 | 说明 |
|------|------|------|
| `reply_log_id` | string? | |
| `pending_assisted_id` | string? | assisted send 必填 |
| `buyer_id` | string | |
| `inbound_message_id` | string? | |
| `buyer_message` | string | |
| `ai_suggested_reply` | string? | |
| `merchant_edited_reply` | string? | |
| `final_reply` | string | **guard 扫描主文本** |

### 2.4 Intent / 风险

| 字段 | 类型 | 说明 |
|------|------|------|
| `intent_category` | string | policy key |
| `intent` | string | classifier raw |
| `intent_bucket` | string | allowed / blocked / uncertain |
| `intent_confidence` | float | |
| `risk_level` | string | low / medium / high |
| `blocked_reason` | string? | |
| `human_takeover_reason` | string? | |

### 2.5 Merchant Policy

| 字段 | 类型 | 说明 |
|------|------|------|
| `policy_id` | string? | |
| `policy_version` | int? | |
| `ai_intervention_mode` | string | 商家配置 |
| `effective_mode` | string | min(merchant, ceiling, reply_mode) |
| `platform_mode_ceiling` | string | |
| `template_id` | string? | |
| `template_version` | int? | |
| `template_validation_status` | string? | passed / rejected / pending_review |

### 2.6 Gate / 模式 / 状态

| 字段 | 类型 | 说明 |
|------|------|------|
| `reply_mode` | string | preview / assisted / auto |
| `product_gate_enabled` | bool | |
| `workspace_pause` | bool | |
| `shop_pause` | bool | |
| `pending_status` | string? | pending / approved / … |
| `expires_at` | string? | ISO8601 |
| `inbound_created_at` | string? | stale 检测 |
| `outbound_channel_status` | string | available / unavailable |
| `idempotency_key` | string? | 通常 `pending_assisted_id` |
| `now` | string | ISO8601 · 测试注入 |

---

## 3. Output（FinalGuardResult）

| 字段 | 类型 | 说明 |
|------|------|------|
| `allowed_to_send` | bool | **caller 发送开关** |
| `decision` | string | `allow` \| `block` |
| `block_code` | string? | 机器可读 · Dashboard 用 |
| `block_reason` | string? | 人类可读 |
| `audit_action` | string | `final_guard_passed` \| `final_guard_blocked` |
| `send_mode` | string | `assisted_send` \| `auto_send` \| `none` |
| `decision_source` | string | 固定 `final_guard` |
| `checked_rules` | string[] | 通过的 rule id 列表 |
| `policy_snapshot` | object | 发送时点 policy 摘要 |
| `template_snapshot` | object? | template 摘要 |
| `created_at` | string | ISO8601 |

### 3.1 policy_snapshot（Output 内）

```json
{
  "policy_id": "...",
  "policy_version": 2,
  "intent_category": "refund_request",
  "ai_intervention_mode": "guide_only",
  "effective_mode": "guide_only",
  "platform_mode_ceiling": "assisted_only"
}
```

---

## 4. Caller 契约

```text
result = evaluate_final_guard(context)

if not result.allowed_to_send:
    append AuditLog final_guard_blocked
    write SendDecisionSnapshot (allowed_to_send=false, block_code=...)
    return  # NO SendMessage

append AuditLog final_guard_passed
write SendDecisionSnapshot (decision_phase=merchant_confirm | auto_final_guard)
# then outbound (separate step · may still fail)
```

| 规则 | 说明 |
|------|------|
| guard pass | 允许 **尝试** outbound · 不等于成功 |
| guard block | **禁止** outbound · 无 exception bypass |
| preview path | 可记录 result · **仍 zero-send** |

---

## 5. SendDecisionSnapshot 映射

| decision_phase | 场景 |
|----------------|------|
| `merchant_confirm` | assisted approve + guard |
| `auto_final_guard` | auto_allowed + guard |
| `ai_preview` | 已有（14n）· 可含 guard preview 结果 optional |

Snapshot 字段：`allowed_to_send` · `block_code` · `block_reason` · `policy_snapshot` · `template_snapshot`

---

*Phase 14t · planning only · 2026-06-03*

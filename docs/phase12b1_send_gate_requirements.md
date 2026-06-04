# Phase 12b.1 — Send Gate Requirements（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only · **未来技术实现验收清单** |
| 关联 | [phase12b1_intent_boundary.md](phase12b1_intent_boundary.md) · [phase12a_safety_and_preview_spec.md](phase12a_safety_and_preview_spec.md) |
| 实现 Phase | **12c**（技术设计）→ 代码 Phase 后续 |

---

## 1. 定位

Send Gate 是 **发送前唯一裁决点**：无论 handler 是否已生成 `reply_text`，**调用平台 send API 之前** 必须通过 gate。

**不是：**

- 环境变量 `USE_UNIFIED_OUTBOUND_RESOLVER`（工程路由 flag，默认 off）
- 商家不可见的 dev flag

**是：**

- **Workspace 级** + **ShopBinding 级** 产品控制
- 与 `reply_mode`、`intent`、`pause`、`human_takeover` 联合求值

---

## 2. Send decision 记录字段（SSOT）

每条入站消息在处理链末端应能持久化（或写入 ReplyLog）如下决策快照：

| 字段 | 类型 | 说明 |
|------|------|------|
| `intent` | string | 如 `product_question`、`refund_request` |
| `intent_confidence` | float | 0–1 |
| `risk_level` | enum | `low` \| `medium` \| `high` |
| `reply_mode` | enum | `preview` \| `assisted` \| `auto` |
| `workspace_pause` | bool | 工作区全局暂停 |
| `shop_pause` | bool | 单店暂停 |
| `blocked_reason` | string? | 如 `intent_blocked`、`commitment_guard`、`paused` |
| `human_takeover_reason` | string? | `keyword` \| `manual` \| `blocked_intent` \| … |
| `allowed_to_send` | bool | **最终是否允许调用 send API** |
| `decision_source` | string | 如 `send_gate_v1` |
| `created_at` | datetime | 决策时间 |

**可选扩展：** `intent_bucket`, `merchant_approve_id`, `commitment_rule_ids[]`.

---

## 3. 发送规则（求值顺序）

与 [phase12b1_intent_boundary.md §4](phase12b1_intent_boundary.md) 优先级一致：

### 3.1 永不发送（`allowed_to_send=false`）

| 条件 | `blocked_reason` 示例 |
|------|----------------------|
| `workspace_pause=true` | `workspace_paused` |
| `shop_pause=true` | `shop_paused` |
| `reply_mode=preview` | `preview_mode` |
| `intent_bucket=blocked` | `intent_blocked` |
| `intent_bucket=uncertain` AND `reply_mode=auto` | `uncertain_intent` |
| `intent_confidence < threshold` AND `reply_mode=auto` | `low_confidence` |
| `human_takeover` 活跃 | `human_takeover` |
| 禁诺 / commitment guard 命中 | `commitment_guard` |

### 3.2 转人工（可不 send，须记 transfer）

| 场景 | 动作 |
|------|------|
| `refund_request` / `complaint` / `compensation_request` / … | `transfer_to_human`；`allowed_to_send=false` |
| `order_change` / `address_change` | 同上 |
| block intent + 任意 `reply_mode` | **不 auto send**；Growth 可执行真实转接 |

### 3.3 允许发送

| 条件 | 说明 |
|------|------|
| `intent_bucket=allowed` | 咨询白名单 |
| `reply_mode=auto` | |
| `intent_confidence ≥ threshold` | 可配置，默认如 0.85 |
| `risk_level=low` | |
| commitment guard **通过** | |
| 非 pause、非 takeover | |
| → `allowed_to_send=true` | 调用平台 outbound / legacy send |

### 3.4 Assisted

| 条件 | 说明 |
|------|------|
| `reply_mode=assisted` | 生成建议后 **等待** `merchant_approve` |
| 无 approve | `allowed_to_send=false` |
| approve + 上述 allow 条件 | 可 send |

### 3.5 Preview

| 规则 |
|------|
| **永不** 调用平台 send API |
| 只写 `suggested_reply` + `outcome=preview_only` |

---

## 4. 概念伪代码（文档，非仓库代码）

```text
function evaluate_send_gate(ctx) -> SendDecision:
    if ctx.workspace_pause or ctx.shop_pause:
        return deny("paused")

    if ctx.human_takeover_active:
        return deny("human_takeover")

    if ctx.intent_bucket == "blocked":
        return deny("intent_blocked", transfer=true)

    if ctx.reply_mode == "preview":
        return deny("preview_mode")  # 仍可有 suggested_reply

    if ctx.intent_bucket == "uncertain" or ctx.intent_confidence < ctx.threshold:
        if ctx.reply_mode == "auto":
            return deny("uncertain_or_low_confidence")

    if not commitment_guard_pass(ctx.reply_text):
        return deny("commitment_guard")

    if ctx.reply_mode == "assisted" and not ctx.merchant_approved:
        return deny("awaiting_approval")

    if ctx.reply_mode == "auto" and ctx.intent_bucket == "allowed" and ctx.risk_level == "low":
        return allow()

    return deny("default_safe")
```

---

## 5. 与 AIReplyHandler 的边界

| 当前 | 目标 |
|------|------|
| 生成后立即 `_send_reply` | 生成与 **send 解耦** |
| send 成功即 `return True` | `preview` 时「业务成功」= 日志写入，**非** send 成功 |
| 无 decision 记录 | 每条 ReplyLog 带 §2 字段 |

**插入点（12c 设计）：** `outbound` / `SendMessage` **唯一入口** 前调用 `evaluate_send_gate`.

---

## 6. 店铺级 / 工作区级配置

| 配置 | 层级 | 说明 |
|------|------|------|
| `reply_mode` | ShopBinding | preview / assisted / auto |
| `workspace_pause` | Workspace | 顶栏暂停全部 |
| `shop_pause` | ShopBinding | 单店暂停 |
| `consultation_only` / `default_reply_scope` | ShopBinding | 默认 true（12b.1） |
| `low_confidence_threshold` | SafetySettings | Workspace 默认，Shop 可覆盖 |
| `human_takeover_keywords` | SafetySettings | 与 block intent 并联 |

**默认新绑定：** `reply_mode=preview` + `consultation_only=true`.

---

## 7. 验收标准（12c 技术设计须覆盖）

| # | 验收项 |
|---|--------|
| 1 | Preview 模式下 **零** 平台 send 调用（可测） |
| 2 | `auto` + `refund_request` → `allowed_to_send=false` |
| 3 | `workspace_pause` 覆盖 `reply_mode=auto` |
| 4 | 每条建议有 `intent` + `allowed_to_send` + `blocked_reason` |
| 5 | gate **不** 依赖 `USE_UNIFIED_OUTBOUND_RESOLVER` 默认值 |

---

## 8. 与 Phase 12e DB 的字段对齐

ReplyLog / MessageDecision 表须能存储 §2 全部字段；ShopBinding 增加 `consultation_only`（见 [phase12b_shop_binding_state_model.md](phase12b_shop_binding_state_model.md)）。

---

*Phase 12b.1 · Send Gate Requirements · docs only*

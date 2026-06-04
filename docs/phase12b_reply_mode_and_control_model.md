# Phase 12b — Reply Mode & Control Model

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 关联 | [phase12a_safety_and_preview_spec.md](phase12a_safety_and_preview_spec.md) |

---

## 1. ReplyMode 枚举（持久化在 ShopBinding）

| 值 | 发送行为 | 默认 |
|----|----------|------|
| `preview` | 只写 ReplyLog.suggested；**不调用**平台 send | **✅** |
| `assisted` | 商家 approve 后 send | Growth |
| `auto` | 过 Safety 后自动 send | 须二次确认 |

**`paused`：** 非 `reply_mode` 值；由标志推导 **effective_mode**。

---

## 2. Effective Reply Control（运行时求值）

```python
# 概念逻辑（文档，非代码）

def effective_send_allowed(shop_binding, workspace) -> bool:
    if workspace.workspace_pause or shop_binding.shop_pause:
        return False  # paused — 最高优先级
    if shop_binding.reply_mode == "preview":
        return False
    if shop_binding.binding_status != "connected":
        return False
    if shop_binding.connection_status not in ("healthy", "degraded"):
        return False  # 产品可配置 degraded 是否允许 assisted
    return True  # assisted/auto 仍须各自 gate
```

| 优先级 | 条件 | 结果 |
|--------|------|------|
| 1 | `workspace_pause` OR `shop_pause` | **paused** — 不自动发 |
| 2 | `reply_mode == preview` | 不发送 |
| 3 | 未 `connected` / auth 失败 | 不发送 |
| 4 | Safety 拦截 | 不发送 / 转人工 |
| 5 | `assisted` 无 approve | 不发送 |
| 6 | `auto` | 发送 |

---

## 3. 开启 auto 的二次确认（数据记录）

| 字段 | 说明 |
|------|------|
| `auto_enabled_at` | 开启时间 |
| `auto_enabled_by` | merchant_id |
| `AuditLog.action` | `reply_mode.auto_enabled` |
| 前置检查 | SafetySettings 最低配置满足（12a onboarding） |

**降级：** `reply_mode` 改回 `preview` 或 `assisted` → 写 AuditLog；**不需** 二次确认。

---

## 4. Pause 模型

| 层级 | 字段 | UI |
|------|------|-----|
| **Workspace** | `workspace_pause: bool` | 顶栏「暂停全部店铺」 |
| **Shop** | `shop_pause: bool` | 店铺卡片开关 |

| paused 时 | preview 建议生成 | assisted/auto 发送 |
|-----------|------------------|-------------------|
| **推荐** | 可继续（观察） | **禁止** |
| 可选严格 | 也停止 | 禁止 |

---

## 5. SafetySettings（Workspace 或 Shop 级）

**MVP：** Workspace 级默认 + Shop 可选覆盖（`shop_binding_id NULL` = workspace 默认）。

| 字段 | 类型 | 说明 |
|------|------|------|
| `safety_settings_id` | UUID | PK |
| `workspace_id` | FK | ✅ |
| `shop_binding_id` | FK nullable | 覆盖 |
| `forbidden_promises` | JSON list | 禁诺短语/规则 ID |
| `sensitive_keywords` | JSON list | 额外敏感词 |
| `refund_policy_mode` | enum | `block` / `transfer` / `warn` |
| `shipping_time_policy_mode` | enum | 同上 |
| `price_promise_policy_mode` | enum | 同上 |
| `low_confidence_threshold` | float 0–1 | 低于则转人工 |
| `human_takeover_keywords` | JSON list | 转人工词 |
| `after_sales_to_human` | bool | 售后场景 |
| `complaint_to_human` | bool | 投诉场景 |
| `max_auto_replies_per_conversation` | int | 防刷屏 |
| `quiet_hours` | JSON | 如 `{"start":"22:00","end":"08:00"}` 禁止 auto |
| `updated_by` | FK merchant | |
| `updated_at` | datetime | |

### 5.1 风险场景 → 动作

| 场景 | 检测 | 默认动作 |
|------|------|----------|
| 禁诺命中 | 规则引擎 | `blocked` + reason |
| 低置信 | AI score | `transfer` / 仅 preview |
| 售后/退换 | 关键词+意图 | `transfer` |
| 金额/赔付 | 正则 | `transfer` |
| 投诉 | 关键词 | `transfer` |
| quiet_hours | 时间 | 强制 `assisted` 或 preview |

**强制转 assisted / human：** `reply_mode=auto` 时命中高风险 → 降级为 **仅写 suggested + 待人工**（不发送）。

---

## 6. Human Takeover（会话级 · 后期表）

| 字段 | 说明 |
|------|------|
| `conversation_id` | |
| `shop_binding_id` | |
| `taken_over_by` | merchant_id |
| `until` | 可选超时 |
| `reason` | manual / keyword / low_confidence |

MVP 可仅在 ReplyLog 记 `outcome=transfer`；**12c** 定义运行时会话 cache。

---

## 7. 与工程 flag 边界

| 工程（现有） | SaaS（目标） |
|--------------|--------------|
| `USE_UNIFIED_OUTBOUND_RESOLVER` env | **不** 作为商家可见开关 |
| `reply_mode` 列 | **店铺级** 产品配置 |
| Preview gate send | 12c 技术设计 |

**默认：** 新 ShopBinding `reply_mode=preview`；**不** 依赖 env 默认。

---

## 8. 不变量签收

| 不变量 | ✅ |
|--------|---|
| default `reply_mode` = `preview` | ✅ |
| `connected` ≠ auto enabled | ✅ |
| `paused` 覆盖 auto/assisted 发送 | ✅ |
| auto 开启须审计 + 二次确认 | ✅ |

---

*Phase 12b · Reply Mode & Control*

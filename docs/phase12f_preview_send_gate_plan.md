# Phase 12f — Preview Send Gate Implementation Plan（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | **implementation plan only** · **本 Phase 不写代码** |
| 前置 | [phase12c_preview_dry_run_technical_design.md](phase12c_preview_dry_run_technical_design.md) · [phase12e_migration_sequence.md](phase12e_migration_sequence.md) |
| 关联 | [phase12f_guarded_send_design.md](phase12f_guarded_send_design.md) · [phase12f_handler_integration_steps.md](phase12f_handler_integration_steps.md) |

---

## 1. Phase 12f 总体目标

| 做 | 不做 |
|----|------|
| 规划第一批 **product gate** 代码如何落地 | 写 Python、改 handler、改 `SendMessage` |
| 定义 **legacy → guarded send** 过渡路径 | 创建 DB migration、改 `database/models.py` |
| 对齐 H0–H6 与 M4–M7（12e） | 改 UI、API 实现、PDD/Doudian Channel |
| 锁定测试矩阵 T1–T12（13a/13b 执行） | 默认开启任何 gate |

**核心策略：**

```text
product_gate_enabled=false  →  100% 今日 PDD legacy（AIReplyHandler._send_reply → SendMessage）
product_gate_enabled=true   →  SendDecision + send_text_guarded（final guard）
```

**Gate 维度：** **店铺级** `ShopBinding.product_gate_enabled` + `reply_mode` — **非** 全局 env，**非** 默认 `USE_UNIFIED_OUTBOUND_RESOLVER`。

---

## 2. 从 legacy auto send 到 product gate send

### 2.1 当前（as-is）

```text
KeywordDetectionHandler (TEXT only) → transfer → break
AIReplyHandler → bot.reply → _send_reply → outbound? → SendMessage.send_text
```

- 无 SendDecision、无 Preview gate、无 intent 分类（除关键词子串）。
- `config.json` / 线程启停 ≠ SaaS `reply_mode`。

### 2.2 目标（to-be · gate on）

```text
normalize → keyword risk → intent classify → build SendDecision
  → (optional) AI generate if allowed_to_generate
  → send_text_guarded → ReplyLog
  → outbound.send_text ONLY if guard allows
```

### 2.3 过渡原则

| 原则 | 说明 |
|------|------|
| **Flag-gated / shop-gated** | 仅 `product_gate_enabled=true` 的店走新路径 |
| **Shadow-first** | H2 可先写 decision 不改变 send（对齐 12e M4） |
| **单店试点** | H3–H5 先 1 个测试 `shop_binding_id` |
| **PDD 队列不变** | `pdd_{shop_id}` |
| **Doudian** | mock 非 production；gate 不引入真实 Doudian send |

---

## 3. 核心不变量（实现验收 SSOT）

| # | 不变量 | 实现检查 |
|---|--------|----------|
| I1 | **Preview 永不 send** | `reply_mode=preview` → guard 不调用 outbound/SendMessage；`send_status=not_sent_preview` |
| I2 | **Assisted 须商家确认** | 无 `merchant_approve` → `allowed_to_send=false` |
| I3 | **Auto 仅** allowlist + 高置信 + 低风险 | 见 12b.1 allowed intents |
| I4 | **blocked intent 永不 auto send** | `intent_bucket=blocked` → `allowed_to_send=false` |
| I5 | **paused 永不 send** | workspace/shop pause 最高优先级 |
| I6 | **final send guard** 在所有 outbound **之前** | 无 handler 直连 SendMessage（gate on 时） |
| I7 | **`reply_mode=auto` 不覆盖 intent gate** | SendDecision 求值顺序见 12c |
| I8 | **`product_gate_enabled=false` → legacy 不变** | T1 回归 |

---

## 4. 模块交付物（代码 Phase 映射）

| 模块 | 文档 | 代码 Phase |
|------|------|------------|
| `send_text_guarded` | [phase12f_guarded_send_design.md](phase12f_guarded_send_design.md) | 13a |
| Intent classifier | [phase12f_intent_classifier_plan.md](phase12f_intent_classifier_plan.md) | 13a |
| Handler 接入 | [phase12f_handler_integration_steps.md](phase12f_handler_integration_steps.md) | 13b–13d |
| 测试 | [phase12f_test_implementation_plan.md](phase12f_test_implementation_plan.md) | 13a+ |

---

## 5. 配置来源（非 env 默认）

| 字段 | 存储 | 默认 |
|------|------|------|
| `product_gate_enabled` | ShopBinding（或 M1 前：config overlay JSON） | **false** |
| `reply_mode` | ShopBinding | **preview** |
| `workspace_pause` / `shop_pause` | Workspace / ShopBinding | false |

**开发 override（可选）：** `DEV_FORCE_PRODUCT_GATE_SHOP_IDS` — 仅 dev，**禁止** production 默认。

---

## 6. 与 12e migration 对齐

| 12e 阶段 | 12f Handler 阶段 |
|----------|------------------|
| M4 shadow SendDecision | H2 |
| M5 Preview test shop | H3 |
| M6 Assisted | H4 |
| M7 Auto allowlist | H5 |
| M8 Dashboard read | H6 |

---

## 7. Rollback 总策略

| 级别 | 动作 |
|------|------|
| L1 单店 | `product_gate_enabled=false` |
| L2 工作区 | 全部店 gate off |
| L3 代码 | feature 模块未 import handler（编译期隔离） |
| L4 紧急 | 回滚 release；legacy 路径无 gate 分支 |

---

## 8. 非目标（12f）

- 实现 `send_text_guarded` 本体
- 修改 `AutoReplyThread` 结构
- 默认 `product_gate_enabled=true`
- 替换 legacy SQLite 表

---

*Phase 12f · Preview Send Gate Plan · docs only*

# Phase 13c — Single Test Shop Preview Gate Plan（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | **docs only** · **本 Phase 不写代码** |
| 前置 | [phase13b_done.md](phase13b_done.md) · [phase12f_handler_integration_steps.md](phase12f_handler_integration_steps.md) H3 |
| 关联 | [phase12f_preview_send_gate_plan.md](phase12f_preview_send_gate_plan.md) · [phase12c_preview_dry_run_technical_design.md](phase12c_preview_dry_run_technical_design.md) |

---

## 1. 总体目标

从 **Phase 13b shadow 观察** 推进到 **单测试店 Preview gate** 的**可实施规划**（实现落在 **Phase 13d**）。

| 做 | 不做 |
|----|------|
| 定义 allowlisted test shop 的 preview zero-send 路径 | 全量 PDD 默认 gate |
| 明确 non-test shop **100% legacy** | Assisted / Auto 模式 |
| 对齐 H3 + Z1–Z10 测试矩阵 | 改 handler / SendMessage / DB（本 Phase） |
| 为 13d 实现提供 SSOT | Doudian production |

**第一目标：** **zero-send safety**（Preview 只生成建议、永不出站），不是 assisted 审批流，也不是 auto 发送。

```text
13a 纯函数 → 13b shadow（gate off）→ 13c 规划 → 13d 单店 preview 实现 → 13e ReplyLog/Dashboard 读模型
```

---

## 2. 范围边界

| 维度 | test shop（allowlist 命中） | non-test shop |
|------|---------------------------|---------------|
| `product_gate_enabled` | **true**（仅显式配置） | **false**（默认） |
| `reply_mode` | **preview** | legacy（无 gate 分支） |
| AI 生成 | ✅ 建议回复 | ✅ 现有行为 |
| 出站 | ❌ **永不** SendMessage / outbound | ✅ legacy `_send_reply` |
| `guarded_send` | **final guard**（决策后不 send） | 不进入发送决策链 |
| Shadow logger | 可保留（gate off 记录对比） | 13b fail-open 继续 |

**Doudian / Taobao / JD：** 不进入 preview gate production path（见 [phase13c_test_shop_gate_selection.md](phase13c_test_shop_gate_selection.md)）。

---

## 3. 核心不变量（13d 实现验收 SSOT）

| # | 不变量 | test shop | non-test shop |
|---|--------|-----------|---------------|
| I1 | **Preview 永不 send** | `reply_mode=preview` + gate on → 不调用 `_send_reply` / SendMessage / `outbound.send_text` | N/A |
| I2 | **Legacy 不变** | N/A | 与 13b 前完全一致（T1/Z2 回归） |
| I3 | **`product_gate_enabled` 默认 false** | 仅 allowlist 显式 true | 默认 false |
| I4 | **`reply_mode` 默认 preview**（SaaS 模型） | test shop 固定 preview | legacy 不读 SaaS reply_mode |
| I5 | **paused 最高优先级** | `workspace_pause` / `shop_pause` → no send | legacy 不受影响 |
| I6 | **blocked intent** | human takeover / `not_sent_human_takeover`；no send | keyword/legacy 仍按今日逻辑 |
| I7 | **`guarded_send` 是 final guard** | 所有真实发送入口前必须经 `evaluate_guarded_send`；preview 路径 **不应** 到达 send 入口 | 不调用 guarded send 做拦截 |
| I8 | **Fail-safe 不对称** | 任何 gate/classifier/guard/logger 异常 → **不发送**（宁可漏发） | 异常 → **不改变 legacy**（13b shadow fail-open 仍适用） |
| I9 | **consultation_only** | test shop 绑定 consultation-only 产品边界 | 无 gate 时不强制 |
| I10 | **队列名不变** | `pdd_{shop_id}` | 同左 |

---

## 4. 与 13a / 13b 的关系

| Phase | 状态 | 本规划如何使用 |
|-------|------|----------------|
| **13a** | 已实现 | `classify_consultation_intent` · `build_send_decision` · `evaluate_guarded_send` |
| **13b** | 已实现 | shadow 旁路保留；test shop 可走**独立** gate-on 分支，shadow 可并行对比 |
| **13c** | 本文档 | 选型 + flow + 测试 + rollback |
| **13d** | 待实现 | handler 最小分支 + in-memory config/log |
| **13e** | 待实现 | ReplyLog 持久化 + Dashboard read model |

**13d 原则：** 不默认 `product_gate_enabled=true`；不重构整条 handler 链；优先 **早分支**（gate selection 后 test shop 跳过 `_send_reply`）。

---

## 5. 文档索引（Phase 13c 包）

| 文档 | 内容 |
|------|------|
| [phase13c_test_shop_gate_selection.md](phase13c_test_shop_gate_selection.md) | allowlist · 配置字段 · 选型规则 |
| [phase13c_preview_integration_flow.md](phase13c_preview_integration_flow.md) | as-is / to-be handler flow |
| [phase13c_zero_send_test_plan.md](phase13c_zero_send_test_plan.md) | Z1–Z10 测试（13d/13e 执行） |
| [phase13c_rollback_and_safety.md](phase13c_rollback_and_safety.md) | 回滚 · Go/No-Go · 人工清单 |
| [phase13c_done.md](phase13c_done.md) | 签收 |

---

## 6. 明确非目标（13c / 13d）

- 全量商家 `product_gate_enabled=true`
- `reply_mode=assisted` / `auto`（→ Phase 13f+ / H4–H5）
- `database/models.py` migration（→ 12e M*，13e 后）
- UI / REST API 实现
- Doudian 真实 API / production outbound
- 修改 `SendMessage` 签名或 PDD Channel 热路径

---

*Phase 13c planning SSOT · 2026-06-03*

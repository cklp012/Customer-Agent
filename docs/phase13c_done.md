# Phase 13c 完成 — Single Test Shop Preview Gate Planning

| 项 | 内容 |
|----|------|
| 状态 | **docs only · 规划完成** |
| 日期 | 2026-06-03 |
| 范围 | H3 规划（[phase12f_handler_integration_steps.md](phase12f_handler_integration_steps.md)） |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 类型 | **仅文档** |
| 代码 | **未写** |
| tests | **未改** |
| handler / SendMessage / DB | **未改** |
| PDD / Doudian 热路径 | **未改** |
| product gate enforcement | **未开始**（13d） |

---

## 新增文档

| 文档 | 内容 |
|------|------|
| [phase13c_single_test_shop_preview_plan.md](phase13c_single_test_shop_preview_plan.md) | 总目标 · 不变量 · 范围 |
| [phase13c_test_shop_gate_selection.md](phase13c_test_shop_gate_selection.md) | allowlist · 选型规则 |
| [phase13c_preview_integration_flow.md](phase13c_preview_integration_flow.md) | as-is / to-be handler flow |
| [phase13c_zero_send_test_plan.md](phase13c_zero_send_test_plan.md) | Z1–Z10 |
| [phase13c_rollback_and_safety.md](phase13c_rollback_and_safety.md) | 回滚 · Go/No-Go |

---

## 规划结论（签收）

| # | 结论 |
|---|------|
| 1 | **test shop preview = zero-send**（永不 SendMessage / outbound） |
| 2 | **non-test shop = legacy unchanged** |
| 3 | **allowlist 必须显式**（`platform_id=pinduoduo` + `shop_id`/`account_id` + `workspace_id`） |
| 4 | **`product_gate_enabled` 默认 false**；仅 test 行 true |
| 5 | **`reply_mode=preview`**；非 assisted/auto |
| 6 | **`guarded_send`** 为 test shop final guard |
| 7 | **13d** 用 in-memory config + preview log；**13e** ReplyLog + Dashboard |

---

## 前置 Phase

| Phase | 状态 |
|-------|------|
| 13a | ✅ 纯函数 |
| 13b | ✅ shadow logging |

---

## 下一步

| Phase | 内容 |
|-------|------|
| **13d** | single test shop preview gate **implementation**（in-memory config/log） |
| **13e** | preview ReplyLog + Dashboard read model integration |
| **12g** | merchant console wireframe（可并行） |

---

*签收：Phase 13c · docs only · 2026-06-03*

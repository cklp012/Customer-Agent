# Phase 14h 完成 — Preview ReplyLog Service Integration Planning

| 项 | 内容 |
|----|------|
| 状态 | **docs only · 规划完成** |
| 日期 | 2026-06-03 |
| 前置 | [phase14g_done.md](phase14g_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 类型 | **仅文档** |
| Python 代码 | **未写** |
| tests | **未改** |
| handler | **未改** |
| `product_persistence` code | **未改** |
| DB / SQLite / engine | **未创建** |
| SendMessage / PDD / Doudian | **未改** |

---

## 新增文档

| 文档 | 内容 |
|------|------|
| [phase14h_preview_service_integration_plan.md](phase14h_preview_service_integration_plan.md) | 总体 integration 计划 · as-is / to-be flow |
| [phase14h_handler_boundary_plan.md](phase14h_handler_boundary_plan.md) | handler ↔ service 边界 · 最小改动策略 |
| [phase14h_zero_send_regression_plan.md](phase14h_zero_send_regression_plan.md) | H1–H10 回归测试计划 |
| [phase14h_failure_policy.md](phase14h_failure_policy.md) | failure / fail-safe 策略 |

---

## 规划结论（签收）

| # | 结论 |
|---|------|
| 1 | **test shop preview = zero-send**（集成后仍不变） |
| 2 | **non-test shop = legacy unchanged**（不调用 service） |
| 3 | handler 只 orchestration；gates 纯函数不变 |
| 4 | **`PreviewReplyLogService` = preview ReplyLog 唯一写入边界**（14i 起） |
| 5 | 14i：`record_preview` 内部包装 `append_preview_log` |
| 6 | handler **不** import db_manager / repository / ORM |
| 7 | service failure **不得** fallback SendMessage |
| 8 | SQLite shadow write **仍未实现**（14j planning） |
| 9 | assisted / auto **未实现** |
| 10 | Doudian **不进入** production product persistence |

---

## 当前 runtime（unchanged）

- handler 仍直接 `append_preview_log`
- `PreviewReplyLogService` 仅 read adapter（14g）
- 无 DB · 无 handler wiring

---

## 下一步

| Phase | 内容 |
|-------|------|
| **14i** | PreviewReplyLogService handler integration for **test shop only** |
| **14j** | optional SQLite shadow write **planning only** |
| **14k** | Dashboard read API **planning only** |

---

*签收：Phase 14h · docs only · 2026-06-03*

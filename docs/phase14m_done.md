# Phase 14m 完成 — SendDecision Snapshot Shadow Write Planning

| 项 | 内容 |
|----|------|
| 状态 | **docs only · 规划完成** |
| 日期 | 2026-06-03 |
| 前置 | [phase14l_done.md](phase14l_done.md) · [phase14k_done.md](phase14k_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 类型 | **仅文档** |
| Python 代码 | **未写** |
| `send_decision_snapshots` 表 | **未创建** |
| handler / SendMessage / PDD / Doudian | **未改** |
| ReplyLog SQLite（14l） | **已实现** |
| Snapshot SQLite | **未实现** |

---

## 新增文档

| 文档 | 内容 |
|------|------|
| [phase14m_senddecision_snapshot_plan.md](phase14m_senddecision_snapshot_plan.md) | 总体规划 · append-only |
| [phase14m_senddecision_schema_detail.md](phase14m_senddecision_schema_detail.md) | 表 schema · indexes |
| [phase14m_snapshot_write_flow.md](phase14m_snapshot_write_flow.md) | write flow · flags |
| [phase14m_dashboard_detail_decision_view.md](phase14m_dashboard_detail_decision_view.md) | Dashboard 决策链展示 |
| [phase14m_failure_and_rollback.md](phase14m_failure_and_rollback.md) | failure · rollback |
| [phase14m_test_plan.md](phase14m_test_plan.md) | M1–M10 |

---

## 规划结论（签收）

| # | 结论 |
|---|------|
| 1 | SendDecision snapshot **append-only** |
| 2 | preview 阶段 `decision_phase=ai_preview` |
| 3 | future assisted `decision_phase=merchant_confirm` |
| 4 | 关联 `reply_log_id` · 弱关联 · 无 legacy FK |
| 5 | flags：`WRITE_SEND_DECISION` 独立于 `WRITE_REPLY_LOG` |
| 6 | snapshot failure **不得** fallback SendMessage |
| 7 | ReplyLog SQLite fail → skip snapshot（推荐） |
| 8 | handler **不直接**写 snapshot |
| 9 | auto / assisted send **未实现** |
| 10 | Doudian **非 production** |

---

## 当前 runtime（unchanged）

- 14l：`reply_logs` shadow behind flags
- 无 `send_decision_snapshots` 表
- test shop zero-send · non-test legacy 不变

---

## 下一步

| Phase | 内容 |
|-------|------|
| **14n** | SendDecision snapshot SQLite **implementation** behind flag |
| **14o** | Dashboard read API **skeleton only** |
| **14p** | AuditLog / PendingAssisted planning |

---

*签收：Phase 14m · docs only · 2026-06-03*

# Phase 15p 完成 — Wire LivePdd Port Selection Planning

| 项 | 内容 |
|----|------|
| 状态 | **port selection planning complete · docs only** |
| 日期 | 2026-06-03 |
| 前置 | [phase15m_done.md](phase15m_done.md) · [phase15o_done.md](phase15o_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 类型 | **仅文档** |
| Python 代码 | **未写** |
| `LivePddAssistedOutboundPort` 接入 service | ❌ **未做** |
| live assisted send | ❌ **未实现** |
| retry / auto send | ❌ **未实现** |
| handler / SendMessage / PDD / Doudian | ❌ **未改** |
| DB schema | ❌ **无变更** |
| PDD queue | **`pdd_{shop_id}` 不变** |

---

## 规划要点

| # | 要点 |
|---|------|
| 1 | **Port selection chooses an adapter; it must never decide safety.** |
| 2 | **Default remains `DryRunAssistedOutboundPort`** |
| 3 | Future live → **all gates** + manual approve + pinduoduo + allowlist |
| 4 | Selection **after** guard · audit · snapshot · idempotency acquire |
| 5 | **Route 不直接选 port** |
| 6 | **No fallback legacy send** |
| 7 | dry_run / Doudian / auto → **never live** |

---

## 文档清单

| 文档 | 内容 |
|------|------|
| [phase15p_live_port_selection_plan.md](phase15p_live_port_selection_plan.md) | 总体规划 |
| [phase15p_port_selection_decision_tree.md](phase15p_port_selection_decision_tree.md) | 决策树 |
| [phase15p_service_integration_boundary.md](phase15p_service_integration_boundary.md) | 集成边界 |
| [phase15p_flag_and_allowlist_gate.md](phase15p_flag_and_allowlist_gate.md) | Flag · allowlist |
| [phase15p_no_fallback_and_rollback.md](phase15p_no_fallback_and_rollback.md) | No fallback |
| [phase15p_test_plan.md](phase15p_test_plan.md) | P1–P20 |

---

## 下一步建议

| Phase | 内容 |
|-------|------|
| **15q** | ✅ Reconciliation **schema planning only** — [phase15q_done.md](phase15q_done.md) |
| **15r** | Local dashboard smoke test **script skeleton** |
| **15s** | `OutboundPortSelector` **skeleton implementation** · dry-run only |
| **15t** | Reconciliation schema **implementation behind flags** |

---

*签收：Phase 15p · docs only · 2026-06-03*

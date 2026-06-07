# Phase 15h 完成 — Live PDD AssistedOutboundPort Planning

| 项 | 内容 |
|----|------|
| 状态 | **docs only · live port planned** |
| 日期 | 2026-06-03 |
| 前置 | [phase15g_done.md](phase15g_done.md) · [phase15f_done.md](phase15f_done.md) · [phase15c_done.md](phase15c_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 类型 | **仅文档** |
| `LivePddAssistedOutboundPort` | **未实现** |
| live assisted send | **未实现** |
| auto send | **未实现** |
| handler / SendMessage / PDD / Doudian | **未改** |
| PDD queue | **`pdd_{shop_id}` 不变** |

---

## 规划要点

| # | 要点 |
|---|------|
| 1 | **Live PDD port is a platform adapter, not a workflow owner** |
| 2 | **AssistedReplyService owns safety, state, audit, idempotency** |
| 3 | Port 复用 `AssistedOutboundRequest` / `AssistedOutboundResult` |
| 4 | Port **不** final guard / audit / snapshot / idempotency / pending / DB |
| 5 | Single test shop live gate · flags + allowlist · manual approve only |
| 6 | **timeout → unknown** · reconciliation · **不自动重发** |
| 7 | **No fallback legacy send** |
| 8 | 当前系统仍只支持 **dry-run assisted outbound** |

---

## 文档清单

| 文档 | 内容 |
|------|------|
| [phase15h_live_pdd_outbound_port_plan.md](phase15h_live_pdd_outbound_port_plan.md) | 总体规划 |
| [phase15h_pdd_outbound_boundary_and_adapter.md](phase15h_pdd_outbound_boundary_and_adapter.md) | Adapter 边界 |
| [phase15h_pdd_queue_and_message_contract.md](phase15h_pdd_queue_and_message_contract.md) | Queue · message |
| [phase15h_single_test_shop_live_gate.md](phase15h_single_test_shop_live_gate.md) | Live gate |
| [phase15h_timeout_unknown_and_reconciliation.md](phase15h_timeout_unknown_and_reconciliation.md) | Timeout · reconciliation |
| [phase15h_failure_rollback_policy.md](phase15h_failure_rollback_policy.md) | Failure · rollback |
| [phase15h_test_plan.md](phase15h_test_plan.md) | H1–H20 |

---

## 下一步建议

| Phase | 内容 |
|-------|------|
| **15i** | ✅ Dashboard action endpoint **dry-run skeleton** — [phase15i_done.md](phase15i_done.md) |
| **15j** | Action idempotency / `client_request_id` **skeleton** |
| **15k** | `LivePddAssistedOutboundPort` **skeleton planning only** |
| **15l** | Register action routes for local dashboard **behind flags** |

---

*签收：Phase 15h · docs only · 2026-06-03*

# Phase 15e — Live Assisted Send Integration Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不写代码** |
| 日期 | 2026-06-03 |
| 前置 | [phase15d_done.md](phase15d_done.md) · [phase15c_done.md](phase15c_done.md) · [phase15b_done.md](phase15b_done.md) · [phase15a_done.md](phase15a_done.md) · [phase14x_done.md](phase14x_done.md) · [phase14v_done.md](phase14v_done.md) |

---

## 1. Phase 15e 定位

| 项 | 结论 |
|----|------|
| 交付 | **仅文档** |
| Python 代码 | **未写** |
| live assisted send | **未实现** |
| auto send | **未实现** |
| `approve_pending` 当前行为 | **不变** · guard allow 后仍 `guard_passed_but_send_not_implemented` · **不发送** |
| handler / SendMessage / outbound resolver | **未改** |
| PDD / Doudian 热路径 | **未改** |
| legacy database | **未改** |
| Dashboard API（15d read skeleton） | **未改** |
| 新 DB 表 | **未创建** |
| assisted / send flags | **默认全部 off / dry_run true** |

Phase 15e 在 **15a–15d 已实现 skeleton** 基础上，规划未来 **live assisted send** 如何由 **`AssistedReplyService` 编排** idempotency repository + outbound port — **本 phase 不写代码、不发送**。

---

## 2. 已实现 skeleton（15b–15d · unchanged）

| 组件 | Phase | 状态 |
|------|-------|------|
| `OutboundIdempotencyRepositorySQLite` · acquire/mark | 15b | ✅ · no send |
| `DryRunAssistedOutboundPort` · would_send only | 15c | ✅ · no real outbound |
| `PendingAssistedDashboardReadService` · GET list/detail | 15d | ✅ · read-only |
| `AssistedReplyService.approve_pending` | 14x | ✅ · guard only · **no send** |

---

## 3. 核心原则（签收）

| # | 原则 |
|---|------|
| **E1** | **未来 live send 必须由 `AssistedReplyService` 编排** — handler 不直接 `SendMessage` |
| **E2** | **Dashboard read（15d）不触发 send** — list/detail 只读 |
| **E3** | **Live send 只能来自未来明确的 action endpoint 或内部 approved workflow** — 本 phase 不实现 endpoint |
| **E4** | **Final guard pass 仅允许 outbound attempt** — 不等于平台发送成功 |
| **E5** | **No final guard pass → no outbound** |
| **E6** | **No audit / snapshot / idempotency → no outbound** |
| **E7** | **No fallback legacy send** — DB / port 失败不得 bypass 到 handler 直发 |
| **E8** | **PDD legacy hot path 不变** · queue **`pdd_{shop_id}`** |
| **E9** | **Doudian production 不启用** |
| **E10** | **Dry-run 为默认安全路径** · live 需显式 flags + allowlist |

---

## 4. 未来集成拓扑

```text
Future action endpoint (15g+) or internal workflow
    → AssistedReplyService.approve_pending (live path · 15f+ dry-run wire first)
        → evaluate_final_guard (14v · already wired in 14x)
        → AuditLog append (14q)
        → SendDecisionSnapshot merchant_confirm (14n)
        → OutboundIdempotencyRepository.acquire (15b)
        → AuditLog outbound_send_attempted
        → AssistedOutboundPort.send (15c dry-run · future LivePdd port)
            → Unified outbound / PDD adapter (existing · not modified in 15e)
            → queue: pdd_{shop_id}
```

**AssistedReplyService 不得 import legacy `SendMessage`。** Live port 封装平台 outbound。

---

## 5. 子文档索引

| 文档 | 内容 |
|------|------|
| [phase15e_flag_gate_and_allowlist_policy.md](phase15e_flag_gate_and_allowlist_policy.md) | Flags · allowlist · live gate |
| [phase15e_assisted_service_live_sequence.md](phase15e_assisted_service_live_sequence.md) | approve_pending live 顺序 |
| [phase15e_live_outbound_port_boundary.md](phase15e_live_outbound_port_boundary.md) | Port 边界 · LivePdd 规划 |
| [phase15e_audit_snapshot_idempotency_order.md](phase15e_audit_snapshot_idempotency_order.md) | audit · snapshot · idempotency 顺序 |
| [phase15e_failure_rollback_and_reconciliation.md](phase15e_failure_rollback_and_reconciliation.md) | 失败 · rollback · reconciliation |
| [phase15e_test_plan.md](phase15e_test_plan.md) | E1–E24 未来测试 |

---

## 6. 与 15a 关系

| 项 | 15a | 15e |
|----|-----|-----|
| 类型 | planning | planning（在 15b–15d skeleton 落地后细化） |
| 代码 | 无 | 无 |
| live send | 未实现 | **仍未实现** |
| skeleton 引用 | 规划 | **引用已实现的 15b/15c/15d 组件** |

15e **不重复实现** 15a 文档中的代码任务；仅更新集成规划以反映 15b–15d 交付物。

---

## 7. 明确不在本 phase

| 项 | 状态 |
|----|------|
| Wire dry-run port into AssistedReplyService | **15f** |
| Dashboard approve/reject/send action endpoint | **15g planning** |
| LivePddAssistedOutboundPort implementation | **15h planning** |
| Handler 修改 | ❌ |
| Auto send | ❌ |

---

*Phase 15e · docs only · 2026-06-03*

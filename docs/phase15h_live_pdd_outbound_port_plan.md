# Phase 15h — Live PDD AssistedOutboundPort Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不写代码** |
| 日期 | 2026-06-03 |
| 前置 | [phase15f_done.md](phase15f_done.md) · [phase15g_done.md](phase15g_done.md) · [phase15c_done.md](phase15c_done.md) · [phase15e_done.md](phase15e_done.md) |

---

## 1. Phase 15h 定位

| 项 | 结论 |
|----|------|
| 交付 | **仅文档** |
| Python 代码 | **未写** |
| `LivePddAssistedOutboundPort` | **未实现** |
| live assisted send | **未实现** |
| auto send | **未实现** |
| handler / SendMessage / outbound resolver | **未改** |
| PDD / Doudian 热路径 | **未改** |
| legacy database | **未改** |
| Dashboard API code | **未改** |
| assisted / send flags | **默认 off** |

**当前系统仍只支持 dry-run assisted outbound**（15c `DryRunAssistedOutboundPort` + 15f service wire）。Phase 15h 规划未来 **`LivePddAssistedOutboundPort`** 如何封装 PDD outbound — **本 phase 不写代码、不发送**。

---

## 2. 已实现基础（unchanged）

| 组件 | Phase | 状态 |
|------|-------|------|
| `AssistedOutboundPort` interface | 15c | ✅ |
| `DryRunAssistedOutboundPort` | 15c | ✅ would_send only · no SendMessage |
| `AssistedReplyService.approve_pending` dry-run wire | 15f | ✅ `dry_run_would_send` |
| Dashboard action endpoint contract | 15g | 📋 planned · not implemented |
| live send | — | ❌ `live_send_not_implemented` when dry_run=false |

---

## 3. 核心原则（签收）

| # | 原则 |
|---|------|
| **H1** | **Live PDD port is a platform adapter, not a workflow owner.** |
| **H2** | **AssistedReplyService owns safety, state, audit, idempotency.** |
| **H3** | 未来 `LivePddAssistedOutboundPort` **只能**作为 `AssistedOutboundPort` 的一种实现 |
| **H4** | Port **只负责**平台发送尝试 · 返回 success/failure/timeout/unknown |
| **H5** | Service 负责 final guard / audit / snapshot / idempotency / pending state |
| **H6** | **handler 不直接参与** assisted send |
| **H7** | **Dashboard endpoint 不直接** `SendMessage` |
| **H8** | **PDD legacy hot path 不变** · queue `pdd_{shop_id}` |
| **H9** | **Doudian production not enabled** |
| **H10** | **No fallback legacy send** |

---

## 4. 未来架构拓扑

```text
Dashboard POST approve (15i+ · future)
    → auth / CSRF / scope
    → AssistedReplyService.approve_pending
        → final guard
        → audit / snapshot
        → idempotency acquire
        → AssistedOutboundPort.send
            ├── DryRunAssistedOutboundPort (15c · default · dry_run=true)
            └── LivePddAssistedOutboundPort (future · 15k+ impl · explicit DI)
                    → thin PDD adapter
                    → existing PDD send primitive (read-only call · hot path unchanged)
                    → queue: pdd_{shop_id}
        → service updates pending / idempotency / audit from port result
    → JSON response · no handler bypass
```

**AssistedReplyService 不得 import legacy `SendMessage`。** 仅 live port 封装平台 outbound。

---

## 5. LivePddAssistedOutboundPort 职责摘要

| 负责 | 不负责 |
|------|--------|
| 将 `final_reply` 发送到指定 buyer/session | final guard |
| 返回 `provider_message_id` / `platform_status` / error | merchant policy |
| timeout → mark **unknown** | audit / snapshot / idempotency |
| 区分 sent / failed / timeout_unknown / rejected / unavailable | pending status mutation |
| | dashboard permission |
| | fallback legacy handler |

详见 [phase15h_pdd_outbound_boundary_and_adapter.md](phase15h_pdd_outbound_boundary_and_adapter.md)。

---

## 6. Single test shop gate

Live PDD port **默认不可用**。须同时满足 flags + allowlist + guard + idempotency — 见 [phase15h_single_test_shop_live_gate.md](phase15h_single_test_shop_live_gate.md)。

---

## 7. Timeout / unknown / reconciliation

Outbound timeout **不能**简单视为 failed — 见 [phase15h_timeout_unknown_and_reconciliation.md](phase15h_timeout_unknown_and_reconciliation.md)。

---

## 8. 文档清单

| 文档 | 内容 |
|------|------|
| [phase15h_pdd_outbound_boundary_and_adapter.md](phase15h_pdd_outbound_boundary_and_adapter.md) | Adapter 边界 |
| [phase15h_pdd_queue_and_message_contract.md](phase15h_pdd_queue_and_message_contract.md) | Queue · message contract |
| [phase15h_single_test_shop_live_gate.md](phase15h_single_test_shop_live_gate.md) | Single test shop gate |
| [phase15h_timeout_unknown_and_reconciliation.md](phase15h_timeout_unknown_and_reconciliation.md) | Timeout · reconciliation |
| [phase15h_failure_rollback_policy.md](phase15h_failure_rollback_policy.md) | Failure · rollback |
| [phase15h_test_plan.md](phase15h_test_plan.md) | H1–H20 |

---

## 9. 下一步（不在 15h 实现）

| Phase | 内容 |
|-------|------|
| **15i** | Dashboard action endpoint **dry-run skeleton** |
| **15j** | Action idempotency / `client_request_id` **skeleton** |
| **15k** | `LivePddAssistedOutboundPort` **skeleton planning only** |

---

*Phase 15h · docs only · 2026-06-03*

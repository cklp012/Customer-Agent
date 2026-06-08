# Phase 15p — Live Port Selection Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不写代码** |
| 日期 | 2026-06-03 |
| 前置 | [phase15m_done.md](phase15m_done.md) · [phase15o_done.md](phase15o_done.md) · [phase15e_live_assisted_send_integration_plan.md](phase15e_live_assisted_send_integration_plan.md) |

---

## 1. Phase 15p 定位

| 项 | 结论 |
|----|------|
| 交付 | **仅文档** — outbound port selection 规划 |
| Python 代码 | **未写** |
| `LivePddAssistedOutboundPort` 接入 service | ❌ **未做** |
| live assisted send | ❌ **未实现** |
| auto retry / auto send | ❌ **未实现** |
| handler / SendMessage / PDD hot path | ❌ **未改** |
| PDD queue | **`pdd_{shop_id}` 不变** |

**当前实现：** `AssistedReplyService._outbound_port_instance()` 始终返回注入 port 或 **`DryRunAssistedOutboundPort()`** — 无 live selector。

---

## 2. 核心原则

| # | 原则 |
|---|------|
| **P1** | **Port selection chooses an adapter; it must never decide safety.** |
| **P2** | Final guard · allowlist · flags · idempotency · pending status 由 **service / guard** 决定；selector 只读结论 |
| **P3** | **默认** `DryRunAssistedOutboundPort` |
| **P4** | Dashboard route **不**直接选择 live port · **不** SendMessage |
| **P5** | Selection 发生在 workflow **后半段**（见 §3） |
| **P6** | **No fallback legacy send** |
| **P7** | Doudian / auto mode **never** live port（当前与未来初期） |

---

## 3. Selection 时序（future · 在 service 内）

```text
Dashboard POST approve
    → route: CSRF / RBAC / scope / action idempotency (15j)
    → AssistedReplyService.approve_pending
        1. pending load + status check
        2. final guard (FinalGuard · service)
        3. audit + SendDecisionSnapshot
        4. outbound idempotency acquire
        ──► 5. port selection (selector/factory)  ◄── 15p 规划点
        6. port.send(request)
        7. result → pending / idempotency / audit update
    → JSON response
```

**Selection 不得早于步骤 4。** 若 1–4 任一失败 → **no port selected** · no send。

---

## 4. 未来组件（规划 · 未实现）

| 组件 | 职责 |
|------|------|
| `AssistedReplyService` | workflow owner · 调用 selector |
| `OutboundPortSelector`（或 factory） | 只读 gates · 返回 port 实例 |
| `DryRunAssistedOutboundPort` | 默认 adapter |
| `LivePddAssistedOutboundPort` | 未来 live adapter · 15m skeleton 已存在 |

Route **不** import 任一 port 实现。

---

## 5. 文档清单

| 文档 | 内容 |
|------|------|
| [phase15p_port_selection_decision_tree.md](phase15p_port_selection_decision_tree.md) | 决策树 |
| [phase15p_service_integration_boundary.md](phase15p_service_integration_boundary.md) | 集成边界 |
| [phase15p_flag_and_allowlist_gate.md](phase15p_flag_and_allowlist_gate.md) | Flag · allowlist |
| [phase15p_no_fallback_and_rollback.md](phase15p_no_fallback_and_rollback.md) | No fallback · rollback |
| [phase15p_test_plan.md](phase15p_test_plan.md) | P1–P20 |

---

## 6. 禁止（签收）

| 禁止 |
|------|
| 本 phase 修改 `assisted_reply_service.py` 接入 LivePdd |
| route 根据 body flag 选择 live port |
| selector 绕过 final guard |
| selector 绕过 outbound idempotency |
| fallback `SendMessage` / handler / outbound resolver |
| auto send 路径选择 live port |

---

## 7. 下一步（不在 15p 实现）

| Phase | 内容 |
|-------|------|
| **15q** | Reconciliation **schema planning only** |
| **15r** | Local dashboard smoke test **script skeleton** |
| **15s** | `OutboundPortSelector` **skeleton implementation** · dry-run only |

---

*Phase 15p · docs only · 2026-06-03*

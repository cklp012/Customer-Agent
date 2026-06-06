# Phase 15a — Assisted Send Implementation Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不写代码** |
| 日期 | 2026-06-03 |
| 前置 | [phase14y_done.md](phase14y_done.md) · [phase14x_done.md](phase14x_done.md) · [phase14v_done.md](phase14v_done.md) · [phase14z_done.md](phase14z_done.md) |

---

## 1. Phase 15a 定位

| 项 | 结论 |
|----|------|
| 交付 | **仅文档** |
| Python 代码 | **未写** |
| assisted send 实现 | **未实现** |
| auto send 实现 | **未实现** |
| handler / SendMessage / outbound | **未改** |
| PDD / Doudian 热路径 | **未改** |
| legacy database | **未改** |
| Dashboard API | **未改** |
| 新 DB 表 | **未创建** |
| flags 默认 | **全部 off** |

Phase 15a 规划 **`AssistedReplyService.approve_pending`** 从 14x 的 `guard_passed_but_send_not_implemented` **未来**升级为真实 outbound 的完整实现蓝图 — **本 phase 不写代码、不发送**。

---

## 2. 14x 当前 runtime（unchanged）

| 行为 | 现状 |
|------|------|
| `approve_pending` guard allow | `status=guard_passed_but_send_not_implemented` |
| outbound / SendMessage | **未调用** |
| pending → sent | **未实现** |
| `outbound_send_attempted` audit | **未写** |

---

## 3. 核心原则（签收）

| # | 原则 |
|---|------|
| **A1** | **No final guard pass, no outbound attempt.** |
| **A2** | **No audit/snapshot/idempotency, no outbound attempt.** |
| **A3** | **No fallback legacy send.** |
| **A4** | **Final guard pass ≠ 发送成功** — 仅允许尝试 outbound |
| **A5** | **AssistedReplyService owns the outbound attempt** |
| **A6** | **handler 不直接** SendMessage |
| **A7** | **Dashboard 不触发** send |
| **A8** | **PDD legacy hot path 不变** · queue `pdd_{shop_id}` |
| **A9** | **Doudian production not enabled** |
| **A10** | **assisted / send flags 默认 off** |

---

## 4. 未来真实 assisted send 前置条件（全部满足）

| # | 条件 |
|---|------|
| 1 | `PRODUCT_ASSISTED_SERVICE_ENABLED=true` |
| 2 | `PRODUCT_ASSISTED_SEND_ENABLED=true`（15a 规划 · 15b+ 实现） |
| 3 | **single test shop allowlist** match（workspace · shop · account · platform） |
| 4 | pending status valid（pending/approved · 非 terminal） |
| 5 | `evaluate_final_guard` → `allowed_to_send=true` |
| 6 | AuditLog `final_guard_passed` 写入成功 |
| 7 | SendDecisionSnapshot `merchant_confirm` 写入成功 |
| 8 | idempotency lock **acquired** |
| 9 | AuditLog `outbound_send_attempted` 写入成功 |
| 10 | `outbound_channel_status=available` |
| 11 | dry_run=false（若 live send）或 dry_run=true（would_send only） |

**任一失败 → no-send · 不 fallback legacy。**

---

## 5. 升级路径（14x → future）

```text
14x approve_pending
    guard allow → assisted_approved audit
    → return guard_passed_but_send_not_implemented
    → STOP (no outbound)

15b+ (future implementation phases)
    guard allow
    → final_guard_passed audit
    → merchant_confirm snapshot
    → idempotency acquire
    → outbound_send_attempted audit
    → AssistedOutboundPort.send(...)
    → sent/failed status + succeeded/failed audit
```

---

## 6. 组件边界

```text
Handler (future · test shop only)
    → AssistedReplyService.approve_pending
        → evaluate_final_guard (14v)
        → AuditLog / Snapshot repositories (14q/14n)
        → IdempotencyStore (15b)
        → AssistedOutboundPort (15c dry-run · 15d+ live)
            → unified outbound / PDD adapter
                → pdd_{shop_id} queue (unchanged)

Final Guard — decision only
Outbound Port — transport only
AssistedReplyService — orchestration owner
```

---

## 7. 文档索引（15a）

| 文档 | 内容 |
|------|------|
| [phase15a_outbound_contract.md](phase15a_outbound_contract.md) | Outbound adapter |
| [phase15a_idempotency_lock_contract.md](phase15a_idempotency_lock_contract.md) | 幂等锁 |
| [phase15a_status_transition_and_audit.md](phase15a_status_transition_and_audit.md) | 状态 · audit |
| [phase15a_single_test_shop_rollout.md](phase15a_single_test_shop_rollout.md) | 灰度 |
| [phase15a_failure_rollback_policy.md](phase15a_failure_rollback_policy.md) | 失败 · rollback |
| [phase15a_test_plan.md](phase15a_test_plan.md) | A1–A21 |

---

## 8. 实现 phase 建议（post-15a · 非本 phase）

| Phase | 内容 |
|-------|------|
| **15b** | Idempotency skeleton behind flags |
| **15c** | Assisted outbound **dry-run port** skeleton |
| **15d** | PendingAssisted dashboard read API skeleton |
| **15e+** | test shop live assisted send（单独 planning） |

---

*Phase 15a · planning only · 2026-06-03*

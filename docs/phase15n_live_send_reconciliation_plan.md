# Phase 15n — Live Send Reconciliation Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不写代码** |
| 日期 | 2026-06-03 |
| 前置 | [phase15m_done.md](phase15m_done.md) · [phase15h_timeout_unknown_and_reconciliation.md](phase15h_timeout_unknown_and_reconciliation.md) · [phase15k_result_mapping_contract.md](phase15k_result_mapping_contract.md) |

---

## 1. Phase 15n 定位

| 项 | 结论 |
|----|------|
| 交付 | **仅文档** |
| Python 代码 | **未写** |
| live assisted send | **未实现** |
| reconciliation worker | **未实现** |
| auto retry / auto resend | **未实现** |
| handler / SendMessage / outbound resolver | **未改** |
| PDD / Doudian 热路径 | **未改** |
| app.py | **未改** |
| DB schema | **未改** |
| PDD queue | **`pdd_{shop_id}` 不变** |

Phase 15n 在 15h/15k timeout_unknown 规划基础上，**细化未来 live send reconciliation** 的状态机、task 契约、operator runbook、duplicate 防护、audit 规则与 rollback 策略 — **本 phase 不写代码、不发送、不重试**。

---

## 2. 核心原则

| # | 原则 |
|---|------|
| **N1** | **Reconciliation confirms what happened; it must not create a second send.** |
| **N2** | `timeout_unknown` 是未来 live send 的**最高风险状态** — 可能已发、可能未发 |
| **N3** | reconciliation 目标是**确认事实**，不是自动重发 |
| **N4** | unknown 时默认进入 **`manual_review_required`** |
| **N5** | **No fallback legacy send** — 不得绕过 port 调 SendMessage / handler |
| **N6** | PDD hot path / queue **`pdd_{shop_id}`** 不变 |
| **N7** | Doudian production live send **not enabled** |
| **N8** | `provider_message_id` **不可伪造** — 仅平台确认后写入 |
| **N9** | reconciliation task 失败 → **只重试查询**，不重试发送 |

---

## 3. 问题域（future live send）

| 场景 | 风险 | 15n 规划方向 |
|------|------|--------------|
| HTTP timeout 后响应丢失 | 平台可能已发送 | `timeout_unknown` → manual review → reconciliation |
| 平台已发送 · 本地无记录 | duplicate send 风险 | reconciliation 确认 sent → idempotency succeeded |
| 平台未发送 · 本地卡 `in_progress` | 卡住 · 误重发 | reconciliation 确认 not sent → manual review · **不自动重发** |
| `provider_message_id` 缺失 | 不能推断未发送 | 保持 unknown / manual review |
| duplicate approve on unknown | 第二次发送 | block → `manual_review_required` |
| DB 写入失败但平台已发 | danger state | manual review · reconciliation |

---

## 4. 文档清单

| 文档 | 内容 |
|------|------|
| [phase15n_unknown_outcome_state_machine.md](phase15n_unknown_outcome_state_machine.md) | 状态机 |
| [phase15n_reconciliation_task_contract.md](phase15n_reconciliation_task_contract.md) | Task 契约 |
| [phase15n_manual_review_and_operator_runbook.md](phase15n_manual_review_and_operator_runbook.md) | Operator runbook |
| [phase15n_duplicate_send_prevention.md](phase15n_duplicate_send_prevention.md) | 防重复发送 |
| [phase15n_audit_snapshot_status_updates.md](phase15n_audit_snapshot_status_updates.md) | Audit · snapshot · status |
| [phase15n_failure_rollback_policy.md](phase15n_failure_rollback_policy.md) | Failure · rollback |
| [phase15n_test_plan.md](phase15n_test_plan.md) | N1–N20 |

---

## 5. 与已实现组件关系

| 组件 | Phase | 15n 关系 |
|------|-------|----------|
| `DryRunAssistedOutboundPort` | 15c | 不变 · default |
| `LivePddAssistedOutboundPort` skeleton | 15m | 不变 · `live_send_not_implemented` |
| `AssistedReplyService` | 15f | **未接入 live port** · reconciliation 未来在 service 层消费 |
| Outbound idempotency repo | 15b | 状态扩展 **15q schema planning** |
| Action `client_request_id` idempotency | 15j | replay 不得绕过 outbound idempotency |
| Dashboard action routes | 15l | unknown 时 approve **不得**触发第二次 send |

---

## 6. 拓扑（future · post-live-send）

```text
approve_pending (manual dashboard)
    → final guard · audit · snapshot
    → outbound idempotency acquire
    → LivePddAssistedOutboundPort.send
        ├── sent → pending sent · idempotency succeeded
        ├── failed_before_send → pending failed · idempotency failed
        ├── rejected_by_platform → pending failed · audit
        └── timeout_unknown → pending send_unknown · idempotency timeout_unknown
                → audit: outbound_send_timeout_unknown
                → pending → manual_review_required (safe default)
                → schedule/trigger reconciliation task (future)
                    → confirmed_sent → idempotency succeeded · pending sent
                    → confirmed_not_sent → manual_review_required · NO auto retry
                    → still_unknown → stay manual_review_required
```

**Reconciliation 分支永远不调用 send primitive。**

---

## 7. 禁止（签收）

| 禁止 |
|------|
| 自动重发 / auto retry |
| timeout → 隐式 retry approve |
| reconciliation worker 调 SendMessage |
| reconciliation 绕过 idempotency |
| fallback legacy PDD hot path |
| Doudian live outbound |
| 伪造 `provider_message_id` |
| 本 phase 写 Python / 改 schema |

---

## 8. 下一步（不在 15n 实现）

| Phase | 内容 |
|-------|------|
| **15o** | Local dashboard action route **smoke test / runbook** |
| **15p** | Wire LivePdd port selection **planning only** |
| **15q** | Reconciliation **schema planning only** |

---

*Phase 15n · docs only · 2026-06-03*

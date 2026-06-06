# Phase 14y — Final Guard + Assisted Service Integration Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不写代码** |
| 日期 | 2026-06-03 |
| 前置 | [phase14x_done.md](phase14x_done.md) · [phase14v_done.md](phase14v_done.md) · [phase14t_done.md](phase14t_done.md) |

---

## 1. Phase 14y 定位

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

Phase 14y 在 **14v Final Guard pure function** 与 **14x AssistedReplyService skeleton** 之上，规划未来 **真实 assisted outbound 集成** 的边界、顺序、幂等与失败策略。

---

## 2. 14x 当前 runtime（unchanged）

| 行为 | 14x 现状 |
|------|----------|
| `create_pending_from_preview` | flags on → PendingAssisted + audit · **no send** |
| `approve_pending` guard block | audit `final_guard_blocked` · pending 保持 pending · **no send** |
| `approve_pending` guard allow | 返回 `guard_passed_but_send_not_implemented` · audit `assisted_approved` · **no outbound_send_attempted** |
| outbound / SendMessage | **未调用** |
| pending status → sent | **未实现** |

**14y 只规划未来升级路径，不改变 14x 代码行为。**

---

## 3. 核心原则（签收）

| # | 原则 |
|---|------|
| **P1** | **Final Guard allows an outbound attempt, but does not perform the outbound.** |
| **P2** | **AssistedReplyService owns the outbound attempt** after audit/snapshot/idempotency checks pass. |
| **P3** | 未来真实 assisted send **必须**在 `evaluate_final_guard` → `allowed_to_send=true` 之后才允许尝试 outbound |
| **P4** | **final guard pass ≠ 发送成功** — 仅表示 caller **可以**尝试 outbound |
| **P5** | **handler 不直接**调用 `evaluate_final_guard` |
| **P6** | **handler 不直接**调用 `SendMessage` |
| **P7** | outbound 必须由 **AssistedReplyService** 编排（未来 assisted 专用路径） |
| **P8** | merchant policy / template / approve / auto_allowed **不能绕过** final guard |
| **P9** | audit/snapshot/idempotency **before outbound failure → no-send** |
| **P10** | **DB failure 不 fallback legacy send** |
| **P11** | **non-test legacy unchanged** — `_send_reply` / `pdd_{shop_id}` 不变 |
| **P12** | **Doudian production not enabled** — 本集成规划仅 PDD assisted path 设计参考 |
| **P13** | **assisted / auto 默认 off** — flags 未显式开启时不发送 |

---

## 4. 组件职责边界（future）

```text
Handler (future assisted branch only · test/allowlisted shop)
    → AssistedReplyService.approve_pending(...)
        → PendingAssistedRepositorySQLite (14q)
        → AuditLogRepositorySQLite (14q)
        → evaluate_final_guard (14v pure fn)
        → SendDecisionRepositorySQLite (14n)
        → IdempotencyStore (15b planning)
        → OutboundResolver → SendMessage (future · service-owned only)

PreviewReplyLogService — preview zero-send · 不变
Legacy handler _send_reply (non-test) — 不变
Final Guard — decision only · 不 outbound
```

| 组件 | 14y 规划状态 |
|------|--------------|
| `evaluate_final_guard` | ✅ 14v implemented · pure function |
| `AssistedReplyService` skeleton | ✅ 14x implemented · no send |
| approve → outbound 完整序列 | 📋 本 phase |
| Idempotency / send lock | 📋 15b |
| Assisted send impl | 📋 15a planning only |

---

## 5. 何时从 `send_not_implemented` 升级为 outbound

| 条件 | 说明 |
|------|------|
| Phase | **15a+** 实现阶段 · 非 14y |
| flags | `PRODUCT_ASSISTED_SERVICE_ENABLED` + assisted send 专用子 flag（15a 定义） |
| shop scope | allowlisted test shop / 显式开启 assisted 的 shop · **非** non-test legacy |
| guard | `allowed_to_send=true` |
| pre-outbound | audit `final_guard_passed` + snapshot `merchant_confirm` + idempotency acquired + audit `outbound_send_attempted` 全部成功 |
| ownership | AssistedReplyService 独占 outbound 调用 · handler 只调 service |

**升级前 14x skeleton 保持：** guard allow → `guard_passed_but_send_not_implemented` · 无 outbound。

---

## 6. 文档索引（14y）

| 文档 | 内容 |
|------|------|
| [phase14y_approve_to_outbound_sequence.md](phase14y_approve_to_outbound_sequence.md) | approve → outbound 推荐顺序 |
| [phase14y_idempotency_and_state_transition.md](phase14y_idempotency_and_state_transition.md) | 状态机 · 幂等 |
| [phase14y_audit_snapshot_ordering.md](phase14y_audit_snapshot_ordering.md) | AuditLog · Snapshot 顺序 |
| [phase14y_failure_and_recovery_policy.md](phase14y_failure_and_recovery_policy.md) | 失败 · recovery · rollback |
| [phase14y_test_plan.md](phase14y_test_plan.md) | Y1–Y17 未来测试 |

---

## 7. 与 Final Guard 关系（14t 签收延续）

| 场景 | policy | guard | service | 结果 |
|------|--------|-------|---------|------|
| assisted approve + safe template | allow participate | pass | outbound attempt | 可尝试发送 |
| assisted approve + forbidden edit | allow participate | **block** | no outbound | no-send |
| guide_only + safe guide | allow | pass | outbound attempt | 可尝试发送 |
| auto_allowed + forbidden text | allow participate | **G22 block** | no outbound | no-send |

**Redline block 优先级高于 mode allow · guard block 优先级高于 merchant approve 意图。**

---

*Phase 14y · planning only · 2026-06-03*

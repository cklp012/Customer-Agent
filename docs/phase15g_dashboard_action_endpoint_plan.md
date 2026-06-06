# Phase 15g — Dashboard Action Endpoint Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不写代码** |
| 日期 | 2026-06-03 |
| 前置 | [phase15f_done.md](phase15f_done.md) · [phase15d_done.md](phase15d_done.md) · [phase14z_done.md](phase14z_done.md) |

---

## 1. Phase 15g 定位

| 项 | 结论 |
|----|------|
| 交付 | **仅文档** |
| Python 代码 | **未写** |
| approve / reject endpoint | **未实现** |
| live assisted send | **未实现** |
| auto send | **未实现** |
| handler / SendMessage / outbound | **未改** |
| PDD / Doudian 热路径 | **未改** |
| legacy database | **未改** |
| Dashboard API code（15d read skeleton） | **未改** |
| assisted / send flags | **默认 off** |

Phase 15g 规划未来 **Dashboard action endpoints**（approve · reject · 可选 expire/cancel）与 **15d read endpoints** 分离 — **本 phase 不写代码、不发送**。

---

## 2. 已实现基础（unchanged）

| 组件 | Phase | 状态 |
|------|-------|------|
| `PendingAssistedDashboardReadService` · GET list/detail | 15d | ✅ read-only |
| `AssistedReplyService.approve_pending` dry-run wire | 15f | ✅ `dry_run_would_send` · no send |
| `AssistedReplyService.reject_pending` | 14x | ✅ status + audit · no send |
| `approve_pending` live send | — | ❌ `live_send_not_implemented` when dry_run=false |

---

## 3. 核心原则（签收）

| # | 原则 |
|---|------|
| **G1** | Dashboard action endpoints **may request workflow transitions** — must **never bypass** `AssistedReplyService`, Final Guard, idempotency, or audit |
| **G2** | Action routes **不得**直接 `SendMessage` / outbound resolver / PDD / Doudian |
| **G3** | **Read 与 Action 分离** — GET（15d）vs POST approve/reject（future） |
| **G4** | **Approve 默认 dry-run only** — first implementation returns `would_send` · not live send |
| **G5** | **Reject** 仅 pending 状态 + audit · 不 final guard · 不 outbound |
| **G6** | **viewer 禁止** approve/reject |
| **G7** | **No fallback legacy send** |
| **G8** | **PDD legacy hot path 不变** · queue `pdd_{shop_id}` |
| **G9** | **Doudian production not enabled** |

---

## 4. 未来路由拓扑

```text
Dashboard UI
    → GET  /api/product/pending-assisted              (15d · read-only · implemented skeleton)
    → GET  /api/product/pending-assisted/{id}         (15d · read-only)
    → POST /api/product/pending-assisted/{id}/approve (15g planned · 15i skeleton · not in 15g)
    → POST /api/product/pending-assisted/{id}/reject  (15g planned · 15i skeleton · not in 15g)
    → POST /api/product/pending-assisted/{id}/expire  (optional · future)

Action route handler (future)
    → auth + CSRF + scope check
    → client_request_id dedupe
    → AssistedReplyService.approve_pending | reject_pending
        → Final Guard (approve only)
        → audit / snapshot / idempotency (approve dry-run · 15f)
        → DryRunAssistedOutboundPort (approve dry-run · 15f)
    → JSON response · no SendMessage
```

**Action route 不得 import handler / SendMessage / outbound resolver。**

---

## 5. 与 15d read 边界

| 维度 | Read（15d） | Action（15g planned） |
|------|-------------|----------------------|
| HTTP | GET only | POST only |
| Service | `PendingAssistedDashboardReadService` | `AssistedReplyService` |
| Mutations | ❌ | ✅ pending status / audit（via service） |
| Final guard | ❌ 不执行 | ✅ approve 经 service 执行 |
| Outbound | ❌ | ❌ dry-run port only（15f） |
| app.py 注册 | ❌ not registered | ❌ not in 15g |

---

## 6. 子文档索引

| 文档 | 内容 |
|------|------|
| [phase15g_approve_endpoint_contract.md](phase15g_approve_endpoint_contract.md) | POST approve contract |
| [phase15g_reject_endpoint_contract.md](phase15g_reject_endpoint_contract.md) | POST reject contract |
| [phase15g_permissions_csrf_idempotency.md](phase15g_permissions_csrf_idempotency.md) | RBAC · CSRF · replay |
| [phase15g_action_audit_and_response_codes.md](phase15g_action_audit_and_response_codes.md) | Audit actions · HTTP codes |
| [phase15g_dry_run_only_boundary.md](phase15g_dry_run_only_boundary.md) | Dry-run stage boundary |
| [phase15g_failure_rollback_policy.md](phase15g_failure_rollback_policy.md) | Failure · rollback |
| [phase15g_test_plan.md](phase15g_test_plan.md) | G1–G25 |

---

## 7. 明确不在本 phase

| 项 | Phase |
|----|-------|
| Action route implementation | **15i** skeleton |
| Live PDD outbound port | **15h** planning |
| client_request_id persistence skeleton | **15j** |
| Live assisted send | **later** |

---

*Phase 15g · docs only · 2026-06-03*

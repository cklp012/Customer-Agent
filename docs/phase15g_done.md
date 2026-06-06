# Phase 15g 完成 — Assisted Dashboard Action Endpoint Planning

| 项 | 内容 |
|----|------|
| 状态 | **docs only · action endpoint planned** |
| 日期 | 2026-06-03 |
| 前置 | [phase15f_done.md](phase15f_done.md) · [phase15d_done.md](phase15d_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 类型 | **仅文档** |
| approve / reject endpoint | **未实现** |
| live assisted send | **未实现** |
| auto send | **未实现** |
| handler / SendMessage / PDD / Doudian | **未改** |
| 15d read API | **未改** · read-only |

---

## 规划要点

| # | 要点 |
|---|------|
| 1 | **Read 与 Action 分离** — GET（15d）vs POST approve/reject（future） |
| 2 | Action **只能**调用 `AssistedReplyService` — 不 bypass guard/idempotency/audit |
| 3 | **First implementation must be dry-run only**（15i） |
| 4 | Approve 默认 `dry_run_would_send` · `live_send_attempted=false` |
| 5 | Reject 仅 status + audit · 无 guard/outbound |
| 6 | **viewer 禁止** · CSRF + client_request_id + expected_pending_status |
| 7 | **No fallback legacy send** |

---

## 文档清单

| 文档 | 内容 |
|------|------|
| [phase15g_dashboard_action_endpoint_plan.md](phase15g_dashboard_action_endpoint_plan.md) | 总体规划 |
| [phase15g_approve_endpoint_contract.md](phase15g_approve_endpoint_contract.md) | POST approve |
| [phase15g_reject_endpoint_contract.md](phase15g_reject_endpoint_contract.md) | POST reject |
| [phase15g_permissions_csrf_idempotency.md](phase15g_permissions_csrf_idempotency.md) | RBAC · CSRF · replay |
| [phase15g_action_audit_and_response_codes.md](phase15g_action_audit_and_response_codes.md) | Audit · HTTP |
| [phase15g_dry_run_only_boundary.md](phase15g_dry_run_only_boundary.md) | Dry-run boundary |
| [phase15g_failure_rollback_policy.md](phase15g_failure_rollback_policy.md) | Failure · rollback |
| [phase15g_test_plan.md](phase15g_test_plan.md) | G1–G25 |

---

## 下一步建议

| Phase | 内容 |
|-------|------|
| **15h** | ✅ Live PDD AssistedOutboundPort **planning** — [phase15h_done.md](phase15h_done.md) |
| **15i** | Dashboard action endpoint **dry-run skeleton** |
| **15j** | Action idempotency / `client_request_id` **skeleton** |
| **15k** | `LivePddAssistedOutboundPort` **skeleton planning only** |

---

*签收：Phase 15g · docs only · 2026-06-03*

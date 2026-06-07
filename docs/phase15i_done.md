# Phase 15i 完成 — Dashboard Action Endpoint Dry-run Skeleton

| 项 | 内容 |
|----|------|
| 状态 | **action route dry-run skeleton implemented** |
| 日期 | 2026-06-03 |
| 前置 | [phase15h_done.md](phase15h_done.md) · [phase15g_done.md](phase15g_done.md) · [phase15f_done.md](phase15f_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| approve / reject routes | ✅ skeleton in `pending_assisted_action_routes.py` |
| app.py registration | ❌ **not registered** |
| approve → `AssistedReplyService.approve_pending` | ✅ only |
| reject → `AssistedReplyService.reject_pending` | ✅ only |
| first implementation | ✅ **dry-run only** |
| live assisted send | ❌ **未实现** |
| auto send | ❌ **未实现** |
| SendMessage / PDD / Doudian outbound | ❌ **未调用** |
| handler integration | ❌ **未改** |
| `dry_run_expected=false` | → `dry_run_required` / `live_send_not_implemented` · **no live send** |

---

## Routes

| Method | Path | Handler |
|--------|------|---------|
| POST | `/api/product/pending-assisted/<id>/approve` | `handle_approve_pending_assisted` |
| POST | `/api/product/pending-assisted/<id>/reject` | `handle_reject_pending_assisted` |

---

## 安全 / dry-run 约束

| 约束 | 状态 |
|------|------|
| CSRF token required | ✅ placeholder validation |
| `confirm_checkbox=true` required | ✅ |
| viewer forbidden | ✅ |
| `dry_run_expected=true` required (approve) | ✅ |
| scope: workspace_id + shop_id match | ✅ |
| `expected_pending_status` optimistic concurrency | ✅ |
| forbidden body overrides (buyer_id etc.) | ✅ |
| route 不直接 final guard / audit / outbound / port | ✅ |
| `live_send_attempted=false` always | ✅ |

---

## 测试

`tests/test_pending_assisted_action_routes_dry_run.py` — **I1–I18**

---

## 下一步建议

| Phase | 内容 |
|-------|------|
| **15j** | Action idempotency / `client_request_id` **skeleton** |
| **15k** | `LivePddAssistedOutboundPort` **skeleton planning only** |
| **15l** | Register action routes for local dashboard **behind flags** |

---

*签收：Phase 15i · 2026-06-03*

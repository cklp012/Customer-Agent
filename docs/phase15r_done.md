# Phase 15r 完成 — Local Dashboard Smoke Test Script Skeleton

| 项 | 内容 |
|----|------|
| 状态 | **smoke script skeleton implemented** |
| 日期 | 2026-06-03 |
| 前置 | [phase15o_done.md](phase15o_done.md) · [phase15q_done.md](phase15q_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| Script | `scripts/smoke_dashboard_action_routes.py` |
| Run | `python scripts/smoke_dashboard_action_routes.py` |
| Tests | `tests/test_phase15r_smoke_script_skeleton.py` — R1–R16 |
| live assisted send | ❌ **未实现** |
| retry / reconciliation worker | ❌ **未实现** |
| SendMessage / PDD / Doudian outbound | ❌ **未调用** |
| handler / app.py | ❌ **未改** |
| DB schema | ❌ **无变更** |
| Temp DB | `temp/product_smoke_dashboard_action.db` only · cleaned after run |
| Env | **restored** after temporary flag checks |
| PDD queue | **`pdd_{shop_id}` 不变** |

---

## Script 检查项

| Check | 说明 |
|-------|------|
| `forbidden_imports_absent` | 脚本无 SendMessage/PDD/handler 等 import |
| `default_flags_safe` | dashboard off · send off · dry_run default |
| `pdd_queue_name_unchanged` | `pdd_shop123` |
| `import_no_db_side_effect` | import routes 不建 DB |
| `route_registration` | flag off=0 · flag on=2 routes |
| `dry_run_request_guards` | CSRF · dry_run_required |
| `dry_run_response_shape` | dry_run · no live_send · no provider id |
| `no_send_runtime` | SendMessage/handler mocks not called |

---

## 下一步建议

| Phase | 内容 |
|-------|------|
| **15s** | `OutboundPortSelector` skeleton · dry-run only |
| **15t** | Reconciliation schema implementation behind flags |
| **15u** | Live PDD send primitive **planning only** |

---

*签收：Phase 15r · 2026-06-03*

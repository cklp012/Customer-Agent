# Phase 15l 完成 — Register Action Routes Behind Flags

| 项 | 内容 |
|----|------|
| 状态 | **flag-gated action route registration implemented** |
| 日期 | 2026-06-03 |
| 前置 | [phase15i_done.md](phase15i_done.md) · [phase15j_done.md](phase15j_done.md) · [phase15k_done.md](phase15k_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| Flag | `PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED` · **default false** |
| Bootstrap | `apply_dashboard_action_route_bootstrap()` in `pending_assisted_action_routes.py` |
| app.py hook | calls bootstrap after `apply_app_startup_bootstrap()` |
| Default startup | **no routes registered** (flag off) |
| Flag on | registers POST approve/reject on Flask app (dry-run only) |
| live assisted send | ❌ **未实现** |
| auto send | ❌ **未实现** |
| SendMessage / PDD / Doudian outbound | ❌ **未调用** |
| DB schema changes | ❌ **无** |
| PDD queue | **`pdd_{shop_id}` 不变** |

---

## Flag

| Flag | 默认 | Helper |
|------|------|--------|
| `PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED` | **false** | `is_dashboard_action_routes_enabled()` |

Independent of read dashboard flags · assisted service flags · send flags.

---

## Registration behavior

| 场景 | 行为 |
|------|------|
| flag off | bootstrap returns False · no routes |
| flag on + Flask app available | `register_pending_assisted_action_routes(app)` |
| flag on + no Flask | safe no-op if Flask unavailable |
| registration failure | warning logged · startup continues |
| repeated registration | idempotent · no duplicate crash |

---

## 测试

`tests/test_pending_assisted_action_routes_registration.py` — **L1–L15**

---

## 下一步建议

| Phase | 内容 |
|-------|------|
| **15m** | ✅ `LivePddAssistedOutboundPort` **skeleton implementation** — [phase15m_done.md](phase15m_done.md) |
| **15n** | Live send **reconciliation planning** |
| **15o** | Local dashboard action route **smoke test / runbook** |

---

*签收：Phase 15l · 2026-06-03*

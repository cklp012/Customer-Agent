# Phase 15j 完成 — Dashboard Action Idempotency / client_request_id Skeleton

| 项 | 内容 |
|----|------|
| 状态 | **action idempotency skeleton implemented** |
| 日期 | 2026-06-03 |
| 前置 | [phase15i_done.md](phase15i_done.md) · [phase15g_permissions_csrf_idempotency.md](phase15g_permissions_csrf_idempotency.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| `DashboardActionIdempotencyRow` ORM | ✅ |
| `ActionIdempotencyRepositorySQLite` | ✅ acquire / complete / fail |
| Route integration | ✅ behind `PRODUCT_PERSISTENCE_WRITE_ACTION_IDEMPOTENCY` |
| same client_request_id + same payload | ✅ replay previous result |
| same client_request_id + different payload | ✅ 409 conflict |
| action routes | ✅ still dry-run only |
| live assisted send | ❌ **未实现** |
| auto send | ❌ **未实现** |
| SendMessage / PDD / Doudian outbound | ❌ **未调用** |
| handler integration | ❌ **未改** |
| app.py registration | ❌ **not registered** |
| flags | **default off** |

---

## Flag

| Flag | 默认 |
|------|------|
| `PRODUCT_PERSISTENCE_WRITE_ACTION_IDEMPOTENCY` | **false** |

Active when `PRODUCT_PERSISTENCE_ENABLED=true` **and** flag true.

---

## Repository

| Method | 行为 |
|--------|------|
| `acquire` | new → in_progress · same+completed → replay · same+in_progress → already_in_progress · different payload → conflict |
| `complete` | in_progress → completed · store response_json |
| `fail` | in_progress → failed · store error response |

---

## Route behavior

| 场景 | 行为 |
|------|------|
| flag off | 15i behavior unchanged |
| flag on + replay_completed | return stored http_status/body · no service call |
| flag on + already_in_progress | 409 |
| flag on + client_request_conflict | 409 |
| flag on + service success | complete idempotency |
| flag on + service exception | fail idempotency · 500 |

---

## 测试

- `tests/test_action_idempotency_repository.py`
- `tests/test_pending_assisted_action_routes_idempotency.py`

---

## 下一步建议

| Phase | 内容 |
|-------|------|
| **15k** | `LivePddAssistedOutboundPort` **skeleton planning only** |
| **15l** | Register action routes for local dashboard **behind flags** |
| **15m** | Action route CSRF/auth hardening **planning** |

---

*签收：Phase 15j · 2026-06-03*

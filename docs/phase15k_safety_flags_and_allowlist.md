# Phase 15k — Safety Flags and Allowlist

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15h_single_test_shop_live_gate.md](phase15h_single_test_shop_live_gate.md) · [phase15j_done.md](phase15j_done.md) |

---

## 1. 默认状态

| 项 | 默认 |
|----|------|
| `LivePddAssistedOutboundPort` | **不可用** |
| Live send | **never** without multi-gate pass |
| `PRODUCT_ASSISTED_SEND_DRY_RUN` | **true** |
| Action routes in app.py | **not registered** |

---

## 2. Live send 必要条件（ALL must pass · future 15m）

| # | Gate |
|---|------|
| 1 | `PRODUCT_PERSISTENCE_ENABLED=true` |
| 2 | `PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED=true` |
| 3 | `PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG=true` |
| 4 | `PRODUCT_PERSISTENCE_WRITE_SEND_DECISION=true` |
| 5 | `PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY=true` |
| 6 | `PRODUCT_PERSISTENCE_WRITE_ACTION_IDEMPOTENCY=true` |
| 7 | `PRODUCT_ASSISTED_SERVICE_ENABLED=true` |
| 8 | `PRODUCT_ASSISTED_SEND_ENABLED=true` |
| 9 | `PRODUCT_ASSISTED_SEND_DRY_RUN=false` |
| 10 | `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID` match pending.shop_id |
| 11 | `platform_id=pinduoduo` |
| 12 | final guard allowed |
| 13 | outbound idempotency acquired |
| 14 | manual dashboard approve only |

**任一 fail → service 不调用 live port · no-send**

---

## 3. Allowlist 推荐（future flags）

| Flag | 用途 |
|------|------|
| `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID` | **minimum** · shop match |
| `PRODUCT_ASSISTED_SEND_TEST_WORKSPACE_ID` | recommended · workspace match |
| `PRODUCT_ASSISTED_SEND_TEST_ACCOUNT_ID` | recommended · account match |
| `PRODUCT_ASSISTED_SEND_DAILY_CAP` | recommended · e.g. 3/day · enforced in **service** |

Port **不读取** allowlist — service 在调用 port 前 gate。

---

## 4. dry_run 规则

| 条件 | 行为 |
|------|------|
| `PRODUCT_ASSISTED_SEND_DRY_RUN=true` | **永远不** live outbound · `DryRunAssistedOutboundPort` only |
| route `dry_run_expected=true` (15i) | approve skeleton dry-run only until live phase |
| `dry_run=false` without live port | `live_send_not_implemented` |

---

## 5. 禁止路径

| 项 | 状态 |
|----|------|
| Non-allowlisted shop | **no-send** |
| Doudian `platform_id` | **reject** · live port never called |
| Auto send | **禁止** |
| Handler-triggered live port | **禁止** |

---

## 6. Rollout checklist（future · before first live）

| # | Check |
|---|-------|
| 1 | Dry-run audit logs reviewed on test shop |
| 2 | Action idempotency tested (15j) |
| 3 | Human sign-off |
| 4 | Daily cap configured |
| 5 | Rollback flags documented |

---

*Phase 15k · docs only · 2026-06-03*

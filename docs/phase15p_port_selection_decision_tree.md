# Phase 15p — Port Selection Decision Tree

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15p_live_port_selection_plan.md](phase15p_live_port_selection_plan.md) · [phase15k_safety_flags_and_allowlist.md](phase15k_safety_flags_and_allowlist.md) |

---

## 1. 决策树（ASCII）

```text
approve_pending reached (guard/idempotency pre-checks passed)
    │
    ├─ dry_run path (PRODUCT_ASSISTED_SEND_DRY_RUN=true OR route dry_run_expected=true)
    │       └─► DryRunAssistedOutboundPort  [TERMINAL · always for dry-run smoke]
    │
    ├─ platform_id != pinduoduo
    │       └─► no-send / DryRun only  [Doudian · others: never live]
    │
    ├─ auto_mode / non-manual approve
    │       └─► no live port  [auto send not enabled]
    │
    ├─ final_guard_allowed == false
    │       └─► no port selected  [already returned guard_blocked]
    │
    ├─ outbound idempotency NOT acquired
    │       └─► no port selected
    │
    ├─ reconciliation risk active (send_unknown / manual_review_required)
    │       └─► no port selected  [no retry via re-approve]
    │
    ├─ daily cap exceeded (future)
    │       └─► no port selected
    │
    ├─ live gate ALL true? (see §2)
    │       ├─ NO  → DryRunAssistedOutboundPort OR explicit no-send result
    │       └─ YES → LivePddAssistedOutboundPort (future impl only)
    │
    └─ default / any ambiguity
            └─► DryRunAssistedOutboundPort
```

**Never branch:** `LivePdd failed → SendMessage` · `timeout → auto retry port.send`

---

## 2. Future live candidate — ALL must be true

| # | Gate |
|---|------|
| 1 | `PRODUCT_PERSISTENCE_ENABLED=true` |
| 2 | `PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED=true` |
| 3 | `PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG=true` |
| 4 | `PRODUCT_PERSISTENCE_WRITE_SEND_DECISION=true` |
| 5 | `PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY=true` |
| 6 | `PRODUCT_PERSISTENCE_WRITE_ACTION_IDEMPOTENCY=true` |
| 7 | `PRODUCT_ASSISTED_SERVICE_ENABLED=true` |
| 8 | `PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED=true` |
| 9 | `PRODUCT_ASSISTED_SEND_ENABLED=true` |
| 10 | `PRODUCT_ASSISTED_SEND_DRY_RUN=false` |
| 11 | `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID` **matches** `pending.shop_id` |
| 12 | `platform_id == pinduoduo` |
| 13 | Actor action = **manual dashboard approve** (not auto) |
| 14 | `final_guard_allowed == true` |
| 15 | Outbound idempotency **acquired** |
| 16 | Daily cap **not** exceeded (future) |
| 17 | Reconciliation risk **not** active (not `send_unknown` / `manual_review_required`) |

**任一 false → 不得选择 `LivePddAssistedOutboundPort`。**

---

## 3. 明确规则

| 条件 | 选择 |
|------|------|
| `dry_run=true`（flag 或 request） | **永远** `DryRunAssistedOutboundPort` |
| Non-allowlisted shop | **永远** no live |
| `platform_id=doudian` | **永远** no live |
| Auto mode / handler trigger | **永远** no live（当前与未来初期） |
| Phase 15m 当前 | Live port 存在但返回 `live_send_not_implemented` · **未 wired** |

---

## 4. Default

| 状态 | Port |
|------|------|
| 生产默认 · flags off | `DryRunAssistedOutboundPort`（或 approve disabled） |
| 本地 smoke（15o） | `DryRunAssistedOutboundPort` |
| 15p 当下代码 | `DryRunAssistedOutboundPort` only |

---

## 5. Selector 输出（future enum · planning）

| Outcome | Port / behavior |
|---------|-----------------|
| `dry_run` | `DryRunAssistedOutboundPort` |
| `live_pdd` | `LivePddAssistedOutboundPort` |
| `no_send_guard` | 不调用 port · 已返回 guard |
| `no_send_idempotency` | 不调用 port |
| `no_send_policy` | 不调用 port · allowlist/cap/platform |
| `dry_run_fallback_safe` | 任何歧义 → DryRun · **never** legacy |

---

*Phase 15p · docs only · 2026-06-03*

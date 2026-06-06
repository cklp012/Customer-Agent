# Phase 15h — Single Test Shop Live Gate

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15e_flag_gate_and_allowlist_policy.md](phase15e_flag_gate_and_allowlist_policy.md) · [phase13c_single_test_shop_preview_plan.md](phase13c_single_test_shop_preview_plan.md) |

---

## 1. 默认状态

| 项 | 默认 |
|----|------|
| Live PDD port | **不可用** |
| `PRODUCT_ASSISTED_SEND_ENABLED` | **false** |
| `PRODUCT_ASSISTED_SEND_DRY_RUN` | **true** |
| `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID` | **empty** |
| Live outbound | **never** without explicit multi-gate pass |

**dry_run=true 一律不 live outbound** — 始终 `DryRunAssistedOutboundPort`。

---

## 2. Live send 必要条件（ALL must pass）

| # | Gate | 说明 |
|---|------|------|
| 1 | `PRODUCT_ASSISTED_SEND_ENABLED=true` | master switch |
| 2 | `PRODUCT_ASSISTED_SEND_DRY_RUN=false` | explicit live intent |
| 3 | `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID` match | pending.shop_id |
| 4 | `platform_id=pinduoduo` | PDD only · Doudian **拒绝** |
| 5 | workspace allowlist match | cross-workspace → no-send |
| 6 | account allowlist match | recommended |
| 7 | shop allowlist match | **至少** shop_id match |
| 8 | persistence writes enabled | audit/snapshot/idempotency |
| 9 | final guard allowed | service evaluates before port |
| 10 | idempotency acquired | in_progress before port |
| 11 | manual dashboard approve | **不允许 auto send** |
| 12 | dry-run logs reviewed | human sign-off before first live |

**非 allowlist 一律 no-send。** 任一 gate fail → service 不调用 live port。

---

## 3. Allowlist 推荐策略

| 层级 | 推荐 |
|------|------|
| Minimum | `shop_id` == `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID` |
| Recommended | `workspace_id` + `account_id` + `shop_id` + `platform_id=pinduoduo` **全部 match** |

Allowlist 校验在 **`AssistedReplyService`** — port 不做 policy 决策。

---

## 4. Rollout 流程（future）

```text
1. Enable dry-run on test shop (15f path)
2. Review dry_run_would_send audit logs (dashboard + audit table)
3. Human sign-off checklist
4. Set DRY_RUN=false + TEST_SHOP_ID + ENABLED=true (staging only)
5. First live: single manual approve · monitor audit
6. Daily cap enforced (e.g. 3 messages/day)
7. Expand only after reconciliation clean
```

---

## 5. Daily cap（初期推荐）

| 项 | 值 |
|----|-----|
| Cap | e.g. **3 messages/day** per test shop |
| Enforcement | **AssistedReplyService** · before port call |
| Exceeded | `rate_limited` · no-send · audit `assisted_send_daily_cap_exceeded` |
| Port | unaware of cap |

---

## 6. Auto send 禁止

| 项 | 状态 |
|----|------|
| Auto approve | ❌ **禁止** |
| Auto send on guard pass | ❌ **禁止** |
| Handler-triggered assisted send | ❌ **禁止** |
| Live send trigger | **Dashboard manual approve only** |

---

## 7. Doudian

| 项 | 状态 |
|----|------|
| Doudian live port | ❌ **not in scope** |
| `platform_id=doudian` | reject at service gate · port never called |

---

*Phase 15h · docs only · 2026-06-03*

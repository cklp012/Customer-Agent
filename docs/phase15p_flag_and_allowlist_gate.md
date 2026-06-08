# Phase 15p — Flag and Allowlist Gate

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15o_flag_matrix_and_safe_env.md](phase15o_flag_matrix_and_safe_env.md) · [phase15h_single_test_shop_live_gate.md](phase15h_single_test_shop_live_gate.md) |

---

## 1. Flag 评估顺序（selector · future）

评估在 **service 已确认** guard pass + idempotency acquired 之后：

```text
1. Kill switch: PRODUCT_ASSISTED_SEND_ENABLED == false  → DryRun / no-send
2. Dry run: PRODUCT_ASSISTED_SEND_DRY_RUN == true       → DryRunAssistedOutboundPort
3. Persistence + assisted service flags               → if any false → no live
4. Action routes enabled (dashboard manual path)        → if false → no live
5. platform_id == pinduoduo                           → else no live
6. allowlist: TEST_SHOP_ID matches pending.shop_id    → else no live
7. recommended: workspace_id / account_id match       → else no live (future strict)
8. daily cap                                          → else no live (future)
9. reconciliation risk inactive                       → else no live
10. All pass                                          → LivePddAssistedOutboundPort candidate
```

**Selector 不重新解析 route body 覆盖 flags。**

---

## 2. Allowlist 要求

| 级别 | Flag / 字段 | 15p 要求 |
|------|-------------|----------|
| **Minimum** | `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID` == `pending.shop_id` | 必须 |
| Recommended | `PRODUCT_ASSISTED_SEND_TEST_WORKSPACE_ID` == `pending.workspace_id` | 未来严格模式 |
| Recommended | `PRODUCT_ASSISTED_SEND_TEST_ACCOUNT_ID` == `pending.account_id` | 未来严格模式 |
| Platform | `pending.platform_id == pinduoduo` | 必须 |

**Test shop only** — 非 allowlist 店 **永远** no live port。

---

## 3. Kill switch（紧急）

| 动作 | 效果 |
|------|------|
| `PRODUCT_ASSISTED_SEND_ENABLED=false` | 强制 no live · selector → DryRun or disabled |
| `PRODUCT_ASSISTED_SEND_DRY_RUN=true` | 强制 DryRun |
| `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID=`（清空） | `would_assisted_send_live()` false |
| `PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED=false` | 可选 · 阻断 dashboard manual live path |

---

## 4. 不安全组合示例

| 组合 | 结果 |
|------|------|
| `SEND_ENABLED=true` + `DRY_RUN=true` | **DryRun only** |
| `DRY_RUN=false` + empty `TEST_SHOP_ID` | **no-send** · never live |
| Live requested + `platform_id=doudian` | **no-send** |
| `final_guard_allowed=false` | **no port** · guard_blocked 已返回 |
| Idempotency not acquired | **no port** |
| Idempotency conflict | **no port** |
| `send_unknown` pending | **no port** · manual review |
| `SEND_ENABLED=true` + persistence off | **no live** · inconsistent → DryRun/safe |

---

## 5. 与 route `dry_run_expected`

| Route body | Selector |
|------------|----------|
| `dry_run_expected=true`（15i 当前强制） | 即使 live flags on · service 走 **dry-run outbound path** · DryRun port |
| `dry_run_expected=false` | route 422 · selector **未到达** |

Live port selection 仅在 **future** route 允许 live 且 `DRY_RUN=false` 且全 gate pass 时发生 — **不在 15p 实现**。

---

## 6. Helper 对照

| Helper | Live port candidate |
|--------|---------------------|
| `would_assisted_send_live()` | necessary not sufficient |
| `is_assisted_dry_run_outbound_enabled()` | DryRun path |
| `is_assisted_send_test_shop_allowlisted(shop_id)` | necessary |
| `is_dashboard_action_routes_enabled()` | dashboard manual path |

---

*Phase 15p · docs only · 2026-06-03*

# Phase 15a — Single Test Shop Rollout

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase13c_single_test_shop_preview_plan.md](phase13c_single_test_shop_preview_plan.md) · [phase15a_assisted_send_implementation_plan.md](phase15a_assisted_send_implementation_plan.md) |

---

## 1. 总原则

| # | 原则 |
|---|------|
| R1 | **默认 off** — 所有 assisted send flags false |
| R2 | **只允许 single test shop** 首批 live send |
| R3 | **dry_run 先行** — 真实 outbound 前必须 dry_run 验证 |
| R4 | 非 allowlist shop → **no-send** |
| R5 | non-test legacy → **unchanged** |

---

## 2. Allowlist 维度

| 字段 | 必填 | 说明 |
|------|------|------|
| `workspace_id` | ✅ | 租户 |
| `shop_id` | ✅ | 单 test shop |
| `account_id` | ✅ | PDD 账号 |
| `platform_id` | ✅ | `pinduoduo` |

**四元组全部 match 才允许 assisted send path（dry_run 或 live）。**

来源：对齐 [product_gate_config.py](product_gate_config.py) test shop allowlist · 可 env 或 config file · 15b+ 实现细节。

---

## 3. 环境变量（规划）

| Flag | 默认 | 说明 |
|------|------|------|
| `PRODUCT_PERSISTENCE_ENABLED` | off | 总开关 |
| `PRODUCT_ASSISTED_SERVICE_ENABLED` | off | 14x write service |
| `PRODUCT_ASSISTED_SEND_ENABLED` | **off** | assisted **send** 主开关 |
| `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID` | empty | 单 shop allowlist |
| `PRODUCT_ASSISTED_SEND_DRY_RUN` | **true** | true → would_send only |

**子开关规则：** `PRODUCT_ASSISTED_SEND_ENABLED` 需 ENABLED + ASSISTED_SERVICE + allowlist match。

| dry_run | allowlist | 行为 |
|---------|-----------|------|
| true | match | would_send audit · **no** real outbound |
| true | no match | no-send |
| false | match | live outbound（future · 最后阶段） |
| false | no match | **no-send** |

---

## 4.  rollout 阶段

| 阶段 | 内容 | send? |
|------|------|-------|
| **1** | 15a docs only（当前） | ❌ |
| **2** | 15b idempotency skeleton | ❌ |
| **3** | 15c outbound dry-run port skeleton | would_send only |
| **4** | test shop dry_run E2E | would_send · no SendMessage |
| **5** | test shop **live** assisted send | ✅ single shop only |
| **6** | limited multi-shop | 单独 planning · 非 15a |

**每步：** 测试 gate + rollback plan + docs checkpoint。

---

## 5. Rollback per stage

| 阶段 | rollback |
|------|----------|
| 2–4 | `PRODUCT_ASSISTED_SEND_ENABLED=false` |
| 5 live | + `PRODUCT_ASSISTED_SEND_DRY_RUN=true` 紧急切 dry_run |
| any | preview mode 保持 · PDD legacy 不变 |

---

## 6. 与 preview 关系

| 模式 | reply_mode | send |
|------|------------|------|
| preview (13c test shop) | preview | **zero-send** |
| assisted pending | assisted | approve skeleton · 14x no send |
| assisted live (stage 5) | assisted | service-owned outbound · allowlist only |

**preview 与 assisted send 互斥路径 — 同消息不能双发。**

---

*Phase 15a · planning only · 2026-06-03*

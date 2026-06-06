# Phase 15e — Flag Gate and Allowlist Policy

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15e_live_assisted_send_integration_plan.md](phase15e_live_assisted_send_integration_plan.md) · [phase15a_single_test_shop_rollout.md](phase15a_single_test_shop_rollout.md) |

---

## 1. 默认安全 posture

| Flag / 配置 | 默认 | 含义 |
|-------------|------|------|
| `PRODUCT_ASSISTED_SERVICE_ENABLED` | **false** | AssistedReplyService 写路径 off |
| `PRODUCT_ASSISTED_SEND_ENABLED` | **false** | assisted send 总开关 off |
| `PRODUCT_ASSISTED_SEND_DRY_RUN` | **true** | 即使 send enabled，默认 dry-run |
| `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID` | **empty** | allowlist 空 → 无 shop 可 live send |
| `PRODUCT_PERSISTENCE_ENABLED` | **false** | product DB off |
| `PRODUCT_PERSISTENCE_WRITE_*` | **false** | 各写路径 off |

**默认组合 = 零 live outbound。** 15e 不修改任何 flag 解析代码。

---

## 2. Live send 所需 flags（全部 true / 满足）

| # | Flag | 用途 |
|---|------|------|
| 1 | `PRODUCT_PERSISTENCE_ENABLED` | product_gate.db 可用 |
| 2 | `PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED` | pending 读写 |
| 3 | `PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG` | audit append |
| 4 | `PRODUCT_PERSISTENCE_WRITE_SEND_DECISION` | snapshot append |
| 5 | `PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY` | idempotency lock |
| 6 | `PRODUCT_ASSISTED_SERVICE_ENABLED` | AssistedReplyService 激活 |
| 7 | `PRODUCT_ASSISTED_SEND_ENABLED` | send 路径激活 |
| 8 | `PRODUCT_ASSISTED_SEND_DRY_RUN` | **`false`** 才允许 live outbound |
| 9 | outbound port | **live implementation 显式注入**（非默认 DryRun） |

**任一缺失 → no-send。** 不 fallback legacy。

---

## 3. Test shop allowlist

| 项 | 规则 |
|----|------|
| 配置 | `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID`（未来可扩展为多 shop JSON · 15e 规划单 shop） |
| 匹配维度 | **workspace_id · shop_id · account_id · platform_id** 四元组 |
| 最低要求 | **`shop_id` 必须 match** allowlist |
| 非 allowlist | **no-send** · 即使其他 flags 全开 |
| empty allowlist | **no live send** |

```text
allowlist_match =
    PRODUCT_ASSISTED_SEND_TEST_SHOP_ID non-empty
    AND pending.shop_id == TEST_SHOP_ID
    AND pending.workspace_id == configured workspace (if set)
    AND pending.account_id == configured account (if set)
    AND pending.platform_id == configured platform (if set · default pinduoduo)
```

---

## 4. Live send gate 决策表

| 条件 | live outbound |
|------|---------------|
| assisted service disabled | ❌ |
| assisted send disabled | ❌ |
| dry_run=true | ❌ **永远不真实 outbound** · 仅 would_send |
| allowlist mismatch | ❌ |
| persistence write flag missing | ❌ |
| pending status invalid | ❌ |
| final guard blocked | ❌ |
| idempotency not acquired | ❌ |
| pre-outbound audit/snapshot failure | ❌ |
| **全部 pass + dry_run=false + live port** | ✅ attempt allowed |

---

## 5. dry_run vs live

| `DRY_RUN` | `SEND_ENABLED` | allowlist | 行为 |
|-----------|----------------|-----------|------|
| true | any | any | **DryRunAssistedOutboundPort** · would_send · no SendMessage |
| false | false | any | no-send |
| false | true | no | no-send |
| false | true | yes | live port attempt（future · 15h+） |

---

## 6. 与 dashboard read 隔离

| 路径 | 需要 SEND flags? |
|------|------------------|
| `PRODUCT_PERSISTENCE_READ_DASHBOARD` list/detail | **否** |
| Future approve/send action | **是** · 全部 live gate |

15d read API **不得**读取或修改 send flags 以触发 outbound。

---

## 7. Rollback 开关（见 failure doc）

紧急切回安全：

1. `PRODUCT_ASSISTED_SEND_ENABLED=false`
2. `PRODUCT_ASSISTED_SEND_DRY_RUN=true`
3. clear / rotate `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID`

Preview · dashboard read · PDD legacy **保持不变**。

---

*Phase 15e · docs only · 2026-06-03*

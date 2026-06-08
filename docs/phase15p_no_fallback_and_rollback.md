# Phase 15p — No Fallback and Rollback

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15k_no_fallback_and_hot_path_boundary.md](phase15k_no_fallback_and_hot_path_boundary.md) · [phase15o_rollback_checklist.md](phase15o_rollback_checklist.md) |

---

## 1. No fallback legacy send

| 场景 | 行为 |
|------|------|
| LivePdd port exception | **no** SendMessage fallback |
| LivePdd `unavailable` | no-send · audit · manual review later |
| Selector exception | no-send · safe error · **DryRun not auto-promoted to live** |
| Port `live_send_not_implemented` (15m) | no-send · 保持现状 |
| DryRun rejected | no legacy补发 |

**禁止路径：**

```text
LivePddAssistedOutboundPort.send failed
    → SendMessage.send_text   ❌
    → AIReplyHandler._send_reply   ❌
    → outbound_resolver   ❌
    → pdd_{shop_id} queue producer for assisted   ❌
```

---

## 2. Pre-selection no-send

| 条件 | 结果 |
|------|------|
| Final guard block | **no port selected** |
| Idempotency conflict | **no port selected** |
| Idempotency not acquired | **no port selected** |
| DB failure before port | **no port selected** |
| Pending terminal / unknown | **no port selected** |

---

## 3. Post-send（future）

| 结果 | 行为 |
|------|------|
| `timeout_unknown` | reconciliation / manual review · **no retry** · **no** second port selection on same key |
| `rejected_by_platform` | failed · no fallback |
| `validation_failed` | failed · no fallback |

---

## 4. Rollback

### 4.1 立即开关

| Flag | 值 |
|------|-----|
| `PRODUCT_ASSISTED_SEND_ENABLED` | false |
| `PRODUCT_ASSISTED_SEND_DRY_RUN` | true |
| `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID` | 清空 |
| `PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED` | false（可选） |

效果：selector **永远** DryRun 或 disabled · 即使代码已 wired live port。

### 4.2 保持不变

| 项 | 状态 |
|----|------|
| Read dashboard flags / routes | **可保持** |
| PDD legacy PyQt hot path | **unchanged** |
| Queue `pdd_{shop_id}` | **unchanged** |
| Handler / AutoReplyThread | **unchanged** |

### 4.3 回滚后验证

- `would_assisted_send_live()` → false
- `_outbound_port_instance()` 行为 → DryRun only（或 15p 前现状）
- 全量测试 green
- [phase15o_rollback_checklist.md](phase15o_rollback_checklist.md)

---

## 5. Selector 异常策略（future）

```text
try:
    port = selector.select(context)
except Exception:
    log warning
    return no_send_result  # NOT SendMessage
```

**不得** catch 后切换 legacy adapter。

---

*Phase 15p · docs only · 2026-06-03*

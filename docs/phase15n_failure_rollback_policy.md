# Phase 15n — Failure and Rollback Policy

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15h_failure_rollback_policy.md](phase15h_failure_rollback_policy.md) · [phase15e_failure_rollback_and_reconciliation.md](phase15e_failure_rollback_and_reconciliation.md) |

---

## 1. Failure 分类与响应

| Failure | 响应 | auto retry send? |
|---------|------|------------------|
| `timeout_unknown` | pending `send_unknown` → `manual_review_required` · reconciliation | ❌ |
| DB failure **after** platform success | danger state · manual review · reconciliation | ❌ |
| provider success · no `provider_message_id` | **仍可能已发送** · reconciliation | ❌ |
| platform query unavailable | stay `manual_review_required` · retry query only | ❌ |
| reconciliation task failure | audit · stay unknown · retry query | ❌ |
| `failed_before_send` | pending `send_failed` · 同 key terminal | ❌ |
| operator mis-mark | audit trail · escalation | ❌ auto |

---

## 2. timeout → no auto retry

| 规则 |
|------|
| 任何 `timeout_unknown` **不得**触发自动第二次 `port.send` |
| 不得由 AutoReply / queue consumer / handler 补发 |
| 仅 reconciliation 或 operator 推进状态 |
| reconciliation 查询可 backoff 重试 · **发送不可** |

---

## 3. DB failure after platform success

```text
platform may have sent
    local DB write failed (pending / idempotency / audit)
        → treat as danger state
        → pending: manual_review_required
        → idempotency: timeout_unknown or manual_review_required
        → audit: append failure + manual_review_required
        → trigger reconciliation (NOT resend)
```

**禁止：** 因 DB 失败而“再发一次”以修复状态。

---

## 4. provider_message_id 缺失

| 情况 | 处理 |
|------|------|
| port 返回 success 但无 id | 弱确认 · audit sent · reconciliation 补 id |
| timeout 且无 id | unknown · manual review |
| reconciliation 找到 id | 补写 audit · idempotency succeeded |

**缺失 id ≠ 未发送。**

---

## 5. Operator mistake mitigation

| 措施 |
|------|
| 每个 operator 动作 append audit |
| `confirm_checkbox` 必填 |
| RBAC · shop scope |
| audit timeline 可回溯 |
| optional **two-person approval**（future · 高风险 mark_sent） |
| `mark_confirmed_sent` 要求 `provider_message_id` 或平台截图 ref（future UI） |

---

## 6. Rollback 策略

### 6.1 紧急开关（immediate）

| 动作 | 效果 |
|------|------|
| `PRODUCT_ASSISTED_SEND_ENABLED=false` | 停止新 live send |
| `PRODUCT_ASSISTED_SEND_DRY_RUN=true` | 强制 dry-run path |
| `PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED=false` | 可选 · 禁用 action routes |

### 6.2 数据与流程

| 动作 | 效果 |
|------|------|
| unknown / manual_review pending | **保持** · 不批量 auto-retry |
| reconciliation docs / runbook | **保留** · 继续人工处理 |
| 已 `sent` 记录 | **不**回滚删除 · audit 保留 |

### 6.3 不变项

| 项 | 状态 |
|----|------|
| PDD legacy hot path | **unchanged** |
| Queue `pdd_{shop_id}` | **unchanged** |
| SendMessage default path | **unchanged** |
| Doudian | **not enabled** |
| handler | **unchanged** |

---

## 7. 恢复路径（post-rollback）

1. 清空 manual review 队列中的 unknown 项（reconciliation + operator）
2. 验证 dry-run audit 正常
3. 单店 allowlist 重新开启 live send（flags）
4. 人工 sign-off（15k rollout checklist）
5. **禁止**批量重发 unknown 项

---

*Phase 15n · docs only · 2026-06-03*

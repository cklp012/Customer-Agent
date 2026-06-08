# Phase 15n — Audit, Snapshot, and Status Updates

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15e_audit_snapshot_idempotency_order.md](phase15e_audit_snapshot_idempotency_order.md) |

---

## 1. Audit 原则

| 规则 |
|------|
| append-only · **不 mutate** 历史 audit 行 |
| 每条含 `actor_user_id` / `actor_role` / `trace_id` / timestamp |
| **no** token / cookie / credential / session raw value |
| reconciliation 与 operator 动作均写 audit |

---

## 2. Planned audit actions（future）

| Action | 触发时机 |
|--------|----------|
| `outbound_send_attempted` | idempotency acquired · **before** `port.send` |
| `outbound_send_timeout_unknown` | port 返回 `timeout_unknown` |
| `outbound_send_failed_before_send` | port 返回 `failed_before_send` / pre-wire failure |
| `outbound_send_failed_after_unknown` | reconciliation 确认 not sent after prior unknown |
| `reconciliation_started` | task 开始 |
| `reconciliation_confirmed_sent` | task 确认已发 |
| `reconciliation_confirmed_not_sent` | task 确认未发 |
| `reconciliation_still_unknown` | task 无法确认 |
| `manual_review_required` | pending 进入人工队列 |
| `operator_marked_sent` | 人工 mark_confirmed_sent |
| `operator_marked_not_sent` | 人工 mark_confirmed_not_sent |
| `operator_cancelled_pending` | 人工 cancel |

### 2.1 与 live success 对齐（future · 非 15n）

| Action | 时机 |
|--------|------|
| `outbound_send_succeeded` | port `sent` + provider_message_id |
| `outbound_send_rejected` | `rejected_by_platform` |

---

## 3. Snapshot / status 顺序（live approve · future）

```text
1. final guard pass
2. append SendDecisionSnapshot (immutable)
3. outbound idempotency acquire
4. audit: outbound_send_attempted
5. port.send
6. branch on platform_status:
     sent → audit success · pending sent · idempotency succeeded
     failed_before_send → audit failed_before_send · pending send_failed
     timeout_unknown → audit timeout_unknown · pending send_unknown
                         → pending manual_review_required (safe default)
     rejected → audit rejected · pending send_failed
```

---

## 4. Reconciliation audit 顺序

```text
reconciliation_started
    → (query platform + local)
    → one of:
        reconciliation_confirmed_sent
        reconciliation_confirmed_not_sent
        reconciliation_still_unknown
    → optional operator_* overlay
```

**Reconciliation 只 append — 不删除 `outbound_send_timeout_unknown`。**

---

## 5. Status update 规则

| 规则 |
|------|
| 单调：terminal `sent` 不可回退 `pending` |
| `send_unknown` 仅经 reconciliation 或 operator → `sent` / `send_failed` / `manual_review_required` |
| status 变更必须与 audit 成对 |
| idempotency status 与 pending status **一致化**（见 state machine） |
| DB 部分失败 → danger · manual review · **不**补发 |

---

## 6. SendDecisionSnapshot 规则

| 规则 |
|------|
| 在 outbound attempt **之前** 写入 |
| 含 guard 结果 · policy mode · template ref · **不含** secrets |
| reconciliation UI 只读展示 |
| 不随 reconciliation 修改 snapshot 内容 |

---

## 7. 敏感信息

| 禁止写入 audit |
|----------------|
| PDD cookie |
| MMS token |
| API key |
| session blob |
| 完整 credential JSON |

错误信息使用 dashboard-safe machine codes + 短描述。

---

*Phase 15n · docs only · 2026-06-03*

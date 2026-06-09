# Phase 15q — Status Transition Rules

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15n_unknown_outcome_state_machine.md](phase15n_unknown_outcome_state_machine.md) |

---

## 1. Outbound idempotency transitions

### Allowed

| From | To | Trigger |
|------|-----|---------|
| (acquire) | `in_progress` | service acquire |
| `in_progress` | `succeeded` | port sent + confirm |
| `in_progress` | `failed` | platform reject |
| `in_progress` | `failed_before_send` | pre-wire failure |
| `in_progress` | `timeout_unknown` | timeout |
| `in_progress` | `sent_unconfirmed` | weak success signal |
| `timeout_unknown` | `succeeded` | reconciliation confirmed_sent |
| `timeout_unknown` | `failed_before_send` | reconciliation confirmed_not_sent |
| `timeout_unknown` | `manual_review_required` | still_unknown / default |
| `sent_unconfirmed` | `succeeded` | reconciliation + provider id |
| `manual_review_required` | `succeeded` | operator_mark_confirmed_sent |
| `manual_review_required` | `failed` / `failed_before_send` | operator_mark_confirmed_not_sent |
| `manual_review_required` | `cancelled` | operator cancel |
| `*` (non-terminal) | `cancelled` | operator |

### Forbidden

| From | To | Reason |
|------|-----|--------|
| `timeout_unknown` | `in_progress` | **auto retry** via re-approve |
| `succeeded` | `in_progress` | terminal |
| `failed` | `in_progress` | same key |
| `manual_review_required` | `in_progress` | without **new key** |
| any | second `succeeded` | duplicate send |

---

## 2. Pending assisted transitions

### Allowed

| From | To | Trigger |
|------|-----|---------|
| `pending` | `approved_dry_run` | dry-run approve |
| `pending` | `send_in_progress` | live approve + acquire |
| `send_in_progress` | `sent` | success / reconciliation |
| `send_in_progress` | `send_failed` | failure |
| `send_in_progress` | `send_unknown` | timeout |
| `send_unknown` | `manual_review_required` | safe default |
| `manual_review_required` | `sent` | operator_mark_confirmed_sent |
| `manual_review_required` | `send_failed` | operator_mark_confirmed_not_sent |
| `manual_review_required` | `cancelled` | operator |
| `pending` | `rejected` | reject |
| `pending` | `expired` | TTL |
| (operator) | **new pending row** | create_new_pending_after_manual_decision |

### Forbidden

| From | To | Reason |
|------|-----|--------|
| `send_unknown` | `send_in_progress` | **auto** re-approve |
| `timeout_unknown` (idempotency) | live send | auto retry |
| `sent` | `pending` | terminal rollback |
| `rejected` | `pending` | terminal |
| `expired` | `pending` | terminal |
| `approved_dry_run` | `sent` | dry-run ≠ live sent |
| `manual_review_required` | live send | without new action + new key |

---

## 3. Cross-entity consistency

状态变更必须 **成对**（service transaction · future）：

```text
pending.send_unknown + idempotency.timeout_unknown + audit.timeout_unknown
    → reconciliation
    → pending.sent + idempotency.succeeded + audit.reconciliation_confirmed_sent
```

**不一致 → freeze assisted actions · manual inspection（见 rollback doc）。**

---

## 4. Audit 要求

每次 transition → append `audit_logs` with `before_state` / `after_state` JSON · 不 UPDATE 旧 audit。

---

*Phase 15q · docs only · 2026-06-03*

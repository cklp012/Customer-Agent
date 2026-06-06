# Phase 15e — Audit · Snapshot · Idempotency Order

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15e_assisted_service_live_sequence.md](phase15e_assisted_service_live_sequence.md) · [phase14y_audit_snapshot_ordering.md](phase14y_audit_snapshot_ordering.md) |

---

## 1. Before outbound（严格顺序）

| # | 步骤 | 组件 | 失败 → |
|---|------|------|--------|
| 1 | AuditLog **`assisted_approved`** | AuditLogRepository | no-send |
| 2 | **`evaluate_final_guard`** | 14v pure fn | no-send (block audit) |
| 3 | AuditLog **`final_guard_passed`** | AuditLogRepository | no-send |
| 4 | SendDecisionSnapshot **`merchant_confirm`** | SendDecisionRepository | **no outbound** |
| 5 | **idempotency acquire** `assisted_send:{id}` | OutboundIdempotencyRepository (15b) | **no outbound** |
| 6 | AuditLog **`outbound_send_attempted`** | AuditLogRepository | **no outbound call** |

**任一步失败 → 不调用 outbound port。** 不 fallback legacy send。

---

## 2. Idempotency acquire 结果

| existing status | acquire result | outbound |
|-----------------|----------------|----------|
| new key | acquired | allowed if prior steps ok |
| `in_progress` | `already_in_progress` | **no-send** |
| `succeeded` | `already_sent` | **no-send** |
| `failed` | `manual_review_required` | **no-send · 不自动 retry** |

---

## 3. After outbound

### Success path

| # | 步骤 |
|---|------|
| 1 | idempotency **`mark_succeeded`** · `provider_message_id`, `platform_status` |
| 2 | pending status → **`sent`** |
| 3 | AuditLog **`outbound_send_succeeded`** |

### Failure path

| # | 步骤 |
|---|------|
| 1 | idempotency **`mark_failed`** · `error_code`, `error_message` |
| 2 | pending status → **`failed`** |
| 3 | AuditLog **`outbound_send_failed`** |

---

## 4. Terminal states

| 状态 | 含义 | 可自动 retry? |
|------|------|---------------|
| pending `sent` | live success 终态 | ❌ |
| idempotency `succeeded` | 最多一次成功 send | ❌ duplicate → already_sent |
| idempotency `failed` | 需人工 | ❌ → manual_review_required |
| pending `failed` | outbound 失败 | ❌ 不 auto retry |

**sent 是终态。** failed 进入 **manual review**，不 silent retry。

---

## 5. Audit timeline（15d read）

Dashboard read (15d) 应展示完整 timeline，顺序 **created_at asc**：

```text
pending_assisted_created
→ assisted_approved
→ final_guard_passed | final_guard_blocked
→ (snapshot implicit in merchant_confirm phase)
→ outbound_send_attempted
→ outbound_send_succeeded | outbound_send_failed
```

Read path **不 re-run guard** · 只读 persisted audit。

---

## 6. dry_run 分支顺序差异

| 项 | live | dry_run |
|----|------|---------|
| pre-outbound 1–6 | 相同 | 相同 |
| port call | LivePdd | DryRun |
| idempotency mark | succeeded + provider id | succeeded null id OR policy TBD 15f |
| pending → sent | yes | **no** · keep pending |
| audit | outbound_send_succeeded | attempted + dry_run metadata |

---

## 7. 与 15b repository 对齐

| Method | When |
|--------|------|
| `acquire` | before port · step 5 |
| `mark_succeeded` | after live/dry-run port success |
| `mark_failed` | after live port failure |
| `get` | reconciliation only |

Repository **不 send** · **不写 audit** · 15e 不改 repository 代码。

---

*Phase 15e · docs only · 2026-06-03*

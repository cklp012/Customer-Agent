# Phase 15e — Assisted Service Live Sequence

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15e_live_assisted_send_integration_plan.md](phase15e_live_assisted_send_integration_plan.md) · [phase14y_approve_to_outbound_sequence.md](phase14y_approve_to_outbound_sequence.md) |

---

## 1. 范围

规划 **`AssistedReplyService.approve_pending`** 未来 **live send path** 顺序。  
**14x 当前行为不变：** guard allow → `guard_passed_but_send_not_implemented` · **no outbound**。

---

## 2. 逐步顺序（future live path）

### Step 0 — Gate

1. **Validate flags and allowlist** — 见 [flag_gate doc](phase15e_flag_gate_and_allowlist_policy.md)
2. **Validate actor role** — `operator` / `admin` / `owner` only

### Step 1 — Load & validate pending

3. **Load pending** by `pending_assisted_id`
4. **Validate ownership / status / expiry**
   - workspace match
   - status ∈ `{pending, approved}`（非 rejected/expired/sent/failed terminal）
   - not expired

### Step 2 — Approve intent audit

5. **Write AuditLog** `assisted_approved`
   - `target_type=pending_assisted`
   - `before_state` / `after_state` status transition intent
   - **失败 → no-send · 不继续**

### Step 3 — Final guard

6. **Build `FinalGuardInput`** from pending + actor + template/policy metadata
7. **`evaluate_final_guard`** (14v pure function)
8. **If block:**
   - Write AuditLog **`final_guard_blocked`**
   - Keep pending **not sent**
   - Return **no-send** · reason = block_code / block_reason
9. **If allow:**
   - Write AuditLog **`final_guard_passed`**
   - Continue ↓

### Step 4 — Snapshot

10. **Write SendDecisionSnapshot** `decision_phase=merchant_confirm`
    - **失败 → no-send · 不 outbound**

### Step 5 — Idempotency

11. **Acquire idempotency key** `assisted_send:{pending_assisted_id}`
    - `OutboundIdempotencyRepository.acquire` (15b)
    - **acquire fail** (`already_sent` / `already_in_progress` / `manual_review_required`) → **no-send**
    - **失败 → no outbound**

### Step 6 — Outbound attempt audit

12. **Write AuditLog** **`outbound_send_attempted`**
    - metadata: `dry_run`, `idempotency_key`, `trace_id`
    - **失败 → no outbound call**（lock 已持有时需 reconciliation · 见 failure doc）

### Step 7 — Outbound port

13. **Build `AssistedOutboundRequest`** (15c)
14. **Call `AssistedOutboundPort.send`**
    - default: **`DryRunAssistedOutboundPort`** · would_send only
    - future live: **`LivePddAssistedOutboundPort`**

#### 7a — dry_run branch

- **No real send**
- `platform_status=dry_run_would_send`
- pending status: **keep `pending`** or future `dry_run_would_send`（schema 扩展在 15f+ 规划 · 15e 不建表）
- AuditLog optional `outbound_send_attempted_dry_run` or metadata `dry_run=true`
- idempotency: **mark_succeeded** with `provider_message_id=null` · or release policy TBD in 15f

#### 7b — live success branch

15. **mark idempotency succeeded** — `provider_message_id`, `platform_status`
16. **mark pending status `sent`**
17. **Write AuditLog `outbound_send_succeeded`**

#### 7c — live failure branch

15. **mark idempotency failed** — error_code, error_message
16. **mark pending status `failed`**
17. **Write AuditLog `outbound_send_failed`**

---

## 3. 硬停止规则

| 失败点 | 行为 |
|--------|------|
| `outbound_send_attempted` audit 写失败 | **no outbound call** |
| SendDecisionSnapshot 写失败 | **no outbound** |
| idempotency acquire 失败 | **no outbound** |
| final guard block | **no outbound** |
| live success 后 final audit 写失败 | **recovery task · 不重发** |
| idempotency **failed** 重复 approve | **manual_review_required · 不自动 retry** |

---

## 4. 与 14x 差异

| 项 | 14x 当前 | future live |
|----|----------|-------------|
| guard pass 后 | `send_not_implemented` | idempotency + port |
| audit after guard | `assisted_approved` only | + passed + attempted + succeeded/failed |
| pending → sent | never | on live success |
| outbound | never | dry-run or live port |

---

## 5. 触发入口（future）

| 入口 | Phase |
|------|-------|
| Internal `approve_pending` call | 15f dry-run wire · 15h+ live |
| Dashboard POST approve/send | **15g planning only** |
| Handler direct | **禁止** |

---

*Phase 15e · docs only · 2026-06-03*

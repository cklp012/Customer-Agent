# Phase 14y — Audit and Snapshot Ordering

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14y_approve_to_outbound_sequence.md](phase14y_approve_to_outbound_sequence.md) · [phase14n_done.md](phase14n_done.md) · [phase14t_audit_snapshot_integration.md](phase14t_audit_snapshot_integration.md) |

---

## 1. AuditLog actions（approve / outbound 路径）

| action | 时机 | send? |
|--------|------|-------|
| `pending_assisted_created` | create_pending 成功 | ❌ |
| `assisted_approved` | merchant 点击 approve 意图（可在 guard 前或紧接 validate 后） | ❌ |
| `final_guard_passed` | `allowed_to_send=true` | ❌ |
| `final_guard_blocked` | `allowed_to_send=false` | ❌ |
| `outbound_send_attempted` | **实际 outbound 调用之前** | 即将 attempt |
| `outbound_send_succeeded` | platform send 成功 | 已发送 |
| `outbound_send_failed` | platform send 失败 | attempt 已发生 |
| `assisted_rejected` | reject_pending | ❌ |
| `assisted_expired` | expire_pending | ❌ |

**14x skeleton 已写：** `pending_assisted_created` · `assisted_approved` · `final_guard_blocked`  
**14x skeleton 未写：** `final_guard_passed` · `outbound_send_*` · `merchant_confirm` snapshot

---

## 2. SendDecisionSnapshot 阶段

| decision_phase | 时机 | 条件 |
|----------------|------|------|
| `ai_preview` | preview / assisted 建议生成 | 14n 已有 |
| `merchant_confirm` | approve + **final guard pass** 后 · outbound **前** | guard allow only |

**merchant_confirm 字段（规划）：**

- `allowed_to_send=true`
- `decision_source=final_guard`
- `block_code` / `block_reason` = null
- `policy_snapshot` / `template_snapshot` from guard result
- `pending_assisted_id` · `reply_log_id`

**guard block 时：** 写 snapshot optional（`allowed_to_send=false`）或仅 audit · **不写** merchant_confirm pass snapshot · **no outbound**

---

## 3. Approve 路径 Audit + Snapshot 顺序（strict）

```text
[optional] assisted_approved          — merchant intent
final_guard_passed OR final_guard_blocked
IF blocked → STOP

final_guard_passed
SendDecisionSnapshot merchant_confirm   — append-only
idempotency acquire
outbound_send_attempted                 — MUST before outbound
outbound (SendMessage)
outbound_send_succeeded OR outbound_send_failed
```

---

## 4. 失败与 ordering 规则

| 失败点 | send? | pending | recovery |
|--------|-------|---------|----------|
| assisted_approved audit fail (strict) | ❌ | pending | retry audit · no outbound |
| final_guard_blocked audit fail | ❌ | pending | log error · no outbound |
| final_guard_passed audit fail | ❌ | approved? | **no outbound** |
| merchant_confirm snapshot fail | ❌ | approved? | **no outbound** |
| idempotency acquire fail | ❌ | approved? | **no outbound** |
| outbound_send_attempted audit fail | ❌ | approved | **no outbound** · lock release |
| outbound fail | attempt | failed | audit failed · manual review |
| outbound success + succeeded audit fail | **已发送** | sent | **recovery task · no resend** |

**核心：audit/snapshot before outbound failure → no-send**

---

## 5. Dashboard detail timeline（future）

推荐展示顺序（新 → 旧或旧 → 新一致即可）：

1. outbound_send_succeeded / outbound_send_failed
2. outbound_send_attempted
3. SendDecisionSnapshot merchant_confirm
4. final_guard_passed / final_guard_blocked
5. assisted_approved
6. pending_assisted_created
7. ai_preview snapshot（link reply_log）

**block 场景：** 突出 `block_code` · `block_reason` · 无 outbound_send_attempted 行。

---

## 6. 14x → future 差异

|  artifact | 14x approve guard allow | future 15a+ |
|-----------|-------------------------|-------------|
| audit | `assisted_approved` only | + `final_guard_passed` + attempted + succeeded/failed |
| snapshot | 无 | `merchant_confirm` |
| outbound_send_attempted | **禁止** | **必须** |

---

*Phase 14y · planning only · 2026-06-03*

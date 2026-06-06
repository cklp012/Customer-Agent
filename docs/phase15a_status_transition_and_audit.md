# Phase 15a — Status Transition and Audit

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14y_approve_to_outbound_sequence.md](phase14y_approve_to_outbound_sequence.md) · [phase15a_idempotency_lock_contract.md](phase15a_idempotency_lock_contract.md) |

---

## 1. 状态转换

```text
pending ──approve──► approved ──outbound ok──► sent (terminal)
   │                      │
   │                      └──outbound fail──► failed
   ├──reject──► rejected (terminal)
   ├──expire──► expired (terminal)
   └──cancel──► canceled (terminal)

failed → manual_review (default · no auto retry → sent)
sent / rejected / expired / canceled → 终态
```

| 转换 | 触发 | outbound? |
|------|------|-----------|
| pending → approved | approve 通过 pre-checks · pre-outbound | 尚未 |
| approved → sent | outbound success + mark_succeeded | ✅ 完成 |
| approved → failed | outbound failure | attempt 已发生 |
| pending → rejected | reject_pending | ❌ |
| pending → expired | expire_pending | ❌ |
| pending → canceled | cancel API | ❌ |

**14x 现状：** approve **不**写 approved/sent · 仅 skeleton audit。

---

## 2. Audit 顺序（strict · future live send）

```text
1. assisted_approved              — merchant approve 意图
2. final_guard_passed             — allowed_to_send=true
   OR final_guard_blocked          — STOP
3. send_decision_snapshot_written — merchant_confirm (append-only)
4. idempotency_lock_acquired      — optional dedicated audit or metadata
5. outbound_send_attempted        — MUST before real outbound
6. outbound_send_succeeded        — on platform success
   OR outbound_send_failed        — on platform failure
```

**dry_run 路径：** step 5 metadata `dry_run=true` · 无 step 6 live · status 不变或 `would_send` audit only。

---

## 3. 关键规则

| # | 规则 |
|---|------|
| S1 | **`outbound_send_attempted` 必须在真实 outbound 前写入** |
| S2 | `outbound_send_attempted` 写失败 → **no-send** · release lock |
| S3 | outbound success → pending **status=sent** · lock **succeeded** |
| S4 | outbound failure → pending **status=failed** · lock **failed** |
| S5 | outbound success 后 `outbound_send_succeeded` audit 失败 → **recovery task · no resend** |
| S6 | **sent 是终态** — duplicate approve → already_sent |
| S7 | **failed 默认 manual review** — no auto retry |

---

## 4. SendDecisionSnapshot

| 字段 | 时机 |
|------|------|
| `decision_phase=merchant_confirm` | step 3 · guard pass 后 |
| `allowed_to_send=true` | guard pass |
| `policy_snapshot` / `template_snapshot` | from guard result |
| `pending_assisted_id` | link |

snapshot 写失败 → **no outbound**（strict）。

---

## 5. 14x vs future

| 步骤 | 14x | future 15b+ |
|------|-----|-------------|
| assisted_approved | ✅ | ✅ |
| final_guard_passed | ❌ | ✅ |
| merchant_confirm snapshot | ❌ | ✅ |
| idempotency acquire | ❌ | ✅ |
| outbound_send_attempted | ❌ | ✅ |
| outbound call | ❌ | ✅ dry_run or live |
| status → sent | ❌ | ✅ on success |

---

*Phase 15a · planning only · 2026-06-03*

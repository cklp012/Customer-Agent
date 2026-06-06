# Phase 14y — Approve to Outbound Sequence

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14y_final_guard_assisted_integration_plan.md](phase14y_final_guard_assisted_integration_plan.md) · [phase14x_done.md](phase14x_done.md) · [phase14v_done.md](phase14v_done.md) |

---

## 1. 范围

规划 **`AssistedReplyService.approve_pending`** 未来从 14x skeleton 升级为 **真实 outbound** 时的推荐顺序。

| 项 | 结论 |
|----|------|
| 14x 现状 | guard allow → `guard_passed_but_send_not_implemented` · **无 outbound** |
| 14y | 只规划 · **不写代码** |
| 实现 phase | 15a+ |

---

## 2. 推荐顺序（strict · 默认）

```text
1. validate actor role
       viewer → permission_denied · STOP
2. load pending (pending_assisted_id)
       not found → STOP
3. validate pending status / expiry / ownership
       terminal / expired / ownership mismatch → STOP
4. build FinalGuardInput (final_reply, policy, template, channel, idempotency fields)
5. evaluate_final_guard(ctx)
6. if block (allowed_to_send=false):
       write AuditLog final_guard_blocked
       keep pending NOT sent (status unchanged or approved-without-send per policy)
       return no-send
7. if allow (allowed_to_send=true):
       write AuditLog final_guard_passed
       write SendDecisionSnapshot decision_phase=merchant_confirm
       acquire idempotency / send lock (pending_assisted_id-based)
       write AuditLog outbound_send_attempted
       call outbound (SendMessage · service-owned · assisted path only)
       if success:
           update pending status=sent
           write AuditLog outbound_send_succeeded
       if failure:
           update pending status=failed
           write AuditLog outbound_send_failed
           no auto retry by default
```

---

## 3. 步骤详解

### 3.1 Steps 1–3 — 前置校验

| 检查 | fail 行为 |
|------|-----------|
| `actor_role` ∉ {operator, admin, owner} | `permission_denied` · no-send |
| pending 不存在 | `pending_not_found` · no-send |
| status ∈ {sent, rejected, expired, canceled} | `terminal_state` · no-send |
| `now > expires_at` | `pending_expired` · no-send |
| actor workspace/shop ≠ pending context | `ownership_mismatch` · no-send |

**可选：** Step 1 后写 `assisted_approved` 记录 merchant 点击 approve 意图（见 audit ordering doc）。14x skeleton 在 guard 后写 `assisted_approved`；15a 可调整为 guard 前记录意图 + guard 后记录结果。

### 3.2 Step 4–5 — Final Guard

- 组装 `FinalGuardInput` · 调用 `evaluate_final_guard`（14v · 纯函数 · 无 I/O）
- **handler 不参与此步骤**

### 3.3 Step 6 — Guard block

| 动作 | 说明 |
|------|------|
| AuditLog | `final_guard_blocked` · 含 `block_code` / `block_reason` |
| pending | **不**更新为 sent · 不调用 outbound |
| return | `success=false` · `status=guard_blocked` |

### 3.4 Step 7 — Guard allow（future outbound path）

| 子步骤 | 必须成功才能继续 | fail → |
|--------|------------------|--------|
| 7a AuditLog `final_guard_passed` | ✅ | no-send |
| 7b SendDecisionSnapshot `merchant_confirm` | ✅（strict） | no-send |
| 7c idempotency acquire | ✅ | no-send |
| 7d AuditLog `outbound_send_attempted` | ✅（strict） | no-send · **不得**调用 outbound |
| 7e outbound call | — | status=failed · audit failed |

---

## 4. 关键约束

| # | 约束 |
|---|------|
| S1 | **`outbound_send_attempted` 必须在实际 outbound 调用之前写入** |
| S2 | 若 `outbound_send_attempted` audit **写失败** → **不能发送** |
| S3 | 若 SendDecisionSnapshot `merchant_confirm` **写失败** → **不能发送** |
| S4 | 若 idempotency acquire **失败** → **不能发送** |
| S5 | outbound unavailable（guard G26 或 channel probe）→ **不能发送** |
| S6 | outbound success 后 audit `outbound_send_succeeded` 失败 → **recovery task** · **不得重发** |
| S7 | final guard pass **仅允许尝试** outbound · **不等于** platform send 成功 |

---

## 5. 14x vs future 对比

| 步骤 | 14x skeleton | future (15a+) |
|------|--------------|---------------|
| role / pending validate | ✅ | ✅ |
| evaluate_final_guard | ✅ | ✅ |
| guard block + audit | ✅ `final_guard_blocked` | ✅ |
| guard allow | `assisted_approved` + return `send_not_implemented` | + snapshot + idempotency + attempted + outbound |
| outbound_send_attempted | ❌ 不写 | ✅ 写 |
| status → sent | ❌ | ✅ on success |
| SendMessage | ❌ | ✅ service only |

---

## 6. Handler 契约（future）

```text
# Handler MUST NOT:
- call evaluate_final_guard directly
- call SendMessage directly on assisted path

# Handler MAY:
- call AssistedReplyService.approve_pending(...)
- interpret AssistedServiceResult.status
- show Dashboard / toast based on block_code
```

---

*Phase 14y · planning only · 2026-06-03*

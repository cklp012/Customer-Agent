# Phase 14r — Approve / Reject / Expire Service Flow

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 未实现** |
| 对齐 | [phase14r_assisted_service_plan.md](phase14r_assisted_service_plan.md) · [phase14p_assisted_approve_reject_flow.md](phase14p_assisted_approve_reject_flow.md) |

---

## 1. Approve Flow（`approve_pending`）

### 1.1 前置校验

| 检查 | 失败响应 |
|------|----------|
| `actor_role` ∈ {operator, admin, owner} | 403 · viewer **不能** approve |
| workspace / shop ownership 匹配 pending | 403 |
| pending exists | 404 |
| `status == pending` | 409 · invalid_state |
| `expires_at > now` | 403 · expired |
| `status != sent` | 409 · already_sent |
| `intent_bucket == blocked`（无 elevated） | 403 · blocked |
| `intent_bucket == uncertain` 且无 edit | 400 · edit_required |

### 1.2 可选 merchant edit

```
if final_reply or merchant_edited_reply provided:
    persist merchant_edited_reply
    send_text = merchant_edited_reply
else:
    send_text = ai_suggested_reply
```

### 1.3 Approve 步骤（service 层）

```
approve_pending(pending_assisted_id, actor, final_reply?)
  1. validate actor / state / expiry / intent rules
  2. mark_status(pending, approved, approved_by=actor)  — 或乐观锁 transition
  3. AuditLog assisted_approved
  4. re-classify optional + run final_guard(send_text, context)
  5. if guard blocked:
         AuditLog final_guard_blocked
         **no outbound · no SendMessage**
         return ApproveResult(sent=False, reason=guard_reason)
  6. if guard passed:
         AuditLog final_guard_passed
         SendDecisionSnapshot merchant_confirm (append-only)
  7. AuditLog outbound_send_attempted
  8. outbound.send_text(...)  — **唯一 SendMessage 入口（assisted path）**
  9. if success:
         status=sent · final_reply=send_text
         AuditLog outbound_send_succeeded
     else:
         status=failed
         AuditLog outbound_send_failed
  10. return ApproveResult(sent=..., pending_assisted_id=...)
```

**关键：**

- **final guard pass 后才 outbound send**
- **approve 不等于 sent** — 步骤 9 成功才 `sent`
- outbound failure → `status=failed` · **不 auto retry**

---

## 2. Reject Flow（`reject_pending`）

```
reject_pending(pending_assisted_id, actor, reason?)
  1. validate actor_role ∈ {operator, admin, owner}
  2. validate status == pending
  3. mark_status(rejected, rejected_by=actor)
  4. AuditLog assisted_rejected
  5. **不调用** SendMessage / outbound / _send_reply
  6. return RejectResult(rejected=True)
```

| 检查 | 失败 |
|------|------|
| viewer | 403 |
| status != pending | 409 |
| already sent | 409 |

---

## 3. Expire Flow（`expire_pending`）

```
expire_pending(pending_assisted_id)  — system job or lazy on read/approve
  1. if status != pending: skip
  2. if expires_at >= now: skip
  3. mark_status(expired)
  4. AuditLog assisted_expired
  5. **不发送**
```

| 规则 | 说明 |
|------|------|
| expired 不可 approve | approve 前置检查 403 |
| lazy expire | list/approve API 触发检测 acceptable |
| background job | optional future |

---

## 4. 权限摘要

| 角色 | approve | reject |
|------|---------|--------|
| viewer | ❌ | ❌ |
| operator | ✅ | ✅ |
| admin | ✅ | ✅ |
| owner | ✅ | ✅ |

---

## 5. Intent 规则（approve 时）

| intent_bucket | approve |
|---------------|---------|
| allowed | ✅ + final guard |
| blocked | ❌ 普通 operator |
| uncertain | ✅ 仅当 `merchant_edited_reply` 有效 |

---

## 6. 与 handler 边界

| 层 | 职责 |
|----|------|
| Handler | 调用 `create_pending_from_preview` only（future） |
| AssistedReplyService | approve/reject/expire · guard · outbound |
| Handler | **不**直接 import pending/audit repository |

---

## 7. API 形状（future · 非 14r）

| Method | Path | 14r |
|--------|------|-----|
| POST | `/api/product/pending-assisted/{id}/approve` | ❌ |
| POST | `/api/product/pending-assisted/{id}/reject` | ❌ |

14r 仅规划 service contract · HTTP 属 14t+。

---

*Phase 14r · planning only · 2026-06-03*

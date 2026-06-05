# Phase 14p — Assisted Approve / Reject Flow

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 未实现** |
| 对齐 | [phase14p_auditlog_pending_assisted_plan.md](phase14p_auditlog_pending_assisted_plan.md) · [phase13f_assisted_confirmation_flow.md](phase13f_assisted_confirmation_flow.md) |

---

## 1. 总览

Assisted mode（**future · 未实现**）在 preview 生成建议后，引入 **人工确认** 环节。本 flow **不修改** 当前 test shop preview zero-send 路径。

```
Preview → Pending → Approve/Reject/Expire → Final Guard → Outbound → Snapshot → Audit
```

---

## 2. Preview / Suggestion（当前 partial · 14i–14n）

| 步骤 | 行为 | 当前状态 |
|------|------|----------|
| AI 生成建议 | `_get_ai_reply` | ✅ test shop |
| ReplyLog | `PreviewReplyLogService.record_preview` | ✅ shadow optional |
| SendDecisionSnapshot | `decision_phase=ai_preview` | ✅ shadow optional |
| PendingAssistedReply | `status=pending` | ❌ **未实现** |
| AuditLog | `pending_assisted_created` | ❌ **未实现** |
| SendMessage | — | ❌ preview **zero-send** |

**Assisted mode 扩展（future）：**

- `reply_mode=assisted` 时，在 ReplyLog + snapshot 之后创建 `PendingAssistedReply status=pending`
- 写 `AuditLog action=pending_assisted_created`
- **仍不发送**，等待 Dashboard approve

---

## 3. Approve Flow（future）

### 3.1 前置检查

| 检查 | 失败 |
|------|------|
| `actor_role` ∈ {operator, admin, owner} | 403 · viewer **不能** approve |
| `status == pending` | 409 · 已处理 |
| `expires_at > now` | 403 · expired |
| `status != sent` | 409 · 已发送 |
| `intent_bucket != blocked`（或 elevated） | 403 · blocked 禁止普通 approve |
| `intent_bucket == uncertain` → 须 edit | 400 · 须 `merchant_edited_reply` |

### 3.2 Approve 步骤

```
1. 权限校验 (operator/admin/owner)
2. 加载 PendingAssistedReply + ReplyLog
3. merchant 直接 approve 或 edit 后 approve
      → 更新 merchant_edited_reply（如有）
      → status = approved（或 approved_pending_send）
4. AuditLog assisted_approved
5. Final guard（见 permissions doc）
      → fail: AuditLog final_guard_blocked · **no send · stop**
      → pass: AuditLog final_guard_passed
6. Outbound send（SendMessage · future assisted path only）
      → AuditLog outbound_send_attempted
      → success: status=sent · final_reply 填充 · AuditLog outbound_send_succeeded
      → failure: status=failed · AuditLog outbound_send_failed · **no retry auto**
7. SendDecisionSnapshot decision_phase=merchant_confirm（append-only）
8. ReplyLog send_status 更新（future · 非 14p）
```

**关键：**

- **approved ≠ sent** — 步骤 6 成功前不得标记 sent
- **final guard 失败不得发送**
- blocked intent **不能**普通 approve

---

## 4. Reject Flow（future）

```
1. 权限校验 (operator/admin/owner) · viewer 不能 reject
2. status must be pending
3. status → rejected
4. rejected_by = actor_user_id
5. AuditLog assisted_rejected
6. **不调用** SendMessage / outbound / _send_reply
7. ReplyLog 保持 not_sent_* （不改为 sent）
```

---

## 5. Expire Flow（future）

```
1. 定时或 read-time 检测 expires_at < now
2. status pending → expired
3. AuditLog assisted_expired
4. expired **不可** approve
5. **不发送**
```

**触发方式（规划）：**

- background job（future）
- approve API 前置检查（必须）
- Dashboard list 展示 expired badge

---

## 6. Cancel Flow（optional · 规划）

| 场景 | status |
|------|--------|
| 新买家消息 supersede | `canceled`（或 future `superseded`） |
| admin 强制取消 | `canceled` |

不发送 · 写 audit（扩展 action 可选）。

---

## 7. 与当前 runtime 边界

| 路径 | 14p 行为 |
|------|----------|
| test shop preview | zero-send · 无 pending · 无 approve API |
| non-test legacy | `_send_reply` legacy · **不受影响** |
| Doudian | 无 production assisted · **不受影响** |
| handler | **不直接** import pending/audit repository |

---

## 8. API 形状（规划 · 14r+ · 非 14p）

| Method | Path | 14p |
|--------|------|-----|
| POST | `/api/product/pending-assisted/{id}/approve` | ❌ 不实现 |
| POST | `/api/product/pending-assisted/{id}/reject` | ❌ 不实现 |

14o 仅 GET read skeleton；approve/reject 属 future phase。

---

*Phase 14p · planning only · 2026-06-03*

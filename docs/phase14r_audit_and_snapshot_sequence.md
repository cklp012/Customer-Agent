# Phase 14r — Audit and Snapshot Sequence

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14r_approve_reject_service_flow.md](phase14r_approve_reject_service_flow.md) · [phase14n_done.md](phase14n_done.md) |

---

## 1. Audit action 清单

| action | 触发 |
|--------|------|
| `pending_assisted_created` | create pending 成功 |
| `assisted_approved` | merchant approve 意图确认 |
| `assisted_rejected` | merchant reject |
| `assisted_expired` | pending 超时 |
| `final_guard_passed` | final guard 通过 |
| `final_guard_blocked` | final guard 拒绝 · **未发送** |
| `outbound_send_attempted` | 调用 outbound 前 |
| `outbound_send_succeeded` | SendMessage 成功 |
| `outbound_send_failed` | SendMessage 失败 |

---

## 2. SendDecisionSnapshot 阶段

| decision_phase | 时机 |
|----------------|------|
| `ai_preview` | preview/assisted 建议生成（14n · handler/service record 路径） |
| `merchant_confirm` | approve + final guard **pass** 后 · outbound **前** |

**merchant_confirm 写入条件：** guard pass · **非** guard block · **非** reject/expired。

---

## 3. Create Pending 顺序

```
1. ReplyLog (+ optional shadow)
2. SendDecisionSnapshot ai_preview (+ optional shadow)
3. PendingAssistedReply status=pending
4. AuditLog pending_assisted_created
— no outbound —
```

| 步骤 fail | send |
|-----------|------|
| 3 fail | ❌ |
| 4 fail (strict) | ❌ · rollback 3 |

---

## 4. Approve 推荐顺序（strict · 默认）

```
1. validate actor / state / expiry / intent
2. transition pending → approved (or record approval_intent)
3. AuditLog assisted_approved
4. run final_guard
5. if blocked:
       AuditLog final_guard_blocked
       STOP — no snapshot merchant_confirm · no outbound
6. if passed:
       AuditLog final_guard_passed
7. SendDecisionSnapshot merchant_confirm (append-only)
8. AuditLog outbound_send_attempted
9. call outbound (SendMessage · assisted path only)
10. if success:
        AuditLog outbound_send_succeeded
        status → sent
    else:
        AuditLog outbound_send_failed
        status → failed
```

---

## 5. Reject / Expire 顺序

**Reject:**

```
1. validate actor / status=pending
2. status → rejected
3. AuditLog assisted_rejected
— no guard · no snapshot merchant_confirm · no outbound —
```

**Expire:**

```
1. detect expires_at < now · status=pending
2. status → expired
3. AuditLog assisted_expired
— no outbound —
```

---

## 6. Failure 与顺序约束

| 失败点 | 默认策略 | send |
|--------|----------|------|
| audit before outbound (step 3–8) | **阻止发送** | ❌ |
| snapshot merchant_confirm fail (step 7) | **阻止发送**（推荐） | ❌ |
| guard block (step 5) | 已 audit · 不 outbound | ❌ |
| outbound fail (step 9) | audit failed · status failed | 已 attempt · 不重发 |
| audit after outbound success (step 10) | **recovery task** · 不重发 | 已成功 · 不可撤销 |

### 6.1 Audit failure before outbound

**推荐：strict block**

```
if not append_audit(outbound_send_attempted):
    abort before outbound
    return failure — no SendMessage
```

### 6.2 Snapshot failure before outbound

**推荐：block send**

```
if not write_snapshot(merchant_confirm):
    abort before outbound
    AuditLog optional snapshot_write_failed (extension)
    return failure — no SendMessage
```

Degraded mode 需 explicit flag · 默认 **off**。

### 6.3 Outbound success + audit failure

- 发送 **不可逆**
- 异步补写 audit · alert ops
- **禁止** 因 audit fail 重发

---

## 7. before_state / after_state 建议

| action | before_state | after_state |
|--------|--------------|-------------|
| assisted_approved | `{status: pending}` | `{status: approved}` |
| final_guard_blocked | `{status: approved}` | `{guard: blocked, reason}` |
| outbound_send_succeeded | `{status: approved}` | `{status: sent, final_reply}` |

**禁止** 存 password / token / cookie。

---

## 8. 与 14q repository 映射

| 顺序步骤 | Repository |
|----------|------------|
| pending create | `PendingAssistedRepositorySQLite.create_pending` |
| audit | `AuditLogRepositorySQLite.append_audit_log` |
| merchant_confirm | `SendDecisionRepositorySQLite.create_snapshot` |
| status update | `PendingAssistedRepositorySQLite.mark_status` |

Service 编排顺序 · repository **无** send 逻辑。

---

*Phase 14r · planning only · 2026-06-03*

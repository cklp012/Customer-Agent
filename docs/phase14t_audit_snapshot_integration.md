# Phase 14t — Audit and Snapshot Integration

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14r_audit_and_snapshot_sequence.md](phase14r_audit_and_snapshot_sequence.md) · [phase14s_policy_snapshot_and_audit.md](phase14s_policy_snapshot_and_audit.md) |

---

## 1. AuditLog actions

| action | when | target |
|--------|------|--------|
| `final_guard_passed` | `allowed_to_send=true` | pending_assisted / reply_log |
| `final_guard_blocked` | `allowed_to_send=false` | pending_assisted / reply_log |

**append-only** · 14q repository · before outbound attempt

---

## 2. 推荐顺序（assisted approve + send）

```text
1. validate actor / pending state
2. AuditLog assisted_approved          (14r)
3. result = evaluate_final_guard(...)
4. if block:
       AuditLog final_guard_blocked
       SendDecisionSnapshot (allowed_to_send=false, block_code, policy_snapshot)
       STOP — no outbound
5. if pass:
       AuditLog final_guard_passed
       SendDecisionSnapshot (decision_phase=merchant_confirm, allowed_to_send=true, ...)
6. AuditLog outbound_send_attempted      (14r · only if step 5 pass)
7. outbound(...)
8. AuditLog outbound_send_succeeded | outbound_send_failed
```

---

## 3. SendDecisionSnapshot 字段（guard 段）

| 字段 | 说明 |
|------|------|
| `decision_phase` | `merchant_confirm` · `auto_final_guard` |
| `allowed_to_send` | bool |
| `block_code` | nullable |
| `block_reason` | nullable |
| `decision_source` | `final_guard` |
| `policy_snapshot` | JSON · 来自 guard output |
| `template_snapshot` | JSON optional |
| `checked_rules` | JSON array optional |

**append-only** · 新 UUID 行 · 不 UPDATE 14n 已有 `ai_preview` 行

---

## 4. auto_final_guard phase

| 场景 | decision_phase |
|------|----------------|
| assisted approve + guard | `merchant_confirm` |
| auto_allowed path + guard | `auto_final_guard` |

两者均需完整 guard result · **auto 不可 skip**

---

## 5. Failure before outbound

| failure | send | recovery |
|---------|------|----------|
| AuditLog before outbound fail | ❌ strict | retry audit · no send |
| Snapshot before outbound fail | ❌ strict | no send |
| guard block | ❌ | audit blocked recorded |
| outbound success + audit fail | 已发送 | **recovery task** · **no resend** |

---

## 6. Dashboard detail（future）

14o detail 扩展（规划）：

```json
{
  "send_decision_snapshots": [
    { "decision_phase": "ai_preview", "...": "..." },
    {
      "decision_phase": "merchant_confirm",
      "allowed_to_send": false,
      "block_code": "forbidden_promise",
      "block_reason": "回复含不允许的承诺用语"
    }
  ]
}
```

---

## 7. preview zero-send snapshot

可选 `decision_phase=ai_preview` 附带：

- `guard_preview_allowed_to_send`
- `guard_block_code`

**不改变 zero-send.**

---

*Phase 14t · planning only · 2026-06-03*

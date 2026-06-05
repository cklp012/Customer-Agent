# Phase 14p — AuditLog / PendingAssisted Planning

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不写代码** |
| 日期 | 2026-06-03 |
| 前置 | [phase14o_done.md](phase14o_done.md) · [phase14n_done.md](phase14n_done.md) · [phase13f_done.md](phase13f_done.md) |

---

## 1. Phase 14p 定位

| 项 | 结论 |
|----|------|
| 交付 | **仅文档** |
| Python 代码 | **未写** |
| DB 表 | **未创建**（`pending_assisted_replies` · `audit_logs`） |
| handler / SendMessage / PDD / Doudian | **未改** |
| Dashboard API（14o） | **未改** |
| assisted mode | **仍未实现** |
| auto mode | **仍未实现** |

Phase 14p 在 14l（ReplyLog shadow）· 14n（SendDecision snapshot shadow）· 14o（Dashboard read skeleton）之上，规划未来 **Assisted Mode** 所需的数据模型、流程、权限、final guard 与失败策略。

---

## 2. 核心概念

### 2.1 PendingAssistedReply

保存 **等待人工确认** 的 AI 建议回复。

| 原则 | 说明 |
|------|------|
| pending ≠ sent | 创建 pending 不触发 SendMessage |
| pending ≠ approved | approve 后仍需 final guard + outbound 成功才 `sent` |
| 有过期时间 | `expires_at` 超时 → `expired`，不可再 approve |
| 弱关联 | `reply_log_id` 关联 `reply_logs`，无 legacy FK |

### 2.2 AuditLog

记录 **谁、何时、对什么、做了什么、为什么**。

| 原则 | 说明 |
|------|------|
| append-only | 不 UPDATE / DELETE 历史行 |
| 无凭证 | 不保存 password / cookie / token |
| 保守策略 | audit 写入失败在 approve/send 路径上必须保守处理 |

---

## 3. Assisted send 必经链路（future · 未实现）

```
1. preview / suggestion generated
      → ReplyLog (preview or assisted branch)
      → SendDecisionSnapshot (decision_phase=ai_preview)

2. pending assisted created
      → PendingAssistedReply status=pending
      → AuditLog pending_assisted_created

3. merchant approve / reject
      → role check (operator/admin/owner)
      → reject: AuditLog assisted_rejected · no send
      → approve: status transition · AuditLog assisted_approved

4. final guard
      → re-evaluate gate / intent / pause / stale / forbidden keywords
      → fail: AuditLog final_guard_blocked · **no send**
      → pass: AuditLog final_guard_passed

5. outbound send
      → outbound resolver / SendMessage (future assisted path only)
      → AuditLog outbound_send_attempted / succeeded / failed

6. SendDecision snapshot
      → decision_phase=merchant_confirm (append-only)

7. AuditLog
      → append-only trail for entire assisted lifecycle
```

**当前 runtime（14o）：** 仅步骤 1 的 preview 分支（test shop zero-send）；步骤 2–7 **均未实现**。

---

## 4. Intent 与 approve 约束

| intent_bucket | approve 规则 |
|---------------|--------------|
| `allowed` | operator+ 可直接 approve（final guard 仍必须通过） |
| `blocked` | **禁止**普通 approve；须 human takeover / 升级权限 |
| `uncertain` | 须 **edit**（`merchant_edited_reply`）或 human takeover 后才可提交 |

| 检查 | 失败行为 |
|------|----------|
| final guard | **不得发送** · `final_guard_blocked` audit |
| audit before send（保守模式） | **阻止发送** 或 degraded（见 failure doc） |
| expired pending | **不得发送** · `assisted_expired` |

---

## 5. 与已实现 phase 的关系

| Phase | 状态 | 与 14p 关系 |
|-------|------|-------------|
| 14l ReplyLog SQLite | ✅ | pending 弱关联 `reply_log_id` |
| 14n SendDecision snapshot | ✅ | preview 阶段 `ai_preview`；assisted 未来 `merchant_confirm` |
| 14o Dashboard read | ✅ | detail 占位 `pending_assisted_reply=null` · `audit_logs=[]` |
| 14p Pending + Audit | 📋 planning | schema · flow · permissions · failure |
| assisted send | ❌ | 14q+ 实现 |
| auto send | ❌ | 未规划实现 |

---

## 6. Flags（规划 · 默认 off）

| Flag | 用途 |
|------|------|
| `PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED` | shadow 写 pending（future 14q） |
| `PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG` | shadow 写 audit（future 14q） |
| `PRODUCT_PERSISTENCE_ENABLED` | 总开关 |

**不默认开启 assisted。** preview zero-send 仍为 test shop 默认行为。

---

## 7. 文档索引

| 文档 | 内容 |
|------|------|
| [phase14p_pending_assisted_schema_detail.md](phase14p_pending_assisted_schema_detail.md) | `pending_assisted_replies` schema |
| [phase14p_auditlog_schema_detail.md](phase14p_auditlog_schema_detail.md) | `audit_logs` schema |
| [phase14p_assisted_approve_reject_flow.md](phase14p_assisted_approve_reject_flow.md) | approve / reject / expire flow |
| [phase14p_permissions_and_final_guard.md](phase14p_permissions_and_final_guard.md) | 角色 · final guard |
| [phase14p_failure_and_rollback.md](phase14p_failure_and_rollback.md) | failure · rollback |
| [phase14p_test_plan.md](phase14p_test_plan.md) | P1–P14 未来测试 |

**对齐早期规划：** [phase14a_pending_assisted_reply_schema.md](phase14a_pending_assisted_reply_schema.md) · [phase14a_auditlog_schema.md](phase14a_auditlog_schema.md) · [phase13f_assisted_confirmation_flow.md](phase13f_assisted_confirmation_flow.md)

---

## 8. 非目标（14p）

- 不实现 POST approve/reject API
- 不修改 handler / AutoReplyThread
- 不改变 PDD queue name（仍为 `pdd_{shop_id}`）
- Doudian 不进入 production assisted send path
- 不 fallback legacy send on DB failure

---

*Phase 14p · planning only · 2026-06-03*

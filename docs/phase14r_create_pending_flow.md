# Phase 14r — Create Pending Flow

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 未实现** |
| 对齐 | [phase14r_assisted_service_plan.md](phase14r_assisted_service_plan.md) · [phase14p_create_pending 等价 phase14p flow](phase14p_assisted_approve_reject_flow.md) |

---

## 1. 触发条件（future assisted branch）

| 条件 | 必须 |
|------|------|
| `reply_mode=assisted` | ✅ |
| `product_gate_enabled=true` | ✅ |
| shop 在 allowlist / assisted 启用列表 | ✅ |
| platform = `pinduoduo`（production assisted 首期） | ✅ |
| AI 建议非空 | ✅ |
| **非** test shop preview zero-send 路径 | assisted 与 preview 分支互斥 |

**当前 runtime：** test shop 走 preview zero-send（14i）· **不创建 pending**。

---

## 2. 输入

| 输入 | 来源 |
|------|------|
| `ReplyLog` / `reply_log_id` | PreviewReplyLogService / shadow write（14l） |
| `SendDecision` | classify + build_send_decision |
| `ai_suggested_reply` | AI handler |
| buyer context | metadata：`workspace_id`, `shop_id`, `account_id`, `platform_id`, `buyer_id`, `inbound_message_id`, `conversation_id` |
| intent / intent_bucket / risk_level | classification |
| `blocked_reason` / `human_takeover_reason` | send_decision |

---

## 3. 流程步骤

```
create_pending_from_preview(...)
  1. 校验 reply_mode=assisted · gate enabled · shop allowed
  2. 校验 intent_bucket != blocked（blocked 仍可创建 pending 但 UI 禁用 approve — 或 status=blocked 变体 · 14t 定）
  3. PendingAssistedRepositorySQLite.create_pending(
         status=pending,
         expires_at=now+24h,
         ai_suggested_reply=...,
         reply_log_id=...,
     )
  4. AuditLogRepositorySQLite.append_audit_log(
         action=pending_assisted_created,
         target_type=pending_assisted,
         target_id=pending_assisted_id,
     )
  5. 返回 CreatePendingResult(pending_assisted_id, recorded=True)
  6. **不调用** SendMessage / outbound / _send_reply
```

**前置（同 handler 批次 · 规划）：**

- ReplyLog 已写入（in-memory + optional shadow）
- SendDecisionSnapshot `decision_phase=ai_preview` 已写入（optional shadow · 14n）

---

## 4. `expires_at` 规则

| 项 | 规则 |
|----|------|
| 必填 | ✅ |
| 默认 | `created_at + 24h` |
| 格式 | ISO8601 TEXT |
| 超时 | `expire_pending` 或 approve 前置检查 → `expired` |

---

## 5. 失败策略

| 场景 | 行为 | send |
|------|------|------|
| create pending DB fail | 返回 `pending_recorded=False` · error | ❌ |
| audit fail **strict**（默认） | pending 回滚或标记 invalid · 不暴露可 approve 状态 | ❌ |
| audit fail **degraded**（可选 flag · 默认 off） | pending 存在 · warning · approve 仍 blocked until audit recovered | ❌ |
| ReplyLog shadow fail | in-memory ok · pending 可 skip 或 proceed（与 14n 一致：shadow 失败不 send） | ❌ |

**create pending failure → 不发送。**

---

## 6. Audit failure 策略（create 阶段）

**推荐 default：strict**

```
try:
    pending_id = repo.create_pending(...)
    audit_id = audit_repo.append_audit_log(action=pending_assisted_created, ...)
except AuditError:
    rollback pending row OR mark pending status=canceled
    return failure — merchant 不可 approve
```

Degraded mode 需 explicit flag · 14r 不推荐默认开启。

---

## 7. non-test legacy 不受影响

| 路径 | create pending |
|------|----------------|
| non-test shop legacy `_send_reply` | ❌ 不进入 |
| test shop preview zero-send | ❌ 不创建 pending |
| Doudian | ❌ 不创建 pending（production） |
| assisted allowlisted shop（future） | ✅ 唯一 create 路径 |

---

## 8. 与 Preview 路径对比

| 项 | Preview（14i） | Assisted create（future） |
|----|----------------|---------------------------|
| ReplyLog | ✅ | ✅ |
| snapshot ai_preview | ✅ optional | ✅ optional |
| PendingAssisted | ❌ | ✅ |
| audit pending_assisted_created | ❌ | ✅ |
| SendMessage | ❌ zero-send | ❌ 等待 approve |

---

*Phase 14r · planning only · 2026-06-03*

# Phase 14p — AuditLog Schema Detail

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不建表** |
| 表名 | `audit_logs`（`product_gate.db` shadow · future） |
| 对齐 | [phase14p_auditlog_pending_assisted_plan.md](phase14p_auditlog_pending_assisted_plan.md) · [phase14a_auditlog_schema.md](phase14a_auditlog_schema.md) |

---

## 1. 职责

**append-only** 审计轨 — 记录商家与系统对 product gate / assisted 的操作，用于安全复盘与合规追踪。

| 原则 | 说明 |
|------|------|
| append-only | **禁止** UPDATE / DELETE 覆盖历史行 |
| 无凭证 | **禁止** 保存 password / cookie / token / API secret |
| 保守写入 | approve/send 路径上 audit 失败策略见 [phase14p_failure_and_rollback.md](phase14p_failure_and_rollback.md) |

---

## 2. 字段

| 列 | 类型 | 必填 | 说明 |
|----|------|------|------|
| `audit_log_id` | TEXT PK | ✅ | UUID |
| `workspace_id` | TEXT | ✅ | 租户 |
| `shop_id` | TEXT | | 店级操作 |
| `account_id` | TEXT | | 账号 |
| `platform_id` | TEXT | | 平台 |
| `actor_user_id` | TEXT | ✅ | 操作者 ID · 系统可用 `system` |
| `actor_role` | TEXT | ✅ | owner / admin / operator / viewer / system |
| `action` | TEXT | ✅ | enum · 见 §3 |
| `target_type` | TEXT | ✅ | 如 `pending_assisted` · `reply_log` · `shop_binding` |
| `target_id` | TEXT | ✅ | 目标实体 ID |
| `reply_log_id` | TEXT | | 关联 ReplyLog（可选） |
| `pending_assisted_id` | TEXT | | 关联 PendingAssisted（可选） |
| `before_state` | TEXT | | JSON string · 变更前快照 |
| `after_state` | TEXT | | JSON string · 变更后快照 |
| `reason` | TEXT | | 人工或系统原因 |
| `ip_address` | TEXT | | 客户端 IP（future auth） |
| `user_agent` | TEXT | | UA（future auth） |
| `created_at` | TEXT | ✅ | ISO8601 · **仅插入** |

**类型约定：**

- enum 存 **TEXT**
- `before_state` / `after_state` 为 **JSON string**（非 JSONB · SQLite shadow）
- timestamp 为 **ISO8601 TEXT**
- **不 FK** legacy tables

---

## 3. `action` 枚举

| action | 触发场景 |
|--------|----------|
| `preview_generated` | preview 建议生成（可选 · debug 级） |
| `pending_assisted_created` | 创建 PendingAssistedReply |
| `assisted_approved` | 商家 approve |
| `assisted_rejected` | 商家 reject |
| `assisted_expired` | pending 超时 |
| `final_guard_passed` | final guard 通过 |
| `final_guard_blocked` | final guard 拒绝 · **未发送** |
| `outbound_send_attempted` | 调用 outbound 前 |
| `outbound_send_succeeded` | SendMessage 成功 |
| `outbound_send_failed` | SendMessage 失败 |
| `reply_mode_changed` | preview ↔ assisted 切换 |
| `product_gate_changed` | product_gate_enabled 变更 |
| `shop_paused` | 店铺暂停 |
| `shop_resumed` | 店铺恢复 |

**写入时机（assisted path · future）：**

| 事件 | 必须 audit? |
|------|-------------|
| pending 创建 | ✅ `pending_assisted_created` |
| approve | ✅ `assisted_approved` |
| reject | ✅ `assisted_rejected` |
| expire | ✅ `assisted_expired` |
| final guard pass/block | ✅ |
| outbound attempt/success/fail | ✅ |
| reply_mode / gate / pause 变更 | ✅ |
| preview zero-send（当前 14i） | ❌ 可选（非必须） |

---

## 4. 索引

| 索引名 | 列 | 用途 |
|--------|-----|------|
| `idx_audit_workspace_created_at` | `workspace_id`, `created_at` | workspace 审计流 |
| `idx_audit_shop_created_at` | `shop_id`, `created_at` | 店铺审计 |
| `idx_audit_actor_created_at` | `actor_user_id`, `created_at` | 操作者追踪 |
| `idx_audit_target` | `target_type`, `target_id` | 实体审计链 |

---

## 5. 安全与隐私

| 规则 | 说明 |
|------|------|
| 禁止 credential | `before_state` / `after_state` 不得含 cookie / password / token |
| 脱敏 | buyer 敏感字段按 Dashboard 脱敏规则 |
| 不可变 | 合规/legal hold 仅追加更正记录，不 DELETE 原行 |
| 用途 | 商家操作追踪 · 安全复盘 · 权限争议 |

---

## 6. 与 Dashboard read 关系

14o detail API 占位：

```json
{
  "audit_logs": []
}
```

14q+ 当 `READ_DASHBOARD=true` 且 audit shadow 存在时，detail 可填充 `audit_logs[]`（read-only）。

---

## 7. 非目标

- 14p **不创建** 此表
- 不修改 repository / service 代码
- 不实现 audit write path

---

*Phase 14p · planning only · 2026-06-03*

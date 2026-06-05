# Phase 14a — AuditLog Schema

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 对齐 | [phase13f_auditlog_and_permissions.md](phase13f_auditlog_and_permissions.md) |
| 表名 | `audit_logs`（shadow） |

---

## 1. 职责

**append-only** 审计轨 — 谁、何时、对什么、改了什么。

**禁止：** 普通 UPDATE 覆盖历史行（仅合规/legal hold 例外流程）。

---

## 2. 字段

| 列 | 类型 | 必填 | 说明 |
|----|------|------|------|
| `audit_log_id` | UUID PK | ✅ | |
| `workspace_id` | UUID FK | ✅ | |
| `shop_id` | string? | | 店级操作必填 |
| `account_id` | string? | | |
| `actor_member_id` | UUID FK | ✅ | 系统动作可用 `system` UUID |
| `actor_role` | enum | ✅ | owner / admin / operator / viewer / system |
| `action` | enum | ✅ | 见 §3 |
| `target_type` | enum | ✅ | pending_reply / reply_log / shop_binding / credential / allowlist |
| `target_id` | string | ✅ | 目标实体 ID |
| `before_state` | JSONB | | |
| `after_state` | JSONB | | |
| `reason` | text? | | 人工填写或系统 reason |
| `ip_address` | string? | | |
| `user_agent` | string? | | |
| `created_at` | datetime | ✅ | **仅插入** |

---

## 3. `action` 枚举

| action | 触发 | 必填 target |
|--------|------|-------------|
| `assisted_reply_approved` | 商家确认发送 | `pending_reply` |
| `assisted_reply_rejected` | 商家拒绝 | `pending_reply` |
| `reply_mode_changed` | preview↔assisted 等 | `shop_binding` |
| `product_gate_enabled_changed` | gate 开关 | `shop_binding` |
| `shop_paused` | 暂停店铺 | `shop_binding` |
| `shop_resumed` | 恢复店铺 | `shop_binding` |
| `test_shop_allowlist_changed` | allowlist 增删 | `allowlist` |
| `credential_updated` | 凭证更新 | `credential` |
| `credential_revoked` | 凭证吊销 | `credential` |

**扩展（可选）：** `workspace_paused` · `send_failed` · `elevated_approve_denied`

---

## 4. 写入策略

| 事件 | 必须 AuditLog? |
|------|----------------|
| assisted 确认发送（成功/被 guard 拒绝） | ✅ |
| assisted reject | ✅ |
| reply_mode 切换 | ✅ |
| product_gate_enabled 切换 | ✅ |
| shop/workspace pause/resume | ✅ |
| test shop allowlist 变更 | ✅ |
| credential 更新/吊销 | ✅ |
| preview zero-send（13d） | ❌（可选 debug 事件，非 14a 必须） |
| AI handler 自动生成建议 | ❌（用 SendDecision + ReplyLog） |

---

## 5. 索引

| 索引 | 用途 |
|------|------|
| `(workspace_id, created_at DESC)` | 管理审计流 |
| `(shop_id, created_at DESC)` | 店级审计 |
| `(actor_member_id, created_at DESC)` | 操作人追溯 |
| `(action, created_at)` | 合规报表 |
| `(target_type, target_id)` | 实体历史 |

---

## 6. 保留与合规

| 项 | 建议 |
|----|------|
| 保留期 | ≥ 365 天（可配置） |
| 删除 | 仅 anonymize job；不物理删 approve 记录 |
| PII | `ip_address` 可选哈希 |

---

*AuditLog schema · Phase 14a · 2026-06-03*

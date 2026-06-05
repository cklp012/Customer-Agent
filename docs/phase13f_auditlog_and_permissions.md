# Phase 13f — AuditLog and Permissions

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 对齐 | [phase12b_merchant_workspace_model.md](phase12b_merchant_workspace_model.md) · [phase12e_send_decision_reply_log_schema.md](phase12e_send_decision_reply_log_schema.md) § AuditLog |
| 持久化 | Phase **14a** shadow schema |

---

## 1. Member 角色

| 角色 | 说明 | Assisted 确认 | 改 reply_mode | 改 product_gate |
|------|------|---------------|---------------|-----------------|
| **owner** | 工作区所有者 | ✅ | ✅ | ✅ |
| **admin** | 管理员 | ✅ | ✅ | ✅ |
| **operator** | 客服操作员 | ✅ | ❌ | ❌ |
| **viewer** | 只读 | ❌ | ❌ | ❌ |

**规则：**

- **viewer 不能发送** — approve/reject API 返回 403
- **operator** 可 `assisted_reply_approved` / `assisted_reply_rejected`
- **admin/owner** 可 `reply_mode_changed` · `product_gate_enabled_changed` · pause/resume

---

## 2. 权限检查点

| 检查点 | 最低角色 |
|--------|----------|
| 查看 preview / pending 列表 | viewer |
| 编辑 suggested_reply 后确认 | operator |
| 一键 approve（allowed + low risk） | operator |
| Elevated approve（uncertain / 边缘 case） | admin |
| blocked intent 强制发送 | **禁止**（无角色可普通 bypass） |
| 切换 preview → assisted | admin |
| 开启 product_gate | admin |

---

## 3. AuditLog 实体（规划）

| 字段 | 类型 | 必填 |
|------|------|------|
| `audit_log_id` | UUID PK | ✅ |
| `workspace_id` | UUID FK | ✅ |
| `shop_id` | string | ✅ |
| `account_id` | string? | 推荐 |
| `actor_member_id` | UUID FK | ✅ |
| `action` | enum | ✅ |
| `before_state` | JSON | 可选 |
| `after_state` | JSON | 可选 |
| `reason` | string? | 可选 |
| `created_at` | datetime | ✅ |

**关联（可选）：** `pending_id` · `reply_log_id` · `decision_id`

---

## 4. 关键 action 枚举

| action | 触发 | before_state / after_state 示例 |
|--------|------|--------------------------------|
| `assisted_reply_approved` | 商家确认发送 | pending: awaiting → approved_sent |
| `assisted_reply_rejected` | 商家拒绝 | pending: awaiting → rejected |
| `reply_mode_changed` | admin 改模式 | preview → assisted |
| `product_gate_enabled_changed` | admin 开关 gate | false → true |
| `shop_paused` | 暂停店铺 | pause: false → true |
| `shop_resumed` | 恢复店铺 | pause: true → false |

**14a 要求：** 所有 assisted 发送成功/失败均写 AuditLog；与 ReplyLog `sent_at` 可 join。

---

## 5. AuditLog 写入时机

| 事件 | action | actor |
|------|--------|-------|
| Approve 成功 send | `assisted_reply_approved` | operator+ |
| Approve 被 guard 拒绝 | `assisted_reply_rejected` + reason | operator+ |
| 商家点击拒绝 | `assisted_reply_rejected` | operator+ |
| Dashboard 改 reply_mode | `reply_mode_changed` | admin+ |
| Allowlist / gate 变更 | `product_gate_enabled_changed` | admin+ |
| 暂停/恢复 | `shop_paused` / `shop_resumed` | admin+ |

**禁止：** AI handler 自动写 `assisted_reply_approved`（无 actor）。

---

## 6. API / Command 鉴权（14b 规划）

```text
POST /workspaces/{ws}/shops/{shop}/assisted-replies/{id}/approve
  Authorization: member session
  Required role: operator | admin | owner
  Body: { final_reply?: string, elevated_ack?: bool }

POST .../reject
  Required role: operator+
```

**14b：** 仅规划 OpenAPI 草案；**13f 不实现 endpoint**。

---

## 7. 与 12e migration 对齐

AuditLog 表列入 Phase **14a** shadow schema（M7+），先于 production 写库。

---

*AuditLog & permissions · Phase 13f · 2026-06-03*

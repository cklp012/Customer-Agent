# Phase 14p — Permissions and Final Guard

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 未实现** |
| 对齐 | [phase14p_assisted_approve_reject_flow.md](phase14p_assisted_approve_reject_flow.md) · [phase13f_auditlog_and_permissions.md](phase13f_auditlog_and_permissions.md) · [phase14k_dashboard_filters_and_permissions.md](phase14k_dashboard_filters_and_permissions.md) |

---

## 1. 角色定义

| 角色 | 说明 |
|------|------|
| `owner` | workspace 所有者 |
| `admin` | 管理员 |
| `operator` | 日常运营 · 可处理 assisted |
| `viewer` | 只读 |

**14o 现状：** Dashboard read API auth 为 **placeholder**；本 doc 为 future enforcement 规划。

---

## 2. 权限矩阵

| 能力 | viewer | operator | admin | owner |
|------|--------|----------|-------|-------|
| 读 ReplyLog / Dashboard | ✅ | ✅ | ✅ | ✅ |
| 读 PendingAssisted 列表 | ✅ | ✅ | ✅ | ✅ |
| 读 AuditLog | ✅（脱敏） | ✅ | ✅ | ✅ |
| approve assisted | ❌ | ✅ | ✅ | ✅ |
| reject assisted | ❌ | ✅ | ✅ | ✅ |
| edit 后 approve | ❌ | ✅ | ✅ | ✅ |
| reply_mode 变更 | ❌ | ❌ | ✅ | ✅ |
| product_gate 变更 | ❌ | ❌ | ✅ | ✅ |
| shop pause/resume | ❌ | ❌ | ✅ | ✅ |
| workspace ownership | ❌ | ❌ | ❌ | ✅ |

**规则：**

- **viewer：read only** — approve/reject **403**
- **operator：read + approve/reject assisted**
- **admin：operator + settings**（gate · mode · pause）
- **owner：admin + workspace ownership**

---

## 3. Approve / Reject 权限检查（future）

```
approve/reject request
  → authenticate actor
  → resolve workspace scope
  → actor_role in {operator, admin, owner}
  → else 403 viewer_cannot_approve
```

blocked intent approve 需 **elevated** 权限（admin/owner + human takeover workflow）— 普通 operator **禁止**。

---

## 4. Final Guard（发送前最后一道门）

Final guard 在 **approve 之后、outbound 之前** 执行，重评估全部 gate 条件。**失败不得发送。**

### 4.1 必检项

| # | 检查 | 失败 reason 示例 |
|---|------|------------------|
| G1 | `product_gate_enabled == true` | `gate_disabled` |
| G2 | workspace **not** paused | `workspace_paused` |
| G3 | shop **not** paused | `shop_paused` |
| G4 | `reply_mode == assisted`（发送时） | `reply_mode_mismatch` |
| G5 | pending status 允许 send transition | `invalid_pending_status` |
| G6 | intent 仍为 allowed consultation | `intent_blocked` |
| G7 | `risk_level` acceptable（policy） | `risk_too_high` |
| G8 | `blocked_reason` 为空 | `blocked_reason_set` |
| G9 | `human_takeover_reason` 为空（普通 send） | `human_takeover_required` |
| G10 | message **not stale**（`expires_at` · 新消息 supersede） | `stale_message` |
| G11 | **no forbidden promise keywords** | `forbidden_promise` |
| G12 | no refund / compensation / order change / address change **promise** | `forbidden_commitment` |
| G13 | outbound channel available | `channel_unavailable` |

### 4.2 Forbidden promise keywords（示例 · 非 exhaustive）

- 退款承诺 / 补偿承诺 / 改价承诺
- 改地址 / 改订单 / 包邮承诺（未授权）
- 100% / 一定 / 保证 等过度承诺（policy 可配置）

对齐 [phase13f_risk_controls.md](phase13f_risk_controls.md)。

---

## 5. Final Guard 结果处理

| 结果 | 行为 |
|------|------|
| **pass** | AuditLog `final_guard_passed` → 允许 outbound attempt |
| **block** | AuditLog `final_guard_blocked` → **no SendMessage** → pending 保持 `approved` 或转 `failed`（implementation 决策 · 14s） |

**明确：**

- **final guard 失败不得发送**
- **final guard pass ≠ 发送成功** — outbound 仍可能失败
- outbound failure → AuditLog `outbound_send_failed` · status `failed`

---

## 6. 与 preview zero-send 关系

| 模式 | final guard | send |
|------|-------------|------|
| preview（当前 test shop） | evaluate_guarded_send · preview_only | **zero-send** |
| assisted（future） | final guard at approve | outbound once |
| auto（未实现） | N/A | N/A |

Preview path **不调用** assisted final guard outbound。

---

## 7. Audit 与 guard 联动

| 事件 | audit action |
|------|--------------|
| guard pass | `final_guard_passed` |
| guard block | `final_guard_blocked` |
| outbound attempt | `outbound_send_attempted` |
| outbound success | `outbound_send_succeeded` |
| outbound failure | `outbound_send_failed` |

---

## 8. 非目标

- 14p 不实现 guard 代码
- 不修改 `evaluate_guarded_send` 热路径
- 不修改 handler / SendMessage

---

*Phase 14p · planning only · 2026-06-03*

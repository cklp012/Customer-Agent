# Phase 12d — Exception & Alert Model（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 关联 | [phase12d_connection_status_read_model.md](phase12d_connection_status_read_model.md) · [phase12d_dashboard_ia.md](phase12d_dashboard_ia.md) |

---

## 1. Alert 实体

| 字段 | 类型 | 说明 |
|------|------|------|
| `alert_id` | UUID | |
| `workspace_id` | UUID | |
| `shop_binding_id` | UUID? | null = 工作区级 |
| `alert_type` | enum | 见 §2 |
| `severity` | enum | `info` \| `warning` \| `critical` |
| `visible_to_merchant` | bool | 默认 true |
| `title` | string | 商家可见 |
| `message` | string | |
| `recommended_action` | string | CTA key |
| `suppressible` | bool | 商家可「不再提醒」 |
| `auto_pause_required` | bool | 为 true 时系统 **建议** 或 **强制** pause（产品配置） |
| `created_at` | datetime | |
| `dismissed_at` | datetime? | |
| `dismissed_by` | merchant_id? | |

---

## 2. Alert 类型定义

### 2.1 `credential_expiring`

| 属性 | 值 |
|------|-----|
| severity | `warning` |
| visible_to_merchant | true |
| recommended_action | 请在 N 天内重新授权，避免收消息中断 |
| suppressible | true（一次/7天） |
| auto_pause_required | false |

---

### 2.2 `credential_expired`

| 属性 | 值 |
|------|-----|
| severity | `critical` |
| visible_to_merchant | true |
| recommended_action | **立即重新授权** — 授权已过期，无法收消息 |
| suppressible | false |
| auto_pause_required | false（effective_status → auth_action_required） |

**必须：** 明确 CTA「重新授权」，**不** 显示为「已连接」。

---

### 2.3 `auth_failed`

| 属性 | 值 |
|------|-----|
| severity | `critical` |
| visible_to_merchant | true |
| recommended_action | **重新登录拼多多账号** 并完成授权 |
| suppressible | false |
| auto_pause_required | false |

---

### 2.4 `receive_failed`

| 属性 | 值 |
|------|-----|
| severity | `warning` → `critical`（持续 >30min） |
| visible_to_merchant | true |
| recommended_action | 检查网络与账号状态；若持续请重新授权 |
| suppressible | true |
| auto_pause_required | false |

---

### 2.5 `send_failed`

| 属性 | 值 |
|------|-----|
| severity | `warning` |
| visible_to_merchant | true |
| recommended_action | 查看发送失败日志；失败率 >阈值 **建议暂停自动发送** |
| suppressible | true |
| auto_pause_required | **true**（当 `failed_send_rate > 10%` 且 `auto_active`，建议弹窗 pause） |

---

### 2.6 `ai_provider_failed`

| 属性 | 值 |
|------|-----|
| severity | `warning` |
| visible_to_merchant | true |
| recommended_action | AI 暂时不可用，请稍后重试；已自动切换备用（若有） |
| suppressible | true |
| auto_pause_required | false |

---

### 2.7 `ai_quota_exceeded`

| 属性 | 值 |
|------|-----|
| severity | `warning` |
| visible_to_merchant | true |
| recommended_action | **升级套餐** 或切换 **仅预览模式** 继续观察 |
| suppressible | false（直至升级或新月） |
| auto_pause_required | false（停止 **新生成** 可选） |

---

### 2.8 `high_block_rate`

| 属性 | 值 |
|------|-----|
| severity | `info` → `warning` |
| visible_to_merchant | true |
| recommended_action | 今日较多 **非售前咨询** 消息，建议安排人工值班；检查是否误开自动发送 |
| suppressible | true |
| auto_pause_required | false |

**定义：** `blocked_intent_count / inbound_messages_count > 40%`（可配置）。

**含义：** 很多消息不是售前咨询，商家应人工处理 — **不是** 系统故障。

---

### 2.9 `high_failed_send_rate`

| 属性 | 值 |
|------|-----|
| severity | `critical` |
| visible_to_merchant | true |
| recommended_action | **建议立即暂停** 自动发送并检查连接 |
| suppressible | true |
| auto_pause_required | **true**（建议，非强制 MVP） |

---

### 2.10 `product_gate_disabled`

| 属性 | 值 |
|------|-----|
| severity | `info` |
| visible_to_merchant | false（仅管理员/内部）或 true（过渡期） |
| recommended_action | 安全发送 gate 未启用，行为与旧版自动回复一致 |
| suppressible | true |
| auto_pause_required | false |

**商家版（若可见）：** 「您处于兼容模式，建议联系客服开启安全预览。」

---

### 2.11 `platform_waitlist`

| 属性 | 值 |
|------|-----|
| severity | `info` |
| visible_to_merchant | true |
| recommended_action | 预约内测；**该平台尚未开放绑定** |
| suppressible | true |
| auto_pause_required | false |

**必须：** **不能** 显示为「已连接 / 自动回复中」。`effective_status=waitlist`。

---

## 3. Alert 与 Dashboard 模块映射

| alert_type | Dashboard 模块 |
|------------|----------------|
| credential_* / auth_failed | F |
| receive_failed / send_failed | F · A |
| ai_quota_exceeded | G |
| high_block_rate | E |
| high_failed_send_rate | F · H（建议 pause） |
| platform_waitlist | A（badge） |

---

## 4. 顶栏铃铛优先级

```text
critical (auth_failed, credential_expired, high_failed_send_rate)
  > warning (send_failed, ai_quota, credential_expiring)
  > info (high_block_rate, platform_waitlist, product_gate_disabled)
```

---

## 5. 与 pause 联动

| alert | 建议 UI |
|-------|---------|
| `send_failed` + 高失败率 | 一键暂停本店（H） |
| `ai_quota_exceeded` | 降级 reply_mode → preview（POST reply-mode + audit） |
| `auth_failed` | 禁用 pause 以外的发送；引导 reauth |

---

## 6. 抑制与审计

| 操作 | AuditLog |
|------|----------|
| dismiss alert | `alert.dismissed` |
| suppress 7d | `alert.suppressed` |

---

*Phase 12d · Exception & Alert Model · docs only*

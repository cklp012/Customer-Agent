# Phase 12d — Dashboard Information Architecture（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only · **未实现 UI / API** |
| 前置 | [phase12b_shop_binding_state_model.md](phase12b_shop_binding_state_model.md) · [phase12c_send_decision_model.md](phase12c_send_decision_model.md) |
| 关联 | [phase12d_connection_status_read_model.md](phase12d_connection_status_read_model.md) · [phase12d_api_contract.md](phase12d_api_contract.md) |

---

## 1. Dashboard 目标（商家五问）

| # | 商家问题 | 主要模块 |
|---|----------|----------|
| 1 | 我的店有没有连上？ | A · F |
| 2 | AI 现在有没有在自动发？ | B · A（effective_status） |
| 3 | 没发是因为 preview、paused、blocked、低置信还是授权异常？ | B · D · E · F |
| 4 | 今天 AI 帮我处理了多少？ | C |
| 5 | 有多少需要人工接管？ | D · E |
| 6 | 能不能马上暂停？ | H |

**产品原则（12a–12c）：**

- **`connected` ≠ auto enabled`** — 须在 B 模块显性展示
- **Preview 不会自动发送** — 即使 connected + 健康
- **Paused 优先级最高** — 覆盖 auto/assisted
- **绑定 ≠ 自动回复**

---

## 2. 页面结构

```text
┌──────────────────────────────────────────────────────────────────┐
│ 顶栏：工作区名 · 全局暂停(H) · 套餐用量(G) · 告警铃铛(F)            │
├──────────────────────────────────────────────────────────────────┤
│ 今日活动概览 (C) — 工作区级聚合，可按店筛选                          │
├────────────────────────────┬─────────────────────────────────────┤
│ 店铺列表 / 连接卡片 (A×N)    │ 待人工处理 (D)                        │
│ + 回复模式摘要 (B 内嵌)      │ 风险拦截摘要 (E)                      │
├────────────────────────────┴─────────────────────────────────────┤
│ 授权/连接异常 (F) — 仅在有 alert 时展开                             │
└──────────────────────────────────────────────────────────────────┘
```

**MVP 桌面版：** 可折叠为单店视图；SaaS Web 为多店卡片网格。

---

## 3. 模块 A — 店铺连接状态卡片

| 字段 | 类型 | 商家展示 |
|------|------|----------|
| `platform` | enum | 平台 badge（拼多多 / 即将支持） |
| `shop_name` | string | 主标题 |
| `shop_id` | string | 次要 · 可复制 |
| `binding_status` | enum | **不直接暴露**；映射到 `effective_status` 副文案 |
| `connection_status` | enum | 同上 |
| `inbound_status` | enum | 收消息：正常 / 异常（图标） |
| `outbound_status` | enum | 发消息：正常 / 异常（图标） |
| `last_heartbeat_at` | datetime | 「最后在线：x 分钟前」 |
| `last_error` | string? | 友好摘要（非内部 code） |
| `reauth_required` | bool | 「需要重新授权」CTA |

**主状态展示：** 使用 `effective_status`（见 connection read model），**非** 原始 `binding_status` 枚举。

| effective_status（示例） | 商家文案 |
|--------------------------|----------|
| `paused` | 已暂停 — 不会自动发送 |
| `preview_active` | 已连接 · **仅预览** — 买家不会收到 AI 消息 |
| `assisted_active` | 已连接 · **辅助模式** — 需您确认后发送 |
| `auto_active` | 已连接 · **自动发送已开启** |
| `auth_action_required` | 授权异常 — 请重新登录 |
| `offline` | 连接已断开 |
| `waitlist` | 即将支持 — 尚未开放 |

---

## 4. 模块 B — 回复模式卡片

| 字段 | 类型 | 说明 |
|------|------|------|
| `reply_mode` | enum | `preview` / `assisted` / `auto` |
| `workspace_pause` | bool | 工作区级 |
| `shop_pause` | bool | 单店 |
| `product_gate_enabled` | bool | 产品 gate 是否启用（12c） |
| `consultation_only` | bool | 售前咨询范围 |
| `auto_enabled_at` | datetime? | 开启 auto 时间 |
| `last_mode_changed_by` | string | 商家成员名 |
| `last_mode_changed_at` | datetime | |

**派生展示 `reply_mode_display`：**

| 条件 | 展示 |
|------|------|
| `workspace_pause` OR `shop_pause` | **`paused`**（覆盖 raw reply_mode） |
| else | `preview` / `assisted` / `auto` |

**必须显示的说明条（info banner）：**

| 场景 | 文案 |
|------|------|
| connected + preview | 「店铺已连接。**当前为预览模式**，AI 只生成建议，**不会**发给买家。」 |
| connected + auto | 「**自动发送已开启**。仅低风险售前咨询会自动发送；退款/投诉等会转人工。」 |
| connected 但非 auto | 「**已连接 ≠ 已开启自动回复**。您可在设置中开启自动发送（需二次确认）。」 |
| paused | 「**已暂停** — 优先级最高，所有自动/辅助发送已停止。」 |

---

## 5. 模块 C — 今日活动概览

**范围：** 工作区默认「今日 0:00–now」；可按 `shop_binding_id` 筛选。

| 字段 | 说明 |
|------|------|
| `inbound_messages_count` | 入站买家消息数 |
| `ai_suggestions_count` | AI 生成建议次数 |
| `preview_only_count` | 仅预览、未发送 |
| `assisted_required_count` | 待商家确认 |
| `auto_sent_count` | 实际自动发送成功 |
| `blocked_count` | 被 gate 拦截（含 intent / 禁诺） |
| `human_takeover_count` | 转人工或标记接管 |
| `failed_send_count` | 发送失败 |

**钻取：** 点击指标 → `reply-logs` 列表（带 filter）。

**「AI 处理了多少」定义：** `ai_suggestions_count`（含 preview），**非** 仅 `auto_sent_count`。

---

## 6. 模块 D — 待人工处理

| 字段 | 说明 |
|------|------|
| `buyer_id` | 脱敏展示 |
| `shop_name` | |
| `latest_message` | 摘要 ≤120 字 |
| `intent` | 如 `refund_request` |
| `blocked_reason` | |
| `human_takeover_reason` | |
| `created_at` | |
| `priority` | `high` / `medium` / `low` |

**入队规则（read model）：** `send_mode=human_takeover` OR `intent_bucket=blocked` OR `assisted_required` 超时。

**操作（未来 API）：** 「标记已处理」「接管会话」— 12g wireframe。

---

## 7. 模块 E — 风险 / 拦截摘要

| 字段 | 聚合维度 |
|------|----------|
| `refund_request_count` | intent |
| `complaint_count` | intent |
| `compensation_request_count` | intent |
| `order_change_count` | intent |
| `low_confidence_count` | `blocked_reason` |
| `blocked_intent_count` | bucket=blocked |

**解读文案：** 「今日有 N 条非售前咨询消息，已转人工或仅预览，**未自动发送**。」

---

## 8. 模块 F — 授权 / 连接异常

| 字段 | 说明 |
|------|------|
| `auth_failed` | bool |
| `receive_failed` | bool |
| `send_failed` | bool |
| `token_expiring` | bool · 7 天内过期 |
| `token_expired` | bool |
| `last_error_message` | 商家友好 |
| `recommended_action` | CTA 文案 key |

**与 alert 模型联动：** 见 [phase12d_exception_and_alert_model.md](phase12d_exception_and_alert_model.md)。

---

## 9. 模块 G — 用量 / 套餐

| 字段 | 说明 |
|------|------|
| `plan_name` | Starter / Growth / Pro |
| `ai_suggestions_used` | 本月建议条数 |
| `ai_suggestions_limit` | |
| `auto_sent_used` | 本月自动发送 |
| `auto_sent_limit` | |
| `shops_used` | |
| `shops_limit` | |
| `renews_at` | |

**额度将尽：** 联动 `ai_quota_exceeded` alert。

---

## 10. 模块 H — 一键暂停区域

| 控件 | 行为 |
|------|------|
| **暂停全部店铺** | `workspace_pause=true` · POST audit |
| **暂停本店** | `shop_pause=true` |
| `pause_reason` | 可选下拉 + 自由文本 |
| `resumed_by` | resume 时记录 |
| **audit trail** | 最近 10 条 pause/resume/mode 变更 |

**暂停后顶栏 Banner：** 「工作区已暂停 — 买家不会收到 AI 自动/辅助回复」（Preview 建议可继续，见 12a）。

---

## 11. 信息层级与权限

| 角色 | 可见 |
|------|------|
| 所有者 / 管理员 | 全部 + pause + reply-mode |
| 客服 | C/D/E 只读；无 pause |
| 只读 | C/D 脱敏 |

---

## 12. 非目标（12d）

- 不画高保真 UI（见 **12g** wireframe）
- 不实现 API / DB

---

*Phase 12d · Dashboard IA · docs only*

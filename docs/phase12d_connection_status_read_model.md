# Phase 12d — Connection Status Read Model（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only · read model / CQRS 视图 |
| 关联 | [phase12b_shop_binding_state_model.md](phase12b_shop_binding_state_model.md) · [phase12d_dashboard_ia.md](phase12d_dashboard_ia.md) |

---

## 1. 设计原则

| # | 原则 |
|---|------|
| R1 | **`effective_status` 给商家看**；底层 `binding_status` / `connection_status` 给运维与诊断 |
| R2 | UI **不直接暴露** 内部 enum 全集 |
| R3 | **`connected` ≠ `auto_enabled`** — `effective_status` 必须区分 preview / auto |
| R4 | **`paused` 覆盖** 一切「active」展示 |

---

## 2. WorkspaceStatusSummary

| 字段 | 类型 | 说明 |
|------|------|------|
| `workspace_id` | UUID | |
| `workspace_name` | string | |
| `workspace_pause` | bool | |
| `paused_at` | datetime? | |
| `paused_by` | merchant_id? | |
| `pause_reason` | string? | |
| `shop_count_total` | int | |
| `shop_count_connected` | int | `binding_status=connected` |
| `shop_count_auto_active` | int | `effective_status=auto_active` |
| `shop_count_preview` | int | `effective_status=preview_active` |
| `shop_count_paused` | int | |
| `shop_count_needs_auth` | int | |
| `active_alerts_count` | int | warning+critical |
| `today_activity` | ReplyActivitySummary | 嵌入或引用 ID |
| `as_of` | datetime | 缓存时间 |

---

## 3. ShopConnectionSummary

| 字段 | 类型 | 必填 |
|------|------|------|
| `workspace_id` | UUID | ✅ |
| `shop_binding_id` | UUID | ✅ |
| `platform_id` | enum | ✅ |
| `shop_id` | string | ✅ |
| `shop_name` | string | ✅ |
| `shop_logo_url` | string? | |
| `account_display_name` | string? | |
| `binding_status` | enum | ✅ 底层 |
| `connection_status` | enum | ✅ 底层 |
| `inbound_status` | enum | ✅ |
| `outbound_status` | enum | ✅ |
| `reply_mode` | enum | ✅ 底层 raw |
| `product_gate_enabled` | bool | ✅ |
| `consultation_only` | bool | ✅ |
| `workspace_pause` | bool | ✅ |
| `shop_pause` | bool | ✅ |
| `effective_status` | enum | ✅ **商家主状态** |
| `effective_status_label` | string | ✅ 中文文案 |
| `auto_enabled` | bool | ✅ 派生：`reply_mode=auto` 且二次确认完成 |
| `is_sending_to_buyers` | bool | ✅ 派生：auto/assisted 且 allowed 且非 paused |
| `last_heartbeat_at` | datetime? | ✅ |
| `last_inbound_at` | datetime? | ✅ |
| `last_outbound_at` | datetime? | ✅ |
| `last_error_code` | string? | 对内可选 |
| `last_error_message` | string? | 商家友好 |
| `recommended_action` | enum? | 见 §5 |
| `reauth_required` | bool | ✅ |
| `waitlist` | bool | ✅ |
| `as_of` | datetime | ✅ |

---

## 4. `effective_status` 求值规则（SSOT）

**求值顺序（先匹配先返回）：**

```text
1. if workspace_pause OR shop_pause → paused
2. if waitlist OR platform_id != pinduoduo (MVP non-prod) → waitlist
3. if binding_status in (unbound, binding) → connecting
4. if binding_status in (disabled, error) → disabled_or_error
5. if credential expired OR binding_status=expired OR auth_failed → auth_action_required
6. if connection_status=offline → offline
7. if inbound_status=failed OR outbound_status=failed → degraded
8. if binding_status != connected → not_ready
9. if connected AND reply_mode=preview → preview_active
10. if connected AND reply_mode=assisted → assisted_active
11. if connected AND reply_mode=auto AND product_gate_enabled → auto_active
12. if connected AND reply_mode=auto AND NOT product_gate_enabled → preview_active*
    (* 文案：已连接 · 自动模式待启用产品安全 gate — 工程过渡期)
13. default → unknown
```

| effective_status | 商家 label（示例） |
|----------------|-------------------|
| `paused` | 已暂停 |
| `waitlist` | 即将支持 |
| `connecting` | 连接中 |
| `disabled_or_error` | 已停用 / 连接异常 |
| `auth_action_required` | 需重新授权 |
| `offline` | 已离线 |
| `degraded` | 部分异常 |
| `not_ready` | 未完成连接 |
| `preview_active` | 已连接 · 仅预览 |
| `assisted_active` | 已连接 · 辅助确认 |
| `auto_active` | 已连接 · 自动发送中 |
| `unknown` | 状态未知 |

### 4.1 与「AI 有没有在自动发」

| effective_status | `is_sending_to_buyers` |
|------------------|------------------------|
| `auto_active` + healthy + not paused | **true**（仅 auto 路径且 gate 允许） |
| `assisted_active` | **false**（须逐条 approve） |
| `preview_active` | **false** |
| `paused` | **false** |
| `auth_action_required` / `offline` | **false** |

---

## 5. `recommended_action` 枚举

| 值 | 场景 |
|----|------|
| `reauthorize` | token 过期 / auth_failed |
| `check_network` | offline |
| `fix_inbound` | receive_failed |
| `fix_outbound` | send_failed |
| `resume_shop` | shop_pause |
| `resume_workspace` | workspace_pause |
| `review_preview_logs` | preview_active · 引导观察 |
| `enable_auto_confirm` | 商家显式开启 auto（二次确认） |
| `contact_support` | error 不可恢复 |
| `join_waitlist` | waitlist 平台 |
| `none` | 健康 |

---

## 6. CredentialHealthSummary

| 字段 | 类型 |
|------|------|
| `credential_ref_id` | UUID |
| `shop_binding_id` | UUID |
| `status` | `active` \| `expiring` \| `expired` \| `revoked` |
| `expires_at` | datetime? |
| `last_validated_at` | datetime? |
| `auth_failed` | bool |
| `token_expiring` | bool · ≤7d |
| `token_expired` | bool |
| `recommended_action` | `reauthorize` \| `none` |

**嵌入：** `ShopConnectionSummary.reauth_required = (status in expired, revoked) OR auth_failed`.

---

## 7. PauseStateSummary

| 字段 | 类型 |
|------|------|
| `workspace_id` | UUID |
| `workspace_pause` | bool |
| `workspace_paused_at` | datetime? |
| `workspace_paused_by` | merchant_id? |
| `workspace_pause_reason` | string? |
| `shops` | list[{ shop_binding_id, shop_pause, shop_paused_at, shop_pause_reason }] |

**派生：** 任一层 pause → Dashboard `reply_mode_display=paused`.

---

## 8. 底层 vs UI 状态分离

| 层 | 消费者 |
|----|--------|
| **持久化** | ShopBinding, CredentialRef, Workspace |
| **运行时** | 连接器心跳、队列深度（内部） |
| **Read model** | ShopConnectionSummary + effective_status |
| **Dashboard** | 仅 read model + alerts |

```text
ShopBinding (DB)
  → projection job / on-read assemble
  → ShopConnectionSummary
  → Dashboard module A/B
```

---

## 9. 数据来源（实现参考 · 非 12d）

| 信号 | 来源 |
|------|------|
| heartbeat | AutoReplyThread / connector（现有） |
| last_inbound | 入站消息时间戳 |
| last_outbound | ReplyLog `outcome=sent` |
| reply_mode | ShopBinding 列 |
| pause | Workspace / ShopBinding |

---

*Phase 12d · Connection Status Read Model · docs only*

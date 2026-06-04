# Phase 12b — ShopBinding & Connection State Model

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 关联 | [phase12b_data_model_plan.md](phase12b_data_model_plan.md) · [phase12a_shop_binding_playbook.md](phase12a_shop_binding_playbook.md) |

---

## 1. ShopBinding 实体

| 字段 | 类型 | MVP | 说明 |
|------|------|-----|------|
| `shop_binding_id` | UUID | ✅ | PK |
| `workspace_id` | FK | ✅ | 租户隔离 |
| `platform_id` | enum | ✅ | `pinduoduo` \| `doudian` \| `taobao` \| `jingdong` |
| `shop_id` | string | ✅ | 平台侧店铺 ID |
| `shop_name` | string | ✅ | 展示 |
| `shop_logo_url` | string | 可选 | |
| `account_id` | string | ✅ | 平台侧客服/子账号 ID（PDD user_id） |
| `account_display_name` | string | 可选 | 客服名 |
| `credential_ref_id` | FK | ✅ | 凭证抽象 |
| `binding_status` | enum | ✅ | 授权生命周期 |
| `connection_status` | enum | ✅ | 运行时健康 |
| `inbound_status` | enum | ✅ | 收消息健康 |
| `outbound_status` | enum | ✅ | 发消息健康 |
| `reply_mode` | enum | ✅ | preview / assisted / auto（**≠ 发送许可**，须 intent gate） |
| `consultation_only` | bool | ✅ | 默认 **true**；售前咨询范围（12b.1） |
| `default_reply_scope` | JSON | 可选 | allowlist intent 覆盖；与 `consultation_only` 二选一或并存 |
| `shop_pause` | bool | ✅ | 单店暂停（与 workspace_pause 叠加） |
| `waitlist` | bool | 可选 | 非 PDD MVP 平台 |
| `last_heartbeat_at` | datetime | ✅ | 连接器心跳 |
| `last_inbound_at` | datetime | ✅ | 最后收消息 |
| `last_outbound_at` | datetime | ✅ | 最后成功发送 |
| `last_error_code` | string | 可空 | 对内 |
| `last_error_message` | string | 可空 | 商家友好文案 |
| `auto_enabled_at` | datetime | 可空 | 二次确认开启 auto 时间 |
| `auto_enabled_by` | FK merchant | 可空 | 审计 |
| `created_at` | datetime | ✅ | |
| `updated_at` | datetime | ✅ | |

**唯一约束（建议）：** `(workspace_id, platform_id, shop_id, account_id)`。

---

## 2. binding_status（授权生命周期）

| 状态 | 含义 | 商家 UI |
|------|------|---------|
| `unbound` | 未开始绑定 | 「去绑定」 |
| `binding` | 授权流程进行中 | 「连接中…」 |
| `connected` | 授权成功且通过健康检查 | 「已连接」 |
| `expired` | token/会话过期 | 「授权已过期 · 重新授权」 |
| `disabled` | 商家或平台禁用 | 「已停用」 |
| `error` | 不可恢复错误 | 「连接异常」+ 原因 |
| `waitlist` | 平台未开放（抖店/淘宝/京东 MVP） | 「即将支持」 |

**非 PDD production 规则：**

- `platform_id != pinduoduo` 在 MVP **不得** 设为 `connected` 用于真实收发；最高 `waitlist` 或 `unbound` + 预约标记。
- Doudian mock 工程能力 **不** 映射为 `connected`。

---

## 3. connection_status（综合健康）

| 状态 | 含义 |
|------|------|
| `unknown` | 初始 / 未探测 |
| `healthy` | 收+发正常 |
| `degraded` | 部分异常（如仅发送失败率高） |
| `offline` | 心跳超时 |
| `auth_failed` | 凭证无效 |
| `send_failed` | 发送通道异常 |
| `receive_failed` | 收消息异常 |

**派生逻辑（设计）：**

```text
if binding_status != connected → connection 不展示 healthy
elif inbound_status fail OR outbound_status fail → degraded / specific
elif heartbeat stale → offline
else → healthy
```

### inbound_status / outbound_status（分项）

| 值 | 说明 |
|----|------|
| `ok` | 正常 |
| `stale` | 超时无消息/无发送 |
| `failed` | 错误率超阈 |
| `not_applicable` | waitlist / preview-only 无探测 |

---

## 4. reply_mode（回复模式 · 与 binding / intent 正交）

| 值 | 含义 | 默认 |
|----|------|------|
| `preview` | 只生成建议，**不发送** | **✅ 新绑定** |
| `assisted` | 商家确认后发送（须过 send gate） | Growth |
| `auto` | 仅 **allowed consultation intent + 高置信** 可自动发送 | 须二次确认 |

**`reply_mode` 与 `intent gate` 分离：** `reply_mode` 决定「是否允许进入发送流程」；`intent` + `consultation_only` 决定「本条消息是否可 auto send」。详见 [phase12b1_intent_boundary.md](phase12b1_intent_boundary.md)。

**`consultation_only`（12b.1）：** 新绑定默认 `true`。为 `false` 时仅 Growth/Pro 且须额外合规确认（非 MVP）。

**`paused` 不是 reply_mode 枚举值**，而是控制标志（见 reply_mode doc）：

- `workspace_pause=true` OR `shop_pause=true` → **有效模式 = paused**，覆盖 preview/assisted/auto 的**发送**行为。

---

## 5. 核心不变量（12a / 12b SSOT）

| # | 不变量 |
|---|--------|
| 1 | **`binding_status=connected` ≠ `reply_mode=auto`** |
| 2 | 新绑定 **`reply_mode` 默认 `preview`** |
| 3 | **`paused` 优先级最高** — 禁止 auto/assisted 发送 |
| 4 | `waitlist` 平台 **不能** production `connected`（不得标「已连接可收发」） |
| 5 | 开启 `auto` 须写 `auto_enabled_at` + `AuditLog` + 确认售前咨询范围 |
| 6 | 默认 `consultation_only=true`；**refund/complaint/after-sales** → human takeover by default（产品，12c 实现） |

```text
商家可见「已连接」+ 「仅预览模式」  ← 正常且推荐初始状态
商家可见「已连接」+ 「自动回复已开启」 ← 须曾二次确认
```

---

## 6. 状态转换（binding_status）

```text
unbound → binding → connected
connected → expired（token TTL）
connected → error（连续失败）
connected → disabled（商家停用）
expired → binding（重新授权）
error → binding（重试）
任意 → disabled（管理员）
```

**进入 `connected` 条件：**

- 凭证 `CredentialRef.status=active`
- 健康检查通过（inbound/outbound 探针）
- `platform_id=pinduoduo` 且 MVP 平台开关允许

---

## 7. 与运行时 / 队列

| 项 | 说明 |
|----|------|
| PDD queue | 仍为 `pdd_{shop_id}`（工程不变） |
| SaaS 映射 | `ShopBinding` 提供 shop_id + credential_ref → 运行时加载 |
| 未 connected | **不启动** AutoReplyThread / 连接器 |

---

## 8. ConnectionStatus 嵌入 vs 分表

**MVP：** 字段嵌入 `ShopBinding`（`connection_status`, `inbound_status`, `outbound_status`）。

**后期：** 高频心跳可写 `connection_status_history` 时序表。

---

*Phase 12b · ShopBinding State*

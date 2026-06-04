# Phase 12b — Data Model Plan（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | **数据模型设计**（docs only；**无 DB migration**） |
| 目标 | 从**本地单租户工具模型** → **SaaS 多租户模型** |
| 前置 | [phase12a_done.md](phase12a_done.md) |
| 实现 | **未开始**（12e+ migration / API） |

---

## 1. Phase 12b 目标

| 项 | 说明 |
|----|------|
| 定义对象 | Merchant、Workspace、ShopBinding、CredentialRef、控制与计量 |
| 定义状态机 | binding / connection / reply_mode / pause |
| 对齐 12a 产品 | Preview 默认、connected ≠ auto、平台托管 AI |
| **不做** | SQL migration、ORM 改动、API 实现 |

---

## 2. 与现有工程映射（legacy）

当前桌面版 DB（`database/models.py`）：

```text
Channel (channel_name = platform_id)
  → Shop (shop_id)
    → Account (user_id, username, password, cookies, status)
```

**演进策略（设计，非本 Phase 执行）：**

| Legacy | SaaS 目标 |
|--------|-----------|
| 隐式「本机用户」 | `Merchant` + `Workspace` |
| `Channel/Shop/Account` 行 | `ShopBinding` + `CredentialRef` |
| `account_data` dict | `ShopBinding` 读模型 + 运行时 cache |
| 明文 password/cookies 列 | **废弃展示**；迁入 `CredentialRef.encrypted_payload_ref` |

PDD 生产路径（`AutoReplyThread`、`pdd_{shop_id}`）在 migration 完成前 **继续读 legacy 表**。

---

## 3. 核心对象列表

| 对象 | MVP | 后期 | 文档 |
|------|-----|------|------|
| **Merchant** | ✅ | — | [merchant_workspace_model.md](phase12b_merchant_workspace_model.md) |
| **Workspace** | ✅ | — | 同上 |
| **WorkspaceMember** | 模型预留 | RBAC UI | 同上 |
| **ShopBinding** | ✅ | — | [shop_binding_state_model.md](phase12b_shop_binding_state_model.md) |
| **CredentialRef** | ✅ | vault/KMS | [credential_security_model.md](phase12b_credential_security_model.md) |
| **ConnectionStatus** | ✅ 嵌入 ShopBinding | 分表可选 | shop_binding |
| **ReplyMode** | ✅ | — | [reply_mode_and_control_model.md](phase12b_reply_mode_and_control_model.md) |
| **SafetySettings** | ✅ 基础字段 | 规则引擎 | reply_mode |
| **UsageMeter** | ✅ | 实时流 | [plan_usage_model.md](phase12b_plan_usage_model.md) |
| **PlanSubscription** | ✅ | 发票/税务 | plan_usage |
| **AuditLog** | ✅ 最小 | 全量审计 | 本文 §4 |
| **ReplyLog** | ✅ | 检索/导出 | 本文 §4 |

---

## 4. AuditLog / ReplyLog（概要）

### ReplyLog（商家可见 · 业务审计）

| 字段 | MVP | 说明 |
|------|-----|------|
| `reply_log_id` | ✅ | PK |
| `workspace_id` | ✅ | 租户 |
| `shop_binding_id` | ✅ | 店 |
| `platform_id` | ✅ | |
| `conversation_id` | ✅ | 平台会话 ID |
| `buyer_id_redacted` | ✅ | 脱敏买家 ID |
| `inbound_summary` | ✅ | 摘要，非全文可选 |
| `suggested_reply` | ✅ | AI 建议 |
| `actual_reply` | 可空 | 仅 sent 时有 |
| `reply_mode_at_time` | ✅ | preview/assisted/auto |
| `outcome` | ✅ | preview_only / sent / blocked / transfer / failed |
| `blocked_reason` | 可空 | |
| `transfer_reason` | 可空 | |
| `ai_provider` | ✅ | `platform_hosted` / `byok` |
| `created_at` | ✅ | |

**禁止：** 完整 cookie、password、raw token 进入 ReplyLog。

### AuditLog（操作审计 · 管理员/合规）

| 字段 | MVP | 说明 |
|------|-----|------|
| `audit_log_id` | ✅ | |
| `workspace_id` | ✅ | |
| `actor_merchant_id` | ✅ | 谁操作 |
| `action` | ✅ | e.g. `reply_mode.auto_enabled`, `global_pause.on` |
| `target_type` | ✅ | shop_binding / workspace / subscription |
| `target_id` | ✅ | |
| `payload_json` | ✅ | 无敏感字段 |
| `ip_hash` | 后期 | |
| `created_at` | ✅ | |

---

## 5. MVP 必须 vs 后期扩展

| 能力 | MVP 必须 | 后期 |
|------|----------|------|
| 单 Merchant 单 Workspace owner | ✅ | 多 member |
| ShopBinding + 状态机 | ✅ | 分 region |
| CredentialRef 抽象 | ✅ | cloud KMS |
| reply_mode=preview 默认 | ✅ | — |
| workspace_pause + shop pause | ✅ | 定时 pause |
| SafetySettings 模板 | ✅ | 可视化规则 builder |
| UsageMeter 月度 | ✅ | 实时计费 |
| PlanSubscription Starter/Growth | ✅ | Pro 合同 |
| ReplyLog 查询 7–30 天 | ✅ | 90 天 + 导出 |
| waitlist 平台 binding | `binding_status=waitlist` | production connect |

---

## 6. 实体关系（ER 概要）

```text
Merchant ──< WorkspaceMember >── Workspace
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
            PlanSubscription  SafetySettings  UsageMeter
                    │
            ShopBinding ──> CredentialRef
                    │
                 ReplyLog (1:N)
```

---

## 7. 子文档索引

| 文档 | 内容 |
|------|------|
| [phase12b_merchant_workspace_model.md](phase12b_merchant_workspace_model.md) | Merchant / Workspace / Member |
| [phase12b_shop_binding_state_model.md](phase12b_shop_binding_state_model.md) | ShopBinding 状态机 |
| [phase12b_credential_security_model.md](phase12b_credential_security_model.md) | CredentialRef 安全 |
| [phase12b_reply_mode_and_control_model.md](phase12b_reply_mode_and_control_model.md) | ReplyMode / Safety / Pause |
| [phase12b_plan_usage_model.md](phase12b_plan_usage_model.md) | Plan / Usage |

---

## 8. Phase 12b 禁止项

- DB migration / Alembic
- 修改 `database/models.py`
- 修改 UI / AutoReplyThread / Channel 代码
- 默认 `reply_mode=auto` 或默认注册 Doudian production

---

*Phase 12b · Data Model Plan · docs only*

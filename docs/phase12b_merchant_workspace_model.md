# Phase 12b — Merchant / Workspace / Member Model

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 关联 | [phase12b_data_model_plan.md](phase12b_data_model_plan.md) · [phase12a_merchant_onboarding_ux.md](phase12a_merchant_onboarding_ux.md) |

---

## 1. Merchant（登录主体）

| 字段 | 类型 | MVP | 说明 |
|------|------|-----|------|
| `merchant_id` | UUID / string | ✅ | 全局唯一 |
| `email` | string | ✅ | 登录标识之一 |
| `phone` | string | 可选 | 国内主登录 |
| `display_name` | string | ✅ | 展示名 |
| `status` | enum | ✅ | `active` / `suspended` / `deleted` |
| `created_at` | datetime | ✅ | |
| `updated_at` | datetime | ✅ | |

**不包含（MVP）：** 店铺凭证、API Key（BYOK 放 Workspace 级设置）。

---

## 2. Workspace（租户 / 组织）

| 字段 | 类型 | MVP | 说明 |
|------|------|-----|------|
| `workspace_id` | UUID | ✅ | 计费与数据隔离边界 |
| `owner_merchant_id` | FK | ✅ | 创建者；默认 owner |
| `name` | string | ✅ | 「我的工作区」 |
| `status` | enum | ✅ | `active` / `suspended` / `closed` |
| `plan_id` | FK | ✅ | 当前套餐 |
| `workspace_pause` | bool | ✅ | **全局暂停**自动发送（12a） |
| `ai_provider_mode` | enum | ✅ | `platform_hosted`（默认）/ `byok` |
| `created_at` | datetime | ✅ | |
| `updated_at` | datetime | ✅ | |

**一个 Workspace 可绑定多个 ShopBinding（多店）。**

---

## 3. WorkspaceMember（成员 · RBAC 预留）

| 字段 | 类型 | MVP | 说明 |
|------|------|-----|------|
| `workspace_member_id` | UUID | 预留 | MVP 可仅 seed owner 一行 |
| `workspace_id` | FK | ✅ | |
| `merchant_id` | FK | ✅ | |
| `role` | enum | ✅ | 见下表 |
| `permissions` | JSON / bitmask | 预留 | 细粒度后期 |
| `status` | enum | ✅ | `invited` / `active` / `removed` |
| `invited_at` | datetime | 预留 | |
| `joined_at` | datetime | ✅ | owner 即 created_at |

### 3.1 Role 定义

| role | 说明 | MVP |
|------|------|-----|
| `owner` | 全权限、计费、删 workspace | ✅ 仅 owner |
| `admin` | 绑店、改规则、开 auto、邀请成员 | 后期 |
| `operator` | 看日志、确认 assisted、暂停 | 后期 |
| `viewer` | 只读日志与状态 | 后期 |

### 3.2 Permissions（后期扩展示例）

```text
shop.bind
shop.unbind
reply_mode.change
safety.edit
billing.view
billing.manage
member.invite
logs.view
logs.export
global_pause.toggle
```

MVP：**不实现** 邀请流；代码路径假定 `owner_merchant_id` 有全部权限。

---

## 4. 关系规则

| 规则 | 说明 |
|------|------|
| 一 Merchant 多 Workspace | 代运营可为不同客户建 workspace |
| 一 Merchant 多 WorkspaceMember | 可被邀请进他人 workspace |
| 一 Workspace 多 ShopBinding | 多店管理 |
| 计费主体 | **Workspace**（非 Merchant） |
| AI 额度 | Workspace 级 `UsageMeter` |

```text
Merchant A ──owner──> Workspace「我的拼多多店」
                 └──> ShopBinding (PDD shop 1)
                 └──> ShopBinding (PDD shop 2)

Merchant A ──operator──> Workspace「客户X-代运营」（后期）
Merchant B ──owner──>     同上
```

---

## 5. 代运营 / 外包场景

| 需求 | 模型支持 |
|------|----------|
| 客户不让代运营看到密码 | `CredentialRef` 抽象；代运营无 decrypt 权限（后期） |
| 客户只读报表 | `viewer` role |
| 操作审计 | `AuditLog.actor_merchant_id` |

---

## 6. MVP 简化 vs 预留

| MVP | 预留 |
|-----|------|
| 注册即创建 1 Workspace + owner member | 多 workspace 切换 UI |
| 无邀请 | `invited` status + email invite |
| `permissions` 空 = 全权 | JSON schema 版本化 |

---

## 7. 与 legacy 映射

| SaaS | Legacy（当前） |
|------|----------------|
| Workspace | 无（本机单用户） |
| ShopBinding | Shop + Account 行组合 |
| `platform_id` | `channel_name` |

Migration（12e）：`workspace_id` 写入新表；legacy 行 `workspace_id NULL` 表示未迁移。

---

*Phase 12b · Merchant / Workspace*

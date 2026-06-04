# Phase 12b — Credential Security Model（CredentialRef）

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 关联 | [phase12a_shop_binding_playbook.md](phase12a_shop_binding_playbook.md) |

---

## 1. 设计原则

| 原则 | 说明 |
|------|------|
| **不存明文密码于业务表** | UI / ShopBinding / ReplyLog 无 password 字段 |
| **CredentialRef 间接引用** | 加密载荷存后端；业务只持 `credential_ref_id` |
| **长期 OAuth 优先** | Playwright/cookie **过渡** |
| **过期驱动状态** | → `binding_status=expired` + `connection_status=auth_failed` |
| **日志脱敏** | token/cookie/password 不得进入普通 logs（延续 7i/7j） |

---

## 2. CredentialRef 实体

| 字段 | 类型 | MVP | 说明 |
|------|------|-----|------|
| `credential_ref_id` | UUID | ✅ | PK |
| `workspace_id` | FK | ✅ | 租户隔离 |
| `platform_id` | enum | ✅ | |
| `shop_binding_id` | FK | ✅ | 可空：BYOK 可能 workspace 级 |
| `credential_type` | enum | ✅ | 见 §3 |
| `storage_backend` | enum | ✅ | 见 §4 |
| `encrypted_payload_ref` | string | ✅ | KMS key id / blob path / vault path |
| `expires_at` | datetime | 可空 | OAuth refresh 策略 |
| `rotated_at` | datetime | 可空 | |
| `last_validated_at` | datetime | ✅ | 探针时间 |
| `status` | enum | ✅ | 见 §5 |
| `created_at` | datetime | ✅ | |
| `updated_at` | datetime | ✅ | |

**禁止出现在 CredentialRef 之外的持久化：** 明文 `password`、`cookies` JSON 于 `accounts` 表（migration 目标：废弃列或加密迁移）。

---

## 3. credential_type

| 类型 | 用途 | MVP PDD | 长期 |
|------|------|---------|------|
| `oauth_token` | access + refresh | 目标 | ✅ 主路径 |
| `refresh_token` | 仅 refresh 句柄 | 可选 | ✅ |
| `cookie_bundle` | 会话 cookie | **过渡** | 淘汰 |
| `session_ref` | 托管连接器内部会话 ID | 过渡 | 托管 |
| `api_key` | 平台开放 API key | 少见 | 按平台 |
| `byok_key` | 商家自带 AI Key | ❌ MVP | Pro/Enterprise |

**BYOK：** 存 `workspace` 级 `CredentialRef`，`credential_type=byok_key`，**不**与店铺 IM 凭证混用。

---

## 4. storage_backend

| 值 | 场景 |
|----|------|
| `local_encrypted` | 桌面过渡 / 开发 |
| `cloud_kms` | **SaaS 生产目标** |
| `external_vault` | 企业版 HashiCorp 等 |

MVP SaaS 设计目标：**cloud_kms**；不在 12b 实现。

---

## 5. status

| 状态 | 含义 | 触发 ShopBinding |
|------|------|------------------|
| `active` | 可用 | `connected` 前提 |
| `expiring` | TTL < 7d | Dashboard 黄条 |
| `expired` | 不可用 | `binding_status=expired` |
| `revoked` | 商家撤销授权 | `disabled` |
| `invalid` | 校验失败 | `error` / `auth_failed` |

---

## 6. 生命周期

```text
创建（授权回调 / 安全登录向导）
  → encrypt(payload) → encrypted_payload_ref
  → status=active, last_validated_at=now

定时校验
  → 成功：刷新 last_validated_at
  → 失败：status=invalid → 商家提示重新授权

OAuth refresh
  → rotated_at=now, 新 expires_at

商家撤销
  → status=revoked, 删除或封存 payload
```

---

## 7. Playwright / 密码过渡方案

| 项 | 要求 |
|----|------|
| 存储 | 仅 `encrypted_payload_ref`；算法 AES-GCM + per-workspace DEK |
| UI | **不得**「您的密码将明文保存」；改为「安全连接」 |
| 营销 | **不作为** SaaS 主卖点 |
| 迁移 | legacy `accounts.password` / `cookies` → 一次性导入 CredentialRef 后清空明文列（12e） |

---

## 8. Redaction 策略

| 场景 | 规则 |
|------|------|
| ReplyLog | 无 token/cookie |
| AuditLog | payload 仅 action 元数据 |
| 应用 log | `format_account_ref` 类脱敏延续 |
| 错误 message | 商家可见文案不含 secret |
| 支持导出 | 导出前扫描敏感键 |

---

## 9. 与 connection 联动

```text
CredentialRef.status in (expired, invalid, revoked)
  → ShopBinding.binding_status = expired | error
  → connection_status = auth_failed
  → 禁止 auto/assisted 发送（仍可 preview 可选：否 — 建议 preview 也暂停直到 auth 修复）
```

**推荐：** auth 失效时 **停止新生成 AI 建议**，避免商家依赖无效连接。

---

*Phase 12b · Credential Security*

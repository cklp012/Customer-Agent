# Phase 12e — Product Gate Tables（DDL Planning · SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only · **非 executable migration** |
| PK 类型 | UUID（SaaS）；legacy 保持 Integer |

---

## 1. `merchants`

| 列 | 类型 | 说明 |
|----|------|------|
| `merchant_id` | UUID PK | |
| `phone` | string unique? | 登录 |
| `display_name` | string | |
| `status` | enum | active / suspended |
| `created_at` | datetime | |
| `updated_at` | datetime | |

| 项 | 值 |
|----|-----|
| **目的** | 商家自然人 |
| **MVP** | ✅（桌面可单例） |
| **索引** | `UNIQUE(phone)` |
| **约束** | status 非 null |

---

## 2. `workspaces`

| 列 | 类型 | 说明 |
|----|------|------|
| `workspace_id` | UUID PK | |
| `owner_merchant_id` | UUID FK → merchants | |
| `name` | string | |
| `plan_id` | string FK → plan_limits | |
| `workspace_pause` | bool default false | |
| `ai_provider_mode` | enum | platform_hosted / byok |
| `status` | enum | active / suspended |
| `created_at` | datetime | |
| `updated_at` | datetime | |

| 项 | 值 |
|----|-----|
| **目的** | 租户、计费、全局暂停 |
| **MVP** | ✅ |
| **索引** | `(owner_merchant_id)` |
| **约束** | `workspace_pause` 与 12d PauseStateSummary 一致 |

---

## 3. `workspace_members`

| 列 | 类型 |
|----|------|
| `member_id` | UUID PK |
| `workspace_id` | UUID FK |
| `merchant_id` | UUID FK |
| `role` | enum: owner / admin / agent / readonly |
| `created_at` | datetime |

| 项 | 值 |
|----|-----|
| **MVP** | 预留（单用户可仅 owner） |
| **索引** | `UNIQUE(workspace_id, merchant_id)` |

---

## 4. `shop_bindings`

| 列 | 类型 | 说明 |
|----|------|------|
| `shop_binding_id` | UUID PK | |
| `workspace_id` | UUID FK | |
| `platform_id` | enum | pinduoduo / doudian / … |
| `shop_id` | string | 平台店 ID |
| `shop_name` | string | |
| `shop_logo_url` | string? | |
| `account_id` | string | 平台客服 user_id |
| `account_display_name` | string? | |
| `credential_ref_id` | UUID FK? | |
| `legacy_shop_id` | int? | 映射 `shops.id` · M2 |
| `legacy_account_id` | int? | 映射 `accounts.id` · M2 |
| `binding_status` | enum | unbound / binding / connected / … |
| `connection_status` | enum | unknown / healthy / offline / … |
| `inbound_status` | enum | ok / stale / failed / n/a |
| `outbound_status` | enum | ok / stale / failed / n/a |
| `reply_mode` | enum default **preview** | preview / assisted / auto |
| `consultation_only` | bool default **true** | |
| `product_gate_enabled` | bool default **false** | |
| `shop_pause` | bool default false | |
| `waitlist` | bool default false | |
| `auto_enabled_at` | datetime? | |
| `auto_enabled_by` | UUID FK? | |
| `last_heartbeat_at` | datetime? | |
| `last_inbound_at` | datetime? | |
| `last_outbound_at` | datetime? | |
| `last_error_code` | string? | |
| `last_error_message` | string? | |
| `created_at` | datetime | |
| `updated_at` | datetime | |

| 项 | 值 |
|----|-----|
| **目的** | 产品 gate 主实体；Dashboard connection 卡片 |
| **MVP** | ✅ |
| **唯一约束** | `UNIQUE(workspace_id, platform_id, shop_id, account_id)` |
| **索引** | `(workspace_id, binding_status)`；`(platform_id, shop_id)` |
| **关键** | `connected` + `reply_mode=preview` → **非** auto enabled |

---

## 5. `credential_refs`

| 列 | 类型 |
|----|------|
| `credential_ref_id` | UUID PK |
| `workspace_id` | UUID FK |
| `shop_binding_id` | UUID FK |
| `platform_id` | enum |
| `credential_type` | enum | session_cookie / oauth_token / password_vault |
| `storage_backend` | enum | local_encrypted / kms / vault |
| `encrypted_payload_ref` | string | 指针，非明文 |
| `expires_at` | datetime? |
| `rotated_at` | datetime? |
| `last_validated_at` | datetime? |
| `status` | enum | active / expiring / expired / revoked |
| `created_at` | datetime |
| `updated_at` | datetime |

| 项 | 值 |
|----|-----|
| **目的** | 替代 UI/DB 明文 password、cookies |
| **MVP** | ✅ shadow（M3） |
| **索引** | `(shop_binding_id)` unique |
| **约束** | 应用层禁止返回 `encrypted_payload` 给前端 |

---

## 6. `safety_settings`

| 列 | 类型 |
|----|------|
| `safety_settings_id` | UUID PK |
| `workspace_id` | UUID FK |
| `shop_binding_id` | UUID FK nullable |
| `forbidden_promises` | JSON |
| `sensitive_keywords` | JSON |
| `human_takeover_keywords` | JSON |
| `low_confidence_threshold` | float default 0.85 |
| `after_sales_to_human` | bool default true |
| `complaint_to_human` | bool default true |
| `max_auto_replies_per_conversation` | int |
| `quiet_hours` | JSON |
| `updated_by` | UUID FK |
| `updated_at` | datetime |

| 项 | 值 |
|----|-----|
| **MVP** | ✅ workspace 默认一行 |
| **索引** | `UNIQUE(workspace_id, shop_binding_id)` nullable 部分唯一 |
| **约束** | shop_binding_id NULL = workspace 默认 |

---

## 7. `audit_logs`

| 列 | 类型 |
|----|------|
| `audit_log_id` | UUID PK |
| `workspace_id` | UUID FK |
| `actor_merchant_id` | UUID FK |
| `action` | string | workspace.pause / shop.reply_mode_changed / … |
| `target_type` | string | workspace / shop_binding |
| `target_id` | UUID |
| `before_json` | JSON? |
| `after_json` | JSON? |
| `ip_address` | string? |
| `user_agent` | string? |
| `created_at` | datetime |

| 项 | 值 |
|----|-----|
| **目的** | pause / resume / reply-mode / auto enable（12d API） |
| **MVP** | ✅ |
| **索引** | `(workspace_id, created_at DESC)`；`(target_type, target_id)` |
| **约束** | append-only |

---

## 8. `plan_limits` / `plan_subscriptions` / `usage_meters`

### `plan_limits`

| 列 | 说明 |
|----|------|
| `plan_id` | PK string starter / growth / pro |
| `ai_suggestions_limit` | int |
| `auto_sent_limit` | int |
| `shops_limit` | int |
| `log_retention_days` | int |

### `plan_subscriptions`

| 列 | 说明 |
|----|------|
| `subscription_id` | UUID PK |
| `workspace_id` | FK |
| `plan_id` | FK |
| `status` | active / cancelled |
| `renews_at` | datetime |

### `usage_meters`（明细见 send_decision doc）

| 项 | MVP |
|----|-----|
| **目的** | Dashboard 模块 G |
| **索引** | `UNIQUE(workspace_id, period_start)` |

---

## 9. ER 简图

```text
Merchant ──< WorkspaceMember >── Workspace
                  │
                  ├──< ShopBinding >── CredentialRef
                  │         │
                  │         ├── SafetySettings (optional override)
                  │         ├── SendDecision ── ReplyLog
                  │         └── HumanTakeoverQueue
                  ├── SafetySettings (default)
                  ├── AuditLog
                  ├── UsageMeter
                  └── PlanSubscription ── PlanLimit
```

---

## 10. 与 legacy 共存

新表使用 **前缀或 schema** `saas_*` 可选；M1 建议 **同 SQLite 文件新表名**（`shop_bindings` 等），不 DROP legacy。

---

*Phase 12e · Product Gate Tables · docs only*

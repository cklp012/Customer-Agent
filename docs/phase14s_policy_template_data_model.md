# Phase 14s — Policy and Template Data Model

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不建表** |
| 未来表名 | `merchant_safety_policies` · `merchant_reply_templates`（`product_gate.db` shadow · 14u） |

---

## 1. MerchantSafetyPolicy

| 列 | 类型 | 必填 | 说明 |
|----|------|------|------|
| `policy_id` | TEXT PK | ✅ | UUID |
| `workspace_id` | TEXT | ✅ | 租户 |
| `shop_id` | TEXT | ✅ | 店铺 |
| `intent_category` | TEXT | ✅ | 归一分类 key |
| `ai_intervention_mode` | TEXT | ✅ | 五档 enum |
| `platform_mode_ceiling` | TEXT | ✅ | 系统写入或 seed · 商家只读参考 |
| `allowed_template_ids` | TEXT | | JSON array · 允许的 template_id 列表 |
| `require_human_confirmation` | INTEGER | ✅ | 0/1 · assisted 强制确认 |
| `allow_auto_reply` | INTEGER | ✅ | 0/1 · 与 mode 冗余校验 |
| `forbidden_keywords_extra` | TEXT | | JSON array · **仅加严** · 不可删平台禁词 |
| `policy_version` | INTEGER | ✅ | 变更递增 |
| `enabled` | INTEGER | ✅ | 0/1 |
| `created_at` | TEXT | ✅ | ISO8601 |
| `updated_at` | TEXT | ✅ | ISO8601 |

**约束（future · 14u）：**

- UNIQUE `(shop_id, intent_category)` 或 `(workspace_id, shop_id, intent_category)`
- `ai_intervention_mode` ≤ `platform_mode_ceiling`（应用层 + DB check 可选）
- 不 FK legacy tables

---

## 2. MerchantReplyTemplate

| 列 | 类型 | 必填 | 说明 |
|----|------|------|------|
| `template_id` | TEXT PK | ✅ | UUID |
| `workspace_id` | TEXT | ✅ | |
| `shop_id` | TEXT | ✅ | |
| `intent_category` | TEXT | ✅ | |
| `title` | TEXT | ✅ | 商家可见标题 |
| `content` | TEXT | ✅ | 模板正文 · 含 `{variable}` |
| `variables` | TEXT | | JSON · 白名单变量 schema |
| `content_hash` | TEXT | ✅ | SHA256 · 变更检测 |
| `validation_status` | TEXT | ✅ | `pending_review` · `passed` · `rejected` |
| `validation_warnings` | TEXT | | JSON array |
| `template_version` | INTEGER | ✅ | 内容变更递增 |
| `enabled` | INTEGER | ✅ | 0/1 · rejected 不可 enabled |
| `created_at` | TEXT | ✅ | ISO8601 |
| `updated_at` | TEXT | ✅ | ISO8601 |

**`validation_status` 规则：**

| 值 | 含义 |
|----|------|
| `pending_review` | 可疑但未命中硬红线 · 人工复核 |
| `passed` | 保存 scan 通过 · **发送仍须 final guard** |
| `rejected` | 命中禁诺/红线 · 不可 enable |

---

## 3. 类型约定

| 项 | 约定 |
|----|------|
| enum | **TEXT**（非 SQLite native enum） |
| timestamps | **ISO8601 TEXT** |
| JSON 字段 | `allowed_template_ids` · `variables` · `validation_warnings` · `forbidden_keywords_extra` |
| versioning | `policy_version` · `template_version` |

---

## 4. 历史与追溯

| 规则 | 说明 |
|------|------|
| 配置变更 **不 retroactive** 改历史 ReplyLog | 旧记录保留当时 snapshot |
| 发送/记录时点 | 写入 `policy_id` · `policy_version` · `template_id` · `template_version`（见 snapshot doc） |
| 缺省 policy | 使用 [default_policy_matrix](phase14s_default_policy_matrix.md) |

---

## 5. AuditLog actions（future · 14q repository）

| action | 触发 |
|--------|------|
| `merchant_policy_changed` | policy create/update/disable |
| `template_created` | 新模板 |
| `template_updated` | 内容/version 变更 |
| `template_disabled` | enabled=0 或 rejected |

append-only · 不 DELETE · 见 [phase14s_policy_snapshot_and_audit.md](phase14s_policy_snapshot_and_audit.md)

---

## 6. 模块归属（规划）

| 项 | 建议 |
|----|------|
| 存储 | `product_gate.db` shadow（与 14l–14q 一致） |
| 逻辑目录 | `product_persistence/merchant_policy/` 或 `product_config/`（14u 定） |
| flags（future） | `PRODUCT_PERSISTENCE_WRITE_MERCHANT_POLICY` · `..._TEMPLATES` 默认 off |

---

*Phase 14s · planning only · 2026-06-03*

# Phase 14z — Filters, Permissions, and Pagination

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14z_pending_list_api_contract.md](phase14z_pending_list_api_contract.md) · [phase12d_api_contract.md](phase12d_api_contract.md) |

---

## 1. Scope 校验

| 规则 | 说明 |
|------|------|
| workspace scope | 请求 `workspace_id` **必须**等于 auth member.workspace_id |
| shop scope | member 仅授权 shop 列表内 · 跨 shop 403 |
| 跨 workspace | **禁止** · 403 |
| platform_id | 可选 filter · 不 bypass scope |

---

## 2. 角色权限

| 角色 | list | detail 完整文本 | approve/reject |
|------|------|-----------------|----------------|
| owner | ✅ 全 workspace | ✅ | ❌（14z/15c read） |
| admin | ✅ 授权 shops | ✅ | ❌ |
| operator | ✅ 授权 shops | ✅ | ❌ |
| viewer | ✅ 授权 shops | ⚠️ **可能脱敏** | ❌ |
| system | internal only | service · 非 Dashboard | ❌ |

### 2.1 Viewer 脱敏（规划）

| 字段 | viewer |
|------|--------|
| buyer_message | preview only 或 `[redacted]` |
| ai_suggested_reply | preview only |
| merchant_edited_reply | hidden |
| buyer_id | 可 hash 后 4 位 |

**operator/admin/owner：** detail 返回完整文本。

---

## 3. 默认 filters

| 默认 | 值 |
|------|-----|
| status（列表首次加载） | `pending` · `failed`（active queue） |
| sort_by | `created_at` |
| sort_order | `desc` |
| page_size | 20 |

**UI 可切换显示 terminal：** sent · rejected · expired · canceled。

---

## 4. Pagination

| 参数 | 规则 |
|------|------|
| `page` | ≥1 · 默认 1 |
| `page_size` | 默认 20 · **max 100** · 超过 → 400 或 clamp to 100（15c 实现时统一） |
| `total` | repository count · 非 estimate |
| `has_next` | `page * page_size < total` |

---

## 5. sort_by allowlist

**不允许任意 SQL sort/filter。**

| sort_by | 允许 |
|---------|------|
| `created_at` | ✅ |
| `updated_at` | ✅ |
| `expires_at` | ✅ |
| `risk_level` | ✅（映射序 low < medium < high） |
| `status` | ✅（枚举序） |
| 其他 | ❌ 400 |

| sort_order | `asc` \| `desc` |

---

## 6. 敏感字段脱敏

| 类别 | 列表 | detail（operator+） |
|------|------|---------------------|
| buyer_message | preview 80 chars | full |
| reply text | preview | full |
| credential / token | **never** | **never** |
| ip_address | omit list | optional admin |
| session_id / cookie | **never** | **never** |

Audit `before_state` / `after_state` 展示前 strip sensitive keys（对齐 14q repository sanitize）。

---

## 7. Read-only boundary

本 doc 定义的所有 API **仅 GET** — 无 mutation · 无 approve/reject/send。

---

*Phase 14z · planning only · 2026-06-03*

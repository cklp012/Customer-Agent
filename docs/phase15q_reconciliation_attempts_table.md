# Phase 15q — Reconciliation Attempts Table (Future)

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 表未创建** |
| 实现 | Phase **15t** behind flags |

---

## 1. 表名

`reconciliation_attempts` — product DB only · **无** legacy database FK。

---

## 2. 字段建议

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | TEXT (UUID) | ✅ | PK |
| `workspace_id` | TEXT | ✅ | 租户 |
| `shop_id` | TEXT | ✅ | 店 |
| `account_id` | TEXT | optional | PDD 账号 |
| `platform_id` | TEXT | ✅ | `pinduoduo` |
| `pending_assisted_id` | TEXT | ✅ | FK logical → `pending_assisted_replies` |
| `reply_log_id` | TEXT | optional | 关联 preview/reply |
| `outbound_idempotency_key` | TEXT | ✅ | 关联 `outbound_idempotency_keys` |
| `client_request_id` | TEXT | optional | dashboard action idempotency 追溯 |
| `buyer_id` | TEXT | ✅ | 平台查询用 |
| `trace_id` | TEXT | ✅ | 全链路 |
| `provider_message_id` | TEXT | optional | 弱/强信号 · 不伪造 |
| `attempt_no` | INTEGER | ✅ | 从 1 递增 · 同 pending+key |
| `attempt_type` | TEXT | ✅ | `automated` · `operator_triggered` · `scheduled` |
| `status` | TEXT | ✅ | 见 §3 |
| `platform_status_before` | TEXT | optional | e.g. `timeout_unknown` |
| `platform_status_after` | TEXT | optional | reconciliation 后 |
| `query_window_start` | TEXT | optional | ISO · 平台查询时间窗 |
| `query_window_end` | TEXT | optional | ISO |
| `matched_platform_message_id` | TEXT | optional | 平台确认 ID |
| `matched_message_text_hash` | TEXT | optional | SHA-256 · **不存全文** |
| `matched_at` | TEXT | optional | ISO |
| `operator_user_id` | TEXT | optional | 人工触发/确认 |
| `operator_role` | TEXT | optional | operator/admin/owner |
| `result_reason` | TEXT | ✅ | machine-readable summary |
| `error_code` | TEXT | optional | dashboard-safe |
| `error_message_sanitized` | TEXT | optional | **无 secrets** |
| `metadata_json` | TEXT | optional | 扩展 · 无 credential |
| `created_at` | TEXT | ✅ | ISO |
| `updated_at` | TEXT | ✅ | ISO |

---

## 3. `status` 枚举

| Status | 含义 |
|--------|------|
| `started` | 尝试开始 |
| `confirmed_sent` | 证据确认已发 |
| `confirmed_not_sent` | 证据确认未发 |
| `still_unknown` | 仍无法确认 |
| `platform_unavailable` | 平台 API 不可用 |
| `permission_error` | 凭证/权限 |
| `cancelled` | 人工取消本次尝试 |
| `failed` | 尝试逻辑失败（非 send 失败） |

---

## 4. 设计规则

| 规则 |
|------|
| **Append-first** — 新 attempt 新 row · **不 UPDATE 覆盖** 历史 attempt 结论 |
| `updated_at` 仅本 row 元数据 · 不改旧 attempt 的 `status` 含义 |
| **不存** cookie · token · credential · session blob |
| `final_reply` **不存** 本表 — 从 `pending_assisted_replies` 读 |
| 消息正文 → `matched_message_text_hash` only |

---

## 5. 建议索引（future）

| 索引 | 列 |
|------|-----|
| `idx_recon_pending` | `pending_assisted_id`, `created_at` |
| `idx_recon_idempotency` | `outbound_idempotency_key`, `attempt_no` |
| `idx_recon_workspace_shop_status` | `workspace_id`, `shop_id`, `status`, `updated_at` |
| `idx_recon_trace` | `trace_id` |
| `idx_recon_buyer` | `buyer_id`, `shop_id`, `created_at` |

---

## 6. 查询模式

| 用例 | 查询 |
|------|------|
| Manual review detail | `WHERE pending_assisted_id = ? ORDER BY attempt_no` |
| Idempotency timeline | `WHERE outbound_idempotency_key = ?` |
| Shop queue | `WHERE workspace_id = ? AND shop_id = ? AND status IN (...)` |
| Operator audit | `WHERE operator_user_id = ?` |

---

## 7. 与 audit 关系

每次 attempt 状态落地 → **append** `audit_logs`：

- `reconciliation_started`
- `reconciliation_confirmed_sent` / `_not_sent` / `_still_unknown`

**reconciliation_attempts 是结构化查询索引；audit 是不可变时间线 SSOT。**

---

*Phase 15q · planned table only · 2026-06-03*

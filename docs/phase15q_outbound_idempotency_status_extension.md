# Phase 15q — Outbound Idempotency Status Extension

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 表 | `outbound_idempotency_keys`（已存在 · **本 phase 不改**） |

---

## 1. 当前实现（15b）

| `status` 值 | 代码常量 |
|-------------|----------|
| `in_progress` | acquire 成功 |
| `succeeded` | `mark_succeeded` |
| `failed` | `mark_failed` |

**Acquire deny 语义（reason · 非 row status）：**

| existing `status` | acquire `reason` |
|-------------------|------------------|
| `succeeded` | `already_sent` |
| `in_progress` | `already_in_progress` |
| `failed` | `manual_review_required` |

---

## 2. 未来建议 `status` 扩展

| Status | 含义 | Terminal? | 可同 key 再 send? |
|--------|------|-----------|-------------------|
| `in_progress` | 锁定 · port 调用中 | no | ❌ |
| `succeeded` | 确认已发送 | **yes** | ❌ |
| `failed` | 平台明确失败/关闭 | **yes** | ❌ |
| `failed_before_send` | 确认未发出（pre-wire） | **yes** | ❌ |
| `timeout_unknown` | 超时 · 结果未知 | no* | ❌ auto |
| `sent_unconfirmed` | 弱信号可能已发 · 无 provider id | no | ❌ |
| `manual_review_required` | 需人工 | no | ❌ |
| `cancelled` | 人工取消 outbound 路径 | **yes** | ❌ auto |

\* `timeout_unknown` 可经 reconciliation → `succeeded` | `failed_before_send` | `manual_review_required` — **非** auto retry send。

---

## 3. 必须区分

| 对比 | 说明 |
|------|------|
| `timeout_unknown` vs `failed` | timeout **≠** 失败 · 可能已发 |
| `failed_before_send` vs `timeout_unknown` | 前者确认未离开发送层 · 后者不确定 |
| `succeeded` vs `sent_unconfirmed` | 后者无 provider_message_id · 需 reconciliation |

---

## 4. `platform_status` 列（已有）

复用现有 `platform_status` TEXT 字段存储 port 返回：

- `sent` · `rejected_by_platform` · `validation_failed` · `unavailable` · `timeout_unknown` · `live_send_not_implemented` 等

**`status`（idempotency 生命周期）与 `platform_status`（port 结果）成对更新 + audit。**

---

## 5. 行为规则

| 规则 |
|------|
| `succeeded` terminal — **禁止** 同 key 第二次 succeeded |
| `manual_review_required` — duplicate approve **deny** · reason `idempotency_manual_review_required` |
| `timeout_unknown` — acquire deny · **禁止** auto → `in_progress` via re-approve |
| `sent_unconfirmed` — 必须触发 reconciliation · 不得推断未发送 |
| `cancelled` — 不允许自动重试 · 新 send 需 **新 idempotency_key** |
| 每次 status 变更 → append audit |

---

## 6. 与 `reconciliation_attempts`

| 关联 |
|------|
| `outbound_idempotency_key` PK 关联 |
| reconciliation 确认 sent → `mark_succeeded` + `provider_message_id` if available |
| confirmed not sent → `failed_before_send` or `manual_review_required` |
| still unknown → 保持 `timeout_unknown` / → `manual_review_required` |

---

## 7. metadata_json（已有列）

可存（future · sanitized）：

- `trace_id` · `reconciliation_attempt_id` · `last_query_at`
- **禁止** raw credential

---

*Phase 15q · docs only · 2026-06-03*

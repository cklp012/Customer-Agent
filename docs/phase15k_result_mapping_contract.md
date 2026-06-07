# Phase 15k — Result Mapping Contract

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15h_timeout_unknown_and_reconciliation.md](phase15h_timeout_unknown_and_reconciliation.md) · [phase15c_done.md](phase15c_done.md) |

---

## 1. 映射原则

| # | 原则 |
|---|------|
| 1 | PDD primitive outcome → **`AssistedOutboundResult`**（15c 类型） |
| 2 | **`provider_message_id` 不能伪造** — 仅平台返回时填充 |
| 3 | **`timeout_unknown` 不能自动重发** |
| 4 | Error 不暴露 cookie / token / credential |
| 5 | Result echo **`trace_id`** · **`idempotency_key`** when available |

---

## 2. Outcome 映射表

### 2.1 success / sent

| 字段 | 值 |
|------|-----|
| `success` | `true` |
| `dry_run` | `false` |
| `would_send` | `true` |
| `platform_status` | `sent` |
| `provider_message_id` | 平台返回 · 无则 null |
| `sent_at` | ISO timestamp if available |
| `error_code` | null |

### 2.2 rejected_by_platform

| 字段 | 值 |
|------|-----|
| `success` | `false` |
| `platform_status` | `rejected_by_platform` |
| `error_code` | machine-readable |
| `error_message` | dashboard-safe · no secrets |

### 2.3 validation_failed（port-local）

| 字段 | 值 |
|------|-----|
| `success` | `false` |
| `platform_status` | `validation_failed` |
| `error_code` | e.g. `missing_buyer_id` · `empty_final_reply` |
| `would_send` | `false` |

### 2.4 unavailable

| 字段 | 值 |
|------|-----|
| `success` | `false` |
| `platform_status` | `unavailable` |
| `error_code` | e.g. `pdd_adapter_unavailable` |
| 场景 | 连接不可用 · adapter 未配置 · pre-send fatal |

### 2.5 timeout

| 字段 | 值 |
|------|-----|
| `success` | `false` |
| `platform_status` | `timeout_unknown` |
| `error_code` | e.g. `platform_timeout` |
| 行为 | **must not auto retry** · service → reconciliation |

### 2.6 exception before send attempt

| 字段 | 值 |
|------|-----|
| `success` | `false` |
| `platform_status` | `unavailable` or `failed_before_send` |
| 行为 | 明确未发送 · no idempotency succeeded |

### 2.7 exception after unknown send state

| 字段 | 值 |
|------|-----|
| `success` | `false` |
| `platform_status` | `timeout_unknown` or `unknown` |
| 行为 | **requires reconciliation** · 不自动重发 |

---

## 3. Service 消费 mapping（future · 15m+）

| `platform_status` | Service 后续 |
|-------------------|--------------|
| `sent` | pending → sent · idempotency mark_succeeded · audit succeeded |
| `rejected_by_platform` | pending failed · audit failed |
| `validation_failed` | no sent · audit failed · idempotency failed |
| `unavailable` | no sent · manual retry later |
| `timeout_unknown` | pending unknown · idempotency in_progress · reconciliation |

---

## 4. 禁止

| 禁止 |
|------|
| 将 timeout 映射为 `sent` |
| 伪造 `provider_message_id` |
| 错误响应含 session / cookie / API key |
| Port 内自动 retry loop |
| Port 直接 mark idempotency succeeded |

---

## 5. 示例（sent · future）

```json
{
  "success": true,
  "dry_run": false,
  "would_send": true,
  "platform_status": "sent",
  "provider_message_id": "pdd-msg-12345",
  "sent_at": "2026-06-03T12:00:00+00:00",
  "trace_id": "assisted-live:pa-uuid:...",
  "idempotency_key": "assisted_send:pa-uuid",
  "error_code": null,
  "error_message": null
}
```

---

*Phase 15k · docs only · 2026-06-03*

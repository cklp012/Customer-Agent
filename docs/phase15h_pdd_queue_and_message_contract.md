# Phase 15h — PDD Queue and Message Contract

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase10e_done.md](phase10e_done.md) · [phase15h_live_pdd_outbound_port_plan.md](phase15h_live_pdd_outbound_port_plan.md) |

---

## 1. PDD queue 不变

| 项 | 值 |
|----|-----|
| Queue name | **`pdd_{shop_id}`** |
| 变更 | **禁止** · assisted send 不得 rename queue |
| Legacy consumer | `MessageConsumer` / `AutoReplyThread` / `pdd_message_handler` **行为不变** |
| Assisted send | **不应**改变 legacy auto-reply queue 语义 |

Assisted outbound 与 inbound auto-reply **隔离** — live port 借用 PDD 发送 primitive，**不**将 assisted approve 混入 auto-reply 入队逻辑。

---

## 2. AssistedOutboundRequest 必填字段（future live）

| 字段 | 必填 | 说明 |
|------|------|------|
| `workspace_id` | ✅ | tenant scope |
| `shop_id` | ✅ | PDD shop · missing → **fail · no send** |
| `account_id` | ✅ | PDD account binding |
| `platform_id` | ✅ | must be `pinduoduo` |
| `buyer_id` | ✅ | recipient · missing → **fail · no send** |
| `pending_assisted_id` | ✅ | workflow correlation |
| `reply_log_id` | ✅ | audit correlation |
| `final_reply` | ✅ | guard-pass text · missing/empty → **fail · no send** |
| `idempotency_key` | ✅ | service-generated · port passes through for logging only |
| `trace_id` | ✅ | distributed trace |
| `dry_run` | ✅ | live port only called when `false` + gates pass |

**Port 不得添加或修改上述字段语义。**

---

## 3. final_reply 规则

| 规则 |
|------|
| `final_reply` **必须**是 final guard pass 后的文本 |
| Port **不允许**使用 AI draft 重新生成 |
| Port **不允许**修改、截断、模板替换 `final_reply` |
| Service 在 guard 后 freeze text · port 只 transmit |

---

## 4. 输入校验失败（port-local · before send）

| 条件 | 结果 |
|------|------|
| empty `final_reply` | `failed` · `validation_empty_reply` · **no send** |
| missing `buyer_id` | `failed` · `validation_missing_buyer` · **no send** |
| missing `shop_id` | `failed` · `validation_missing_shop` · **no send** |
| `platform_id` ≠ `pinduoduo` | `rejected` · `unsupported_platform` · **no send** |

校验在 port 内做 **transport safety only** — 不是 final guard 替代。

---

## 5. AssistedOutboundResult 状态枚举（future）

| `platform_status` | 含义 | Service 后续 |
|-------------------|------|--------------|
| `sent` | 平台确认发送成功 | pending → sent · idempotency succeeded |
| `failed` | 明确失败（非 timeout） | pending → failed · manual review |
| `timeout_unknown` | 超时 · 结果未知 | pending → unknown · reconciliation |
| `rejected_by_platform` | 平台拒绝（频控/封禁等） | pending → failed · audit |
| `unavailable` | PDD adapter/连接不可用 | no-send · retry later · manual |

Port **必须**区分以上状态 — 不得将 timeout 映射为 `failed`。

---

## 6. Success response 字段

| 字段 | 说明 |
|------|------|
| `provider_message_id` | PDD 平台返回的 message id |
| `platform_status` | `sent` |
| `sent_at` | optional ISO timestamp |
| `trace_id` | echo request |

---

## 7. Failure response 字段

| 字段 | 说明 |
|------|------|
| `platform_status` | see §5 |
| `error_code` | machine-readable |
| `error_message` | human-readable · dashboard-safe |
| `provider_message_id` | null unless partial success known |

---

## 8. Legacy 隔离清单

| 项 | Assisted send | Legacy auto-reply |
|----|---------------|-------------------|
| Trigger | Dashboard approve → service | Inbound message → handler |
| Queue | **不**经 auto-reply enqueue | `pdd_{shop_id}` consumer |
| Handler | **不参与** | `ai_handler` / `keyword_handler` |
| SendMessage | port thin adapter only | legacy hot path |
| AI generation | **禁止** in port | handler LLM path |

---

*Phase 15h · docs only · 2026-06-03*

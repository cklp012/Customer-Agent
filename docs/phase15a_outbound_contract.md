# Phase 15a — Outbound Contract

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15a_assisted_send_implementation_plan.md](phase15a_assisted_send_implementation_plan.md) · [phase14y_approve_to_outbound_sequence.md](phase14y_approve_to_outbound_sequence.md) |

---

## 1. 设计原则

| # | 原则 |
|---|------|
| 1 | **AssistedReplyService 不应直接 import/call legacy `SendMessage`** |
| 2 | 未来通过 **`AssistedOutboundPort`**（封装 unified outbound resolver 或 platform adapter）调用 |
| 3 | Outbound port **不负责** final guard |
| 4 | Outbound port **不负责** merchant policy |
| 5 | Outbound port **不负责** audit append |
| 6 | 必须支持 **`dry_run` / test_shop** 模式 |
| 7 | PDD queue name **不变**：`pdd_{shop_id}` |
| 8 | **Doudian production 不启用** |

---

## 2. AssistedOutboundPort（规划接口）

### 2.1 Input — `AssistedOutboundRequest`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `workspace_id` | string | ✅ | |
| `shop_id` | string | ✅ | |
| `account_id` | string | ✅ | |
| `platform_id` | string | ✅ | e.g. `pinduoduo` |
| `buyer_id` | string | ✅ | |
| `pending_assisted_id` | string | ✅ | |
| `reply_log_id` | string | ✅ | |
| `final_reply` | string | ✅ | guard 已扫描文本 |
| `idempotency_key` | string | ✅ | `assisted_send:{pending_assisted_id}` |
| `trace_id` | string | ✅ | 全链路追踪 |
| `dry_run` | bool | ✅ | true → would_send only |
| `conversation_id` | string? | 可选 | |
| `inbound_message_id` | string? | 可选 | |

### 2.2 Output — `AssistedOutboundResult`

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | bool | platform 是否接受发送 |
| `provider_message_id` | string? | 平台消息 id |
| `platform_status` | string? | e.g. `accepted` · `rejected` |
| `error_code` | string? | 机器可读 |
| `error_message` | string? | 人类可读 |
| `sent_at` | string? | ISO8601 |
| `dry_run` | bool | 是否 dry_run 路径 |
| `would_send` | bool? | dry_run=true 时为 true |

---

## 3. 调用链（future · PDD only）

```text
AssistedReplyService
    → AssistedOutboundPort.send(request)
        → UnifiedOutboundResolver.resolve(...)   [existing · not modified in 15a]
        OR PinduoduoAssistedAdapter              [thin wrapper]
            → enqueue / SendMessage path
            → queue: pdd_{shop_id}
```

**15a 不改 resolver / SendMessage 代码 — 仅规划 contract。**

---

## 4. dry_run 行为

| dry_run | 行为 |
|---------|------|
| `true` | 校验 request 完整 · 记录 `would_send=true` · **不** enqueue · **不** SendMessage |
| `false` | allowlist + flags 全 pass 后真实 outbound |

dry_run 仍须：`outbound_send_attempted` audit（action 可为 `outbound_send_attempted_dry_run` 或 metadata `dry_run=true` · 15b 实现时统一）。

---

## 5. 错误分类

| error_code | 含义 | pending status |
|------------|------|----------------|
| `channel_unavailable` | 连接/WS 不可用 | failed 或 no attempt |
| `rate_limited` | 平台限流 | failed |
| `invalid_recipient` | buyer_id 无效 | failed |
| `timeout` | 超时 · 未知 | reconciliation · 见 failure doc |
| `platform_rejected` | 平台拒绝 | failed |
| `dry_run_would_send` | dry_run 成功记录 | unchanged |

---

## 6. 职责分离

| 层 | final guard | policy | audit | outbound |
|----|-------------|--------|-------|----------|
| AssistedReplyService | 调用 | 读 snapshot | 编排写入 | 调用 port |
| evaluate_final_guard | ✅ | 读 input | ❌ | ❌ |
| AssistedOutboundPort | ❌ | ❌ | ❌ | ✅ |
| Handler | ❌ | ❌ | ❌ | ❌ |

---

*Phase 15a · planning only · 2026-06-03*

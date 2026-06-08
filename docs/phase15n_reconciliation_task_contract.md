# Phase 15n — Reconciliation Task Contract

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15n_unknown_outcome_state_machine.md](phase15n_unknown_outcome_state_machine.md) |

---

## 1. Task 定位

Future reconciliation task **只确认事实** — 查询平台与本地记录，更新 status/audit — **永不触发 send**。

| 项 | 结论 |
|----|------|
| 实现 | **未实现**（15n docs only） |
| Worker | **未实现** |
| 触发 | future: scheduled · manual dashboard · operator button |
| 重试 | 仅 **reconciliation 查询** 可重试 · **发送不可重试** |

---

## 2. Input（required / optional）

| 字段 | 必填 | 说明 |
|------|------|------|
| `pending_assisted_id` | ✅ | 关联 pending |
| `idempotency_key` | ✅ | outbound idempotency · **不可变** |
| `workspace_id` | ✅ | 租户隔离 |
| `shop_id` | ✅ | allowlist 核对 |
| `account_id` | ✅ | PDD 账号上下文 |
| `platform_id` | ✅ | 必须 `pinduoduo`（15n scope） |
| `buyer_id` | ✅ | 查询平台消息 |
| `trace_id` | ✅ | 全链路关联 |
| `sent_at_candidate` | optional | port 返回或本地时钟 · 查询时间窗参考 |
| `provider_message_id` | optional | 若 port 弱返回 · 用于核对 |

**Task 输入不得包含 cookie / token / credential — 由 adapter 内部安全加载。**

---

## 3. Task 允许（ALLOW）

| # | 动作 |
|---|------|
| A1 | 查询 PDD 平台消息记录（thin read API · future primitive） |
| A2 | 核对 buyer/session 最近 outbound 消息（时间窗 + 内容 hash 弱匹配） |
| A3 | 读取本地 audit timeline · SendDecisionSnapshot · idempotency row |
| A4 | append audit（reconciliation_* actions） |
| A5 | 更新 idempotency status → `succeeded` / `failed_before_send` / `manual_review_required` |
| A6 | 更新 pending status → `sent` / `send_failed` / `manual_review_required` |
| A7 | 写入 reconciliation attempt 计数与时间戳（future metadata） |
| A8 | 重试**查询**（exponential backoff · cap）当 `platform_unavailable` |

---

## 4. Task 禁止（DENY）

| # | 禁止 |
|---|------|
| D1 | **自动重发** / auto retry send |
| D2 | 调 `SendMessage` |
| D3 | 调 `Message.handlers` |
| D4 | 调 legacy auto reply / `AutoReplyThread` |
| D5 | 调 `outbound_resolver` |
| D6 | 修改 `final_reply` |
| D7 | 重新生成 AI 文本 |
| D8 | 绕过 outbound idempotency acquire |
| D9 | 使用同一 `idempotency_key` 再次 `port.send` |
| D10 | fallback PDD hot path / queue `pdd_{shop_id}` producer |
| D11 | Doudian outbound |
| D12 | 伪造 `provider_message_id` |

---

## 5. Task 结果（outcome enum）

| Result | 含义 | 后续 |
|--------|------|------|
| `confirmed_sent` | 平台证据确认消息已发出 | idempotency succeeded · pending sent · audit |
| `confirmed_not_sent` | 平台证据确认未发出 | idempotency failed_before_send or manual_review · **no auto retry** |
| `still_unknown` | 证据不足 | pending manual_review_required · 可稍后重跑 task |
| `platform_unavailable` | 平台 API 不可用 | 保持 unknown · 仅重试查询 |
| `permission_error` | 凭证/权限问题 | manual_review_required · alert operator |

---

## 6. Task 失败处理

| 失败类型 | 行为 |
|----------|------|
| 查询超时 | `platform_unavailable` · 可重试 task · **不重试 send** |
| 查询异常 | audit `reconciliation_still_unknown` · 不 send |
| DB 更新失败 | 保持 prior state · alert · manual review |
| 部分证据冲突 | `still_unknown` → operator |

```text
task failure
    → append audit (reconciliation_still_unknown or platform_unavailable)
    → NO port.send
    → NO handler
    → optional: schedule query retry with backoff
```

---

## 7. 输出（future response shape · planning）

| 字段 | 说明 |
|------|------|
| `result` | enum above |
| `provider_message_id` | 仅平台返回时填充 |
| `evidence_summary` | dashboard-safe 文本 · no secrets |
| `reconciliation_attempt` | 第 N 次尝试 |
| `trace_id` | echo |

---

## 8. 与 service 边界

| 层 | 职责 |
|----|------|
| `AssistedReplyService` | approve 时产生 unknown · 触发 task 入队（future） |
| Reconciliation task | 只读平台 + 更新 status/audit |
| `LivePddAssistedOutboundPort` | **不被 task 调用** |
| Operator actions | 覆盖 task 结论 · 仍写 audit |

---

*Phase 15n · docs only · 2026-06-03*

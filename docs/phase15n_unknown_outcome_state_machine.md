# Phase 15n — Unknown Outcome State Machine

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15h_timeout_unknown_and_reconciliation.md](phase15h_timeout_unknown_and_reconciliation.md) · [phase15n_live_send_reconciliation_plan.md](phase15n_live_send_reconciliation_plan.md) |

---

## 1. 设计目标

| 目标 |
|------|
| `timeout_unknown` 后**不能**自动 `unknown → retry` |
| `unknown → manual_review_required` 是**安全默认** |
| terminal / unknown 状态**不允许** duplicate approve 造成第二次发送 |
| 状态转换必须**单调、可审计、可人工介入** |

**本 phase 不创建表、不实现状态机代码 — 仅规划 future candidates。**

---

## 2. Outbound idempotency status（future candidates）

| Status | 含义 | 可再 send? |
|--------|------|-----------|
| `in_progress` | acquire 成功 · port 调用中 | ❌ |
| `succeeded` | 平台确认已发送（含 reconciliation 晚确认） | ❌ |
| `failed` | 平台明确拒绝或确认未发送且关闭 | ❌ 同 key |
| `failed_before_send` | 确认未发出（adapter 错误 · validation · 连接前失败） | ❌ 同 key |
| `timeout_unknown` | 超时或响应丢失 · 结果未知 | ❌ **禁止自动 retry** |
| `sent_unconfirmed` | 弱信号认为可能已发 · 无 provider_message_id | ❌ |
| `manual_review_required` | 需人工判定 | ❌ |

### 2.1 转换规则（idempotency）

```text
(acquire) → in_progress
in_progress → succeeded          [port sent + provider confirm]
in_progress → failed             [rejected_by_platform · confirmed_not_sent]
in_progress → failed_before_send [failed before wire]
in_progress → timeout_unknown    [timeout / connection lost mid-flight]
timeout_unknown → succeeded        [reconciliation: confirmed_sent ONLY]
timeout_unknown → failed_before_send [reconciliation: confirmed_not_sent]
timeout_unknown → manual_review_required [still_unknown · default landing]
timeout_unknown → timeout_unknown  [reconciliation query retry OK · NO send retry]
succeeded → *                      [TERMINAL]
failed → *                         [TERMINAL for same key]
manual_review_required → succeeded [operator mark_confirmed_sent + reconciliation]
manual_review_required → failed    [operator mark_confirmed_not_sent]
```

| 禁止转换 |
|----------|
| `timeout_unknown → in_progress` via **auto re-approve** |
| `succeeded → in_progress` |
| `manual_review_required → in_progress` without **new idempotency_key** |

---

## 3. Pending assisted status（future candidates）

| Status | 含义 |
|--------|------|
| `pending` | 待人工处理 |
| `approved_dry_run` | dry-run approve 完成 · would_send |
| `send_in_progress` | live approve · outbound 进行中 |
| `sent` | 确认已发送 |
| `send_failed` | 确认发送失败（平台拒绝或 confirmed not sent） |
| `send_unknown` | timeout_unknown · 结果不明 |
| `rejected` | 人工 reject |
| `expired` | TTL 过期 |
| `manual_review_required` | 需运营介入 |

### 3.1 转换规则（pending）

```text
pending → approved_dry_run       [dry-run approve]
pending → send_in_progress       [live approve · idempotency acquired]
send_in_progress → sent          [port success or reconciliation confirmed_sent]
send_in_progress → send_failed   [port failed · confirmed_not_sent]
send_in_progress → send_unknown  [timeout_unknown]
send_unknown → manual_review_required   [SAFE DEFAULT · immediate or after grace]
send_unknown → sent              [reconciliation confirmed_sent ONLY]
send_unknown → send_failed       [reconciliation confirmed_not_sent · operator path]
manual_review_required → sent    [operator mark_confirmed_sent]
manual_review_required → send_failed [operator mark_confirmed_not_sent]
manual_review_required → rejected [operator cancel_pending]
* terminal sent/rejected/expired → NO second live approve on same pending
```

---

## 4. 分支详解

### 4.1 timeout 后不能自动 retry

| 规则 |
|------|
| Port 返回 `timeout_unknown` 后 service **不得**再次调用 `port.send` 同一 `idempotency_key` |
| AutoReply / handler / queue consumer **不得**触发 resend |
| 仅 reconciliation task 或 operator 可推进状态 |
| Approve route 对 `send_unknown` / `manual_review_required` pending → **409 or manual_review_required** |

### 4.2 平台确认已发送

| 实体 | 更新 |
|------|------|
| idempotency | → `succeeded` · 写入真实 `provider_message_id`（若有） |
| pending | → `sent` |
| audit | append `reconciliation_confirmed_sent` · optional `operator_marked_sent` |

### 4.3 平台确认未发送

| 实体 | 更新 |
|------|------|
| idempotency | → `failed_before_send` 或保持 `manual_review_required` |
| pending | → `manual_review_required`（**不**自动回到 `pending` 重 approve） |
| audit | append `reconciliation_confirmed_not_sent` |
| 行为 | **不自动重发** — 若未来重试需新 pending + 新 idempotency_key + 新人工确认 |

### 4.4 无法确认

| 实体 | 更新 |
|------|------|
| idempotency | 保持 `timeout_unknown` 或 → `manual_review_required` |
| pending | 保持 `manual_review_required` |
| audit | append `reconciliation_still_unknown` |

### 4.5 terminal state 与 duplicate approve

| 状态 | duplicate approve 行为 |
|------|------------------------|
| `sent` | 409 · idempotent replay response only |
| `send_unknown` | **block live send** → `manual_review_required` |
| `manual_review_required` | **block live send** · 仅 operator actions |
| `send_in_progress` | 409 · in flight |
| `rejected` / `expired` | 409 · terminal |

**Duplicate approve on unknown 不得触发第二次 port.send。**

---

## 5. 与 15m 当前状态

| 项 | 当前 |
|----|------|
| `LivePddAssistedOutboundPort` | 仅返回 `live_send_not_implemented` |
| 状态机 | **未实现** |
| 本文件 | future SSOT for 15q schema + later impl |

---

*Phase 15n · docs only · 2026-06-03*

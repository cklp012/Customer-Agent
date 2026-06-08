# Phase 15n — Duplicate Send Prevention

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15j_done.md](phase15j_done.md) · [phase15n_unknown_outcome_state_machine.md](phase15n_unknown_outcome_state_machine.md) |

---

## 1. 核心原则

**Same `idempotency_key` 只能成功发送一次。** Reconciliation 确认已发送后，该 key 永久 terminal。

---

## 2. 防护层（defense in depth）

| 层 | 机制 |
|----|------|
| L1 Outbound idempotency | acquire before port.send · terminal on succeeded |
| L2 Pending status | `send_unknown` / `manual_review_required` block live approve |
| L3 Action idempotency (`client_request_id`) | replay 返回 stored response · **不** bypass outbound key |
| L4 Port result | `timeout_unknown` 不映射为 success |
| L5 Reconciliation | 只确认 · 不 send |
| L6 Operator policy | 新 send 必须新 key + 新 pending |
| L7 Flags | dry_run default · allowlist · daily cap（future service） |

---

## 3. timeout_unknown 与 duplicate approve

| 场景 | 行为 |
|------|------|
| 第一次 live approve | acquire key · port.send → `timeout_unknown` |
| 第二次 approve 同一 pending | **block** → 409 / `manual_review_required` |
| 第二次 approve 新 `client_request_id` | action idempotency 新行 · 但 outbound key 仍 held → **no second send** |
| reconciliation 进行中 | approve **block** |

**timeout_unknown 不允许重复 approve 自动发送。**

---

## 4. client_request_id replay

| 规则 |
|------|
| 15j replay 返回**首次** HTTP response body |
| replay **不得**重新 acquire outbound idempotency |
| replay **不得**调用 `port.send` |
| different payload → 409 conflict |

```text
client_request_id replay
    → return stored (status, body)
    → NO port.send
    → NO idempotency re-acquire
```

---

## 5. provider_message_id 与 timeout 语义

| 信号 | 错误推断 |
|------|----------|
| `provider_message_id` missing | **≠** 未发送 |
| `timeout_unknown` | **≠** 未发送 |
| `failed_before_send` | **=** 确认未发出（adapter 层） |
| `rejected_by_platform` | **=** 平台明确拒绝 |

**必须区分 `failed_before_send` 与 `timeout_unknown`：**

| Status | 含义 | 可 reconciliation retry send? |
|--------|------|-------------------------------|
| `failed_before_send` | 未离开本系统 / 连接前失败 | ❌ 同 key · 未来新 key 人工 |
| `timeout_unknown` | 可能已在途 / 已送达 | ❌ **禁止 auto** |

---

## 6. Retry 政策（future · 非 15n 实现）

Retry **必须是未来单独人工动作**，不能隐式发生。

若未来允许 retry（explicit operator + admin）：

| 要求 |
|------|
| 新 dashboard action（非 re-approve 同一 pending） |
| 新 `idempotency_key` |
| 新 audit 链 |
| 再次 final guard |
| 再次人工 confirm_checkbox |
| daily cap 检查 |
| allowlist 检查 |
| **禁止**复用 `timeout_unknown` 的 key |

```text
future manual retry (NOT auto)
    → create_new_pending_after_manual_decision
    → new idempotency_key
    → new approve flow
    → full guard + audit + snapshot
```

---

## 7. Reconciliation 与 duplicate

| reconciliation result | duplicate 风险 |
|----------------------|----------------|
| `confirmed_sent` | key → succeeded · 永久 block |
| `confirmed_not_sent` | key terminal failed · 新 send 需新 key |
| `still_unknown` | key 仍 held · approve block |

---

## 8. 禁止清单

| 禁止 |
|------|
| timeout → 自动第二次 port.send |
| handler 补发 |
| SendMessage 绕过 |
| 同 key 双 succeeded |
| 伪造 provider_message_id 以“完成” reconciliation |

---

*Phase 15n · docs only · 2026-06-03*

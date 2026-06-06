# Phase 15a — Failure and Rollback Policy

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14y_failure_and_recovery_policy.md](phase14y_failure_and_recovery_policy.md) · [phase15a_status_transition_and_audit.md](phase15a_status_transition_and_audit.md) |

---

## 1. 总原则

| # | 原则 |
|---|------|
| F1 | final guard block → **no-send** |
| F2 | audit before outbound failure → **no-send** |
| F3 | snapshot failure → **no-send** |
| F4 | idempotency lock failure → **no-send** |
| F5 | outbound unavailable → **no-send** |
| F6 | outbound failure → **failed + manual review** |
| F7 | outbound timeout → **unknown state · reconciliation · no auto retry** |
| F8 | **DB failure → no fallback legacy send** |
| F9 | duplicate approve → **no double-send** |
| F10 | recovery task **只能补 audit / reconcile · 不自动重发** |

---

## 2. 失败场景矩阵

| 场景 | send? | pending | lock | 备注 |
|------|-------|---------|------|------|
| flag off | ❌ | 不变 | not_started | assisted_disabled |
| non-allowlist shop | ❌ | 不变 | — | |
| dry_run=true | would_send only | 不变 | optional | no SendMessage |
| final guard block | ❌ | pending | not_started | |
| final guard exception | ❌ | 不变 | — | fail-closed |
| audit before outbound fail | ❌ | approved? | release | strict |
| snapshot fail | ❌ | approved? | release | |
| idempotency acquire fail | ❌ | approved? | — | |
| outbound_send_attempted fail | ❌ | approved | release | **must not outbound** |
| outbound fail | attempt | **failed** | failed | manual review |
| outbound timeout | unknown | failed? | in_progress stuck | reconcile |
| outbound success | ✅ | **sent** | succeeded | |
| success + audit fail | 已发送 | sent | succeeded | recovery · **no resend** |
| duplicate sent approve | ❌ | sent | succeeded | already_sent |
| DB failure mid-flow | ❌ | 不变/rollback | — | **no legacy fallback** |

---

## 3. Outbound timeout / unknown

```text
outbound call timeout
    → do NOT auto retry SendMessage
    → mark pending failed OR unknown (implementation choice)
    → enqueue reconciliation job:
        - query platform if message exists
        -补 audit outbound_send_succeeded OR outbound_send_failed
    → operator manual review if ambiguous
```

**绝不因 timeout 自动第二次 outbound。**

---

## 4. Recovery task（规划）

| 允许 | 禁止 |
|------|------|
| 补写 missing audit | 自动重发 SendMessage |
| reconcile pending status vs platform | 推断 success 并 resend |
| Dashboard 标记 reconciled | 绕过 idempotency |

---

## 5. Rollback

| 动作 | 效果 |
|------|------|
| `PRODUCT_ASSISTED_SEND_ENABLED=false` | 立即 stop live send |
| `PRODUCT_ASSISTED_SEND_DRY_RUN=true` | 紧急 would_send only |
| keep preview mode | test shop zero-send 不变 |
| keep pending read-only | Dashboard 14z/15d |
| PDD legacy | **unchanged** · `pdd_{shop_id}` |
| Doudian | **no effect** · production disabled |
| disable ASSISTED_SERVICE | create/approve write disabled |

---

## 6. Legacy 隔离

```text
product_gate.db / assisted path failure
    → AssistedReplyService error result
    → NO call to legacy database send
    → NO handler _send_reply fallback for assisted intent
    → NO SendMessage from Dashboard read
```

---

*Phase 15a · planning only · 2026-06-03*

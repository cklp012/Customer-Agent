# Phase 15g — Failure and Rollback Policy

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15e_failure_rollback_and_reconciliation.md](phase15e_failure_rollback_and_reconciliation.md) |

---

## 1. Pre-mutation failures → no mutation

| 场景 | HTTP | mutation |
|------|------|----------|
| CSRF failure | 403 | ❌ |
| permission / viewer | 403 | ❌ |
| cross-workspace / cross-shop | 403 | ❌ |
| stale `expected_pending_status` | 409 | ❌ |
| service disabled | 403/503 | ❌ |
| rate limited | 429 | ❌ |
| audit failure before mutation | 500 | ❌ where possible |

---

## 2. Approve path failures → no live send

| 场景 | 行为 |
|------|------|
| final guard block | 422 · no outbound |
| allowlist denied | 403 · no dry-run port |
| idempotency denied | 409/422 · no port |
| dry-run port failure | 422 · no live send |
| snapshot failure | 500 · no port |
| `live_send_not_implemented` | documented response · no SendMessage |

---

## 3. Reject path failures

| 场景 | 行为 |
|------|------|
| terminal state | 409 · no double reject |
| duplicate client_request_id same payload | 200 idempotent |
| different payload | 409 conflict |

---

## 4. Duplicate / replay

| 场景 | 行为 |
|------|------|
| same `client_request_id` + same body | return cached · **no double action** |
| same id + different body | 409 |
| duplicate approve on sent pending | terminal · no mutation |

**No fallback legacy send on any failure.**

---

## 5. DB failure

| 场景 | 行为 |
|------|------|
| product DB unavailable | 500 · no-send |
| audit write fails pre-mutation | no mutation |
| legacy DB | **不触碰** |

---

## 6. Rollback policy

紧急关闭 action endpoints **不改变 PDD legacy**：

| 动作 | 效果 |
|------|------|
| disable action routes（feature flag / route off） | POST approve/reject 503 |
| keep read-only dashboard（15d） | GET unchanged |
| keep preview / dry-run service flags off | AssistedReplyService disabled path |
| `PRODUCT_ASSISTED_SEND_ENABLED=false` | no dry-run outbound |
| PDD AutoReply / handler | **unchanged** · `pdd_{shop_id}` |

---

## 7. 禁止

| 禁止 | 原因 |
|------|------|
| fallback handler SendMessage | G7 |
| silent retry live send | idempotency contract |
| mutation after CSRF fail | security |

---

*Phase 15g · docs only · 2026-06-03*

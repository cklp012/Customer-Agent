# Phase 15g — Dry-run Only Boundary

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15f_done.md](phase15f_done.md) · [phase15g_approve_endpoint_contract.md](phase15g_approve_endpoint_contract.md) |

---

## 1. Phase 15g 边界

| 项 | 15g |
|----|-----|
| 写代码 | ❌ |
| 实现 endpoint | ❌ |
| live send | ❌ |

**First action endpoint implementation（15i）must be dry-run only.**

---

## 2. Approve dry-run stage 行为

| 项 | 值 |
|----|-----|
| env default | `PRODUCT_ASSISTED_SEND_DRY_RUN=true` |
| endpoint `dry_run_expected` | **true** |
| service status | `dry_run_would_send` |
| `would_send` | **true** |
| `live_send_attempted` | **false** always |
| pending → sent | **否** |
| idempotency mark_succeeded | **否** · stays `in_progress` |
| audit | `assisted_dry_run_would_send` · **not** `outbound_send_attempted` |
| SendMessage / PDD outbound | **否** |

---

## 3. dry_run=false 请求

| 项 | 行为 |
|----|------|
| UI / body 请求 live | service → `live_send_not_implemented` |
| endpoint response | document 200 or 422 · **no SendMessage** |
| 实现时机 | **15h+ live port** · not 15g/15i first cut |

---

## 4. Reject boundary

| 项 | reject |
|----|--------|
| dry-run port | ❌ 不调用 |
| final guard | ❌ |
| outbound | ❌ |
| status | `rejected` only |

---

## 5. Live PDD port 归属

| 组件 | Phase |
|------|-------|
| `LivePddAssistedOutboundPort` | **15h planning** |
| live single test shop | **later** |
| action endpoint live send | **after** 15h + flags + allowlist |

---

## 6. 禁止清单

- ❌ pending marked `sent` during dry-run
- ❌ idempotency `succeeded` during dry-run
- ❌ `outbound_send_attempted` during dry-run
- ❌ SendMessage / PDD outbound / Doudian
- ❌ handler integration
- ❌ bypass AssistedReplyService

---

*Phase 15g · docs only · 2026-06-03*

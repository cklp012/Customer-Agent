# Phase 15e — Failure · Rollback · Reconciliation

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15a_failure_rollback_policy.md](phase15a_failure_rollback_policy.md) · [phase15e_assisted_service_live_sequence.md](phase15e_assisted_service_live_sequence.md) |

---

## 1. Pre-outbound failures → no-send

| 场景 | 行为 |
|------|------|
| final guard **block** | AuditLog `final_guard_blocked` · pending unchanged · no outbound |
| final guard **exception** | treat as block · no outbound · error audit |
| audit before outbound **failure** | **no-send** · 不调用 port |
| SendDecisionSnapshot **failure** | **no-send** |
| idempotency **acquire failure** | **no-send** |
| `outbound_send_attempted` audit **failure** | **no outbound call** |
| outbound channel **unavailable** | no-send · optional audit `outbound_unavailable` |
| flags / allowlist **missing** | no-send |

**DB failure → no fallback legacy send.**

---

## 2. Outbound failures

| 场景 | idempotency | pending | audit |
|------|-------------|---------|-------|
| platform **rejected** | mark_failed | failed | outbound_send_failed |
| **timeout** | mark_failed OR leave in_progress + reconcile | failed or unchanged | outbound_send_failed / unknown |
| port **exception** | mark_failed | failed | outbound_send_failed |

**Timeout = unknown outcome** · 需要 **reconciliation** · **不自动重发**。

---

## 3. Post-success inconsistency（danger states）

| 场景 | 风险 | 处理 |
|------|------|------|
| live outbound **success** but DB update **failure** | 可能已发但 DB 未 sent | **reconcile** · 查 platform · **不重发** |
| idempotency **succeeded** but pending **not sent** | 状态分裂 | reconcile pending → sent |
| pending **sent** but success audit **missing** | audit 缺口 | **recovery audit append** · **不重发** |
| lock **in_progress** stuck | 阻塞 duplicate | manual / TTL reconcile · 15f+ |

**Live success 后 final audit 失败 → recovery task · 不重发。**

---

## 4. Duplicate / terminal

| 场景 | 行为 |
|------|------|
| duplicate **sent** | acquire → already_sent · **no double send** |
| duplicate **in_progress** | already_in_progress · **no double send** |
| duplicate **failed** | manual_review_required · **no auto retry** |

---

## 5. Rollback policy

紧急关闭 live assisted send **不改变 PDD legacy**：

| 动作 | 效果 |
|------|------|
| `PRODUCT_ASSISTED_SEND_ENABLED=false` | 关闭 send 路径 |
| `PRODUCT_ASSISTED_SEND_DRY_RUN=true` | 强制 would_send only |
| clear `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID` | 清空 allowlist |
| keep preview / product gate | unchanged |
| keep dashboard read (15d) | read-only unchanged |
| PDD AutoReply / handler hot path | **unchanged** · `pdd_{shop_id}` |

**No rollback to legacy direct SendMessage from AssistedReplyService.**

---

## 6. Reconciliation tasks（future ops）

| Task | Trigger |
|------|---------|
| `reconcile_outbound_timeout` | port timeout |
| `reconcile_idempotency_in_progress` | stuck lock |
| `reconcile_pending_sent_mismatch` | idempotency vs pending |
| `append_missing_success_audit` | sent without audit |

All reconciliation: **read platform + DB · fix state · never blind resend**.

---

## 7. 明确禁止

| 禁止 | 原因 |
|------|------|
| Auto retry on failed idempotency | manual_review_required |
| Handler fallback send | no fallback legacy |
| Double send on already_sent | idempotency contract |
| Dashboard read triggering send | read-only |

---

*Phase 15e · docs only · 2026-06-03*

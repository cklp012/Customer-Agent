# Phase 15q 完成 — Reconciliation Schema Planning

| 项 | 内容 |
|----|------|
| 状态 | **reconciliation schema planning complete · docs only** |
| 日期 | 2026-06-03 |
| 前置 | [phase15n_done.md](phase15n_done.md) · [phase15p_done.md](phase15p_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 类型 | **仅文档** |
| Python 代码 | **未写** |
| 新表创建 | **未做**（`reconciliation_attempts` planned） |
| models / repositories | **未改** |
| reconciliation worker | **未实现** |
| live send / retry | **未实现** |
| handler / SendMessage / PDD / Doudian | **未改** |
| PDD queue | **`pdd_{shop_id}` 不变** |

---

## 规划要点

| # | 要点 |
|---|------|
| 1 | **Schema may record uncertainty; it must not imply permission to resend.** |
| 2 | Future `reconciliation_attempts` table — append-first · no secrets |
| 3 | Extend `outbound_idempotency_keys.status` — `timeout_unknown` ≠ `failed` |
| 4 | Extend `pending_assisted_replies.status` — dry-run ≠ `sent` |
| 5 | Manual review queries + RBAC documented |
| 6 | Status transitions — forbidden auto retry paths explicit |
| 7 | Additive migration + rollback preserves evidence |

---

## 文档清单

| 文档 | 内容 |
|------|------|
| [phase15q_reconciliation_schema_plan.md](phase15q_reconciliation_schema_plan.md) | 总体规划 |
| [phase15q_reconciliation_attempts_table.md](phase15q_reconciliation_attempts_table.md) | Future 表 |
| [phase15q_outbound_idempotency_status_extension.md](phase15q_outbound_idempotency_status_extension.md) | Idempotency |
| [phase15q_pending_assisted_status_extension.md](phase15q_pending_assisted_status_extension.md) | Pending |
| [phase15q_manual_review_fields_and_queries.md](phase15q_manual_review_fields_and_queries.md) | Dashboard |
| [phase15q_status_transition_rules.md](phase15q_status_transition_rules.md) | 转换规则 |
| [phase15q_failure_rollback_policy.md](phase15q_failure_rollback_policy.md) | Rollback |
| [phase15q_test_plan.md](phase15q_test_plan.md) | Q1–Q20 |

---

## 下一步建议

| Phase | 内容 |
|-------|------|
| **15r** | ✅ Local dashboard smoke test **script skeleton** — [phase15r_done.md](phase15r_done.md) |
| **15s** | `OutboundPortSelector` skeleton · dry-run only |
| **15t** | Reconciliation schema **implementation behind flags** |
| **15u** | Live PDD send primitive **planning only** |

---

*签收：Phase 15q · docs only · 2026-06-03*

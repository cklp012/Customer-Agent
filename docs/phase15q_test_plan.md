# Phase 15q — Test Plan (Future)

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 实现 | Phase **15t** + repositories · **15q 无测试代码** |

---

## 用例清单

| ID | 用例 | 断言要点 |
|----|------|----------|
| **Q1** | `reconciliation_attempts_schema_fields` | 表含规划字段 · types |
| **Q2** | `reconciliation_attempts_no_secret_fields` | 无 cookie/token 列约定 |
| **Q3** | `reconciliation_attempts_indexes` | pending · idempotency · workspace_shop |
| **Q4** | `outbound_status_timeout_unknown_distinct_from_failed` | 枚举可区分 · 语义不同 |
| **Q5** | `outbound_status_manual_review_blocks_duplicate_approve` | acquire deny |
| **Q6** | `pending_status_send_unknown_blocks_auto_retry` | re-approve 409 |
| **Q7** | `pending_terminal_states_block_mutation` | sent/rejected/expired |
| **Q8** | `manual_review_query_filters_workspace_shop` | list 过滤 |
| **Q9** | `cross_workspace_forbidden` | 403/empty |
| **Q10** | `operator_mark_sent_requires_audit` | audit row |
| **Q11** | `operator_mark_not_sent_requires_audit` | audit row |
| **Q12** | `create_new_pending_requires_new_idempotency_key` | 新 key |
| **Q13** | `rollback_no_destructive_migration` | additive only |
| **Q14** | `schema_import_no_db_side_effect` | flags off · no create |
| **Q15** | `no_SendMessage_import` | repo/model static |
| **Q16** | `no_handler_import` | static |
| **Q17** | `no_PDD_Doudian_import` | product DB only |
| **Q18** | `pdd_queue_name_unchanged` | `pdd_shop123` |
| **Q19** | `no_auto_retry` | unknown → no in_progress |
| **Q20** | `no_live_send_in_phase15q` | 15q 零 impl |

---

## 静态检查（15t impl）

| 禁止 import |
|-------------|
| `SendMessage` · `Message.handlers` · `outbound_resolver` |
| `Channel.pinduoduo` send hot path |
| `database.models` / `database.db_manager` |

---

## 与现有测试

| 现有 | 15q |
|------|-----|
| 15b idempotency | Q4–Q5 扩展 |
| 15n state machine docs | Q6–Q7 对齐 |
| 本 phase | **0 新测试文件** |

---

*Phase 15q · docs only · 2026-06-03*

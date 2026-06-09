# Phase 15q — Reconciliation Schema Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不写代码 · 不创建表** |
| 日期 | 2026-06-03 |
| 前置 | [phase15n_done.md](phase15n_done.md) · [phase15p_done.md](phase15p_done.md) |

---

## 1. Phase 15q 定位

| 项 | 结论 |
|----|------|
| 交付 | **仅文档** — reconciliation / manual review **schema 规划** |
| Python 代码 | **未写** |
| 新表创建 | **未做**（`reconciliation_attempts` 为 future） |
| reconciliation worker | **未实现** |
| live send / retry / auto resend | **未实现** |
| handler / SendMessage / PDD hot path | **未改** |
| PDD queue | **`pdd_{shop_id}` 不变** |

Schema 目标：支撑未来 **reconciliation task** 与 **dashboard manual review** — 只记录事实与人工确认，**不触发发送**。

---

## 2. 核心原则

| # | 原则 |
|---|------|
| **Q1** | **Schema may record uncertainty; it must not imply permission to resend.** |
| **Q2** | `timeout_unknown` ≠ `failed` · 必须可区分存储 |
| **Q3** | `manual_review_required` 阻止 duplicate approve 自动发送 |
| **Q4** | Reconciliation attempts **append-first** · 不覆盖历史 |
| **Q5** | 状态变更 **append audit** · 不 mutate 旧 audit |
| **Q6** | **No fallback legacy send** |
| **Q7** | 无 cookie/token/credential 入库 |
| **Q8** | 无 FK legacy `database/**` |

---

## 3. 与现有 product schema 关系

| 现有表（已实现） | 15q 扩展 |
|------------------|----------|
| `outbound_idempotency_keys` | status / platform_status 枚举扩展（文档） |
| `pending_assisted_replies` | status 枚举扩展（文档） |
| `audit_logs` | 新 action 类型（15n 已规划）· append-only |
| `send_decisions` | final guard snapshot（已有） |
| `dashboard_action_idempotency_keys` | 不变 · 与 outbound key 分离 |
| **`reconciliation_attempts`** | **future 新表** · 15t impl |

---

## 4. 数据流（future）

```text
live port timeout_unknown
    → outbound_idempotency_keys.status = timeout_unknown
    → pending_assisted_replies.status = send_unknown → manual_review_required
    → audit: outbound_send_timeout_unknown
    → reconciliation_attempts row (started)
        → query platform / local evidence
        → status: confirmed_sent | confirmed_not_sent | still_unknown | ...
    → update idempotency + pending (monotonic)
    → audit: reconciliation_* / operator_marked_*
```

**无步骤调用 SendMessage 或 retry port.send。**

---

## 5. 文档清单

| 文档 | 内容 |
|------|------|
| [phase15q_reconciliation_attempts_table.md](phase15q_reconciliation_attempts_table.md) | Future 表 |
| [phase15q_outbound_idempotency_status_extension.md](phase15q_outbound_idempotency_status_extension.md) | Idempotency status |
| [phase15q_pending_assisted_status_extension.md](phase15q_pending_assisted_status_extension.md) | Pending status |
| [phase15q_manual_review_fields_and_queries.md](phase15q_manual_review_fields_and_queries.md) | Dashboard 查询 |
| [phase15q_status_transition_rules.md](phase15q_status_transition_rules.md) | 转换规则 |
| [phase15q_failure_rollback_policy.md](phase15q_failure_rollback_policy.md) | Rollback |
| [phase15q_test_plan.md](phase15q_test_plan.md) | Q1–Q20 |

---

## 6. 禁止（签收）

| 禁止 |
|------|
| 本 phase 修改 `models.py` / repositories |
| schema 字段暗示 auto-retry 权限 |
| 删除 reconciliation 历史 |
| Doudian production reconciliation scope（15q: PDD only） |

---

## 7. 下一步（不在 15q 实现）

| Phase | 内容 |
|-------|------|
| **15r** | Local dashboard smoke test **script skeleton** |
| **15s** | `OutboundPortSelector` skeleton · dry-run only |
| **15t** | Reconciliation schema **implementation behind flags** |

---

*Phase 15q · docs only · 2026-06-03*

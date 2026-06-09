# Phase 15q — Pending Assisted Status Extension

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 表 | `pending_assisted_replies`（已存在 · **本 phase 不改**） |

---

## 1. 当前实现

| `status` 值 | 场景 |
|-------------|------|
| `pending` | 创建默认 |
| `rejected` | reject_pending |
| `expired` | expire flow |

**Service terminal check（approve）：** `rejected` · `expired` · `sent` · `approved`

**注意：** 当前 dry-run approve **不**将 pending 改为 `sent` — 保持 `pending` + audit only（15f）。

---

## 2. 未来建议 `status` 扩展

| Status | 含义 | Terminal? |
|--------|------|-----------|
| `pending` | 待处理 | no |
| `approved_dry_run` | dry-run approve 完成 | no* |
| `send_in_progress` | live outbound 进行中 | no |
| `sent` | 确认已发送 | **yes** |
| `send_failed` | 确认发送失败 | **yes** |
| `send_unknown` | timeout/unknown | no |
| `manual_review_required` | 人工队列 | no |
| `rejected` | 人工拒绝 | **yes** |
| `expired` | TTL 过期 | **yes** |
| `cancelled` | 人工取消 | **yes** |

\* `approved_dry_run` 非 live sent terminal — **不能**等同于 `sent`。

---

## 3. 关键规则

| 规则 |
|------|
| **dry-run 不能变 `sent`** — 最多 `approved_dry_run` 或保持 `pending` |
| `send_unknown` — **不允许**再次 approve 自动发送 |
| `sent` / `rejected` / `expired` / `cancelled` — terminal · 禁止原地复活为 `pending` |
| `manual_review_required` — 仅 operator 动作推进 |
| `create_new_pending_after_manual_decision` — **新** `pending_assisted_id` + **新** `idempotency_key` |
| 每次 status 变更 → append audit（`before_state` / `after_state`） |

---

## 4. 与 outbound idempotency 对齐

| pending status | 典型 idempotency status |
|----------------|-------------------------|
| `send_in_progress` | `in_progress` |
| `sent` | `succeeded` |
| `send_failed` | `failed` or `failed_before_send` |
| `send_unknown` | `timeout_unknown` |
| `manual_review_required` | `manual_review_required` or `timeout_unknown` |
| `approved_dry_run` | dry-run may not lock outbound key succeeded |

---

## 5. 字段复用（已有列）

| 列 | 用途 |
|----|------|
| `final_reply` | manual review 展示 |
| `approved_by` / `rejected_by` | 操作者 |
| `updated_at` | list 排序 |
| `blocked_reason` | optional guard/review 备注 |

**不新增列（15q）— 15t 可评估是否需要 `last_platform_status` 冗余列；优先 audit + idempotency join。**

---

## 6. dry-run vs live 路径

```text
dry-run approve:
    pending: pending → approved_dry_run (or stay pending per 15f compat)
    NEVER → sent

live approve (future):
    pending → send_in_progress → sent | send_failed | send_unknown
    send_unknown → manual_review_required (default)
```

---

*Phase 15q · docs only · 2026-06-03*

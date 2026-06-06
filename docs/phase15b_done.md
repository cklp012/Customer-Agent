# Phase 15b 完成 — Outbound Idempotency Skeleton Behind Flags

| 项 | 内容 |
|----|------|
| 状态 | **schema + repository skeleton implemented** |
| 日期 | 2026-06-03 |
| 前置 | [phase15a_done.md](phase15a_done.md) · [phase14q_done.md](phase14q_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 实现 | `OutboundIdempotencyRow` ORM + `OutboundIdempotencyRepositorySQLite` |
| flags | `WRITE_OUTBOUND_IDEMPOTENCY` 默认 **off** |
| acquire / mark_succeeded / mark_failed | ✅ skeleton |
| AssistedReplyService live send | **未接** |
| assisted send | **未实现** |
| auto send | **未实现** |
| handler / SendMessage / outbound | **未调用** |
| PDD / Doudian 热路径 | **未改** |

---

## ORM / Repository

| 组件 | 文件 |
|------|------|
| `OutboundIdempotencyRow` | `product_persistence/models.py` |
| `OutboundIdempotencyRepositorySQLite` | `sqlite_outbound_idempotency_repository.py` |
| `IdempotencyAcquireResult` / `IdempotencyRecord` | repository module |

**方法：** `acquire` · `get` · `mark_succeeded` · `mark_failed`（无 send）

**acquire reasons：** `already_sent` · `already_in_progress` · `manual_review_required`

---

## Flags

| Flag | 默认 | 激活条件 |
|------|------|----------|
| `PRODUCT_PERSISTENCE_ENABLED` | off | 总开关 |
| `PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY` | off | ENABLED + flag |

import module **不创建 DB**；flags off **不创建 product_gate.db**。

---

## 测试

`uv run python -m unittest discover -s tests -v`

- `tests/test_outbound_idempotency_schema.py`
- `tests/test_outbound_idempotency_repository.py`

---

## 下一步

| Phase | 内容 |
|-------|------|
| **15c** | ✅ Assisted outbound **dry-run port** — [phase15c_done.md](phase15c_done.md) |
| **15d** | PendingAssisted dashboard **read API skeleton** |
| **15e** | Assisted send live integration **planning only** |
| **15f** | Wire dry-run port into AssistedReplyService behind flags |

---

*签收：Phase 15b · 2026-06-03*

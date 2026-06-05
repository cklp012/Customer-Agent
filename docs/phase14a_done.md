# Phase 14a 完成 — Shadow DB Schema Planning

| 项 | 内容 |
|----|------|
| 状态 | **docs only · 规划完成** |
| 日期 | 2026-06-03 |
| 范围 | 持久化层 SSOT（shadow-first） |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 类型 | **仅文档** |
| migration / `database/models.py` | **未创建 / 未改** |
| handler / SendMessage / PDD / Doudian | **未改** |
| persistent DB | **未实现** |
| assisted / auto send | **未实现** |
| 当前运行时 | 13d/13e **in-memory** 仍有效 |

---

## 新增文档

| 文档 | 内容 |
|------|------|
| [phase14a_shadow_db_schema_plan.md](phase14a_shadow_db_schema_plan.md) | 总目标 · shadow-first |
| [phase14a_replylog_schema.md](phase14a_replylog_schema.md) | ReplyLog |
| [phase14a_pending_assisted_reply_schema.md](phase14a_pending_assisted_reply_schema.md) | PendingAssistedReply |
| [phase14a_auditlog_schema.md](phase14a_auditlog_schema.md) | AuditLog |
| [phase14a_senddecision_schema.md](phase14a_senddecision_schema.md) | SendDecision snapshot |
| [phase14a_migration_sequence.md](phase14a_migration_sequence.md) | M0–M9 |

---

## 规划结论（签收）

| # | 结论 |
|---|------|
| 1 | **Shadow-first** — 并行 legacy，不破坏 PDD 热路径 |
| 2 | `product_gate_enabled` **默认 false** · `reply_mode` **默认 preview** |
| 3 | Preview / assisted / auto **分阶段**；auto 仅 M8 规划 |
| 4 | **默认 off + rollback** 每步可逆 |
| 5 | **Non-test shop legacy** 全程不变 |

---

## 下一步

| Phase | 状态 | 内容 |
|-------|------|------|
| **14b** | ✅ | Alembic/SQL migration draft — [phase14b_done.md](phase14b_done.md) |
| **14c** | 待做 | Create empty shadow migration files only |
| **14d** | 待做 | Shadow ReplyLog write planning |
| **14e** | 待做 | Dashboard read API planning only |

---

*签收：Phase 14a · docs only · 2026-06-03*

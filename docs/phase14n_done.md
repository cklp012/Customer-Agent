# Phase 14n 完成 — SendDecision Snapshot SQLite Shadow Write Behind Flags

| 项 | 内容 |
|----|------|
| 状态 | **SendDecision snapshot shadow write implemented** |
| 日期 | 2026-06-03 |
| 前置 | [phase14m_done.md](phase14m_done.md) · [phase14l_done.md](phase14l_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 实现 | `SendDecisionRepositorySQLite` + `SendDecisionSnapshotRow` ORM |
| flags | `WRITE_SEND_DECISION` 默认 **false** |
| 写入顺序 | in-memory → ReplyLog SQLite → **Snapshot SQLite（ReplyLog 成功后才写）** |
| append-only | 每次 `create_snapshot` 新 UUID 新行 |
| `decision_phase` | `ai_preview` |
| legacy / handler / SendMessage / PDD / Doudian | **未改** |
| assisted / auto | **未实现** |

---

## 行为摘要

| 条件 | 行为 |
|------|------|
| flags off | in-memory only |
| WRITE_REPLY_LOG only | reply_logs · 无 snapshot |
| WRITE_REPLY_LOG + WRITE_SEND_DECISION | reply_logs + snapshot |
| ReplyLog SQLite fail | 无 snapshot · in-memory ok · no send |
| Snapshot SQLite fail | `snapshot_recorded=False` · in-memory + reply_log ok · no send |
| test shop preview | **zero-send** 不变 |

---

## PreviewRecordResult 扩展

| 字段 | 说明 |
|------|------|
| `snapshot_recorded` | SQLite snapshot 写入成功 |
| `snapshot_error` | snapshot 失败原因（不抛 handler） |
| `send_decision_id` | 新 snapshot UUID |

---

## 代码变更

| 文件 | 变更 |
|------|------|
| `product_persistence/models.py` | `SendDecisionSnapshotRow` |
| `product_persistence/repositories/sqlite_send_decision_repository.py` | **新增** |
| `product_persistence/services/preview_reply_log_service.py` | snapshot write path |
| `product_persistence/db_manager.py` | `WRITE_SEND_DECISION` activates DB |
| `tests/test_sqlite_send_decision_snapshot_write.py` | M1–M7 |
| `tests/test_handler_send_decision_snapshot_shadow_write.py` | handler integration |

---

## 测试

`uv run python -m unittest discover -s tests -v`

---

## 下一步

| Phase | 内容 |
|-------|------|
| **14o** | ✅ Dashboard read API skeleton — [phase14o_done.md](phase14o_done.md) |
| **14p** | AuditLog / PendingAssisted planning |
| **14q** | Dashboard detail snapshots SQLite read integration |
| **14r** | Auth/permission enforcement planning |

---

*签收：Phase 14n · 2026-06-03*

# Phase 14l 完成 — SQLite ReplyLog Shadow Write Behind Flags

| 项 | 内容 |
|----|------|
| 状态 | **SQLite shadow write implemented** |
| 日期 | 2026-06-03 |
| 前置 | [phase14j_done.md](phase14j_done.md) · [phase14i_done.md](phase14i_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 实现 | `ReplyLogRepositorySQLite` + `ProductDbManager` + ORM `reply_logs` |
| flags 默认 | `PRODUCT_PERSISTENCE_ENABLED=false` · `WRITE_REPLY_LOG=false` |
| 写入顺序 | **in-memory first** → optional SQLite shadow |
| DB 路径 | `./temp/product_gate.db`（`PRODUCT_DB_URL` 可覆盖） |
| legacy `channel_shop.db` | **未改** |
| handler / SendMessage / PDD / Doudian | **未改** |
| assisted / auto | **未实现** |

---

## 行为摘要

| 条件 | 行为 |
|------|------|
| flags off | in-memory only · 不创建 DB |
| flags on | in-memory + SQLite `reply_logs` row |
| SQLite failure | in-memory retained · `db_recorded=False` · **no send** |
| test shop preview | **zero-send** 不变 |
| non-test shop | 不进入 service · legacy 不变 |

---

## 代码变更

| 文件 | 变更 |
|------|------|
| `product_persistence/models.py` | `ProductBase` · `ReplyLogRow` ORM |
| `product_persistence/db_manager.py` | lazy init · `create_all` when flags on |
| `product_persistence/repositories/sqlite_reply_log_repository.py` | **新增** |
| `product_persistence/services/preview_reply_log_service.py` | shadow write + `db_recorded` / `db_error` |
| `tests/test_sqlite_reply_log_shadow_write.py` | S1–S8 |
| `tests/test_handler_sqlite_reply_log_shadow_write.py` | handler integration |

---

## PreviewRecordResult 扩展

| 字段 | 说明 |
|------|------|
| `db_recorded` | SQLite 写入成功 |
| `db_error` | SQLite 失败原因（不抛给 handler） |
| `source` | `in_memory` · `in_memory+sqlite_shadow` |

---

## 测试

`uv run python -m unittest discover -s tests -v`

---

## 下一步

| Phase | 内容 |
|-------|------|
| **14m** | SendDecision snapshot shadow write **planning** |
| **14n** | Dashboard read API **skeleton only** |
| **14o** | AuditLog / PendingAssisted planning |

---

*签收：Phase 14l · 2026-06-03*

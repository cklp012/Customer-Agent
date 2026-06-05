# Phase 14g 完成 — Preview ReplyLog Service In-Memory Adapter

| 项 | 内容 |
|----|------|
| 状态 | **in-memory service adapter** |
| 日期 | 2026-06-03 |
| 前置 | [phase14f_done.md](phase14f_done.md) · [phase13e_done.md](phase13e_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 实现 | `PreviewReplyLogService` 读 `Message/gates` in-memory projection |
| DB / SQLite / engine | **无** |
| handler 接入 | **无** |
| SendMessage / PDD / Doudian | **未改** |
| 发送行为 | **不变** |

---

## Service API

| 方法 | 行为 |
|------|------|
| `list_reply_logs(...)` | `list_preview_reply_logs()` + 可选过滤 |
| `get_reply_log(id)` | 按 `reply_log_id` 查找 |
| `clear_in_memory_logs_for_tests()` | `preview_log.clear()` |
| `record_preview(...)` | 不写 DB、不发送；flag off → `product_persistence_disabled`；flag on 无 repository → `in_memory_deferred`（handler 仍用 `append_preview_log`） |

**Flags：** `PRODUCT_PERSISTENCE_ENABLED=false` 时 **仍可** list in-memory。

---

## 测试

`tests/test_preview_reply_log_service_in_memory.py`

---

## 下一步

| Phase | 内容 |
|-------|------|
| **14h** | Preview ReplyLog service integration **planning** only |
| **14i** | optional SQLite shadow write planning |
| **14j** | Dashboard read API planning |

---

*签收：Phase 14g · 2026-06-03*

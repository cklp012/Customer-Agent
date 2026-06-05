# Phase 14i 完成 — PreviewReplyLogService Handler Integration (Test Shop Only)

| 项 | 内容 |
|----|------|
| 状态 | **test shop handler integration** |
| 日期 | 2026-06-03 |
| 前置 | [phase14h_done.md](phase14h_done.md) · [phase14g_done.md](phase14g_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 实现 | test shop preview branch 经 `PreviewReplyLogService.record_preview` 写 in-memory |
| DB / SQLite / engine | **无** |
| SendMessage / PDD / Doudian | **未改** |
| non-test shop | **legacy unchanged** |
| assisted / auto | **未实现** |

---

## 行为摘要

| 路径 | 行为 |
|------|------|
| test shop preview | `_record_preview_reply_log` → service → `append_preview_log` · **zero-send** |
| service failure | fail-open fallback `append_preview_log` · **仍 zero-send** |
| non-test shop | 不调用 service · legacy `_send_reply` 不变 |
| `PRODUCT_PERSISTENCE_ENABLED=false` | in-memory record **仍可用** |

---

## 代码变更

| 文件 | 变更 |
|------|------|
| `product_persistence/services/preview_reply_log_service.py` | `record_preview` 包装 `append_preview_log` |
| `Message/handlers/ai_handler.py` | `_record_preview_reply_log` helper · preview branch 接入 service |
| `tests/test_handler_preview_reply_log_service_integration.py` | H1–H10 |
| `tests/test_preview_reply_log_service_in_memory.py` | record_preview 写入/读取测试 |

---

## H4 failure policy（14i 实现）

service 抛异常 → handler fallback `append_preview_log` → `return True`（若 fallback 成功）· **永不** legacy send。

---

## 测试

`uv run python -m unittest discover -s tests -v`

---

## 下一步

| Phase | 内容 |
|-------|------|
| **14j** | optional SQLite shadow write **planning only** |
| **14k** | Dashboard read API **planning only** |
| **14l** | SQLite shadow ReplyLog implementation behind flag (later) |

---

*签收：Phase 14i · 2026-06-03*

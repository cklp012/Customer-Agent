# Phase 14j — SQLite Shadow Write Test Plan (Future 14l)

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 实现 | **Phase 14l** |
| 建议文件 | `tests/test_preview_reply_log_sqlite_shadow.py` |

---

## 1. 目的

14l 实现 SQLite shadow write 后，验证：

1. flags off → in-memory only · 无 DB
2. flags on → `product_gate.db` + `reply_logs` row
3. non-test shop 无 DB 副作用
4. SQLite failure → no send · in-memory retained
5. legacy `channel_shop.db` 不动
6. assisted / auto 未引入

---

## 2. 测试矩阵 S1–S10

### S1 — `flags_off_in_memory_only`

| 项 | 内容 |
|----|------|
| 前置 | flags unset / false |
| 操作 | test shop preview `handle()` |
| 断言 | `temp/product_gate.db` **不存在** |
| 断言 | `preview_log` 有 1 条 |
| 断言 | `list_reply_logs()` 可读 |
| 断言 | zero-send |

---

### S2 — `flags_on_creates_product_gate_db`

| 项 | 内容 |
|----|------|
| 前置 | `PRODUCT_PERSISTENCE_ENABLED=true` · `WRITE_REPLY_LOG=true` |
| 操作 | test shop preview |
| 断言 | `product_gate.db` **存在** |
| 断言 | `reply_logs` 表有 1 row |
| 断言 | row `reply_log_id` 与 in-memory 一致 |
| 断言 | zero-send |

---

### S3 — `non_test_shop_no_db_write`

| 项 | 内容 |
|----|------|
| 前置 | flags on · allowlist 未命中 |
| 操作 | legacy AI reply path |
| 断言 | `_send_reply` 调用 |
| 断言 | `record_preview` 未调用 |
| 断言 | `product_gate.db` 无新 row（或不存在） |

---

### S4 — `sqlite_write_failure_no_send`

| 项 | 内容 |
|----|------|
| 前置 | flags on · test shop |
| Patch | `ReplyLogRepository.create_preview_reply_log` → `RuntimeError` |
| Patch | `_send_reply` · `SendMessage` |
| 操作 | preview `handle()` |
| 断言 | **no send** |
| 断言 | in-memory record **存在** |
| 断言 | `PreviewRecordResult.db_recorded=False`（若可观测） |
| 断言 | `handle()` 返回 True（in-memory 成功） |

---

### S5 — `db_does_not_touch_legacy`

| 项 | 内容 |
|----|------|
| 前置 | 记录 `channel_shop.db` mtime/size（若存在） |
| 操作 | S2 full path |
| 断言 | legacy DB **未修改** |
| 断言 | service/handler 不 import `database.db_manager` |

---

### S6 — `handler_no_db_import`

| 项 | 内容 |
|----|------|
| 类型 | 静态源码 |
| 文件 | `Message/handlers/ai_handler.py` |
| 断言 | 无 `product_persistence.db_manager` |
| 断言 | 无 `product_persistence.models` |
| 断言 | 无 `sqlalchemy` |

---

### S7 — `doudian_not_enabled`

| 项 | 内容 |
|----|------|
| 前置 | flags on · `platform_id=doudian` |
| 操作 | handler |
| 断言 | 无 preview branch |
| 断言 | `product_gate.db` 无 write |
| 断言 | legacy send |

---

### S8 — `rollback_flags`

| 项 | 内容 |
|----|------|
| 步骤 1 | flags on → preview → DB row exists |
| 步骤 2 | flags off → preview again |
| 断言 | 新记录仅 in-memory |
| 断言 | 旧 DB row 仍保留（不删除） |
| 断言 | zero-send |

---

### S9 — `schema_fields`

| 项 | 内容 |
|----|------|
| 前置 | flags on · allowed intent preview |
| 断言 | DB row 含 `send_status` · `intent` · `intent_bucket` · `risk_level` |
| 断言 | `shop_id` · `workspace_id` · `buyer_id` 非空 |
| blocked case | `send_mode=human_takeover` · `send_status=not_sent_human_takeover` |

---

### S10 — `no_assisted_auto`

| 项 | 内容 |
|----|------|
| 断言 | 无 assisted approve send path |
| 断言 | 无 auto send path |
| 断言 | `reply_mode` 仍为 preview only in test |
| 源码 | 无 `AssistedReplyService` handler wiring |

---

## 3. 与现有测试关系

| 现有 | 14l 后 |
|------|--------|
| H1–H10（14i） | **仍须 green** |
| Z1–Z10（13d） | **仍须 green** |
| 14g in-memory service tests | **仍须 green** |
| S1–S10 | **新增** |

---

## 4. CI 建议

| 模式 | env |
|------|-----|
| 默认 CI | flags off · S1 pass · 无 DB artifact |
| optional job | flags on · temp dir isolated · S2/S4/S9 |

**CI 默认不创建 `product_gate.db`。**

---

## 5. Go/No-Go（14l 签收）

- [ ] S1–S10 green
- [ ] H1–H10 无回归
- [ ] 全量 unittest green
- [ ] flags 默认 off
- [ ] `channel_shop.db` untouched

---

*Phase 14j · planning only · 2026-06-03*

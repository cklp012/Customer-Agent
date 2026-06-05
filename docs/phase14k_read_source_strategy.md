# Phase 14k — Read Source Strategy

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 对齐 | [phase14j_replylog_shadow_write_flow.md](phase14j_replylog_shadow_write_flow.md) · [phase14j_flags_failure_rollback.md](phase14j_flags_failure_rollback.md) |

---

## 1. 总原则

| # | 原则 |
|---|------|
| 1 | Dashboard read **只读** · 不 send |
| 2 | read failure **不影响** handler / SendMessage |
| 3 | non-test shop legacy **不受影响** |
| 4 | API contract **稳定** · 换 repository 不改 JSON shape |
| 5 | in-memory 可接受数据丢失（preview/test phase） |

---

## 2. Current（14i · as-is）

```
GET /api/product/reply-logs          [14m 实现]
  → PreviewReplyLogService.list_reply_logs(filters...)
  → list_preview_reply_logs()
  → source = "in_memory"
```

| 项 | 行为 |
|----|------|
| 数据生命周期 | 进程内 · 重启丢失 |
| flags | **不依赖** `PRODUCT_PERSISTENCE_ENABLED` |
| DB | 无 |

---

## 3. Future 14l — read source selection

```python
# 规划示意 · 14k 不写代码
def list_reply_logs(...):
    if not flags.should_read_dashboard_from_product_db():
        return _list_from_in_memory(...)

    try:
        rows = repository.list_reply_logs(...)
        return PreviewReplyLogServiceResult(
            success=True,
            source="sqlite_shadow",
            records=rows,
        )
    except Exception as exc:
        fallback = _list_from_in_memory(...)
        return fallback.with_warning("sqlite_read_failed_fallback_in_memory")
```

### 3.1 Flag

| Flag | 默认 | 行为 |
|------|------|------|
| `PRODUCT_PERSISTENCE_READ_DASHBOARD` | `false` | false → **always in_memory** |
| true + SQLite ok | | read `product_gate.db` |
| true + SQLite error | | fallback in_memory + `warnings[]` |

**read flag 与 write flag 独立：**

| WRITE_REPLY_LOG | READ_DASHBOARD | 典型场景 |
|-----------------|----------------|----------|
| false | false | 14i 默认 · in-memory only |
| true | false | shadow 写 DB · Dashboard 仍读 memory |
| true | true | 写+读 SQLite |
| false | true | 只读历史 DB（rollback write 后） |

---

## 4. Fallback 策略

| 场景 | 行为 | send path |
|------|------|-----------|
| in_memory read ok | 200 · `source=in_memory` | 无影响 |
| SQLite read fail | 200 · fallback in_memory · warning | 无影响 |
| both fail | 500 · `read_failed` | 无影响 |
| SQLite write fail (14l) | in-memory ok · `db_recorded=false` | **no send** |

**read failure 绝不能触发 SendMessage。**

---

## 5. in-memory vs SQLite 数据一致性

| 阶段 | 一致性 |
|------|--------|
| 14i | 单一 in-memory · 强一致 |
| 14l write on · read off | memory 有最新 · DB 有 shadow · Dashboard 读 memory |
| 14l write on · read on | 以 SQLite 为主 · memory 作 fallback |
| 进程重启 | memory 空 · SQLite 保留（read on 时） |

**14k 接受 preview phase 重启丢 memory。**

---

## 6. `source` 响应字段

| 值 | 含义 |
|----|------|
| `in_memory` | 来自 projection |
| `sqlite_shadow` | 来自 `product_gate.db` |
| `mixed` | 合并策略（未来 · 低优先级） |

List + Detail API 均返回 `source`（detail 见 detail contract）。

---

## 7. PostgreSQL 未来

| 项 | 说明 |
|----|------|
| repository 接口 | `ReplyLogRepository` Protocol 不变 |
| API contract | **不变** |
| `source` | 可新增 `postgres` enum 值 |
| migration | 14d Option C 长期目标 |

---

## 8. 与 write path 关系

```
Write (14i/14l):  handler → record_preview → in-memory [→ SQLite shadow]
Read  (14m+):     HTTP GET → list_reply_logs → in-memory | SQLite
```

- read 与 write **解耦**
- read API 不调用 `record_preview`
- write 不依赖 read flag

---

## 9. non-test shop

| 路径 | read | write |
|------|------|-------|
| non-test legacy | 空列表或历史（若有） | 无 preview write |
| test shop preview | 有 items | in-memory [+ shadow] |

---

*Phase 14k · planning only · 2026-06-03*

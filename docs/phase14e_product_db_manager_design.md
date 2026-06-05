# Phase 14e — ProductDbManager Design

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 实现 | Phase **14f** skeleton · **14g** optional `create_all` |
| 路径 | `product_persistence/db_manager.py`（规划） |

---

## 1. 独立 SQLite

| 项 | 值 |
|----|-----|
| 默认文件 | `./temp/product_gate.db` |
| 与 legacy 隔离 | `./temp/channel_shop.db` **不共享** engine |

---

## 2. 环境变量（建议）

| 变量 | 默认 | 说明 |
|------|------|------|
| `PRODUCT_PERSISTENCE_ENABLED` | `false` | 总开关 |
| `PRODUCT_DB_URL` | `sqlite:///./temp/product_gate.db` | SQLAlchemy URL |
| `PRODUCT_DB_ECHO` | `false` | SQL debug（dev only） |

**读取：** `product_persistence/flags.py` — 与 `runtime_modes` / `diagnose_runtime` 风格一致。

---

## 3. Schema 创建策略

| Phase | 策略 |
|-------|------|
| **14f** | skeleton：`init_product_db()` **可不** `create_all`（no-op 或 lazy） |
| **14g** | test shop write 前：`Base.metadata.create_all(engine)` **仅 product models** |
| **未来** | product 库专用 Alembic **或** 迁 PostgreSQL（14d Option C） |

**不用 legacy `create_all`：** product 表 **不** 注册到 `database.models.Base`。

---

## 4. 连接生命周期 API（草案）

```python
# 概念 API — 14f skeleton only

def is_product_db_available() -> bool: ...
def init_product_db() -> None: ...       # lazy init if enabled
def get_product_session() -> Session: ... # context manager 推荐
def close_product_db() -> None: ...
```

| 规则 | 说明 |
|------|------|
| Lazy init | `PRODUCT_PERSISTENCE_ENABLED=false` → **不** 创建 engine |
| 单例 | 进程内一个 engine（仿 `DatabaseManager` 但独立） |
| Session | `with get_product_session() as s:` — commit/rollback 在 repository |
| 启动 | **不** 在 `app.py` / `AutoReplyThread` 强制 init — 首次 service 调用时 init |

---

## 5. 失败策略

### 5.1 non-test shop

| 场景 | 行为 |
|------|------|
| persistence disabled | 仅 in-memory（13e） |
| write 失败 | **忽略** DB；legacy send **不变** |
| read 失败 | Dashboard 回退 in-memory / 空列表 |

### 5.2 test shop preview（14g 决策）

| 选项 | 14e 推荐 |
|------|----------|
| A: DB fail → fail-safe no-send | 严格；可能丢建议可查性 |
| B: DB fail → **fallback in-memory** + no-send | **✅ 推荐** |

**推荐 B 理由：**

- 13d 已保证 **zero-send** — DB 失败 **不得** 触发 `_send_reply` / SendMessage
- in-memory `preview_log` 仍写入 → 测试/本地可观测
- 与 13b shadow fail-open（non-test）**不对称**  intentional：test shop 宁可不发不可误发

```text
test shop preview:
  append in-memory (always, gate on)
  try DB shadow write (if flags)
  on DB error: log + continue — return True, no send
  NEVER: fallback to legacy send
```

### 5.3 assisted approve（未来）

| 场景 | 行为 |
|------|------|
| AuditLog write 失败 | **禁止发送**（无审计不发送） |
| ReplyLog update 失败 | **禁止发送** |
| pending mark 失败 | **禁止发送** |

---

## 6. 与 legacy DatabaseManager 对比

| | `DatabaseManager` | `ProductDbManager` |
|--|-------------------|---------------------|
| 路径 | `database/db_manager.py` | `product_persistence/db_manager.py` |
| DB | `channel_shop.db` | `product_gate.db` |
| 启动 | DI 单例 · `create_all` legacy | lazy · flag-gated |
| 14e/14f | **不改** | skeleton only |

---

*ProductDbManager design · Phase 14e · 2026-06-03*

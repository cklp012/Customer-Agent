# Phase 14b — Migration Draft Overview

| 项 | 值 |
|----|-----|
| 类型 | **docs only** · **不创建真实 migration · 不执行 DB 变更** |
| 前置 | [phase14a_done.md](phase14a_done.md) |
| 目标 | 为 **14c+** DB review 提供 Alembic/SQL 草案 |

---

## 1. Phase 14b 边界

| 做 | 不做 |
|----|------|
| 文档化 CREATE TABLE / INDEX / rollback SQL | 新增 `alembic/versions/*.py` |
| 建议 migration 命名与顺序 | 修改 `database/models.py` |
| 对齐 14a schema 字段 | 执行 `alembic upgrade` |
| 说明 shadow-first / 默认 off | 改 handler / runtime 读写 |

**当前运行行为：** 13d/13e in-memory preview **不变**；PDD legacy send **不变**。

---

## 2. Shadow-first 原则

| 原则 | 说明 |
|------|------|
| 新表独立 | 不 ALTER legacy `accounts` / `shops` 热路径表 |
| 默认不读 | runtime 直至 `SHADOW_*` flag 显式开启（14c+） |
| 可空 FK | draft 阶段弱 FK，避免 legacy 库不完整数据阻塞 migration |
| 可回滚 | 每 revision `downgrade()` 可 DROP 全部 shadow 表 |
| non-test legacy | migration 存在与否 **不影响** non-test `_send_reply` |

---

## 3. 建议 migration 文件命名（草案）

实际文件名由真实 migration 阶段确定；以下为 **review 用建议**：

| 顺序 | 建议文件名 | 内容 |
|------|------------|------|
| 1 | `2026_06_03_0001_create_reply_logs_shadow.py` | `reply_logs` |
| 2 | `2026_06_03_0002_create_send_decision_snapshots_shadow.py` | `send_decision_snapshots` |
| 3 | `2026_06_03_0003_create_pending_assisted_replies_shadow.py` | `pending_assisted_replies` |
| 4 | `2026_06_03_0004_create_audit_logs_shadow.py` | `audit_logs` |

**合并策略（可选）：** 单 revision `0001_create_product_gate_shadow_tables.py` 含四表 — 评审二选一。

---

## 4. 技术栈假设

| 项 | 草案选择 |
|----|----------|
| DB | PostgreSQL 14+（推荐）或 SQLite dev |
| PK | UUID `gen_random_uuid()` / app-generated |
| 时间 | `TIMESTAMPTZ` · `DEFAULT now()` |
| 枚举 | **VARCHAR + app validation**（避免 PG ENUM migration 摩擦） |
| JSON | `JSONB`（PG）/ `TEXT`（SQLite dev） |

---

## 5. 文档索引

| 文档 | 表 |
|------|-----|
| [phase14b_reply_logs_migration_draft.md](phase14b_reply_logs_migration_draft.md) | `reply_logs` |
| [phase14b_send_decision_snapshots_migration_draft.md](phase14b_send_decision_snapshots_migration_draft.md) | `send_decision_snapshots` |
| [phase14b_pending_assisted_replies_migration_draft.md](phase14b_pending_assisted_replies_migration_draft.md) | `pending_assisted_replies` |
| [phase14b_audit_logs_migration_draft.md](phase14b_audit_logs_migration_draft.md) | `audit_logs` |
| [phase14b_indexes_constraints_rollback.md](phase14b_indexes_constraints_rollback.md) | 汇总 |

---

## 6. 与 14a M1 对齐

Phase 14a **M1** = 创建空 shadow 表、零写入。14b 提供 **DDL 草案**；**M1 代码** 在 Phase **14c**（空 migration 文件 only）。

---

## 7. Rollback 总览

```text
downgrade (reverse order):
  4. DROP audit_logs
  3. DROP pending_assisted_replies
  2. DROP send_decision_snapshots
  1. DROP reply_logs
```

详见 [phase14b_indexes_constraints_rollback.md](phase14b_indexes_constraints_rollback.md)。

---

*Migration draft overview · Phase 14b · 2026-06-03*

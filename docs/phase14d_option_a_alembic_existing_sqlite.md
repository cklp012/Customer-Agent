# Phase 14d — Option A: Alembic on Existing Legacy SQLite

| 项 | 值 |
|----|-----|
| 类型 | docs only · ADR 选项 |
| 结论 | **不建议当前阶段采用** |

---

## 1. 方案描述

在 **现有** `./temp/channel_shop.db` 上引入 Alembic：

- 新增 `alembic/` + `alembic.ini`
- 将 `channels` / `shops` / `accounts` / `keywords` 作为 baseline revision
- 在同一库追加 `reply_logs` / `send_decision_snapshots` / `pending_assisted_replies` / `audit_logs`
- 逐步替换 `Base.metadata.create_all()` 为 `alembic upgrade head`

---

## 2. 优点

| # | 优点 |
|---|------|
| 1 | **标准 migration 工具** — 业界惯例，schema 版本可追溯 |
| 2 | **版本化清晰** — upgrade/downgrade 文档化 |
| 3 | **适合严肃 DB 演进** — 长期维护单库时有利 |
| 4 | **14b DDL** 可直接迁入 revision |

---

## 3. 缺点

| # | 缺点 |
|---|------|
| 1 | **触碰 legacy DB** — shadow 表与 PDD 账号表同库同生命周期 |
| 2 | **create_all → Alembic 思维迁移** — 需 baseline 现有生产库状态 |
| 3 | **影响 PDD legacy persistence** — `DatabaseManager` 启动路径需改 |
| 4 | **SQLite migration 限制** — 改列/删列繁琐；无原生 ENUM |
| 5 | **当前阶段过重** — 14c 已确认无 framework，引入成本高 |

---

## 4. 风险

| 风险 | 严重度 |
|------|--------|
| baseline revision 与真实 `channel_shop.db` 不一致 → 破坏现有表 | 🔴 |
| 开发/测试/生产 DB 漂移 | 🟡 |
| migration 失败阻塞 GUI 启动 | 🔴 |
| shadow 表 bug 影响 legacy 连接池 | 🟡 |
| rollback 需 downgrade 多 revision | 🟡 |

---

## 5. 实施前提（若未来采用）

- [ ] 冻结 legacy schema 快照
- [ ] 全量备份现有 SQLite
- [ ] `create_all` 与 Alembic 双轨过渡期设计
- [ ] 独立 CI migration 测试
- [ ] **不与** product gate 试点同一次发布

---

## 6. 结论

| 项 | 结论 |
|----|------|
| **当前（14d）** | **No-Go** |
| **未来** | 可作为 **legacy 库正式产品化** 或 **单库合并** 阶段的选项 |
| **替代** | 优先 **Option B** 独立 shadow SQLite |

---

*Option A · Phase 14d · 2026-06-03*

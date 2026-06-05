# Phase 14d — Persistence Route Recommendation（SSOT）

| 项 | 值 |
|----|-----|
| 日期 | 2026-06-03 |
| 决策 | **采用 Option B** |

---

## 推荐路线

## **B — SaaS Shadow Persistence Layer + Independent SQLite DB**

---

## 1. 为什么选 B

| # | 理由 |
|---|------|
| 1 | **14c 已证明** 无 Alembic — B 不要求先解决 legacy baseline |
| 2 | **零触碰** `database/models.py` · `db_manager.py` · PDD 启动路径 |
| 3 | **回滚** = flag off + 删 `product_gate.db` |
| 4 | **对齐 13d–13e** — in-memory 可渐进双写到独立库 |
| 5 | **本地可开发** — 单文件 SQLite，无 Docker 硬性要求 |
| 6 | **预留 C** — repository port 抽象后换 PostgreSQL |

---

## 2. 为什么暂不选 A

| # | 理由 |
|---|------|
| 1 | 与 **生产 legacy SQLite** 绑定，baseline 风险高 |
| 2 | 当前仅需 **4 张 shadow 表**，不值得重构全库 migration 文化 |
| 3 | `create_all` 与 Alembic 共存期长，易出错 |
| 4 | 14c 结论：**不强行引入 Alembic** 仍然正确 |

---

## 3. 为什么暂不选 C

| # | 理由 |
|---|------|
| 1 | 无商家试点、无 Dashboard 运行时、assisted 未实现 |
| 2 | 运维与本地 dev 成本对当前阶段过高 |
| 3 | B 的 schema/DDL 可直接迁移到 PG，不浪费 14a/14b 工作 |

---

## 4. 架构约束（实施后仍有效）

| 约束 | 说明 |
|------|------|
| legacy DB 不动 | `channel_shop.db` + `DatabaseManager` 保持 as-is |
| PDD hot path 不动 | 队列 `pdd_{shop_id}` · SendMessage 不读 product DB |
| product persistence 默认 off | `PRODUCT_PERSISTENCE_ENABLED=false` |
| non-test legacy unchanged | allowlist 外不写、不读 product DB 做 send 决策 |
| test shop failure | gate on 写失败 → fail-safe **no-send** |

---

## 5. 建议物理布局

|  artifact | 路径（建议） |
|-----------|--------------|
| SaaS models | `database/saas_models.py`（14f skeleton） |
| Product DB manager | `database/product_db_manager.py`（14f skeleton） |
| Repository ports | `product_persistence/ports.py`（14e docs → 14f code） |
| SQLite 文件 | `./temp/product_gate.db` |
| Flags | `product_persistence/flags.py` |

**14e（docs only）：** module boundary + `ReplyLogRepository` Protocol 草案 — **不实现写入**。

---

## 6. 后续实现路线

| Phase | 内容 | 类型 |
|-------|------|------|
| **14e** | SaaS shadow persistence **module boundary** planning | docs |
| **14f** | Empty `ProductDbManager` / repository **skeleton only** | minimal code |
| **14g** | in-memory → SQLite **ReplyLog shadow write**（test shop only） | code + tests |
| **14h** | Dashboard read **API planning** | docs |

**可选远期：** product 库专用 Alembic（**非** legacy 库）— 在 14g 稳定后评审。

---

## 7. 与 14b DDL 关系

14b PostgreSQL-oriented DDL 作为 **逻辑 schema SSOT**；B 阶段 SQLite 实现可：

- 使用 `saas_models.py` + `create_all`（首版）
- 或 SQLite 兼容类型（TEXT 替 JSONB）

升级到 C 时执行 PG DDL + 数据迁移工具。

---

## 8. 签收

| 决策者 | 结论 |
|--------|------|
| Phase 14d ADR | **Option B approved for next phases** |
| Option A | Deferred |
| Option C | Future target |

---

*Recommendation SSOT · Phase 14d · 2026-06-03*

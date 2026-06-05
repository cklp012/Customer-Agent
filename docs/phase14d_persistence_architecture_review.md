# Phase 14d — Persistence Architecture Decision Review

| 项 | 值 |
|----|-----|
| 类型 | **docs only** · **ADR 评审 · 不实现** |
| 前置 | [phase14c_done.md](phase14c_done.md) · [phase14b_done.md](phase14b_done.md) · [phase14a_done.md](phase14a_done.md) |
| 结论 | 见 [phase14d_recommendation.md](phase14d_recommendation.md) |

---

## 1. Phase 14d 目标

在 **不实现 persistence** 的前提下，评审未来 SaaS/product 数据落地方向，选定推荐路线供 14e+ 使用。

| 做 | 不做 |
|----|------|
| 比较 A/B/C 三条路线 | 引入 Alembic |
| 定义评审标准与推荐 | 创建 migration / 表 |
| 衔接 14a/14b DDL 草案 | 改 `database/models.py` / `db_manager.py` |
| 明确 legacy 隔离原则 | 改 handler / PDD 热路径 |

---

## 2. 当前 Legacy Persistence 现状（as-is）

```text
database/models.py          → SQLAlchemy Base (channels, shops, accounts, keywords)
database/db_manager.py      → SQLite ./temp/channel_shop.db
                            → Base.metadata.create_all() on startup
                            → 无 Alembic / 无 revision 链
Message/gates/preview_log   → InMemoryPreviewLog (13d/13e)
Message/gates/reply_log_projection → list_preview_reply_logs() 内存读
```

| 特征 | 说明 |
|------|------|
| 单库 SQLite | 与 PDD GUI / 账号 / 关键词同库 |
| 隐式 schema | `create_all` 随模型变更隐式演进 |
| 生产依赖 | AutoReply、账号登录、关键词转人工 **依赖此库** |
| Product gate | **不** 依赖 DB 持久化（13d allowlist 内存） |

---

## 3. 为什么不能贸然引入 Migration（路线 A 风险）

| 原因 | 说明 |
|------|------|
| 无 baseline | 现有表由 `create_all` 创建，无 stamped revision |
| 热路径耦合 | `DatabaseManager` 单例在启动时建表 |
| SQLite 限制 | ALTER 弱、ENUM 差、并发写弱 |
| 14c 结论 | 无 framework — 强行加 Alembic 需全项目 baseline 工程 |
| 产品阶段 | 仅需 shadow SaaS 表，非重构 legacy |

**原则：** product/SaaS persistence **应与 PDD legacy 热路径隔离**，避免 ReplyLog 实验影响 `accounts`/`shops` 稳定性。

---

## 4. 三条路线概览

| 路线 | 摘要 | 文档 |
|------|------|------|
| **A** | Alembic 管理**现有** legacy SQLite | [phase14d_option_a_alembic_existing_sqlite.md](phase14d_option_a_alembic_existing_sqlite.md) |
| **B** | **独立** SaaS shadow SQLite + 新 persistence 层 | [phase14d_option_b_saas_shadow_sqlite.md](phase14d_option_b_saas_shadow_sqlite.md) |
| **C** | 未来 PostgreSQL SaaS 双库 / 服务化 | [phase14d_option_c_postgres_saas_db.md](phase14d_option_c_postgres_saas_db.md) |

---

## 5. 评审标准（加权）

| 维度 | 权重 | 说明 |
|------|------|------|
| **PDD legacy 风险** | 高 | 不得破坏现有客服启动/登录/关键词 |
| **实现复杂度** | 高 | 当前团队阶段可交付 |
| **回滚难度** | 高 | flag off / 删 shadow DB 即可 |
| **SaaS 扩展性** | 中 | 多租户 · AuditLog · Dashboard |
| **Dashboard/API** | 中 | 14e+ read/write 边界 |
| **本地开发** | 中 | 单机可跑、无外部依赖 |
| **→ PostgreSQL 路径** | 中 | B 应可平滑升级至 C |

---

## 6. 评分摘要（定性）

| 维度 | A | B | C |
|------|---|---|---|
| PDD legacy 风险 | 🔴 高 | 🟢 低 | 🟢 低（若双库） |
| 实现复杂度 | 🔴 高 | 🟢 低-中 | 🟡 中-高 |
| 回滚 | 🟡 中 | 🟢 易 | 🟡 中 |
| SaaS 扩展 | 🟢 好 | 🟡 够用 | 🟢 最好 |
| 本地 dev | 🟡 | 🟢 | 🟡 |
| 当前阶段适配 | 🔴 | 🟢 | 🔴 |

**推荐：** **B** — 详见 [phase14d_recommendation.md](phase14d_recommendation.md)。

---

## 7. 与 Product Gate 阶段对齐

| Phase | 持久化 |
|-------|--------|
| 13d/13e | in-memory preview + projection |
| 14a/14b | schema + DDL draft |
| 14c | 无 Alembic |
| **14d** | **路线选定（本文）** |
| 14e+ | module boundary → skeleton → test shop SQLite write |

**不变量：** `product_gate_enabled` 默认 false · non-test legacy · test shop fail-safe no-send。

---

## 8. 文档索引

| 文档 | 内容 |
|------|------|
| [phase14d_option_a_alembic_existing_sqlite.md](phase14d_option_a_alembic_existing_sqlite.md) | 路线 A |
| [phase14d_option_b_saas_shadow_sqlite.md](phase14d_option_b_saas_shadow_sqlite.md) | 路线 B |
| [phase14d_option_c_postgres_saas_db.md](phase14d_option_c_postgres_saas_db.md) | 路线 C |
| [phase14d_recommendation.md](phase14d_recommendation.md) | **推荐 SSOT** |
| [phase14d_done.md](phase14d_done.md) | 签收 |

---

*Persistence ADR review · Phase 14d · 2026-06-03*

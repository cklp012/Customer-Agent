# Phase 14d — Option C: PostgreSQL SaaS DB (Future)

| 项 | 值 |
|----|-----|
| 类型 | docs only · ADR 选项 |
| 结论 | **未来目标，非当前下一步** |

---

## 1. 方案描述

将 SaaS/product 持久化迁至 **独立 PostgreSQL**：

```text
Legacy SQLite (local)          PostgreSQL (SaaS)
channel_shop.db                product_saas DB
PDD 账号/关键词                 reply_logs · audit_logs · workspaces · shop_bindings
```

或全量 SaaS 上云后 legacy 只读 / 逐步退役。

---

## 2. 优点

| # | 优点 |
|---|------|
| 1 | **多租户** — workspace / member / RBAC 原生友好 |
| 2 | **Dashboard/API** — JSONB、复杂索引、分页、聚合 |
| 3 | **审计/计费** — append-only AuditLog、用量统计 |
| 4 | **并发** — assisted approve、多客服同时操作 |
| 5 | **14b DDL** — PostgreSQL 草案已按 PG 编写 |

---

## 3. 缺点

| # | 缺点 |
|---|------|
| 1 | **本地复杂度** — Docker PG、连接串、迁移 |
| 2 | **部署成本** — 托管 PG、备份、监控 |
| 3 | **secrets/env** — `DATABASE_URL`、轮换、网络 |
| 4 | **当前过早** — 无商家试点、无 Dashboard 实现、assisted 未落地 |
| 5 | **双栈运维** — 开发机仍需 legacy SQLite + 可选 PG |

---

## 4. 适用时机（Go 条件）

| # | 条件 |
|---|------|
| G1 | 真实商家试点 ≥ 1 workspace |
| G2 | Dashboard read API 已规划并实现（14h+） |
| G3 | assisted workflow 稳定 + AuditLog 生产需求 |
| G4 | 多 operator 并发确认 |
| G5 | Option B SQLite shadow 已验证 repository 边界 |
| G6 | 运维可接受 PG backup/restore |

---

## 5. 从 Option B 升级路径

```text
B: product_gate.db (SQLite) + Repository ports
        ↓ 同 schema DDL
C: postgresql://.../product_saas
        ↓ 换 sqlite_impl → postgres_impl
   Alembic on product DB only (仍不碰 legacy SQLite)
```

**不建议：** 一步到位 PG 跳过 B — 失去最低风险试点。

---

## 6. 结论

| 项 | 结论 |
|----|------|
| **当前（14d）** | **Defer** |
| **定位** | 12–18 个月 SaaS 规模化目标 |
| **先行** | Option B 验证 schema + repository |

---

*Option C · Phase 14d · 2026-06-03*

# Phase 12e 完成 — DB Migration Planning for Product Gate

| 项 | 内容 |
|----|------|
| 状态 | **纯文档已完成** |
| 日期 | 2026-06-03 |
| SSOT 入口 | [phase12e_db_migration_plan.md](phase12e_db_migration_plan.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 代码 / tests | **未写 / 未改** |
| `database/models.py` | **未改** |
| SQL migration | **未创建** |
| UI / API / handler | **未改** |
| PDD / Doudian 热路径 | **未改** |

---

## 新增文档

| 文件 | 内容 |
|------|------|
| [phase12e_db_migration_plan.md](phase12e_db_migration_plan.md) | 目标、shadow-first、对象列表 |
| [phase12e_legacy_mapping.md](phase12e_legacy_mapping.md) | Channel/Shop/Account → SaaS |
| [phase12e_product_gate_tables.md](phase12e_product_gate_tables.md) | workspaces / shop_bindings / audit 等 |
| [phase12e_send_decision_reply_log_schema.md](phase12e_send_decision_reply_log_schema.md) | SendDecision / ReplyLog / Queue |
| [phase12e_migration_sequence.md](phase12e_migration_sequence.md) | M0–M9 |

---

## 核心签收

| # | 结论 |
|---|------|
| 1 | **Shadow-first** — 新表并行，不替换 legacy |
| 2 | **`product_gate_enabled` 默认 false** |
| 3 | **`reply_mode` 默认 preview** |
| 4 | **`connected` ≠ auto enabled** |
| 5 | **Preview** → ReplyLog `not_sent_preview`，**zero-send** |
| 6 | **blocked intent** → SendDecision + HumanTakeoverQueue |
| 7 | **pause / resume / reply-mode** → AuditLog |
| 8 | **PDD production** 在 M8 前保持 legacy 发送路径 |

---

## 更新的文档

| 文件 |
|------|
| [architecture_current.md](architecture_current.md) |
| [docs/README.md](README.md) |
| [phase12d_done.md](phase12d_done.md) |

---

## 下一步

| Phase | 状态 | 内容 |
|-------|------|------|
| **12f** | ✅ | Preview send gate implementation plan — [phase12f_done.md](phase12f_done.md) |
| **12g** | 待做 | PDD MVP merchant console wireframe |
| **13a** | 待做 | product gate pure functions + tests only（H1） |
| **13b** | 待做 | shadow SendDecision logging（H2） |

---

*签收：Phase 12e · 2026-06-03 · docs only*

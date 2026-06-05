# Phase 14d — Option B: SaaS Shadow Persistence + Separate SQLite

| 项 | 值 |
|----|-----|
| 类型 | docs only · ADR 选项 |
| 结论 | **推荐作为下一阶段路线** |

---

## 1. 方案描述

```text
Legacy (unchanged)                    Product / SaaS (new)
─────────────────────                 ─────────────────────────
database/models.py                    database/saas_models.py (新文件 · 14f+)
database/db_manager.py                database/product_db_manager.py (新 · 14f+)
./temp/channel_shop.db                ./temp/product_gate.db (建议路径)
channels · shops · accounts · keywords   reply_logs · send_decision_snapshots
                                       pending_assisted_replies · audit_logs
```

**Runtime：**

- `PRODUCT_PERSISTENCE_ENABLED=false`（默认）
- 仅 allowlisted test shop + flag on → 双写（14g：内存 + SQLite）
- non-test shop → **仅** legacy；不写 product DB
- write 失败 → test shop fail-safe no-send；non-test 不影响

---

## 2. 优点

| # | 优点 |
|---|------|
| 1 | **风险最低** — legacy DB / `db_manager` / `create_all` **不动** |
| 2 | **回滚简单** — flag off 或删除 `product_gate.db` |
| 3 | **本地开发友好** — 第二个 SQLite 文件，无 PostgreSQL 依赖 |
| 4 | **对齐 14a/14b** — DDL 草案直接用于新库 `create_all` 或首版 migration（仅 product 库） |
| 5 | **→ PostgreSQL 路径** — repository 抽象后换连接串即可（Option C） |
| 6 | **PDD 热路径隔离** — SendMessage / `pdd_{shop_id}` 不读 product DB |

---

## 3. 缺点

| # | 缺点 |
|---|------|
| 1 | **双 DB** — shop/account 维度需 `shop_id`/`account_id` 冗余，无 FK 到 legacy |
| 2 | **一致性** — legacy 删店 vs shadow 行残留；需投影或 TTL 策略 |
| 3 | **Repository 边界** — 必须定义 `ProductReplyLogRepository` 等接口 |
| 4 | **后续迁移** — 最终合并或迁 PG 时需 ETL 计划 |

---

## 4. 风险控制

| 控制 | 说明 |
|------|------|
| 默认 off | `PRODUCT_PERSISTENCE_ENABLED=false` |
| 写入 scope | 仅 gate-on test shop |
| fail-open（non-test） | product write 异常 **不影响** legacy send |
| fail-safe（test shop） | product write 异常 + gate on → no-send（已有 13d 语义） |
| 只读 legacy | product 层 **禁止** UPDATE legacy `accounts` |
| 独立文件 | `product_gate.db` 损坏不阻塞 `channel_shop.db` 启动 |

---

## 5. 建议模块边界（14e 规划）

```text
product_persistence/
  ports.py          # ReplyLogRepository, AuditLogRepository (Protocol)
  sqlite_impl.py    # 14g+ 实现
  flags.py          # PRODUCT_PERSISTENCE_ENABLED, PRODUCT_PERSISTENCE_WRITE
```

Handler 仅依赖 **port**；13e `list_preview_reply_logs()` 可增加 DB backend behind flag。

---

## 6. 表创建策略（14f/14g）

| 阶段 | 策略 |
|------|------|
| 14f | 空 `ProductDbManager` skeleton · `create_all` 可选 lazy |
| 14g | test shop preview → INSERT `reply_logs` |
| 未来 | 可选 **仅 product 库** 小 Alembic（不碰 legacy） |

---

## 7. 结论

| 项 | 结论 |
|----|------|
| **14d 推荐** | **Go** — 下一阶段实施 |
| **legacy** | 不修改 |
| **PDD** | 热路径不依赖 product DB |

---

*Option B · Phase 14d · 2026-06-03*

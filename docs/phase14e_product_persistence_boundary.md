# Phase 14e — Product Persistence Module Boundary

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 决策 | [phase14d_recommendation.md](phase14d_recommendation.md) Option B |
| **14e 不创建** | 下列目录与文件均为 **规划草案** |

---

## 1. 边界原则

| # | 原则 |
|---|------|
| B1 | `product_persistence/` **独立于** `database/`（legacy） |
| B2 | **不** `import database.models` · legacy **不** `import product_persistence` |
| B3 | Handler 仅通过 **service / repository interface** 访问（14g+） |
| B4 | 默认 **disabled** — 所有写入 behind flag |
| B5 | 不调用 SendMessage · 不做 intent classify · 不做 final guard |
| B6 | PDD 队列 `pdd_{shop_id}` · Channel 生命周期 **不依赖** product DB |

```text
database/                    product_persistence/
  models.py (legacy)           models.py (SaaS shadow ORM)
  db_manager.py                db_manager.py
  channel_shop.db              → product_gate.db
        ↑                              ↑
        │ NO cross-import              │
        └──────────┬───────────────────┘
                   │
            AIReplyHandler (future)
                   │
            PreviewReplyLogService
            (gates + in-memory + optional DB)
```

---

## 2. 未来目录草案（14f 创建 · 14e 不创建）

```text
product_persistence/
  __init__.py
  flags.py
  db_manager.py
  models.py
  repositories/
    __init__.py
    reply_log_repository.py
    send_decision_repository.py
    pending_assisted_reply_repository.py
    audit_log_repository.py
  services/
    __init__.py
    preview_reply_log_service.py
    assisted_reply_service.py
```

| 模块 | 职责 |
|------|------|
| `flags.py` | `PRODUCT_PERSISTENCE_*` 解析 |
| `db_manager.py` | `product_gate.db` 连接 · session 生命周期 |
| `models.py` | `reply_logs` 等 ORM（对齐 14a/14b） |
| `repositories/` | CRUD 端口 + SQLite 实现（14g+） |
| `services/` | 编排 gate + guard + repository |

---

## 3. 与 `Message/gates/` 的关系

| 层 | 包 | 职责 |
|----|-----|------|
| 纯逻辑 | `Message/gates/` | classify · SendDecision · guarded_send · in-memory preview_log |
| 持久化 | `product_persistence/` | 可选 DB shadow write/read |
| Handler | `Message/handlers/` | 调用 service；**不** 直接 ORM |

**13e 保留：** `Message/gates/preview_log.py` + `reply_log_projection.py` 作为 **默认** in-memory 路径。

---

## 4. 依赖方向（允许）

```text
Message/handlers/ai_handler.py
  → product_persistence/services/preview_reply_log_service.py  (14g+, behind flag)
  → Message/gates/*  (always)

product_persistence/repositories/*
  → product_persistence/models.py
  → product_persistence/db_manager.py

product_persistence/*
  ✗ database/*
  ✗ Channel/*
  ✗ SendMessage
```

---

## 5. 启用范围

| 店 | persistence |
|----|-------------|
| non-test / gate off | **不进入** product_persistence |
| test shop + preview gate | 14g 可选双写 |
| Doudian | **不进入** production persistence |

---

## 6. 测试策略

- Repository **Protocol** + `InMemory*Repository` fake（14f tests）
- 集成测试：tmp `product_gate.db` · flag on · test shop only
- Legacy `channel_shop.db` 测试 **不** 加载 product_persistence

---

*Module boundary · Phase 14e · 2026-06-03*

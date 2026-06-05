# Phase 14j — SQLite Shadow Write Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 前置 | [phase14i_done.md](phase14i_done.md) · [phase14d_done.md](phase14d_done.md) · [phase14a_done.md](phase14a_done.md) |
| 实现 | **Phase 14l**（SQLite ReplyLog shadow behind flag） |

---

## 1. Phase 14j 定位

| 项 | 结论 |
|----|------|
| 本 Phase | **仅文档规划** |
| 代码 | **不写** |
| DB 文件 | **不创建** `product_gate.db` |
| SQLite 写入 | **不实现** |
| engine / `create_all` | **不建立** |
| handler / SendMessage / PDD / Doudian | **不改** |

---

## 2. 背景（as-is · 14i）

```
allowlisted test shop preview branch
  → PreviewReplyLogService.record_preview
  → append_preview_log (in-memory)
  → zero-send
```

| 状态 | 说明 |
|------|------|
| in-memory | ✅ primary write + read（13e projection） |
| SQLite shadow | ❌ 未实现 |
| flags 默认 | `PRODUCT_PERSISTENCE_ENABLED=false` |
| legacy DB | `./temp/channel_shop.db` **不动** |

---

## 3. 未来目标（to-be · 14l+）

独立 shadow SQLite：`./temp/product_gate.db`（ADR Option B · [phase14d_done.md](phase14d_done.md)）

| 原则 | 说明 |
|------|------|
| **in-memory first** | 始终先写 in-memory；SQLite 为 optional shadow |
| **behind flags** | 仅 `ENABLED=true` + `WRITE_REPLY_LOG=true` 时尝试 SQLite |
| **test shop only** | 仅 allowlisted test shop preview branch 进入 shadow write |
| **non-test shop** | 完全不进入 product persistence write path |
| **zero-send 不变** | test shop preview 永不 SendMessage / outbound |
| **DB failure ≠ send** | SQLite init/write 失败 **不得** fallback legacy send |
| **legacy 隔离** | 不 FK `channel_shop.db` · 不改 `database/` |

---

## 4. 范围边界

| 纳入 14l | 不纳入 14l |
|----------|-----------|
| `reply_logs` 表 shadow write | `send_decision_snapshots`（→ **14m**） |
| `ProductDbManager` lazy init | `pending_assisted_replies` |
| `ReplyLogRepositorySQLite` stub 实现 | `audit_logs` |
| test shop 双写 in-memory + SQLite | assisted / auto send |
| flags-gated create `product_gate.db` | Doudian production path |
| | Dashboard read API（→ **14k** planning） |

---

## 5. 双写策略（test shop preview）

```
record_preview:
  1. append_preview_log (in-memory)     ← always, first
  2. if should_shadow_write_reply_log():
       ReplyLogRepository.create_preview_reply_log(...)
  3. return PreviewRecordResult(
       recorded=True,
       source="in_memory",
       db_recorded=True|False,
       db_error=...|None,
     )
```

- in-memory 成功 + SQLite 失败 → `recorded=True`, `db_recorded=False` · **仍 zero-send**
- handler **不感知** SQLite 细节

---

## 6. 不变量

| # | 不变量 |
|---|--------|
| 1 | product persistence **默认 off** |
| 2 | 仅 allowlisted **PDD test shop** + `reply_mode=preview` 进入 shadow write |
| 3 | **non-test shop** 不调用 persistence write |
| 4 | SQLite write failure **不得** 触发 SendMessage |
| 5 | test shop preview **仍 zero-send** |
| 6 | legacy `channel_shop.db` **不动** |
| 7 | assisted / auto **未实现** |
| 8 | Doudian **不进** production product persistence |
| 9 | PDD queue name 仍为 `pdd_{shop_id}` |

---

## 7. 相关规划文档

| 文档 | 内容 |
|------|------|
| [phase14j_product_gate_db_schema_plan.md](phase14j_product_gate_db_schema_plan.md) | `reply_logs` 最小 schema |
| [phase14j_replylog_shadow_write_flow.md](phase14j_replylog_shadow_write_flow.md) | write flow |
| [phase14j_flags_failure_rollback.md](phase14j_flags_failure_rollback.md) | flags · failure · rollback |
| [phase14j_test_plan.md](phase14j_test_plan.md) | S1–S10 未来测试 |

---

## 8. 未来阶段路线图

| Phase | 内容 |
|-------|------|
| **14k** | Dashboard read API **planning only** |
| **14l** | SQLite ReplyLog shadow **implementation** behind flag |
| **14m** | SendDecision snapshot shadow write planning + implementation |
| **14n** | AuditLog / PendingAssisted planning |

---

*Phase 14j · planning only · 2026-06-03*

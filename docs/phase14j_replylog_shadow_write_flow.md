# Phase 14j — ReplyLog Shadow Write Flow

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 实现 | **Phase 14l** |

---

## 1. 当前流程（14i · as-is）

```
AIReplyHandler.handle()
  → select_product_gate_config(metadata)
  → [test shop + preview] _handle_preview_product_gate
      → classify_consultation_intent
      → build_send_decision
      → _get_ai_reply
      → evaluate_guarded_send
      → _record_preview_reply_log
          → PreviewReplyLogService.record_preview
              → append_preview_log (in-memory)
      → return True
  → zero-send（无 _send_reply / SendMessage / outbound）
```

---

## 2. 未来流程（14l · to-be）

```
AIReplyHandler.handle()
  → [test shop + preview] _handle_preview_product_gate
      → classify / decision / AI / guard（不变）
      → _record_preview_reply_log
          → PreviewReplyLogService.record_preview
              → (1) append_preview_log (in-memory)     ← first write, always
              → (2) if should_shadow_write_reply_log():
                    ProductDbManager.ensure_initialized()
                    ReplyLogRepositorySQLite.create_preview_reply_log(...)
              → (3) return PreviewRecordResult
      → return True
  → zero-send（不变）
```

**handler 调用链不变** — 仍只调 `record_preview`；SQLite 细节封装在 service/repository 内。

---

## 3. 写入顺序与优先级

| 步骤 | 组件 | 失败影响 |
|------|------|----------|
| **1** | `append_preview_log` | `recorded=False` → handler fail-open fallback 或 `return False` · **no send** |
| **2** | SQLite INSERT（optional） | `db_recorded=False` · in-memory 已存在 · **no send** |
| **3** | return result | handler 根据 `recorded` 决定 success |

**in-memory 是 authoritative first write；SQLite 是 shadow copy。**

---

## 4. `should_shadow_write_reply_log()` 条件（14l）

全部满足才尝试 SQLite：

| # | 条件 |
|---|------|
| 1 | `PRODUCT_PERSISTENCE_ENABLED=true` |
| 2 | `PRODUCT_PERSISTENCE_WRITE_REPLY_LOG=true` |
| 3 | allowlist 命中（已由 handler preview branch 保证） |
| 4 | `reply_mode=preview` |
| 5 | `product_gate_enabled=true` |
| 6 | `platform_id` = PDD（非 Doudian） |

任一不满足 → 跳过步骤 2 · 仅 in-memory。

---

## 5. SQLite 写失败处理

### 5.1 init failure（`ProductDbManager.init_product_db`）

```
log warning
skip SQLite for this process / request
return PreviewRecordResult(
    recorded=True,
    source="in_memory",
    db_recorded=False,
    db_error="init_failed: ...",
    reason="recorded_in_memory",
)
```

### 5.2 write failure（repository INSERT）

```
log warning + debug detail
in-memory record retained
return PreviewRecordResult(
    recorded=True,
    source="in_memory",
    db_recorded=False,
    db_error="write_failed: ...",
    reason="recorded_in_memory",
)
```

### 5.3 硬规则

| 规则 | 说明 |
|------|------|
| **禁止** | DB failure → `_send_reply` / SendMessage |
| **禁止** | DB failure → legacy send fallback |
| **允许** | in-memory 已成功 → handler `return True` |
| **允许** | 可观测：`db_recorded=False` · log · future alert |

---

## 6. 层边界

| 层 | 职责 | 禁止 |
|----|------|------|
| **Handler** | orchestration · 调 service | import db_manager / ORM / session |
| **Service** | in-memory + optional shadow 编排 | SendMessage / outbound |
| **Repository** | SQLite INSERT/SELECT | 发送决策 · gate 逻辑 |
| **ProductDbManager** | lazy engine/session · `create_all` or raw DDL | handler 直接调用 |

---

## 7. non-test shop

```
AIReplyHandler.handle()
  → gate miss
  → legacy _get_ai_reply → _send_reply
  → PreviewReplyLogService **不调用**
  → product_gate.db **不写**
```

---

## 8. `PreviewRecordResult` 扩展（14l 规划）

| 字段 | 14i | 14l |
|------|-----|-----|
| `recorded` | ✅ | ✅ |
| `source` | `in_memory` | `in_memory` |
| `reason` | `recorded_in_memory` | 同左 |
| `reply_log_id` | ✅ | ✅ |
| `db_recorded` | — | `True` / `False` |
| `db_error` | — | optional str |

handler 14l **仍只检查** `recorded`（或 fail-open fallback）；**不解析** `db_error`。

---

## 9. 与 Dashboard read（14k）关系

| 阶段 | read path |
|------|-----------|
| 14i | `list_preview_reply_logs()` in-memory |
| 14k planning | API 可读 in-memory 或 DB（flag-gated） |
| 14l+ | shadow DB 可作为 secondary read；in-memory 仍为 test 默认 |

**14l 不实现 Dashboard API。**

---

*Phase 14j · planning only · 2026-06-03*

# Phase 14m — SendDecision Snapshot Write Flow

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 实现 | **Phase 14n** |

---

## 1. 当前流程（14l · as-is）

```
PreviewReplyLogService.record_preview(...)
  → (1) append_preview_log(in-memory)              ← always · first
  → (2) if WRITE_REPLY_LOG:
        ReplyLogRepositorySQLite.create_preview_reply_log(record)
  → return PreviewRecordResult(db_recorded=...)
  → handler return True · zero-send
```

**无 SendDecision snapshot SQLite 写入。**

---

## 2. 未来流程（14n · to-be）

```
PreviewReplyLogService.record_preview(...)
  → (1) append_preview_log(in-memory)              ← always · first
  → (2) if WRITE_REPLY_LOG:
        ReplyLogRepositorySQLite.create_preview_reply_log(record)
  → (3) if WRITE_SEND_DECISION:
        SendDecisionRepositorySQLite.create_snapshot(
            reply_log_id=record.reply_log_id,
            send_decision=...,
            classification=...,
            decision_phase="ai_preview",
            metadata=...,
        )
  → return PreviewRecordResult(
        snapshot_recorded=True|False,
        snapshot_error=...|None,
      )
  → zero-send（不变）
```

**handler 调用链不变** — 仍只调 `record_preview`。

---

## 3. 写入顺序与依赖

| 步骤 | 条件 | 失败影响 |
|------|------|----------|
| **1** in-memory | always | `recorded=False` · no send |
| **2** reply_logs SQLite | `WRITE_REPLY_LOG` | `db_recorded=False` · in-memory ok · no send |
| **3** snapshot SQLite | `WRITE_SEND_DECISION` | `snapshot_recorded=False` · in-memory ok · no send |

### 3.1 ReplyLog 与 Snapshot 依赖

| 规则 | 说明 |
|------|------|
| Snapshot 需要 `reply_log_id` | 来自 in-memory record（always 有） |
| ReplyLog SQLite **失败** | **仍可不写** SQLite snapshot（推荐）· 或写 snapshot 仅带 reply_log_id（14n 决策：skip snapshot if reply_log DB failed） |
| in-memory 成功 | snapshot 可写（即使 reply_log SQLite 失败） |

**推荐 14n：** ReplyLog SQLite 失败 → **跳过** SQLite snapshot · in-memory 仍含完整 SendDecision。

---

## 4. Flags（独立开关）

| Flag | 默认 | 控制 |
|------|------|------|
| `PRODUCT_PERSISTENCE_ENABLED` | false | 总开关 |
| `PRODUCT_PERSISTENCE_WRITE_REPLY_LOG` | false | `reply_logs` |
| `PRODUCT_PERSISTENCE_WRITE_SEND_DECISION` | false | `send_decision_snapshots` |

**推荐组合：**

| WRITE_REPLY_LOG | WRITE_SEND_DECISION | 行为 |
|-----------------|---------------------|------|
| false | false | in-memory only（默认） |
| true | false | reply_logs only |
| true | true | reply_logs + snapshots |
| false | true | snapshot only（不推荐 · 文档化允许但 pilot 禁用） |

---

## 5. decision_phase 写入内容

### 5.1 Preview · `ai_preview`（14n）

| 字段 | 典型值 |
|------|--------|
| `decision_phase` | `ai_preview` |
| `reply_mode` | `preview` |
| `allowed_to_send` | 0（preview zero-send） |
| `send_mode` | `preview_only` 或 `human_takeover` |
| `blocked_reason` | blocked intent 时填充 |

映射：`build_send_decision()` + `evaluate_guarded_send()` + `classification`

### 5.2 Assisted approve · `merchant_confirm`（未来 · 未实现）

| 字段 | 说明 |
|------|------|
| `decision_phase` | `merchant_confirm` |
| 触发 | 商家点击 approve（AssistedReplyService） |
| 行为 | **新 INSERT** · 同一 `reply_log_id` |
| 内容 | re-classify + final guard + AuditLog 关联（14p） |

### 5.3 Auto

**未实现** — 无 snapshot write path。

---

## 6. 层边界

| 层 | 职责 |
|----|------|
| Handler | orchestration · 调 `record_preview` only |
| Service | 编排 in-memory + reply_log + snapshot |
| `SendDecisionRepositorySQLite` | INSERT snapshot · 无 send |
| Handler | **不** import snapshot repository |

---

## 7. Failure 摘要

| 场景 | Send? |
|------|-------|
| snapshot write fail | **NO** · in-memory retained |
| reply_log write fail | **NO** |
| non-test shop | legacy · 无 snapshot |

详见 [phase14m_failure_and_rollback.md](phase14m_failure_and_rollback.md)。

---

*Phase 14m · planning only · 2026-06-03*

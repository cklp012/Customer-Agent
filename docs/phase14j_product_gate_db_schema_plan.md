# Phase 14j — product_gate.db Schema Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| DB 路径 | `./temp/product_gate.db` |
| 实现 | **Phase 14l** |
| 对齐 | [phase14a_replylog_schema.md](phase14a_replylog_schema.md) · [phase14b_reply_logs_migration_draft.md](phase14b_reply_logs_migration_draft.md) |

---

## 1. 设计原则

| 原则 | 说明 |
|------|------|
| shadow-first | 独立 DB，不迁移 legacy |
| 14l 最小表 | **仅 `reply_logs`** |
| 可选延后 | `send_decision_snapshots` → **14m** |
| 不含 | `pending_assisted_replies` · `audit_logs`（14n+） |
| 无 FK legacy | 不引用 `channel_shop.db` 表 |
| boolean | SQLite `INTEGER`（0/1） |
| enum | 先用 `TEXT` |
| timestamps | ISO 8601 `TEXT`（UTC） |

---

## 2. 何时创建 DB

| 条件 | 行为 |
|------|------|
| flags off（默认） | **不创建** `product_gate.db` |
| `PRODUCT_PERSISTENCE_ENABLED=true` + `WRITE_REPLY_LOG=true` | 首次 shadow write 前 lazy init |
| init 失败 | 跳过 SQLite · in-memory only · test shop no-send |

**14j 不创建文件；14l 实现 lazy init。**

---

## 3. 14l 最小表：`reply_logs`

### 3.1 DDL 草案（planning）

```sql
CREATE TABLE IF NOT EXISTS reply_logs (
    reply_log_id            TEXT PRIMARY KEY,
    workspace_id            TEXT,
    shop_id                 TEXT,
    account_id              TEXT,
    platform_id             TEXT,
    buyer_id                TEXT,
    conversation_id         TEXT,
    inbound_message_id      TEXT,
    buyer_message           TEXT NOT NULL,
    ai_suggested_reply      TEXT,
    final_reply             TEXT,
    reply_mode              TEXT NOT NULL,
    send_mode               TEXT NOT NULL,
    send_status             TEXT NOT NULL,
    intent                  TEXT,
    intent_bucket           TEXT,
    intent_confidence       REAL,
    risk_level              TEXT,
    blocked_reason          TEXT,
    human_takeover_reason   TEXT,
    not_sent_explanation    TEXT,
    product_gate_enabled    INTEGER NOT NULL DEFAULT 0,
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL
);
```

### 3.2 字段说明

| 列 | 类型 | 14l preview 填充 |
|----|------|------------------|
| `reply_log_id` | TEXT PK | 与 in-memory `PreviewLogRecord.reply_log_id` 对齐 |
| `workspace_id` | TEXT | gate_config / metadata |
| `shop_id` | TEXT | allowlist shop |
| `account_id` | TEXT | allowlist account |
| `platform_id` | TEXT | `pinduoduo` |
| `buyer_id` | TEXT | `from_uid` |
| `conversation_id` | TEXT | 可选 · metadata |
| `inbound_message_id` | TEXT | `message_id` |
| `buyer_message` | TEXT | 规范化消息文本 |
| `ai_suggested_reply` | TEXT | AI 建议 |
| `final_reply` | TEXT | preview 模式 **NULL** |
| `reply_mode` | TEXT | `preview` |
| `send_mode` | TEXT | `preview_only` / `human_takeover` 等 |
| `send_status` | TEXT | `not_sent_preview` / `not_sent_human_takeover` |
| `intent` | TEXT | classifier intent |
| `intent_bucket` | TEXT | `allowed` / `blocked` / `uncertain` |
| `intent_confidence` | REAL | 0.0–1.0 |
| `risk_level` | TEXT | `low` / `medium` / `high` |
| `blocked_reason` | TEXT | blocked 时填写 |
| `human_takeover_reason` | TEXT | human_takeover 时填写 |
| `not_sent_explanation` | TEXT | 可读解释（projection 对齐） |
| `product_gate_enabled` | INTEGER | 1 = true snapshot |
| `created_at` | TEXT | ISO UTC |
| `updated_at` | TEXT | ISO UTC · 14l insert 时 = created_at |

### 3.3 Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_reply_logs_workspace_created_at
    ON reply_logs (workspace_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_reply_logs_shop_created_at
    ON reply_logs (shop_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_reply_logs_buyer_created_at
    ON reply_logs (buyer_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_reply_logs_send_status
    ON reply_logs (send_status);
```

---

## 4. 明确不在 14l 创建的表

| 表 | Phase |
|----|-------|
| `send_decision_snapshots` | **14m**（可选 shadow） |
| `pending_assisted_replies` | **14n** planning |
| `audit_logs` | **14n** planning |

---

## 5. 与 in-memory projection 映射

| in-memory / projection | `reply_logs` 列 |
|------------------------|-----------------|
| `reply_log_id` | `reply_log_id` |
| `buyer_message` | `buyer_message` |
| `ai_suggested_reply` | `ai_suggested_reply` |
| `send_status` | `send_status` |
| `intent` / `intent_bucket` | `intent` / `intent_bucket` |
| `send_decision.send_mode` | `send_mode` |
| `send_decision.reply_mode` | `reply_mode` |

**14l write：** repository 从 `PreviewLogRecord` + projection 字段组装 INSERT。

---

## 6. legacy 隔离

| 项 | 规则 |
|----|------|
| `channel_shop.db` | **只读 legacy** · 14l 不写 |
| `database/models.py` | **不改** |
| 外键 | 无 cross-DB FK |
| 迁移 | 独立 `product_gate.db` · 可用 raw SQL 或 lightweight migration（14l 决策） |

---

*Phase 14j · planning only · 2026-06-03*

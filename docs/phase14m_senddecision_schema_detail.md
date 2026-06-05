# Phase 14m — send_decision_snapshots Schema Detail

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 表名 | `send_decision_snapshots` |
| DB | `./temp/product_gate.db`（与 `reply_logs` 同库） |
| 实现 | **Phase 14n** |
| 对齐 | [phase14a_senddecision_schema.md](phase14a_senddecision_schema.md) · [phase14b_send_decision_snapshots_migration_draft.md](phase14b_send_decision_snapshots_migration_draft.md) |

---

## 1. 设计原则

| 原则 | 说明 |
|------|------|
| append-only | INSERT only · **不 UPDATE** |
| 弱关联 | `reply_log_id` 逻辑关联 `reply_logs` · 无 cross-DB FK |
| boolean | SQLite `INTEGER`（0/1） |
| enum | `TEXT` |
| timestamps | ISO 8601 UTC `TEXT` |
| 无 legacy FK | 不引用 `channel_shop.db` |

---

## 2. DDL 草案（planning）

```sql
CREATE TABLE IF NOT EXISTS send_decision_snapshots (
    send_decision_id        TEXT PRIMARY KEY,
    reply_log_id            TEXT,
    workspace_id            TEXT,
    shop_id                 TEXT,
    account_id              TEXT,
    platform_id             TEXT,
    inbound_message_id      TEXT,
    decision_phase          TEXT NOT NULL,
    intent                  TEXT,
    intent_bucket           TEXT,
    intent_confidence       REAL,
    risk_level              TEXT,
    reply_mode              TEXT,
    workspace_pause         INTEGER NOT NULL DEFAULT 0,
    shop_pause              INTEGER NOT NULL DEFAULT 0,
    product_gate_enabled    INTEGER NOT NULL DEFAULT 0,
    allowed_to_generate     INTEGER NOT NULL DEFAULT 0,
    allowed_to_send         INTEGER NOT NULL DEFAULT 0,
    send_mode               TEXT,
    blocked_reason          TEXT,
    human_takeover_reason   TEXT,
    decision_source         TEXT,
    created_at              TEXT NOT NULL
);
```

---

## 3. 字段说明

| 列 | 类型 | 说明 |
|----|------|------|
| `send_decision_id` | TEXT PK | UUID · 每条 snapshot 唯一 |
| `reply_log_id` | TEXT | 关联 `reply_logs.reply_log_id`（弱关联） |
| `workspace_id` | TEXT | 租户 |
| `shop_id` | TEXT | 店铺 |
| `account_id` | TEXT | 账号 |
| `platform_id` | TEXT | 默认 `pinduoduo` |
| `inbound_message_id` | TEXT | metadata `message_id` |
| `decision_phase` | TEXT | `ai_preview` · `merchant_confirm`（未来） |
| `intent` | TEXT | classifier intent |
| `intent_bucket` | TEXT | allowed / blocked / uncertain |
| `intent_confidence` | REAL | 0.0–1.0 |
| `risk_level` | TEXT | low / medium / high |
| `reply_mode` | TEXT | preview · assisted · auto · paused |
| `workspace_pause` | INTEGER | snapshot 时刻 |
| `shop_pause` | INTEGER | snapshot 时刻 |
| `product_gate_enabled` | INTEGER | snapshot 时刻 |
| `allowed_to_generate` | INTEGER | SendDecision |
| `allowed_to_send` | INTEGER | SendDecision |
| `send_mode` | TEXT | preview_only / human_takeover / … |
| `blocked_reason` | TEXT | nullable |
| `human_takeover_reason` | TEXT | nullable |
| `decision_source` | TEXT | keyword_rule / gate / combined |
| `created_at` | TEXT | ISO UTC |

**14n 首版不含：** `merchant_approved`（assisted 14p+ 可增列或新 snapshot 行表达）

---

## 4. Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_send_decisions_reply_log_id
    ON send_decision_snapshots (reply_log_id);

CREATE INDEX IF NOT EXISTS idx_send_decisions_workspace_created_at
    ON send_decision_snapshots (workspace_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_send_decisions_shop_created_at
    ON send_decision_snapshots (shop_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_send_decisions_phase
    ON send_decision_snapshots (decision_phase);
```

---

## 5. 映射来源（preview · ai_preview）

| DB 列 | 来源 |
|-------|------|
| `reply_log_id` | `PreviewLogRecord.reply_log_id` |
| `intent` … `human_takeover_reason` | `SendDecision` + `IntentClassification` |
| `allowed_to_generate` | `send_decision.allowed_to_generate` |
| `allowed_to_send` | `send_decision.allowed_to_send` |
| `decision_phase` | 常量 `ai_preview` |
| `decision_source` | `classification.source` 或 `send_decision.decision_source` |
| `inbound_message_id` | metadata |

---

## 6. append-only 规则

| 操作 | 允许 |
|------|------|
| INSERT 新 snapshot | ✅ |
| UPDATE 已有行 | ❌ |
| DELETE（生产） | ❌（rollback 可 drop 表） |
| 同一 inbound 多次 preview | 新 `send_decision_id` · 新行（或 idempotent policy · 见 M6） |

---

## 7. 与 reply_logs 同库

14n `ProductBase.metadata.create_all` 在 flags 启用时创建 **两张表**：

- `reply_logs`（14l 已有）
- `send_decision_snapshots`（14n 新增）

**14m 不创建表。**

---

*Phase 14m · planning only · 2026-06-03*

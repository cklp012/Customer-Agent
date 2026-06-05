# Phase 14b — `send_decision_snapshots` Migration Draft

| 项 | 值 |
|----|-----|
| 类型 | docs only · draft SQL |
| 对齐 | [phase14a_senddecision_schema.md](phase14a_senddecision_schema.md) |
| 建议 revision | `2026_06_03_0002_create_send_decision_snapshots_shadow.py` |

---

## 1. CREATE TABLE（PostgreSQL 草案）

```sql
CREATE TABLE send_decision_snapshots (
    send_decision_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reply_log_id          UUID,
    workspace_id          UUID NOT NULL,
    shop_id               VARCHAR(128) NOT NULL,
    account_id            VARCHAR(128) NOT NULL,
    platform_id           VARCHAR(32) NOT NULL DEFAULT 'pinduoduo',
    inbound_message_id    VARCHAR(128) NOT NULL,
    decision_phase        VARCHAR(32) NOT NULL DEFAULT 'ai_generate',
    intent                VARCHAR(64) NOT NULL,
    intent_bucket         VARCHAR(32) NOT NULL,
    intent_confidence     DOUBLE PRECISION NOT NULL DEFAULT 0,
    risk_level            VARCHAR(16) NOT NULL DEFAULT 'low',
    reply_mode            VARCHAR(32) NOT NULL DEFAULT 'preview',
    workspace_pause       BOOLEAN NOT NULL DEFAULT FALSE,
    shop_pause            BOOLEAN NOT NULL DEFAULT FALSE,
    product_gate_enabled  BOOLEAN NOT NULL DEFAULT FALSE,
    allowed_to_generate   BOOLEAN NOT NULL DEFAULT TRUE,
    allowed_to_send       BOOLEAN NOT NULL DEFAULT FALSE,
    send_mode             VARCHAR(32) NOT NULL,
    blocked_reason        VARCHAR(255),
    human_takeover_reason VARCHAR(255),
    decision_source       VARCHAR(64) NOT NULL DEFAULT 'combined',
    merchant_approved     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**弱 FK（可选 · 14c 评审后）：**

```sql
-- ALTER TABLE send_decision_snapshots
--   ADD CONSTRAINT fk_send_decision_reply_log
--   FOREIGN KEY (reply_log_id) REFERENCES reply_logs(reply_log_id)
--   ON DELETE SET NULL;
```

---

## 2. Indexes

```sql
CREATE INDEX idx_send_decisions_reply_log_id
    ON send_decision_snapshots (reply_log_id, created_at);

CREATE INDEX idx_send_decisions_workspace_created_at
    ON send_decision_snapshots (workspace_id, created_at DESC);

CREATE INDEX idx_send_decisions_shop_created_at
    ON send_decision_snapshots (shop_id, created_at DESC);

CREATE INDEX idx_send_decisions_phase
    ON send_decision_snapshots (decision_phase, created_at DESC);
```

---

## 3. 写入语义

| 场景 | `decision_phase` | 行数 |
|------|------------------|------|
| 13b shadow | `shadow_only` | 1 |
| 13d preview AI | `ai_generate` | 1 |
| assisted AI | `ai_generate` | 1 · `merchant_approved=false` |
| assisted approve | `merchant_confirm` | **+1 新行** |

**append-only：** 不 UPDATE 历史 snapshot；修正 = 新 INSERT。

---

## 4. Rollback draft

```sql
DROP INDEX IF EXISTS idx_send_decisions_phase;
DROP INDEX IF EXISTS idx_send_decisions_shop_created_at;
DROP INDEX IF EXISTS idx_send_decisions_workspace_created_at;
DROP INDEX IF EXISTS idx_send_decisions_reply_log_id;
DROP TABLE IF EXISTS send_decision_snapshots;
```

---

*send_decision_snapshots migration draft · Phase 14b · 2026-06-03*

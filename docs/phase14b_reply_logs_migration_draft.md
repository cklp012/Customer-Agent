# Phase 14b — `reply_logs` Migration Draft

| 项 | 值 |
|----|-----|
| 类型 | docs only · draft SQL |
| 对齐 | [phase14a_replylog_schema.md](phase14a_replylog_schema.md) |
| 建议 revision | `2026_06_03_0001_create_reply_logs_shadow.py` |

---

## 1. CREATE TABLE（PostgreSQL 草案）

```sql
CREATE TABLE reply_logs (
    reply_log_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id          UUID NOT NULL,
    shop_id               VARCHAR(128) NOT NULL,
    account_id            VARCHAR(128) NOT NULL,
    platform_id           VARCHAR(32) NOT NULL DEFAULT 'pinduoduo',
    buyer_id              VARCHAR(128) NOT NULL,
    conversation_id       VARCHAR(128),
    inbound_message_id    VARCHAR(128) NOT NULL,
    buyer_message         TEXT NOT NULL,
    ai_suggested_reply    TEXT,
    final_reply           TEXT,
    reply_mode            VARCHAR(32) NOT NULL DEFAULT 'preview',
    send_mode             VARCHAR(32) NOT NULL,
    send_status           VARCHAR(64) NOT NULL,
    intent                VARCHAR(64) NOT NULL,
    intent_bucket         VARCHAR(32) NOT NULL,
    intent_confidence     DOUBLE PRECISION NOT NULL DEFAULT 0,
    risk_level            VARCHAR(16) NOT NULL DEFAULT 'low',
    blocked_reason        VARCHAR(255),
    human_takeover_reason VARCHAR(255),
    not_sent_explanation  TEXT,
    product_gate_enabled  BOOLEAN NOT NULL DEFAULT FALSE,
    sent_at               TIMESTAMPTZ,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 2. Indexes

```sql
CREATE INDEX idx_reply_logs_workspace_created_at
    ON reply_logs (workspace_id, created_at DESC);

CREATE INDEX idx_reply_logs_shop_created_at
    ON reply_logs (shop_id, created_at DESC);

CREATE INDEX idx_reply_logs_buyer_created_at
    ON reply_logs (buyer_id, shop_id, created_at DESC);

CREATE INDEX idx_reply_logs_send_status
    ON reply_logs (send_status, created_at DESC);

CREATE INDEX idx_reply_logs_intent_bucket
    ON reply_logs (intent_bucket, created_at DESC);

-- optional idempotency
CREATE INDEX idx_reply_logs_inbound_message_id
    ON reply_logs (inbound_message_id);
```

---

## 3. Alembic upgrade 草案（伪代码）

```python
def upgrade() -> None:
    op.create_table(
        "reply_logs",
        sa.Column("reply_log_id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("shop_id", sa.String(128), nullable=False),
        # ... 见 SQL 草案 ...
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_reply_logs_workspace_created_at", ...)
    # ...
```

---

## 4. 应用层约束（非 DB CHECK · 14c+）

| 规则 | 说明 |
|------|------|
| preview | `final_reply IS NULL` · `send_status=not_sent_preview` |
| blocked | `send_status != sent` |
| gate off shadow | 可选 `skipped_gate_disabled` |

---

## 5. Rollback draft

```sql
DROP INDEX IF EXISTS idx_reply_logs_inbound_message_id;
DROP INDEX IF EXISTS idx_reply_logs_intent_bucket;
DROP INDEX IF EXISTS idx_reply_logs_send_status;
DROP INDEX IF EXISTS idx_reply_logs_buyer_created_at;
DROP INDEX IF EXISTS idx_reply_logs_shop_created_at;
DROP INDEX IF EXISTS idx_reply_logs_workspace_created_at;
DROP TABLE IF EXISTS reply_logs;
```

```python
def downgrade() -> None:
    op.drop_index("idx_reply_logs_intent_bucket", table_name="reply_logs")
    # ... 逆序 drop indexes ...
    op.drop_table("reply_logs")
```

---

*reply_logs migration draft · Phase 14b · 2026-06-03*

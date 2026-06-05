# Phase 14b — `pending_assisted_replies` Migration Draft

| 项 | 值 |
|----|-----|
| 类型 | docs only · draft SQL |
| 对齐 | [phase14a_pending_assisted_reply_schema.md](phase14a_pending_assisted_reply_schema.md) |
| 建议 revision | `2026_06_03_0003_create_pending_assisted_replies_shadow.py` |

---

## 1. CREATE TABLE（PostgreSQL 草案）

```sql
CREATE TABLE pending_assisted_replies (
    pending_reply_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reply_log_id              UUID NOT NULL,
    workspace_id              UUID NOT NULL,
    shop_id                   VARCHAR(128) NOT NULL,
    account_id                VARCHAR(128) NOT NULL,
    platform_id               VARCHAR(32) NOT NULL DEFAULT 'pinduoduo',
    buyer_id                  VARCHAR(128) NOT NULL,
    inbound_message_id        VARCHAR(128) NOT NULL,
    suggested_reply           TEXT NOT NULL,
    edited_reply              TEXT,
    status                    VARCHAR(32) NOT NULL DEFAULT 'pending',
    intent                    VARCHAR(64) NOT NULL,
    risk_level                VARCHAR(16) NOT NULL DEFAULT 'low',
    created_by                VARCHAR(32) NOT NULL DEFAULT 'ai_handler',
    approved_by               UUID,
    rejected_by               UUID,
    expires_at                TIMESTAMPTZ NOT NULL,
    superseded_by_message_id  VARCHAR(128),
    created_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**弱 FK（可选）：**

```sql
-- FOREIGN KEY (reply_log_id) REFERENCES reply_logs(reply_log_id) ON DELETE CASCADE
```

---

## 2. Indexes

```sql
CREATE INDEX idx_pending_assisted_workspace_status
    ON pending_assisted_replies (workspace_id, status, created_at DESC);

CREATE INDEX idx_pending_assisted_shop_status
    ON pending_assisted_replies (shop_id, status, created_at DESC);

CREATE INDEX idx_pending_assisted_expires_at
    ON pending_assisted_replies (expires_at)
    WHERE status = 'pending';

CREATE INDEX idx_pending_assisted_reply_log_id
    ON pending_assisted_replies (reply_log_id);
```

---

## 3. 业务规则（migration 后由 app 强制）

| 规则 | 说明 |
|------|------|
| pending ≠ sent | `status=pending` 时 ReplyLog 不得 `sent` |
| approve 后 | `status=approved`；**真实发送结果** 以 ReplyLog.`send_status` / `sent_at` 为准 |
| expired / superseded | approve API 拒绝 |
| blocked | `status=blocked` 或 UI 禁用普通 approve |

---

## 4. Rollback draft

```sql
DROP INDEX IF EXISTS idx_pending_assisted_reply_log_id;
DROP INDEX IF EXISTS idx_pending_assisted_expires_at;
DROP INDEX IF EXISTS idx_pending_assisted_shop_status;
DROP INDEX IF EXISTS idx_pending_assisted_workspace_status;
DROP TABLE IF EXISTS pending_assisted_replies;
```

---

*pending_assisted_replies migration draft · Phase 14b · 2026-06-03*

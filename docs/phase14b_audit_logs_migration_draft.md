# Phase 14b — `audit_logs` Migration Draft

| 项 | 值 |
|----|-----|
| 类型 | docs only · draft SQL |
| 对齐 | [phase14a_auditlog_schema.md](phase14a_auditlog_schema.md) |
| 建议 revision | `2026_06_03_0004_create_audit_logs_shadow.py` |

---

## 1. CREATE TABLE（PostgreSQL 草案）

```sql
CREATE TABLE audit_logs (
    audit_log_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id      UUID NOT NULL,
    shop_id           VARCHAR(128),
    account_id        VARCHAR(128),
    actor_member_id   UUID NOT NULL,
    actor_role        VARCHAR(32) NOT NULL,
    action            VARCHAR(64) NOT NULL,
    target_type       VARCHAR(64) NOT NULL,
    target_id         VARCHAR(128) NOT NULL,
    before_state      JSONB,
    after_state       JSONB,
    reason            TEXT,
    ip_address        VARCHAR(64),
    user_agent        VARCHAR(512),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**无 `updated_at`：** append-only 表。

---

## 2. Indexes

```sql
CREATE INDEX idx_audit_logs_workspace_created_at
    ON audit_logs (workspace_id, created_at DESC);

CREATE INDEX idx_audit_logs_shop_created_at
    ON audit_logs (shop_id, created_at DESC)
    WHERE shop_id IS NOT NULL;

CREATE INDEX idx_audit_logs_actor_created_at
    ON audit_logs (actor_member_id, created_at DESC);

CREATE INDEX idx_audit_logs_action_created_at
    ON audit_logs (action, created_at DESC);

CREATE INDEX idx_audit_logs_target
    ON audit_logs (target_type, target_id);
```

---

## 3. `action` 允许值（app-level · VARCHAR）

- `assisted_reply_approved`
- `assisted_reply_rejected`
- `reply_mode_changed`
- `product_gate_enabled_changed`
- `shop_paused`
- `shop_resumed`
- `test_shop_allowlist_changed`
- `credential_updated`
- `credential_revoked`

---

## 4. 写入策略

| 事件 | 必须写 AuditLog |
|------|----------------|
| assisted approve / reject | ✅ |
| reply_mode / gate 变更 | ✅ |
| pause / resume | ✅ |
| allowlist / credential | ✅ |
| preview zero-send（13d） | ❌（非必须） |

**禁止：** 应用层对 `audit_logs` 做普通 UPDATE/DELETE。

---

## 5. Rollback draft

```sql
DROP INDEX IF EXISTS idx_audit_logs_target;
DROP INDEX IF EXISTS idx_audit_logs_action_created_at;
DROP INDEX IF EXISTS idx_audit_logs_actor_created_at;
DROP INDEX IF EXISTS idx_audit_logs_shop_created_at;
DROP INDEX IF EXISTS idx_audit_logs_workspace_created_at;
DROP TABLE IF EXISTS audit_logs;
```

---

*audit_logs migration draft · Phase 14b · 2026-06-03*

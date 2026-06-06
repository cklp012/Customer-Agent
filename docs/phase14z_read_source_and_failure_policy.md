# Phase 14z — Read Source and Failure Policy

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14o_done.md](phase14o_done.md) · [phase14k_read_source_strategy.md](phase14k_read_source_strategy.md) |

---

## 1. Read source 策略

### 1.1 初期数据源

| source | 条件 |
|--------|------|
| `sqlite_shadow` | `PRODUCT_PERSISTENCE_READ_DASHBOARD=true` + DB available |
| `empty` | flags off 或表空 |
| `error` | DB unavailable · 可选 degraded response |

**DB 路径：** `./temp/product_gate.db`（product_gate · 非 legacy database）

### 1.2 Flags

| Flag | 用途 | 默认 |
|------|------|------|
| `PRODUCT_PERSISTENCE_ENABLED` | 总开关 | off |
| `PRODUCT_PERSISTENCE_READ_DASHBOARD` | Dashboard read from SQLite | off |
| `PRODUCT_ASSISTED_SERVICE_ENABLED` | Assisted **write** service | off |

**关键：**

| 规则 | 说明 |
|------|------|
| R1 | **`PRODUCT_ASSISTED_SERVICE_ENABLED` 不是 read-only dashboard 的必要条件** |
| R2 | Read dashboard 仅需 `READ_DASHBOARD` + pending/audit **表已存在**（由 write flags 创建过） |
| R3 | Write flags off + read flag on → read 空表 + warning · **不创建 pending** |
| R4 | Read-only dashboard **不调用** create_pending / approve |

---

## 2. Repository read（future · 15c）

```text
DashboardPendingAssistedReadService (future)
  → PendingAssistedRepositorySQLite.list_pending(...)
  → AuditLogRepositorySQLite.list_audit_logs(...)
  → SendDecisionRepositorySQLite (read-only list by reply_log_id)
  — no write methods —
```

**14z 不改 repository 代码。**

---

## 3. Failure policy

| 场景 | 行为 | send? |
|------|------|-------|
| READ_DASHBOARD=false | 503 或 empty + `warnings: ["read_dashboard_disabled"]` | ❌ |
| DB file missing | empty items + warning | ❌ |
| DB connection error | 503 或 empty + warning | ❌ |
| partial join fail | 200 + partial detail + warnings | ❌ |
| stale data（cache TTL） | 200 + `warnings: ["stale_read"]` | ❌ |
| cross-workspace | 403 | ❌ |

**总原则：**

| # | 原则 |
|---|------|
| F1 | **read failure 绝不 fallback legacy send** |
| F2 | **DB unavailable 不影响 PDD legacy** |
| F3 | **no mutation on read** |
| F4 | **no audit write on read** |
| F5 | **no final guard execution on read** |
| F6 | **no outbound on read** |

---

## 4. 与 14o ReplyLog read 关系

| API | read flag | 数据源 |
|-----|-----------|--------|
| `/api/product/reply-logs` | READ_DASHBOARD | reply_logs · 14o ✅ |
| `/api/product/pending-assisted` | READ_DASHBOARD | pending_assisted + audit · 15c |

同一 flag 控制 product SQLite read · **独立**于 assisted write flag。

---

## 5. Warnings 示例

```json
{
  "warnings": [
    "read_dashboard_disabled",
    "sqlite_unavailable",
    "stale_read",
    "partial_audit_timeline",
    "assisted_write_disabled"
  ]
}
```

`assisted_write_disabled` —  informational · read 仍可用。

---

*Phase 14z · planning only · 2026-06-03*

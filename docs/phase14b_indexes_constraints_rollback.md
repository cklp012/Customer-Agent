# Phase 14b — Indexes, Constraints & Rollback Summary

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 关联 | phase14b_*_migration_draft.md |

---

## 1. Primary keys

| 表 | PK 列 |
|----|-------|
| `reply_logs` | `reply_log_id` UUID |
| `send_decision_snapshots` | `send_decision_id` UUID |
| `pending_assisted_replies` | `pending_reply_id` UUID |
| `audit_logs` | `audit_log_id` UUID |

---

## 2. Nullable 策略

| 列类 | 策略 |
|------|------|
| 租户/店维度 ID | `workspace_id` · `shop_id` · `account_id` NOT NULL（audit.shop_id 可 NULL 用于 workspace 级操作） |
| 可选关联 | `reply_log_id` on snapshots 可 NULL（shadow-only 决策） |
| 内容 | `ai_suggested_reply` · `final_reply` 可 NULL（preview 无 final） |
| 审计 | `before_state` / `after_state` JSONB 可 NULL |
| 时间 | `sent_at` 仅 sent 时填 |

---

## 3. Timestamp defaults

| 列 | 默认 |
|----|------|
| `created_at` | `DEFAULT now()` · NOT NULL |
| `updated_at` | `reply_logs` · `pending_assisted_replies` — `DEFAULT now()`；app 更新时刷新 |
| `expires_at` | pending — app 设 `now() + interval '24 hours'` |
| `sent_at` | NULL 默认 |

---

## 4. TEXT / JSON 策略

| 类型 | 用途 |
|------|------|
| `TEXT` | `buyer_message` · `ai_suggested_reply` · `suggested_reply` · `not_sent_explanation` |
| `JSONB` | `audit_logs.before_state` · `after_state` |
| `VARCHAR(n)` | IDs · enums · reasons（长度见各表 draft） |

**SQLite dev：** JSONB → TEXT + app JSON parse。

---

## 5. Foreign key 策略（draft 阶段）

| 关系 | 建议 |
|------|------|
| `send_decision_snapshots.reply_log_id` → `reply_logs` | **弱 FK 或暂不添加** |
| `pending_assisted_replies.reply_log_id` → `reply_logs` | 同上 |
| → legacy `accounts` / `shops` | **禁止** 14b 强 FK |

**理由：** legacy 数据不完整时强 FK 阻塞 migration；14c M1 仅空表。

---

## 6. Enum 策略

**不用 PostgreSQL ENUM 类型。**

| 字段 | 存储 | 校验 |
|------|------|------|
| `send_status` | VARCHAR(64) | app + 14a 枚举表 |
| `reply_mode` | VARCHAR(32) | `preview` / `assisted` / `auto` / `paused` |
| `status` (pending) | VARCHAR(32) | 14a pending 枚举 |
| `action` (audit) | VARCHAR(64) | 14a action 列表 |

---

## 7. 全表索引汇总

| 表 | 索引名 |
|----|--------|
| reply_logs | `idx_reply_logs_workspace_created_at` · `shop` · `buyer` · `send_status` · `intent_bucket` |
| send_decision_snapshots | `idx_send_decisions_reply_log_id` · `workspace` · `shop` · `phase` |
| pending_assisted_replies | `idx_pending_assisted_workspace_status` · `shop_status` · `expires_at` · `reply_log_id` |
| audit_logs | `idx_audit_logs_workspace_created_at` · `shop` · `actor` · `action` · `target` |

---

## 8. Rollback 顺序（downgrade SSOT）

```text
1. DROP TABLE audit_logs                    (+ indexes)
2. DROP TABLE pending_assisted_replies      (+ indexes)
3. DROP TABLE send_decision_snapshots       (+ indexes)
4. DROP TABLE reply_logs                    (+ indexes)
```

**依赖方向：** pending / snapshots **引用** reply_logs → 先 drop 子表。

**单命令（PG · 紧急）：**

```sql
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS pending_assisted_replies CASCADE;
DROP TABLE IF EXISTS send_decision_snapshots CASCADE;
DROP TABLE IF EXISTS reply_logs CASCADE;
```

---

## 9. Runtime 与 legacy 隔离

| 场景 | 行为 |
|------|------|
| migration 未执行 | legacy **不变** |
| 表存在 · flag off | legacy **不变** · shadow 零读写 |
| 表存在 · write on | 仅 gate on test shop 双写（14c+） |
| non-test shop | **永不** 依赖 shadow 表发送 |
| rollback DROP | 停 flag → legacy **不变** |

---

## 10. 14c 实施检查清单

- [ ] DDL 与本文档 diff 评审
- [ ] `downgrade()` 在空库/测试库验证
- [ ] 无 legacy 表 ALTER
- [ ] 默认 flag 全 false
- [ ] 13d 全量 unittest 仍绿（无 migration 执行时）

---

*Indexes & rollback · Phase 14b · 2026-06-03*

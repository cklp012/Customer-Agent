# Phase 15q — Failure and Rollback Policy (Schema)

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15n_failure_rollback_policy.md](phase15n_failure_rollback_policy.md) |

---

## 1. Schema rollout 原则

| 规则 |
|------|
| **Additive only** — 新表 `reconciliation_attempts` · 新 status 枚举值 |
| **No destructive migration** — 不 DROP 列 · 不 TRUNCATE audit |
| 旧 row 保留原 `status` 语义 · 新代码向后兼容 `pending`/`in_progress`/`succeeded`/`failed` |
| 15t impl **behind flags** — default off |

---

## 2. Migration 失败

| 场景 | 行为 |
|------|------|
| Alembic/init 失败 | **no live send** · keep dry-run |
| 新表创建失败 | reconciliation disabled · manual review via audit only |
| PDD legacy | **unchanged** |

---

## 3. Rollback（schema 已部署后）

| 动作 | 效果 |
|------|------|
| `PRODUCT_ASSISTED_SEND_ENABLED=false` | 停止 live · schema 保留 |
| `PRODUCT_ASSISTED_SEND_DRY_RUN=true` | 强制 dry-run |
| Disable action routes（可选） | 停止新 assisted actions |
| **Keep** read dashboard | 只读审计 |
| **Keep** `reconciliation_attempts` rows | **不删除** — 审计证据 |
| **Keep** old audit logs | append-only 历史 |

**不回滚删除 reconciliation 数据。**

---

## 4. Status corruption 检测

| 信号 | 响应 |
|------|------|
| pending `sent` but idempotency `timeout_unknown` | **freeze** assisted actions |
| duplicate `succeeded` same key | alert · manual inspection |
| missing audit for status jump | freeze · preserve rows |

响应步骤：

1. `PRODUCT_ASSISTED_SEND_ENABLED=false`
2. 禁止新 approve/reject on affected shop
3. 保留 audit + reconciliation_attempts
4. operator manual inspection（15n runbook）
5. **no** auto repair via resend

---

## 5. No fallback

| 禁止 |
|------|
| schema 错误 → SendMessage 补发 |
| corruption → auto retry |
| migration rollback → delete evidence |

PDD queue `pdd_{shop_id}` · handler · legacy DB — **unchanged**。

---

*Phase 15q · docs only · 2026-06-03*

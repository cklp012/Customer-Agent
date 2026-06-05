# Phase 14a — Shadow DB Schema Plan（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | **docs only** · **本 Phase 不写代码、不建 migration** |
| 前置 | [phase13e_done.md](phase13e_done.md) · [phase13f_done.md](phase13f_done.md) · [phase12e_db_migration_plan.md](phase12e_db_migration_plan.md) |
| 关系 | 细化 12e 表设计；**14b** 输出 Alembic/SQL draft |

---

## 1. Phase 14a 目标

规划 **shadow-first** 持久化层，支撑未来：

| 能力 | 表 / 读模型 |
|------|-------------|
| Preview ReplyLog | `reply_logs` |
| Pending Assisted Reply | `pending_assisted_replies` |
| SendDecision 复盘 | `send_decision_snapshots` |
| 审计 | `audit_logs` |
| 店铺 gate 配置 | `shop_bindings`（扩展字段） |
| Dashboard | 12d read model 投影 |

**14a 明确不做：**

- 创建 migration
- 修改 `database/models.py`
- 改变当前运行时行为（13d in-memory 仍有效）
- 实现 assisted / auto send
- 实现 UI / API

---

## 2. 为什么 Shadow DB

| 原因 | 说明 |
|------|------|
| **保护 legacy** | PDD 客服热路径（`pdd_{shop_id}` · SendMessage）不被 SaaS 表结构绑架 |
| **可回滚** | flag off → 停写 shadow；legacy 独立运行 |
| **Dashboard 读取** | 13e `list_preview_reply_logs()` 可逐步切到 DB read |
| **Assisted confirmation** | pending + approve 需跨请求持久化 |
| **审计与风控** | AuditLog + SendDecision history 可追溯「为何发/没发」 |
| **分阶段 rollout** | preview → assisted → auto（auto 仅规划） |

```text
Legacy PDD (today)          Shadow SaaS tables (parallel)
     │                              │
     ├─ SendMessage ────────────────┤ 不写 outbound 成功到 shadow 直至 gated send
     └─ accounts/shops (legacy)    └─ shop_bindings projection (M2+)
```

---

## 3. 核心默认值（全表约束）

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `product_gate_enabled` | **false** | 非 allowlist 店永不 gate |
| `reply_mode` | **preview** | 新绑定 / 投影默认 |
| `consultation_only` | **true** | 12b.1 产品边界 |

**分阶段：**

| 模式 | 14a 状态 | DB 用途 |
|------|----------|---------|
| preview | 13d/13e 已实现（内存） | ReplyLog `not_sent_preview` |
| assisted | 13f 已规划 | Pending + AuditLog |
| auto | **未实现** | 表预留 `send_mode=auto_send`，**默认禁止写 sent** |

---

## 4. 平台边界

| platform | shadow 写入 | production send |
|----------|-------------|-----------------|
| `pinduoduo` | ✅（gate on 店） | legacy 或 gated |
| `doudian` | mock / 测试 only | **非 production** |
| 其它 | 规划预留 | legacy / 未接入 |

**PDD legacy：** 无 gate 时 **完全独立** 运行，不依赖 shadow 表存在。

---

## 5. 实体关系（ER 概要）

```text
shop_bindings (1) ──< reply_logs (N)
reply_logs (1) ──< send_decision_snapshots (N)
reply_logs (1) ──< pending_assisted_replies (0..1)
workspace (1) ──< audit_logs (N)
```

**与 13e 对齐：** `PreviewReplyLogListItem` 字段 → `reply_logs` 列映射见 [phase14a_replylog_schema.md](phase14a_replylog_schema.md)。

---

## 6. ShopBinding 扩展字段（规划）

| 列 | 类型 | 默认 |
|----|------|------|
| `product_gate_enabled` | bool | false |
| `reply_mode` | enum | preview |
| `consultation_only` | bool | true |
| `workspace_pause` | bool | false |
| `shop_pause` | bool | false |
| `test_shop_allowlisted` | bool | false |

**14a：** 仅文档；不修改 legacy `shops` 表。

---

## 7. 文档索引（Phase 14a 包）

| 文档 | 内容 |
|------|------|
| [phase14a_replylog_schema.md](phase14a_replylog_schema.md) | ReplyLog |
| [phase14a_pending_assisted_reply_schema.md](phase14a_pending_assisted_reply_schema.md) | Pending |
| [phase14a_auditlog_schema.md](phase14a_auditlog_schema.md) | AuditLog |
| [phase14a_senddecision_schema.md](phase14a_senddecision_schema.md) | SendDecision snapshot |
| [phase14a_migration_sequence.md](phase14a_migration_sequence.md) | M0–M9 |
| [phase14a_done.md](phase14a_done.md) | 签收 |

---

## 8. 与 12e 的关系

| 文档 | 关系 |
|------|------|
| phase12e_send_decision_reply_log_schema | 12e 总 SSOT；14a **细化** shadow 实施字段 |
| phase12e_migration_sequence | 12e M0–M9 商户/凭证轨；14a M0–M9 **product gate 轨**（可并行编号，实施时合并） |

---

*Shadow DB schema plan · Phase 14a · 2026-06-03*

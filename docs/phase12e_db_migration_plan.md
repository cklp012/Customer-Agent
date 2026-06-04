# Phase 12e — DB Migration Plan（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | **migration planning only** |
| 状态 | docs only · **无 SQL · 无 ORM 改动** |
| 前置 | [phase12b_data_model_plan.md](phase12b_data_model_plan.md) · [phase12c_send_decision_model.md](phase12c_send_decision_model.md) · [phase12d_api_contract.md](phase12d_api_contract.md) |

---

## 1. Phase 12e 总体目标

| 项 | 说明 |
|----|------|
| **做** | 规划从 legacy 本地 SQLite schema → SaaS product gate schema 的 **分阶段迁移** |
| **不做** | 写代码、创建 Alembic/SQL migration、改 `database/models.py`、切生产发送路径 |
| **策略** | **Shadow-first**：新表并行写入/投影，**不替换** legacy `channels/shops/accounts` |
| **PDD** | 生产热路径继续读 legacy；`pdd_{shop_id}` 队列名不变 |
| **Gate** | `product_gate_enabled` **默认 false**；`reply_mode` **默认 preview** |
| **连接语义** | **`connected` ≠ auto enabled** — 见 ShopBinding 字段 |

---

## 2. 目标对象（SaaS schema）

| 对象 | 用途 | MVP 表 | 文档 |
|------|------|--------|------|
| **Merchant** | 商家身份 | ✅ | [phase12b_merchant_workspace_model.md](phase12b_merchant_workspace_model.md) |
| **Workspace** | 租户 / 计费单元 | ✅ | 同上 |
| **WorkspaceMember** | RBAC | 预留 | 同上 |
| **ShopBinding** | 平台店 + 回复控制 | ✅ | [phase12b_shop_binding_state_model.md](phase12b_shop_binding_state_model.md) · [phase12e_product_gate_tables.md](phase12e_product_gate_tables.md) |
| **CredentialRef** | 凭证抽象 | ✅ | [phase12b_credential_security_model.md](phase12b_credential_security_model.md) |
| **SafetySettings** | 禁诺 / 转人工 / 阈值 | ✅ | [phase12b_reply_mode_and_control_model.md](phase12b_reply_mode_and_control_model.md) |
| **SendDecision** | 为何能/不能发 | ✅ | [phase12e_send_decision_reply_log_schema.md](phase12e_send_decision_reply_log_schema.md) |
| **ReplyLog** | 建议 vs 实际发送 | ✅ | 同上 |
| **HumanTakeoverQueue** | 待人工 | ✅ | 同上 |
| **AuditLog** | pause / mode / auto 开启 | ✅ | [phase12e_product_gate_tables.md](phase12e_product_gate_tables.md) |
| **UsageMeter** | 用量聚合 | ✅ | [phase12b_plan_usage_model.md](phase12b_plan_usage_model.md) |
| **PlanSubscription** | 套餐订阅 | ✅ | plan_usage |
| **PlanLimit** | 套餐限额定义 | ✅ | plan_usage |

**保留 legacy（迁移期）：** `Channel`, `Shop`, `Account`, `Keyword`, `ProductKnowledge`, `CustomerServiceKnowledge` — 见 [phase12e_legacy_mapping.md](phase12e_legacy_mapping.md)。

---

## 3. Shadow-first 原则

```text
┌─────────────────┐     projection      ┌──────────────────┐
│ legacy SQLite   │ ──────────────────► │ shop_bindings    │
│ shops/accounts  │   (read-only sync)  │ (shadow)         │
└────────┬────────┘                     └────────┬─────────┘
         │                                       │
         │ AutoReplyThread (unchanged)           │ optional shadow write
         ▼                                       ▼
    pdd_{shop_id}                          send_decisions / reply_logs
    SendMessage legacy                     (product_gate_enabled=false)
```

| 阶段 | legacy 读 | shadow 写 | 发送路径 |
|------|-----------|-----------|----------|
| M0–M3 | ✅ 唯一 | 可选投影 | legacy only |
| M4 | ✅ | SendDecision 影子日志 | legacy only |
| M5+ | ✅ | ReplyLog preview | gate **仅测试店** on |
| M9 | 可选退役 | 主读 | 产品决策 |

**第一阶段：** 仅 shadow write + Dashboard read model（12d），**不切换**生产发送。

---

## 4. 默认与不变量

| 配置 | 默认值 |
|------|--------|
| `shop_bindings.reply_mode` | `preview` |
| `shop_bindings.product_gate_enabled` | `false` |
| `shop_bindings.consultation_only` | `true` |
| `workspace.workspace_pause` | `false` |
| `shop_bindings.shop_pause` | `false` |

| 不变量 | |
|--------|--|
| Preview | ReplyLog `send_status=not_sent_preview`；**零**平台 send |
| blocked intent | SendDecision `allowed_to_send=false` + HumanTakeoverQueue |
| paused | 覆盖 auto/assisted 发送 |

---

## 5. 与工程 Track 边界

| 禁止（12e） | 允许（后续 Phase） |
|-------------|-------------------|
| 改 `database/models.py` | **13a** 首 shadow 表实现（评审后） |
| 改 handler / SendMessage | **12f** gate 实现计划 |
| 默认 `USE_UNIFIED_OUTBOUND_RESOLVER=true` | 保持 false |
| Doudian production `connected` | waitlist only |

---

## 6. 文档索引（12e 交付）

| 文件 | 内容 |
|------|------|
| [phase12e_legacy_mapping.md](phase12e_legacy_mapping.md) | Legacy → SaaS 映射 |
| [phase12e_product_gate_tables.md](phase12e_product_gate_tables.md) | 核心表 DDL 规划 |
| [phase12e_send_decision_reply_log_schema.md](phase12e_send_decision_reply_log_schema.md) | 决策 / 日志 / 队列 |
| [phase12e_migration_sequence.md](phase12e_migration_sequence.md) | M0–M9 顺序与 go/no-go |

---

## 7. 下一步（post-12e）

| Phase | 内容 |
|-------|------|
| **12f** | flag-gated Preview Send Gate **实现计划** |
| **12g** | Merchant console wireframe |
| **13a** | 首个 shadow 表 **代码** migration（评审 gate） |

---

*Phase 12e · DB Migration Plan · docs only*

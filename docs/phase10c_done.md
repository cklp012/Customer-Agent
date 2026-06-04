# Phase 10c 完成记录 — UnifiedMessage routing / content_type 规划

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| 类型 | **仅文档**（无代码、无 flag、无 schema 变更） |
| 主规划 | [phase10c_plan.md](phase10c_plan.md) |
| 账号 SSOT | [phase10_account_model.md](phase10_account_model.md) |

---

## 1. 交付范围

| 状态 | 文件 |
|------|------|
| 新增 | [phase10c_done.md](phase10c_done.md)（本文） |
| 已有 | [phase10c_plan.md](phase10c_plan.md) — SSOT 主文档 |
| 更新 | [architecture_current.md](architecture_current.md)、[docs/README.md](README.md) |
| 更新 | [phase10_account_model.md](phase10_account_model.md) — platform 三层对齐 |

**代码：** 无 `.py` / `ui/` / `tests/` 变更。

---

## 2. 生产消息路径（未改）

```text
PDD WebSocket
  → PDDChatMessage
  → Context
  → immediate | queue | drop（pdd_message_handler）
  → put_message（queue 路径）
  → MessageConsumer
  → handler_chain（Context + metadata）
```

**UnifiedMessage：** `pdd_to_unified` 已实现；**shadow / dual-track 仍默认 off**（`USE_UNIFIED_MESSAGE_SHADOW`、`USE_UNIFIED_MESSAGE_DUAL_TRACK` 未设置 → false）。

---

## 3. platform 对齐规则

```text
account_data["channel_name"]
  == UnifiedMessage.platform.value   # PlatformType
  == Context.channel_type.value      # bridge.ChannelType
```

| 约定 | 说明 |
|------|------|
| 缺失 `channel_name` | 视为 `pinduoduo`（10a/10b） |
| 10b UI | 仅 `pinduoduo` 可启动 AutoReply；非 PDD 无 WS 入站 |
| dual-track off | handler 以 `Context` 为主；metadata 无 `has_unified` |

详见 [phase10_account_model.md §4.1](phase10_account_model.md#41-与-unifiedmessageplatform-对齐-phase-10c)。

---

## 4. routing 语义

| 值 | 含义 | 生成位置（PDD） |
|----|------|-----------------|
| **immediate** | 不入队；Channel 内 `_handle_immediate_message` | `compute_pdd_routing` ↔ `_should_process_immediately` |
| **queue** | 入 `pdd_{shop_id}` → Consumer → handlers | `compute_pdd_routing` ↔ `_should_queue_message` |
| **drop** | 忽略（日志） | 两分支均 false |

规划：**routing 只在 Channel/mapper 决定**；handler **不**以 routing 作为生产默认分支（Route C 需独立 flag，默认 off）。

---

## 5. content_type 语义

- **跨平台统一**：小写 snake 字符串（如 `text`、`goods_inquiry`）。
- **PDD 当前**：`UnifiedMessage.content_type` = `ContextType.value`（与 `Context.type` 一致）。
- **第二平台（规划）**：各平台 mapper 将原生类型映射到同一词汇表；无法映射 → `unknown` + `routing=drop` 或 `extra.native_type`。

---

## 6. handler 与 Consumer

| 项 | 10c 结论 |
|----|----------|
| 入参 | **仍 Context-first**：`handle(Context, metadata)` |
| `can_handle` | 仍基于 `Context.type`，非 `metadata.routing` |
| metadata | dual-track on 时可观测 `platform` / `routing` / `content_type`（`metadata_adapter`） |
| 发送 | legacy `shop_id` / `user_id` / `from_uid` 优先（7e） |

---

## 7. Phase 10d 入口

**只做契约测试，不改默认行为。**

建议范围：

- 表驱动单测：`ContextType` ↔ `compute_pdd_routing` ↔ immediate/queue/drop
- dual-track **仅在测试中**显式 `true` 的 `metadata.platform` 与 `context.channel_type` 对齐断言
- 文档：`phase10d_done.md`（若编码）

**禁止（10d）：** 改 `pdd_message_handler` / Consumer / handlers 默认路径；改 dual-track 默认；接真实第二平台 WS；默认 handler Route C。

Prompt 全文见 [phase10c_plan.md §11](phase10c_plan.md#11-phase-10d-建议-prompt复制用)。

---

## 8. 下一步

| 阶段 | 内容 |
|------|------|
| **10d** | 契约单测 + 文档 |
| **spike** | 单平台 WS + mapper + queue POC |
| **10e+** | queue 命名 `{platform}_{shop_id}`、AutoReply 按 platform 路由（flag） |

---

*Phase 10c 收尾 · 仅文档 · 无代码变更*

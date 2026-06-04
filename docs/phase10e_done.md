# Phase 10e 完成记录 — Queue 命名与多平台 Message 边界

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| 类型 | **纯文档规划**（无代码、无生产行为变更） |
| 规划 | [phase10e_plan.md](phase10e_plan.md) |
| 前置 | [phase10c_done.md](phase10c_done.md)、[phase10d_done.md](phase10d_done.md)、[phase10_account_model.md](phase10_account_model.md) |

---

## 1. 交付说明

Phase 10e 采用 **Route A**：仅文档 SSOT，**未修改**任何 `.py`、`pdd_lifecycle`、`pdd_message_handler`、`MessageConsumer`、handlers、flag 默认值、UI、database，**未接**真实第二平台。

---

## 2. 当前 PDD queue 命名

生产拼多多入站队列名仍在 `Channel/pinduoduo/core/pdd_lifecycle.py` 生成：

```text
queue_name = f"pdd_{shop_id}"
```

用于：`init` → `_setup_message_consumer` → WS 入队 `put_message` → 停止/清理 `_cleanup_resources`。

**10e 未改、10e 不建议改** 该默认字符串。

---

## 3. 不建议改为 `pinduoduo_{shop_id}`

| 原因 | 说明 |
|------|------|
| 兼容性 | 在途 Consumer / `queue_manager` 注册名、运维与黄金路径均假设 `pdd_*` |
| 成本 | 需停店重建 Consumer；无产品收益（`platform_id` 已是 `pinduoduo`） |
| 策略 | queue 前缀 `pdd` 视为 PDD **实现细节**；账号语义用 `channel_name`（10a） |

**PDD queue 迁移：** 明确 **不做**（除非未来独立 major migration Phase）。

---

## 4. routing / queue_name / platform_id 职责分工

| 概念 | 职责 | 典型值 / 位置 |
|------|------|----------------|
| **routing** | **是否入队**及 Channel 内即时分支 | `immediate` \| `queue` \| `drop`；`compute_pdd_routing` / `pdd_message_handler` |
| **queue_name** | **入哪个隔离队列**（一店一 Consumer） | 生产 PDD：`pdd_{shop_id}` |
| **platform_id** | **账号与消息平台语义**（= `channel_name`） | `pinduoduo`；`UnifiedMessage.platform` / `Context.channel_type`（10c/10d） |

```text
routing 决定「进不进队列」
queue_name 决定「进哪条队列」
platform_id 决定「属于哪个平台」（与队列前缀相关但不相等）
```

---

## 5. 多平台 queue 命名推荐（SSOT）

| platform_id (`channel_name`) | queue_name 格式 | 状态 |
|------------------------------|-----------------|------|
| **pinduoduo** | `pdd_{shop_id}` | **生产 canonical** |
| **demo** | `demo_{shop_id}` | 8a 测试已用 |
| **doudian** | `doudian_{shop_id}` | spike 后 |
| **jingdong** | `jingdong_{shop_id}` | spike 后 |
| **taobao** | `taobao_{shop_id}` | spike 后 |

新平台 **不得** 复用 `pdd_` 前缀，避免与拼多多队列冲突。

---

## 6. Phase 10f 建议

| 项 | 内容 |
|----|------|
| API | `build_queue_name` — 已实现：[Message/queue_naming.py](../Message/queue_naming.py) · [phase10f_done.md](phase10f_done.md) |
| PDD | `pinduoduo`（及缺省）→ **仍** `pdd_{shop_id}` |
| 范围 | helper + `tests/test_queue_naming.py`；**lifecycle 未接入** |
| 可选 | Demo 入队改用 helper（输出仍为 `demo_{shop}`） |
| 明确不做 | 10f **不强制** 替换 `pdd_lifecycle` 内 f-string（若替换则单测断言输出不变） |

Prompt 见 [phase10e_plan.md §14](phase10e_plan.md#14-phase-10f-建议-prompt复制用)。

---

## 7. 禁止项（10e / 10f 默认遵守）

- 不改 PDD queue **默认名**（`pdd_{shop_id}`）
- 不改 `MessageConsumer` **行为**
- 不改 handler **链**默认组成与 `can_handle` 逻辑
- 不默认开启 dual-track / 不改 Phase 9d registry 默认
- 不接真实第二平台 WS / 登录

---

## 8. 后续边界

| 主题 | 阶段 |
|------|------|
| 第二平台 lifecycle + WS + 入队 | **独立 spike** |
| `build_queue_name` helper + 单测 | **Phase 10f**（可选） |
| Consumer 按 platform 分 handler 链 | **11+**（flag，Route D） |
| AutoReply 按 `channel_name` 路由 queue / factory | **10d+**（另 Phase） |
| PDD `pdd_` → `pinduoduo_` 队列迁移 | **不做** |

---

## 9. Consumer 多平台（文档结论）

现网已支持 **多队列并存**：`message_consumer_manager[queue_name] → MessageConsumer`。

「多平台」= 多个 `queue_name`（如 `pdd_S1` 与未来的 `doudian_S2`），**不是** 10e 修改 Consumer 类。

---

*Phase 10e 收尾 · 仅文档 · queue naming 已规划*

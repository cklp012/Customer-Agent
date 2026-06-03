# Phase 9 规划 — AutoReply ChannelRegistry 门控创建

| 项 | 值 |
|---|---|
| 状态 | **9a** 实现中 / 交付见 [phase9_done.md](phase9_done.md) |
| 路线 | **B**：`USE_CHANNEL_REGISTRY_FOR_AUTOREPLY` 默认 false |

---

## 1. 目标

在 **不改变生产默认行为** 的前提下，让 `create_auto_reply_runtime_channel()` 在开关组合允许时经 `ChannelRegistry.create(PINDUODUO)` 创建，失败则 fallback 旧路径。

---

## 2. Flag 矩阵

| `USE_CHANNEL_REGISTRY_FOR_AUTOREPLY` | `USE_PINDUODUO_CHANNEL_WRAPPER` | PINDUODUO 已注册 | 创建路径 |
|--------------------------------------|---------------------------------|------------------|----------|
| false | * | * | `legacy_factory`（3b 原逻辑） |
| true | false | * | `PDDChannel()`（不调用 Registry） |
| true | true | yes | `ChannelRegistry.create` |
| true | true | no / 异常 | `create_pinduoduo_channel` fallback |

---

## 3. 分期

| 阶段 | 内容 |
|------|------|
| **9a** ✅ | flag + `channel_factory` 扩展 + capabilities/diagnose + 测试 |
| **9b** | Registry 工厂与 wrapper-off 等价化（改 `register_pinduoduo_channel` 语义，单独立项） |
| **10+** | UI 多平台、routing、真实第二平台 |

---

## 4. 禁止项（9a）

- 不改 `AutoReplyThread`、`start_auto_reply_account`
- 不改 PDD WS / 登录 / `pdd_message_handler` / handlers / Consumer
- 不删 `create_auto_reply_runtime_channel` / legacy 路径
- 不接 Demo AutoReply、真实第二平台

# Phase 9 规划 — AutoReply ChannelRegistry 门控创建

| 项 | 值 |
|---|---|
| 状态 | **9a–9d** ✅ 见 phase9*_done.md |
| 路线 | 9a–9c：门控 + parity；**9d**：默认 Registry path |

---

## 1. 目标

在 **不改变生产默认行为** 的前提下，让 `create_auto_reply_runtime_channel()` 在开关组合允许时经 `ChannelRegistry.create(PINDUODUO)` 创建，失败则 fallback 旧路径。

---

## 2. Flag 矩阵

| `USE_CHANNEL_REGISTRY_FOR_AUTOREPLY` | `USE_PINDUODUO_CHANNEL_WRAPPER` | PINDUODUO 已注册 | 创建路径 |
|--------------------------------------|---------------------------------|------------------|----------|
| false | * | * | `legacy_factory`（3b 原逻辑） |
| true | false | yes | `ChannelRegistry.create` → `PDDChannel`（9b parity factory） |
| true | true | yes | `ChannelRegistry.create` → `PinduoduoChannel` |
| true | * | no / 异常 | `_create_auto_reply_legacy` fallback |

---

## 3. 分期

| 阶段 | 内容 |
|------|------|
| **9a** ✅ | flag + `channel_factory` 扩展 + capabilities/diagnose + 测试 |
| **9b** ✅ | `create_pinduoduo_registry_channel` + register parity |
| **9c** ✅ | parity hardening；默认仍 legacy path（Route B） |
| **9d** ✅ | `USE_CHANNEL_REGISTRY_FOR_AUTOREPLY` 未设置 → true（Route C） |
| **10+** | UI 多平台、routing、真实第二平台 |

---

## 4. 禁止项（9a）

- 不改 `AutoReplyThread`、`start_auto_reply_account`
- 不改 PDD WS / 登录 / `pdd_message_handler` / handlers / Consumer
- 不删 `create_auto_reply_runtime_channel` / legacy 路径
- 不接 Demo AutoReply、真实第二平台

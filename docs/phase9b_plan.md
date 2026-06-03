# Phase 9b 规划 — PDD registry factory parity

| 项 | 值 |
|---|---|
| 状态 | 交付见 [phase9b_done.md](phase9b_done.md) |
| 路线 | **C**：`create_pinduoduo_registry_channel` + 改 register |

---

## 1. 问题

9a 时 `register_pinduoduo_channel` 注册 `create_pinduoduo_channel`（恒 wrapper），与 `USE_PINDUODUO_CHANNEL_WRAPPER=false` 时的 `PDDChannel` 不等价。

---

## 2. 方案（路线 C）

| 函数 | 职责 |
|------|------|
| `create_pinduoduo_channel` | wrapper-only，直接调用 |
| `create_pinduoduo_registry_channel` | 只调 `_create_auto_reply_legacy`；**禁止**再入 Registry / `create_auto_reply_runtime_channel` |
| `register_pinduoduo_channel` | 注册 `create_pinduoduo_registry_channel` |
| `create_auto_reply_runtime_channel` | registry flag on → `Registry.create`；失败 → `_create_auto_reply_legacy` |

---

## 3. 9b 后 AutoReply 矩阵

| Registry flag | PINDUODUO 已注册 | 行为 |
|---------------|------------------|------|
| false | * | `_create_auto_reply_legacy` |
| true | yes | `ChannelRegistry.create`（wrapper on/off 由 registry factory 决定） |
| true | no / 失败 | warning + `_create_auto_reply_legacy` |

---

## 4. 禁止项

- 不改 AutoReplyThread、PDD 内核、handlers、consumer
- 不删 `create_pinduoduo_channel` / `create_auto_reply_runtime_channel`

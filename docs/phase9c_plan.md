# Phase 9c 规划 — AutoReply Registry parity hardening

| 项 | 值 |
|---|---|
| 状态 | 交付见 [phase9c_done.md](phase9c_done.md) |
| 路线 | **B**：加强测试与文档，**不改** flag 默认值 |

---

## 1. 为何选 Route B

9b 后 `ChannelRegistry.create(PINDUODUO)` 经 `create_pinduoduo_registry_channel` 与 `_create_auto_reply_legacy` **已等价**（wrapper on/off 均尊重 `USE_PINDUODUO_CHANNEL_WRAPPER`）。

在缺少一轮 **生产黄金路径** 与全量默认-on 单测迁移前，不宜把 `USE_CHANNEL_REGISTRY_FOR_AUTOREPLY` 默认改为 `true`。

---

## 2. 9c 交付

| 项 | 内容 |
|----|------|
| 测试 | `test_autoreply_registry_parity.py`：registry vs legacy、默认 legacy、bootstrap 无 fallback |
| 默认值 | `USE_CHANNEL_REGISTRY_FOR_AUTOREPLY` **仍 false** |
| 文档 | 灰度命令、手动 app 清单（待执行） |

---

## 3. 9d（后续，可选）

- 将 `USE_CHANNEL_REGISTRY_FOR_AUTOREPLY` 默认改为 `true`，或 `app.py` `setdefault`
- 全量单测 + 黄金路径通过后上线

---

## 4. 禁止项

- 不改 `channel_factory` 行为、`app.py`、`AutoReplyThread`、PDD 内核、handlers

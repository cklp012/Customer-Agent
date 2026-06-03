# Phase 9a 完成记录 — AutoReply Registry 门控创建

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| 路线 | B（`USE_CHANNEL_REGISTRY_FOR_AUTOREPLY` 默认 false） |

---

## 1. 新增/修改

| 文件 | 作用 |
|------|------|
| `Message/autoreply_registry_flags.py` | 新 flag helper |
| `Channel/pinduoduo/channel_factory.py` | 扩展 `create_auto_reply_runtime_channel` |
| `Message/runtime_capabilities.py` | `infer_autoreply_channel_source` + report 字段 |
| `scripts/diagnose_runtime.py` | 打印 flag 与推断 source |
| `tests/test_autoreply_registry_channel.py` | 9a 矩阵单测 |
| `tests/test_auto_reply_channel_switch.py` | registry flag off 回归 |
| `tests/test_runtime_capabilities.py` | 新 flag / source |

---

## 2. 行为摘要

- **默认**（两 flag 均 false）：与 Phase 3b 完全一致 → `PDDChannel()`。
- **仅 registry flag on**：wrapper off 时仍 `PDDChannel()`，**不** `ChannelRegistry.create`。
- **两 flag on 且已注册**：`ChannelRegistry.create(PINDUODUO)`；未注册/异常/类型不符 → warning + `create_pinduoduo_channel`。
- `AutoReplyThread` **未改**；仍调用 `create_auto_reply_runtime_channel()`。

---

## 3. 9b 留待

- `register_pinduoduo_channel` 工厂与 wrapper-off 的 Registry 等价化
- 全量 registry 测试语义调整

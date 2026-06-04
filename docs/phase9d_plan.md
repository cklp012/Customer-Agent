# Phase 9d 规划 — AutoReply Registry 默认开启

| 项 | 值 |
|---|---|
| 状态 | 交付见 [phase9d_done.md](phase9d_done.md) |
| 路线 | **C**：`autoreply_registry_flags` 未设置 → **true** |

---

## 1. 前置

9b parity、9c 单测、手动 app 灰度与默认路径验证已通过。

---

## 2. 变更

| 项 | 9c | 9d |
|----|-----|-----|
| `USE_CHANNEL_REGISTRY_FOR_AUTOREPLY` unset | false | **true** |
| 回滚 | 不设 env | **`false`** |
| `channel_factory` | 不变 | 不变 |
| fallback | 保留 | 保留 |

---

## 3. 禁止

- 删 legacy / 改 wrapper 默认 / 改 app.py（Route C）

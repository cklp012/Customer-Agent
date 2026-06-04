# Phase 10f 规划 — queue_name helper

| 项 | 值 |
|---|---|
| 前置 | [phase10e_done.md](phase10e_done.md) |
| 交付 | [phase10f_done.md](phase10f_done.md) |

---

## 1. 目标

新增 `Message/queue_naming.py`，统一 `build_queue_name(platform_id, shop_id)` 契约，**不改变** PDD 生产队列名 `pdd_{shop_id}`。

---

## 2. 不改变 PDD queue

- **不**修改 `pdd_lifecycle.py` 内 `f"pdd_{shop_id}"`。
- **不**改为 `pinduoduo_{shop_id}`。
- helper 输出 `build_queue_name("pinduoduo", shop_id) == f"pdd_{shop_id}"` 与现网一致，供 spike/10g 接入。

---

## 3. helper 规则

| platform_id | queue 前缀 |
|-------------|------------|
| `pinduoduo` / `pdd` / None | `pdd` |
| `demo` | `demo` |
| `doudian` | `doudian` |
| `jingdong` | `jingdong` |
| `taobao` | `taobao` |
| 其它 | 归一化原字符串 |

`shop_id` 必填；空 → `ValueError`。

---

## 4. 禁止项

不改 Consumer、handlers、`pdd_message_handler`、WS、AutoReply、channel_factory、UI、DB、flag 默认；不接真实第二平台。

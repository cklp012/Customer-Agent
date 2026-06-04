# Phase 10f 完成记录 — queue_name helper

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| 实现 | [Message/queue_naming.py](../Message/queue_naming.py) |

---

## 1. 交付

| 操作 | 文件 |
|------|------|
| 新增 | `Message/queue_naming.py` — `normalize_platform_id`, `queue_prefix_for_platform`, `build_queue_name` |
| 新增 | `tests/test_queue_naming.py` |
| 新增 | `docs/phase10f_plan.md`、`docs/phase10f_done.md`（本文） |
| 更新 | `architecture_current.md`、`docs/README.md` |

---

## 2. helper 摘要

```python
build_queue_name("pinduoduo", shop_id)  # → pdd_{shop_id}
build_queue_name("pdd", shop_id)        # → pdd_{shop_id}
build_queue_name(None, shop_id)       # → pdd_{shop_id}
build_queue_name("demo", shop_id)     # → demo_{shop_id}
# doudian / jingdong / taobao → {platform}_{shop_id}
# unknown → unknown_{shop_id}
```

支持 `PlatformType` / `ChannelType` 枚举；`shop_id` 空 → `ValueError`。

---

## 3. 测试矩阵

| 用例 | 期望 |
|------|------|
| pinduoduo / pdd / None + S1 | `pdd_S1` |
| demo / doudian / jingdong / taobao + S1 | `{platform}_S1` |
| unknown + S1 | `unknown_S1` |
| pinduoduo + 123 | `pdd_123` |
| PlatformType.PINDUODUO + S1 | `pdd_S1` |
| shop_id None / "" / 空白 | `ValueError` |

---

## 4. PDD 生产路径

| 项 | 状态 |
|----|------|
| `pdd_lifecycle` | **未接入** helper；仍为 `f"pdd_{shop_id}"` |
| 与 helper 等价性 | `build_queue_name("pinduoduo", shop_id)` == 现网字符串 |
| 后续接入 | **Phase 10g/10h** — [phase10g_plan.md](phase10g_plan.md)（10g Route B：`pdd_queue_name`；10h Route C：lifecycle） |

---

## 5. 未改

Consumer、handlers、`pdd_message_handler`、WS、AutoReply、channel_factory、UI、DB、flag 默认；无真实第二平台。

---

## 6. 后续

- spike：第二平台 lifecycle 使用 `build_queue_name`
- 可选 refactor：`pdd_lifecycle` 改调用 helper（行为不变）

---

*Phase 10f · helper + tests only*

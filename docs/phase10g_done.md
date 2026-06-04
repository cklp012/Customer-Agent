# Phase 10g 完成记录 — `pdd_queue_name` + legacy parity（Route B）

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| 路线 | **Route B** — helper + 单测；**未**接入 `pdd_lifecycle` |
| 规划 | [phase10g_plan.md](phase10g_plan.md) |
| 前置 | [phase10f_done.md](phase10f_done.md) |

---

## 1. 交付

| 操作 | 文件 |
|------|------|
| 修改 | `Message/queue_naming.py` — 新增 `pdd_queue_name` |
| 新增 | `tests/test_pdd_queue_name_parity.py` |
| 新增 | [phase10g_done.md](phase10g_done.md)（本文） |
| 更新 | `architecture_current.md`、`docs/README.md` |

**未改：** `pdd_lifecycle.py`、`pdd_message_handler`、Consumer、handlers、WS、AutoReply、UI、DB、flags。

---

## 2. `pdd_queue_name` 摘要

```python
def pdd_queue_name(shop_id) -> str:
    return build_queue_name("pinduoduo", shop_id)
```

| 输入 | 结果 |
|------|------|
| `"123"` / `123` | `pdd_123` |
| 正常 shop_id | 与 `f"pdd_{shop_id}"` 相同（见 parity 测试） |
| `None` / `""` / 仅空白 | `ValueError`（避免 `pdd_None` / `pdd_`） |

`build_queue_name` 规则 **未改**。

---

## 3. Legacy parity 测试

对 `S1`、`123`、`shop-abc`、`店铺001` 等：

```text
pdd_queue_name(shop_id) == f"pdd_{shop_id}"
```

`None` / `""`：仅断言 `raises ValueError`，**不要求** 等于 f-string。

---

## 4. `pdd_lifecycle` 接入状态

| 项 | 状态 |
|----|------|
| 生产路径 | 仍使用 `f"pdd_{shop_id}"`（5 处，见 phase10g_plan） |
| 本 Phase | **未接入** helper |
| 下一步 | **Phase 10h** — [phase10h_plan.md](phase10h_plan.md)（Route C + legacy-compatible 封装） |

---

## 5. 已知差异（10h 前须知晓）

| shop_id | f-string | `pdd_queue_name` |
|---------|----------|------------------|
| 首尾空白 | `pdd_ 123 ` | `pdd_123`（strip） |
| `None` | `pdd_None` | `ValueError` |
| `""` | `pdd_` | `ValueError` |

10h 接入前须确认 DB 无上述坏数据，或先规范化 `shop_id`。

---

*Phase 10g Route B · helper only*

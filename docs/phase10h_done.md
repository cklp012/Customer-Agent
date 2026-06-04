# Phase 10h 完成 — Route C：lifecycle-safe queue helper

| 项 | 内容 |
|----|------|
| 状态 | **Route C 已完成** |
| 日期 | 2026-06-03 |
| 规划 | [phase10h_plan.md](phase10h_plan.md) |

---

## 交付摘要

- `Channel/pinduoduo/core/pdd_lifecycle.py` 新增 `_lifecycle_pdd_queue_name(shop_id)`：
  - 正常 `shop_id` → `pdd_queue_name(shop_id)` → `pdd_{shop_id}`
  - `None` / `""` / 仅空白 → `ValueError` 捕获后 → 历史 `f"pdd_{shop_id}"`（如 `pdd_None`、`pdd_`、`pdd_ `）
- **init**：方法入口绑定单一 `queue_name`；`_setup_message_consumer`、`_message_loop`、正常结束 cleanup、`CancelledError` cleanup、通用 `Exception` cleanup 均复用该变量；**无**新的内联 `f"pdd_{shop_id}"` cleanup。
- **stop_account**：账号存在时 `queue_name = _lifecycle_pdd_queue_name(shop_id)` → `_cleanup_resources(queue_name)`；无账号仍 early return，不 cleanup。
- 生产 PDD 队列名仍为 **`pdd_{shop_id}`**，未改为 `pinduoduo_{shop_id}`。

---

## 测试

- `tests/test_pdd_lifecycle_queue_name.py`：helper parity、init setup/loop 同 queue、init 异常 cleanup、stop_account 有/无账号（unittest.mock，无真实 WS / Consumer / 登录）。

---

## 未改动（本阶段边界）

- `pdd_message_handler`、`Message/core/consumer.py`、`Message/handlers/**`
- PDD WS / 登录、`AutoReplyThread`、`channel_factory`
- `ui/**`、`database/**`、`app.py`、`*_flags.py` 默认值
- 真实第二平台代码

---

## 后续

- **Phase 10i**（已完成）：[phase10i_done.md](phase10i_done.md) — multi-platform capability matrix + spike boundary（纯文档）。
- 第二平台 WS / lifecycle **仍推迟**至 **10j spike 计划** / 11+ 代码 Phase。
- 可选：DB 审计无边缘 `shop_id` 后，收紧 legacy fallback（非本阶段）。

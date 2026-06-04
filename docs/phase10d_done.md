# Phase 10d 完成记录 — routing / platform 契约测试

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| 类型 | **仅 tests + docs**（无生产行为变更） |
| 规划 | [phase10d_plan.md](phase10d_plan.md) · SSOT [phase10c_done.md](phase10c_done.md) |

---

## 1. 交付范围

| 操作 | 文件 |
|------|------|
| 新增 | `tests/test_pdd_routing_parity.py` |
| 新增 | `tests/test_platform_message_contract.py` |
| 扩展 | `tests/test_unified_dual_track.py`（fixture→mapper→enrich；flag 仅测试内设置） |
| 新增 | [phase10d_done.md](phase10d_done.md)（本文） |
| 更新 | [architecture_current.md](architecture_current.md)、[docs/README.md](README.md) |
| 更新 | [phase10c_done.md](phase10c_done.md)（链到 10d） |

**未改：** `pdd_message_handler`、`pdd_to_unified` 逻辑、`consumer`、`handlers`、`metadata_adapter`、各 flag 默认值、UI、DB、WS。

---

## 2. 测试摘要

### routing parity（`test_pdd_routing_parity.py`）

- 遍历 **`ContextType` 全枚举** → `compute_pdd_routing` ∈ {immediate, queue, drop}。
- `HANDLER_*` 集合与 `pdd_message_handler` L138–159 同构；与 mapper `_IMMEDIATE_TYPES` / `_QUEUE_TYPES` **相等**。
- immediate / queue **不重叠**；其余为 **drop**（含 `MALL_SYSTEM_MSG`、`SYSTEM_BIZ`）。
- 合成入站对象 → `pdd_message_to_unified`：`content_type` 与 `extra["routing"]` 与枚举一致。

### platform contract（`test_platform_message_contract.py`）

- `channel_name` / `normalize_channel_name` / `is_autoreply_supported`（pinduoduo）。
- `UnifiedMessage.platform`、`Context.channel_type`、`enrich_metadata_from_unified`、`get_platform` / `get_routing` / `get_content_type` 对齐。

### dual-track（`test_unified_dual_track.py` 扩展）

- fixture → mapper → `MessageWrapper` → enrich；**不**启 WS / Consumer 线程。
- `USE_UNIFIED_MESSAGE_DUAL_TRACK` 仅在用例内显式 `true` 并 `tearDown` 清理；**默认仍 false**。

---

## 3. 生产行为（未变）

| 项 | 状态 |
|----|------|
| 入站路径 | `PDDChatMessage → Context → …` |
| shadow / dual-track 默认 | **off** |
| handler | **Context-first** |
| Phase 9d AutoReply Registry | 未动 |

---

## 4. 后续边界（10e / spike）

- 真实第二平台 mapper + WS + queue 前缀 `{platform}_{shop_id}`
- handler Route C（`metadata.routing`，独立 flag）
- `pdd_message_handler` 端到端 dual-track 集成测（非 10d）

---

*Phase 10d · 契约测试锁定 10c SSOT*

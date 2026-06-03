# Phase 8a 完成记录 — Demo platform runtime spike

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| 范围 | Demo 入站 → 双轨入队 → Consumer → handler(Context) |

---

## 1. 新增 / 修改文件

| 文件 | 说明 |
|------|------|
| `Channel/demo/mappers/demo_to_context.py` | raw → Context |
| `Channel/demo/mappers/demo_to_unified.py` | raw → UnifiedMessage |
| `Channel/demo/demo_inbound.py` | `enqueue_demo_message` |
| `Message/inbound_enqueue.py` | `enqueue_inbound_message` |
| `Channel/demo/demo_channel.py` | `inject_runtime_flow`（默认 off） |
| `tests/test_demo_runtime_flow.py` | 集成测试 |
| `docs/phase8_plan.md` | 总规划 |
| `docs/phase8a_done.md` | 本文档 |

---

## 2. Demo runtime 测试链路

```text
Demo raw dict
  → demo_raw_to_context + demo_raw_to_unified
  → enqueue_inbound_message (DUAL_TRACK on 时带 unified)
  → MessageWrapper → MessageConsumer
  → enrich_metadata_from_unified
  → handler(Context, metadata)
```

**DemoChannel（测试）：** `inject_runtime_flow=True` + `runtime_queue_name` → `start_account` 时自动 `enqueue_demo_message`。

---

## 3. 与 PDD 默认路径边界

| 项 | 状态 |
|----|------|
| `pdd_message_handler` / WS / login | **未改** |
| `app.py` / `ui/` | **未改** |
| `outbound_resolver` 生产逻辑 | **未改** |
| handler 业务 | **未改** |
| 生产 feature flag | **无新增** |

---

## 4. 明确不做（8a）

- 不接真实第二平台
- 不泛化 `AccountOutboundRegistry` / `resolve_outbound`（→ **8b**）
- 不改 `MessageConsumer` 源码

---

## 5. 验收

```powershell
python -m unittest discover -s tests -v
```

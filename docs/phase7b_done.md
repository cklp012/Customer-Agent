# Phase 7b 完成记录 — PDD → UnifiedMessage mapper

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-02 |
| 范围 | `Channel/pinduoduo/mappers/*`、fixtures、单测 |

---

## 1. 新增文件

| 文件 | 说明 |
|------|------|
| `Channel/pinduoduo/mappers/__init__.py` | 导出 `pdd_message_to_unified`、`compute_pdd_routing` |
| `Channel/pinduoduo/mappers/pdd_to_unified.py` | 正向 mapper |
| `tests/fixtures/pdd_messages/*.json` | 匿名 fixture（text / goods_inquiry / withdraw / mall_cs） |
| `tests/test_pdd_to_unified_mapper.py` | 10 个用例 |
| `docs/phase7b_done.md` | 本文档 |

---

## 2. 行为摘要

- **`pdd_message_to_unified`**：`PDDChatMessage` → `UnifiedMessage`；`conversation.extra["routing"]` 为 `immediate` / `queue` / `drop`，规则与 `pdd_message_handler` 中 `_should_*` 同构。
- **`content`**：保留 `str` / `dict` / `list` 原样（**不** `json.dumps`）。legacy `_convert_to_context` 仍会把 dict 转成 string — 两条路径并存直至 Phase 7d。
- **`raw`**：来自 `pdd.raw_data`（即构造时的 WS JSON）。

---

## 3. 明确不做

- 未改 `Channel/pinduoduo/core/pdd_message_handler.py`、WS、login
- 未改 `Message/`、`bridge/`、`app.py`、`ui/`
- 未接入 `put_message` / `MessageConsumer` / `handler_chain`
- 未新增 `unified_outbound_resolver`

---

## 4. 验收命令

```powershell
cd D:\agent
python -m unittest discover -s tests -v
python -m unittest tests.test_pdd_to_unified_mapper -v
```

---

## 5. 相关文档

- [phase7a_plan.md](phase7a_plan.md) — 规划
- [architecture_current.md](architecture_current.md) — 运行时仍为 Context

# Phase 7f 完成记录 — extract 委托 metadata_adapter

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| 范围 | `get_send_context_for_extract` + `extract_pdd_send_context` 薄委托 |

---

## 1. 变更摘要

| 文件 | 说明 |
|------|------|
| `Message/metadata_adapter.py` | 新增 `get_send_context_for_extract` |
| `Message/handlers/outbound_resolver.py` | `extract_pdd_send_context` 委托 adapter |
| `tests/test_extract_adapter_parity.py` | 等价性与边界单测 |
| `tests/test_metadata_adapter.py` | 更新 extract 等价性断言 |
| `docs/phase7f_done.md` | 本文档 |

---

## 2. API 差异

| 函数 | 用途 | unified fallback | strip 空串 |
|------|------|------------------|------------|
| `get_send_context_for_extract` | **发送路径 extract**（与 legacy extract 等价） | ❌ | ❌ |
| `get_send_context` | adapter 通用发送上下文（7e） | ✅ account_id / buyer_uid | ✅ |

**extract 路径优先级：** `metadata` legacy 键 → `context.kwargs`（仅 `is None` 时补）→ 非 None 值 `str()`。

---

## 3. 明确不做

- 未改 `ai_handler` / `keyword_handler` / `MessageConsumer` / `handler_chain`
- 未改 `resolve_pinduoduo_outbound` 其它逻辑
- 未启用发送路径 unified-only fallback
- 未新增 feature flag
- handler 仍 `handle(Context, metadata)`；**7g** 再考虑观测字段 / metadata logging

---

## 4. 验收

```powershell
python -m unittest discover -s tests -v
git diff --stat
git status
```

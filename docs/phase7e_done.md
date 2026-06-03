# Phase 7e 完成记录 — metadata adapter

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-02 |
| 范围 | `Message/metadata_adapter.py` + 单测 |

---

## 1. 新增文件

| 文件 | 说明 |
|------|------|
| `Message/metadata_adapter.py` | 统一 metadata/context 读取 |
| `tests/test_metadata_adapter.py` | 优先级与等价性测试 |
| `docs/phase7e_done.md` | 本文档 |

---

## 2. API 摘要

| 函数 | 说明 |
|------|------|
| `has_unified_metadata` | `metadata["has_unified"]` |
| `get_platform` / `get_content_type` / `get_routing` | has_unified 时优先 metadata；否则 context |
| `get_shop_id` / `get_account_id` / `get_buyer_uid` | 发送字段；legacy 优先 |
| `get_send_context` | `(shop_id, user_id, from_uid)` |

**发送优先级：** `metadata` legacy 键 → `context.kwargs` → unified 键（`account_id` / `buyer_uid`，仅在前两者皆空）。

---

## 3. 与 extract_pdd_send_context

- Consumer 写入 legacy 键后：**与 `extract_pdd_send_context` 结果一致**。
- 仅 unified 键、无 `user_id`/`from_uid`：adapter 可 fallback；**extract 仍返回 None**（7f 再对齐）。

---

## 4. 明确不做

- 未改 `ai_handler` / `keyword_handler` / `outbound_resolver` / `MessageConsumer`
- handler 仍 `handle(Context, metadata)`；不接收 `UnifiedMessage`

---

## 5. 下一步（7f）

- `extract_pdd_send_context` 委托 `get_send_context`（可选）
- handler 日志/分支使用 `get_platform` / `get_routing`

---

## 6. 验收

```powershell
python -m unittest discover -s tests -v
```

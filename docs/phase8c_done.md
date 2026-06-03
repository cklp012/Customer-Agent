# Phase 8c 完成记录 — handler unified outbound 接入

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| 路线 | Route B |

---

## 1. 新增 / 修改

| 文件 | 说明 |
|------|------|
| `Message/handlers/unified_outbound_flags.py` | `USE_UNIFIED_OUTBOUND_RESOLVER` |
| `Message/handlers/ai_handler.py` | `_send_reply` resolver 分支 |
| `Message/handlers/keyword_handler.py` | `handle` resolver 分支 |
| `tests/test_unified_outbound_flags.py` | flag 单测 |
| `tests/test_handler_unified_outbound.py` | handler 选择 + Demo 出站 |

---

## 2. 行为

- **默认**：UNIFIED off → 与 8b 前完全一致
- **UNIFIED on**：`resolve_outbound`；Demo 经 registry/metadata；PDD 委托旧 resolver
- **未改**：`send_text` / `transfer_to_human` 参数、legacy fallback、`pdd_message_handler`

---

## 3. 验收

```powershell
python -m unittest discover -s tests -v
```

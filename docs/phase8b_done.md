# Phase 8b 完成记录 — unified outbound resolver

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| 路线 | Route A |

---

## 1. 新增文件

| 文件 | 说明 |
|------|------|
| `Message/handlers/channel_outbound_registry.py` | `platform:shop_id:account_id` 注册表 |
| `Message/handlers/unified_outbound_resolver.py` | `resolve_outbound` / `infer_platform` |
| `tests/test_channel_outbound_registry.py` | registry 单测 |
| `tests/test_unified_outbound_resolver.py` | unified resolver 单测 |

---

## 2. 行为摘要

- **Registry key**：`{platform}:{shop_id}:{account_id}`
- **平台推断**：`metadata["platform"]` → `kwargs.channel_type` → `pinduoduo`
- **Send context**：`get_send_context_for_extract`（与 `extract_pdd_send_context` 等价）
- **PDD**：`platform==pinduoduo` 时委托 `resolve_pinduoduo_outbound`（含 flag / 旧 registry / factory）
- **Demo**：仅 metadata 注入或 channel registry；不自动 create

---

## 3. 生产边界

| 路径 | 8b 状态 |
|------|---------|
| `ai_handler` / `keyword_handler` | 仍 `resolve_pinduoduo_outbound` |
| `AccountOutboundRegistry` | 未改 |
| Legacy SendMessage fallback | 未改 |

---

## 4. 验收

```powershell
python -m unittest discover -s tests -v
```

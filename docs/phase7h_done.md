# Phase 7h 完成记录 — handler debug observability 接线

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| 范围 | `log_handler_observation` + ai/keyword `handle()` 入口 debug |

---

## 1. 变更摘要

| 文件 | 说明 |
|------|------|
| `Message/metadata_observability.py` | 新增 `log_handler_observation` |
| `Message/handlers/ai_handler.py` | `handle()` 入口 safe debug |
| `Message/handlers/keyword_handler.py` | `handle()` 入口 safe debug；`can_handle` 去掉完整 content |
| `tests/test_handler_observation_debug.py` | 隐私与接线单测 |
| `docs/phase7h_done.md` | 本文档 |

---

## 2. API

```python
log_handler_observation(logger, metadata, context, handler_name)
```

- 内部：`build_handler_observation` → `format_observation_for_log`
- 输出：`logger.debug("handler_observation %s", line)`
- 异常 swallowed，不影响 handler 主流程
- **无 feature flag**；默认 INFO 无新增日志

---

## 3. 接入点

| Handler | 位置 | 说明 |
|---------|------|------|
| `AIReplyHandler` | `handle()` 首行 | 不改发送 / AI / log_message |
| `KeywordDetectionHandler` | `handle()` 首行 | 不改转人工逻辑 |
| `KeywordDetectionHandler` | `can_handle()` | 仅 log `matched keyword`，不含用户正文 |

---

## 4. 明确不做

- 未改 handler 签名 / handler_chain / Consumer / outbound_resolver
- 未改发送、转人工、AI 生成逻辑与返回值
- 未改 `BaseHandler.log_message`（→ **7i**）
- 未清理 ai_handler INFO 级 `回复: {reply}`（→ **7i**）

---

## 5. 联调（可选）

```powershell
$env:LOGURU_LEVEL = "DEBUG"
$env:USE_UNIFIED_MESSAGE_DUAL_TRACK = "true"   # 观测 has_unified 字段
python app.py
```

---

## 6. 下一步（7i）

- `BaseHandler.log_message`：去掉 50 字 content 预览 / UID 脱敏
- ai_handler INFO：`回复: {reply}` 改为不含正文
- `_send_reply` warning 中 UID 脱敏（可选）

---

## 7. 验收

```powershell
python -m unittest discover -s tests -v
git diff --stat
git status
```

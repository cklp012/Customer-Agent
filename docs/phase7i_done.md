# Phase 7i 完成记录 — sensitive INFO log cleanup

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| 范围 | Route B+：`log_sanitizer` + BaseHandler + ai_handler + CatchAllHandler |

---

## 1. 变更摘要

| 文件 | 说明 |
|------|------|
| `Message/log_sanitizer.py` | INFO 日志脱敏 helper |
| `Message/handlers/base.py` | `log_message` 无 content/完整 UID |
| `Message/handlers/ai_handler.py` | `extra_info` → `reply_len=N` |
| `Message/core/handlers.py` | CatchAllHandler `content_len` + UID suffix |
| `tests/test_log_sanitizer.py` | sanitizer 单测 |
| `tests/test_sensitive_log_cleanup.py` | 清理验收单测 |

---

## 2. 日志格式（改后）

**BaseHandler.log_message：**

```text
AIReplyHandler AI回复发送成功 - buyer=***5678 - type=text content_len=42 reply_len=128
```

**CatchAllHandler：**

```text
账号: ***u1
买家: buyer=***5678
content_len: 42
```

---

## 3. sanitizer API

| 函数 | 说明 |
|------|------|
| `redact_uid` | re-export from `metadata_observability` |
| `content_length` | 正文长度，不输出正文 |
| `reply_length` | 同 `content_length` |
| `format_user_ref` | `buyer=***suffix` |
| `format_message_type` | `context.type` → str |

---

## 4. 明确不做

- 未改 keyword_handler `cs_uid`、ai `_send_reply` warning 完整 UID（→ **7j**）
- 未改 outbound_resolver、Consumer、发送/转人工/AI 逻辑
- 未新增 feature flag

---

## 5. 下一步（7j）

- ai_handler `_send_reply` warning UID 脱敏
- keyword_handler 转接成功 `cs_uid` 脱敏
- outbound_resolver debug/warning UID 脱敏

---

## 6. 验收

```powershell
python -m unittest discover -s tests -v
git diff --stat
git status
```

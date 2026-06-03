# Phase 7g 完成记录 — metadata observability helper

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| 范围 | `Message/metadata_observability.py` + 单测（**不改 handler**） |

---

## 1. 新增文件

| 文件 | 说明 |
|------|------|
| `Message/metadata_observability.py` | 安全观测摘要 builder |
| `tests/test_metadata_observability.py` | 隐私边界与 adapter 对齐单测 |
| `docs/phase7g_done.md` | 本文档 |

---

## 2. API

| 符号 | 说明 |
|------|------|
| `OBSERVATION_KEYS` | 固定观测键集合 |
| `redact_uid(uid, visible_suffix=4)` | UID 脱敏，保留末 N 位 |
| `build_handler_observation(metadata, context, *, handler_name=None)` | 构建安全观测 dict |
| `format_observation_for_log(obs)` | 紧凑 `key=value`  debug 串 |

---

## 3. 观测字段表

| 字段 | 来源 | 日志 |
|------|------|------|
| `handler` | 调用方传入 | ✅ |
| `platform` | `get_platform` | ✅ |
| `content_type` | `get_content_type` | ✅ |
| `routing` | `get_routing` | ✅ |
| `has_unified` | `has_unified_metadata` | ✅ |
| `message_id` | `metadata["message_id"]` | ✅ |
| `unified_message_id` | `metadata`（仅 has_unified） | ✅ |
| `shop_id` | `metadata["shop_id"]` | ✅ |
| `account_id_suffix` | `redact_uid(get_account_id(...))` | ✅ 脱敏 |
| `conversation_suffix` | `redact_uid(conversation_id \| buyer_uid)` | ✅ 脱敏 |
| `retry_count` | `metadata["retry_count"]` | ✅ |

---

## 4. 隐私边界

**不输出：** `context.content`、完整 UID、`raw` / `content` / `body` / `cookie` / `token` / `password` / `reply`、完整 metadata dump。

**脱敏：** `account_id_suffix`、`conversation_suffix` 仅 `***` + 末 4 位。

---

## 5. 明确不做

- 未改 `ai_handler` / `keyword_handler` / `MessageConsumer` / `handler_chain`
- 未改 `outbound_resolver` / `metadata_adapter` / 发送逻辑
- 未新增 feature flag
- 未在运行时打 log（默认无额外日志）

---

## 6. 下一步（7h）

- 在 `ai_handler` / `keyword_handler` 中 `logger.debug(format_observation_for_log(...))`
- 清理 keyword_handler 全量 `context.content` debug
- 仍不改 handler 签名、发送逻辑、是否回复

---

## 7. 验收

```powershell
python -m unittest discover -s tests -v
git diff --stat
git status
```

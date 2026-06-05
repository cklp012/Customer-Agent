# Phase 14e — Integration Points

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 原则 | handler **不** 直接 session/ORM |

---

## 1. Current — Phase 13e（as-is）

```text
AIReplyHandler.handle()
  → preprocess
  → select_product_gate_config()
  → [preview gate on]
       → classify + build_send_decision
       → _get_ai_reply()
       → evaluate_guarded_send()
       → append_preview_log()          # Message/gates/preview_log.py
       → return True (zero-send)
  → [legacy]
       → _get_ai_reply() → _send_reply()
```

```text
Dashboard / tests:
  list_preview_reply_logs()            # Message/gates/reply_log_projection.py
    ← preview_log.all() in-memory
```

---

## 2. Future — Phase 14g（preview + optional DB）

```text
AIReplyHandler.handle()
  → [preview gate on]
       → ... (gates unchanged) ...
       → PreviewReplyLogService.record_preview(
            message_text, reply, classification, decision, guarded, metadata
          )
       → return True

PreviewReplyLogService.record_preview():
  1. append_preview_log(in-memory)           # always
  2. if flags.write_reply_log:
       ReplyLogRepository.create_preview_reply_log(...)
  3. if flags.write_send_decision:
       SendDecisionRepository.create_snapshot(...)
  4. never calls _send_reply
```

**Handler 变更（14g 最小）：**

- 将 `append_preview_log(...)` 替换为 `PreviewReplyLogService.record_preview(...)`
- Service 内部仍调用现有 gates + in-memory

---

## 3. Future — Dashboard read（14h+）

```text
GET /preview-reply-logs (planning only)

PreviewReplyLogService.list_for_dashboard(workspace_id, shop_id):
  if PRODUCT_PERSISTENCE_READ_DASHBOARD:
    return ReplyLogRepository.list_reply_logs(...)
  else:
    return list_preview_reply_logs()   # 13e projection
```

---

## 4. Future — Assisted（post-14g）

```text
AI stage (gate on, reply_mode=assisted):
  AssistedReplyService.create_pending_suggestion(...)
    → ReplyLog (not_sent_assisted_required)
    → PendingAssistedReplyRepository.create_pending
    → SendDecisionRepository.create_snapshot (ai_generate)
    → NO SendMessage

Merchant approve command (NOT in AIReplyHandler):
  AssistedReplyService.approve_and_send(pending_id, actor, final_reply):
    → permission check (13f roles)
    → stale / expired check
    → re-classify + evaluate_guarded_send(merchant_approved=true)
    → if not should_send: reject + AuditLog
    → SendMessage / outbound                    # ONLY HERE
    → ReplyLogRepository.update_sent
    → PendingAssistedReplyRepository.mark_approved
    → AuditLogRepository.append (assisted_reply_approved)
```

---

## 5. Handler 禁止清单

| 禁止 | 原因 |
|------|------|
| `from product_persistence.models import ...` | ORM 泄漏 |
| `get_product_session()` in handler | 事务边界在 service |
| 直接 SQL | -repository 封装 |
| persistence 失败时 `_send_reply` | fail-safe |

---

## 6. non-test shop

```text
select_product_gate_config() → disabled
  → PreviewReplyLogService NOT invoked
  → legacy path unchanged
  → no product DB read/write
```

---

## 7. PDD / Channel 隔离

| 组件 | 读 product DB? |
|------|----------------|
| `AutoReplyThread` | ❌ |
| `pdd_message_handler` | ❌ |
| `inbound_enqueue` / `pdd_{shop_id}` | ❌ |
| `SendMessage` | ❌（仅 assisted approve service） |
| `DatabaseManager` (legacy) | ❌ |

---

## 8. 依赖注入（14f 规划）

```text
PreviewReplyLogService(
  reply_log_repo: ReplyLogRepository | None,  # None → in-memory only
  send_decision_repo: SendDecisionRepository | None,
  flags: ProductPersistenceFlags,
)
```

测试注入 `InMemoryReplyLogRepository`；生产 14g 注入 `SqliteReplyLogRepository`。

---

*Integration points · Phase 14e · 2026-06-03*

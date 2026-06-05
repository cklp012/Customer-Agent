# Phase 14p — Test Plan (Future Implementation)

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 测试未编写** |
| 范围 | PendingAssisted · AuditLog · assisted approve/reject · final guard |
| 前置实现 | Phase 14q（schema）· 14r（service）· 14s（final guard） |

---

## 1. 测试原则

| # | 原则 |
|---|------|
| T1 | assisted/auto **未实现前** 本计划 **不跑** |
| T2 | 所有 send 测试 mock SendMessage / `_send_reply` |
| T3 | non-test legacy **不受影响** |
| T4 | Doudian **无 production assisted** |
| T5 | handler **不直接** import assisted repository |
| T6 | final guard blocked → **zero additional send** |

---

## 2. 测试用例

### P1 `pending_schema_fields`

- `pending_assisted_replies` ORM/table 字段与 [phase14p_pending_assisted_schema_detail.md](phase14p_pending_assisted_schema_detail.md) 一致
- indexes 存在
- status enum TEXT 值完整

### P2 `audit_schema_fields`

- `audit_logs` 字段与 [phase14p_auditlog_schema_detail.md](phase14p_auditlog_schema_detail.md) 一致
- append-only · 无 update/delete repository 方法
- indexes 存在

### P3 `create_pending_from_preview`

- assisted mode + flags on
- preview 生成 → ReplyLog + snapshot `ai_preview` + PendingAssisted `pending` + AuditLog `pending_assisted_created`
- **no SendMessage**

### P4 `viewer_cannot_approve`

- actor_role=viewer
- approve API → 403
- SendMessage / `_send_reply` **not called**

### P5 `operator_approve_final_guard_pass`

- actor_role=operator
- pending → approve → final guard pass → outbound once
- status=sent · AuditLog chain complete
- SendMessage **called once**

### P6 `final_guard_blocked_no_send`

- blocked intent / stale message / shop paused / forbidden keyword
- final guard → block
- AuditLog `final_guard_blocked`
- SendMessage **not called**

### P7 `reject_no_send`

- operator reject
- status=rejected · AuditLog `assisted_rejected`
- SendMessage **not called**

### P8 `expired_no_send`

- pending past `expires_at`
- approve → 403
- status=expired · AuditLog `assisted_expired`
- SendMessage **not called**

### P9 `duplicate_approve_idempotent`

- first approve + send → sent
- second approve same id
- SendMessage **not called again**

### P10 `audit_failure_blocks_send`

- strict audit mode
- patch AuditLog create failure before send
- approve path **aborts** · SendMessage **not called**

### P11 `outbound_failure_records_failed`

- final guard pass · outbound raises
- status=failed · AuditLog `outbound_send_failed`
- **no auto retry send**

### P12 `non_test_legacy_unchanged`

- non-test shop + flags on
- legacy `_send_reply` path unchanged
- no pending/audit write on legacy hot path

### P13 `handler_no_assisted_import`

- static scan `Message/handlers/ai_handler.py`
- no `pending_assisted` repository / `audit_log` repository / product ORM direct import

### P14 `doudian_not_enabled`

- Doudian platform + flags on
- no assisted send path
- no pending production write

---

## 3. 测试分层（future）

| 层 | 文件（规划名） |
|----|----------------|
| schema | `test_pending_assisted_schema.py` · `test_auditlog_schema.py` |
| repository | `test_sqlite_pending_assisted_write.py` · `test_sqlite_auditlog_write.py` |
| service | `test_assisted_reply_service.py` |
| guard | `test_assisted_final_guard.py` |
| handler integration | `test_handler_assisted_shadow_write.py` |
| API | `test_assisted_approve_reject_api.py` |

---

## 4. 与现有测试关系

| 现有 | 关系 |
|------|------|
| 14l ReplyLog shadow tests | 保持 green · 不修改 |
| 14n snapshot shadow tests | 保持 green · 不修改 |
| 14o Dashboard read tests | 保持 green · detail 占位不变直至 14q |

---

## 5. 验收命令（future）

```bash
uv run python -m unittest discover -s tests -v
```

**14p：** 无新增测试文件 · 无运行要求。

---

*Phase 14p · planning only · 2026-06-03*

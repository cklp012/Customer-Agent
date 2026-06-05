# Phase 14r — Test Plan (Future Implementation)

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 测试未编写** |
| 范围 | AssistedReplyService · approve/reject/expire · guard · audit · snapshot |
| 前置 | 14s final guard planning · 14t service skeleton |

---

## 1. 测试原则

| # | 原则 |
|---|------|
| T1 | 14r **不编写**测试 · 本计划供 14t+ 使用 |
| T2 | 所有 send 测试 mock SendMessage / `_send_reply` |
| T3 | non-test legacy **不变** |
| T4 | handler **不直接** import assisted repository |
| T5 | Doudian **无** production assisted |
| T6 | approve **不能** bypass final guard |

---

## 2. 测试用例 R1–R15

### R1 `create_pending_success_no_send`

- assisted mode + flags on + allowlisted shop
- `create_pending_from_preview` → pending row + audit `pending_assisted_created`
- SendMessage **not called**

### R2 `create_pending_audit_failure_no_send`

- patch audit append failure · strict mode
- pending rollback or not approvable
- SendMessage **not called**

### R3 `viewer_cannot_approve`

- actor_role=viewer · approve → 403
- SendMessage **not called**

### R4 `operator_approve_guard_pass_sends_once`

- operator approve · guard pass · outbound once
- status=sent · audit chain complete
- SendMessage **called once**

### R5 `final_guard_blocked_no_send`

- blocked intent / paused shop / stale / forbidden keyword
- guard block · audit `final_guard_blocked`
- SendMessage **not called**

### R6 `snapshot_failure_before_send_blocks`

- patch merchant_confirm snapshot failure
- outbound **not called**

### R7 `audit_failure_before_send_blocks`

- patch audit failure before `outbound_send_attempted`
- SendMessage **not called**

### R8 `outbound_failure_marks_failed`

- guard pass · outbound raises
- status=failed · audit `outbound_send_failed`
- **no auto retry**

### R9 `duplicate_approve_no_double_send`

- first approve → sent
- second approve same id → idempotent · SendMessage **not called again**

### R10 `reject_no_send`

- reject → status=rejected · audit `assisted_rejected`
- SendMessage **not called**

### R11 `expire_no_send`

- expired pending · approve → 403
- SendMessage **not called**

### R12 `sent_terminal_state`

- status=sent · approve/reject → invalid_state or already_sent
- **no second outbound**

### R13 `non_test_legacy_unchanged`

- non-test shop · legacy `_send_reply` unchanged
- no pending service on legacy path

### R14 `handler_no_direct_assisted_import`

- static scan handler · no pending/audit repository direct import

### R15 `doudian_not_enabled`

- Doudian + flags · no assisted create/approve/send

---

## 3. 测试分层（future · 14t+）

| 层 | 文件（规划名） |
|----|----------------|
| service unit | `test_assisted_reply_service.py` |
| guard integration | `test_assisted_final_guard_integration.py` |
| audit sequence | `test_assisted_audit_sequence.py` |
| handler boundary | `test_handler_assisted_service_integration.py` |
| idempotency | `test_assisted_approve_idempotency.py` |

---

## 4. 与 14q / 14p 测试关系

| 已有 | 关系 |
|------|------|
| 14q repository tests | 保持 green · mark_status 无 send |
| 14p test plan P1–P14 | 本计划 R1–R15 为 service 层扩展 |

---

## 5. 验收命令（future）

```bash
uv run python -m unittest discover -s tests -v
```

**14r：** 无新增测试 · 无运行要求。

---

*Phase 14r · planning only · 2026-06-03*

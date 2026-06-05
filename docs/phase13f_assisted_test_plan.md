# Phase 13f — Assisted Test Plan（A1–A12）

| 项 | 值 |
|----|-----|
| 类型 | docs only（**14c 实现后执行**） |
| 对齐 | [phase13c_zero_send_test_plan.md](phase13c_zero_send_test_plan.md) Z* · [phase12f_test_implementation_plan.md](phase12f_test_implementation_plan.md) T6 |

---

## 1. 测试分层

| 层 | Phase | 文件（建议） |
|----|-------|--------------|
| Preview regression | 13d/13e ✅ | `test_handler_single_test_shop_preview_gate.py` |
| Assisted unit | 14c | `tests/test_assisted_pending.py` |
| Assisted integration | 14c | `tests/handlers/test_assisted_confirmation_integration.py` |
| AuditLog | 14a/14c | `tests/test_assisted_audit_log.py` |

**Patch 目标（所有发送断言）：** `SendMessage.send_text` · `outbound.send_text` · `AIReplyHandler._send_reply`

---

## 2. 用例矩阵

### A1 — `preview_still_zero_send`

| 项 | 内容 |
|----|------|
| 配置 | `reply_mode=preview`, gate on |
| 断言 | SendMessage **not called** |
| 断言 | `send_status=not_sent_preview` |
| 回归 | 13d Z1 仍绿 |

---

### A2 — `assisted_creates_pending_no_send`

| 项 | 内容 |
|----|------|
| 配置 | `reply_mode=assisted`, gate on, allowed intent |
| 断言 | pending 记录 `awaiting_approval` |
| 断言 | SendMessage **not called** at handle() |
| 断言 | `_send_reply` **not called** |

---

### A3 — `approve_sends_once`

| 项 | 内容 |
|----|------|
| 前置 | A2 pending 存在 |
| 动作 | `approve_assisted_reply` as operator |
| 断言 | SendMessage **called once** |
| 断言 | ReplyLog `send_status=sent` |
| 断言 | 重复 approve → **not** 二次发送 |

---

### A4 — `viewer_cannot_approve`

| 项 | 内容 |
|----|------|
| actor | role=viewer |
| 断言 | 403 / PermissionError |
| 断言 | SendMessage **not called** |

---

### A5 — `paused_shop_cannot_approve`

| 项 | 内容 |
|----|------|
| 前置 | `shop_pause=true` |
| 断言 | approve 拒绝 |
| 断言 | SendMessage **not called** |

---

### A6 — `blocked_intent_cannot_one_click_approve`

| 项 | 内容 |
|----|------|
| 输入 | refund / complaint |
| 断言 | 普通 approve 拒绝 |
| 断言 | `send_mode=human_takeover` |

---

### A7 — `final_guard_reruns_at_confirmation`

| 项 | 内容 |
|----|------|
| Mock | confirm 时 intent 变为 blocked |
| 断言 | approve 后 SendMessage **not called** |
| 断言 | `evaluate_guarded_send` 在 confirm 路径 **called** |

---

### A8 — `stale_pending_cannot_send`

| 项 | 内容 |
|----|------|
| 前置 | pending expired 或 superseded |
| 断言 | approve 拒绝 |
| 断言 | SendMessage **not called** |

---

### A9 — `audit_log_written`

| 项 | 内容 |
|----|------|
| 场景 | approve · reject · reply_mode_changed |
| 断言 | AuditLog 行存在且 `actor_member_id` 正确 |

---

### A10 — `non_test_shop_legacy_unchanged`

| 项 | 内容 |
|----|------|
| 前置 | allowlist 未命中 |
| 断言 | legacy `_send_reply` 仍调用 |
| 回归 | 13d Z2 |

---

### A11 — `no_auto_send`

| 项 | 内容 |
|----|------|
| 配置 | assisted（非 auto） |
| 断言 | 无 `send_mode=auto_send` 路径 |
| 断言 | 无无确认自动 SendMessage |

---

### A12 — `doudian_not_production`

| 项 | 内容 |
|----|------|
| platform | doudian |
| 断言 | 不进入 assisted gate |
| 断言 | 无 pending / 无 assisted approve |

---

## 3. Go/No-Go（进入 14c 实现）

### Go

- A1 + A2 + A3 设计可测
- 发送仅在 confirm command（非 handler AI 阶段）
- AuditLog schema 在 14a 就绪

### No-Go

- assisted handle() 内调用 SendMessage
- viewer 可 approve
- blocked 一键 approve 无 guard

---

*Assisted test plan · Phase 13f · 2026-06-03*

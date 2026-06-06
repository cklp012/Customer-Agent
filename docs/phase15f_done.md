# Phase 15f 完成 — Wire Dry-run Port into AssistedReplyService

| 项 | 内容 |
|----|------|
| 状态 | **DryRunAssistedOutboundPort wired into approve_pending** |
| 日期 | 2026-06-03 |
| 前置 | [phase15e_done.md](phase15e_done.md) · [phase15c_done.md](phase15c_done.md) · [phase15b_done.md](phase15b_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 实现 | `AssistedReplyService.approve_pending` dry-run path |
| live assisted send | **未实现** |
| auto send | **未实现** |
| `dry_run=false` | 返回 **`live_send_not_implemented`** · no SendMessage |
| pending → sent | **否** · status 保持 `pending` |
| idempotency mark_succeeded | **否** · dry-run 后保持 `in_progress` |
| handler / SendMessage / PDD / Doudian outbound | **未调用** |
| flags 默认 | send disabled · dry_run true · allowlist empty |

---

## Dry-run 路径（guard allow 后）

1. AuditLog `assisted_approved` + `final_guard_passed`
2. SendDecisionSnapshot `merchant_confirm`（WRITE_SEND_DECISION on 时）
3. Idempotency acquire `assisted_send:{pending_assisted_id}`
4. `DryRunAssistedOutboundPort.send` · `dry_run=true`
5. AuditLog `assisted_dry_run_would_send`
6. 返回 `status=dry_run_would_send`

---

## 启用条件

`is_assisted_dry_run_outbound_enabled()` = assisted service + **SEND_ENABLED** + **DRY_RUN true** + **WRITE_OUTBOUND_IDEMPOTENCY** + **TEST_SHOP_ID match**

未满足时：send off → `guard_passed_but_send_not_implemented`（14x 行为）

---

## 测试

`tests/test_assisted_reply_service_dry_run_outbound.py`（F1–F18）

---

## 下一步

| Phase | 内容 |
|-------|------|
| **15g** | Assisted dashboard action endpoint **planning only** |
| **15h** | Live PDD AssistedOutboundPort **planning only** |
| **15i** | Live assisted send single test shop **planning only** |

---

*签收：Phase 15f · 2026-06-03*

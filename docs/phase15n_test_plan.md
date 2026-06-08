# Phase 15n — Test Plan (Future)

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 实现 | **未实现** — 15n 不写测试代码 |
| 前置 impl | reconciliation worker · state schema（15q+）· live send（later） |

---

## 1. 测试范围

Future tests 验证：**timeout 不 auto retry** · reconciliation 不 send · duplicate 防护 · audit 完整 · 无 secret 泄漏。

---

## 2. 用例清单

| ID | 用例 | 断言要点 |
|----|------|----------|
| **N1** | `timeout_unknown_no_auto_retry` | port timeout 后 service/task **不**第二次 `port.send` |
| **N2** | `timeout_unknown_moves_manual_review` | pending → `manual_review_required`（或 `send_unknown` 后立即升级） |
| **N3** | `confirmed_sent_updates_idempotency_succeeded` | reconciliation `confirmed_sent` → idempotency `succeeded` |
| **N4** | `confirmed_sent_updates_pending_sent` | pending → `sent` · audit `reconciliation_confirmed_sent` |
| **N5** | `confirmed_not_sent_does_not_auto_retry` | not sent 后 **无** port.send · 无 handler |
| **N6** | `still_unknown_stays_manual_review` | `still_unknown` → pending 保持 manual review |
| **N7** | `duplicate_approve_unknown_no_second_send` | unknown pending 二次 approve → 409/block · no send |
| **N8** | `client_request_replay_does_not_bypass_idempotency` | 15j replay 不 re-acquire outbound key |
| **N9** | `provider_message_id_missing_not_treated_as_not_sent` | 无 id 不映射 failed_before_send |
| **N10** | `failed_before_send_distinct_from_timeout_unknown` | 两种 status / error_code 可区分 |
| **N11** | `reconciliation_task_does_not_import_SendMessage` | task 模块静态检查 |
| **N12** | `reconciliation_task_does_not_import_handler` | 无 `Message.handlers` |
| **N13** | `reconciliation_task_does_not_call_outbound` | runtime mock SendMessage / port.send 未调用 |
| **N14** | `operator_mark_sent_writes_audit` | `operator_marked_sent` audit 行 |
| **N15** | `operator_mark_not_sent_writes_audit` | `operator_marked_not_sent` audit 行 |
| **N16** | `viewer_cannot_manual_review_action` | viewer → 403 |
| **N17** | `retry_requires_new_idempotency_key_future` | 未来 retry 路径新 key · 旧 key terminal |
| **N18** | `no_cookie_token_in_audit` | audit payload 无敏感字段 |
| **N19** | `PDD_queue_name_unchanged` | `pdd_queue_name(id) == f"pdd_{id}"` |
| **N20** | `Doudian_not_enabled` | `platform_id=doudian` live/reconciliation scope 拒绝 |

---

## 3. 静态检查（future impl）

对 reconciliation task / operator route 源文件：

| 禁止出现 |
|----------|
| `SendMessage` |
| `Message.handlers` |
| `outbound_resolver` |
| `Channel.pinduoduo` send hot path import |
| `Channel.doudian` |
| `database.models` / `database.db_manager` |
| `AutoReplyThread` |

---

## 4. Runtime no-send（future）

```text
mock SendMessage.send_text
mock AIReplyHandler._send_reply
mock LivePddAssistedOutboundPort.send (reconciliation path)
run reconciliation task + duplicate approve
assert: no send mocks called
```

---

## 5. 与现有测试关系

| 现有 | 15n |
|------|-----|
| 15c dry-run port tests | 不变 |
| 15m live port skeleton | 不变 · `live_send_not_implemented` |
| 15j action idempotency | N8 扩展 future |
| 本 phase | **0 新测试文件** |

---

*Phase 15n · docs only · 2026-06-03*

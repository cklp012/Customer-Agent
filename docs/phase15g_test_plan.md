# Phase 15g — Test Plan (Future Implementation)

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 前置 | 15i action route skeleton · 15j client_request_id |
| 本 phase | **不写测试代码** |

---

## 1. 测试分层

| 层 | 文件（future） | 范围 |
|----|----------------|------|
| Route | `test_pending_assisted_action_api_skeleton.py` | HTTP · CSRF · RBAC |
| Integration | `test_dashboard_action_assisted_service.py` | route → service |
| Static | existing + action route source | no SendMessage import |

---

## 2. 用例清单

| ID | 名称 | 断言 |
|----|------|------|
| **G1** | `approve_route_requires_auth` | 401 without auth |
| **G2** | `approve_route_requires_csrf` | 403 without csrf |
| **G3** | `viewer_cannot_approve` | 403 viewer |
| **G4** | `operator_can_approve_dry_run` | 200 dry_run_would_send |
| **G5** | `cross_workspace_forbidden` | 403 |
| **G6** | `cross_shop_forbidden` | 403 |
| **G7** | `stale_expected_status_conflict` | 409 |
| **G8** | `duplicate_client_request_same_payload_idempotent` | 200 cached |
| **G9** | `duplicate_client_request_different_payload_conflict` | 409 |
| **G10** | `approve_final_guard_block_no_send` | 422 · SendMessage not called |
| **G11** | `approve_dry_run_would_send_no_live_send` | would_send · live_send_attempted=false |
| **G12** | `approve_dry_run_does_not_mark_sent` | pending stays pending |
| **G13** | `approve_dry_run_does_not_mark_idempotency_succeeded` | no mark_succeeded |
| **G14** | `dry_run_false_live_send_not_implemented` | no SendMessage |
| **G15** | `reject_route_requires_auth_csrf` | 401/403 |
| **G16** | `viewer_cannot_reject` | 403 |
| **G17** | `reject_pending_success_no_send` | status rejected · no outbound |
| **G18** | `reject_terminal_state_no_mutation` | 409 |
| **G19** | `action_audit_written` | dashboard_* + assisted_* audits |
| **G20** | `audit_failure_no_fallback_legacy_send` | no handler send |
| **G21** | `no_handler_direct_send_import` | static route source |
| **G22** | `no_SendMessage_import` | static |
| **G23** | `PDD_queue_name_unchanged` | pdd_{shop_id} |
| **G24** | `Doudian_not_enabled` | no doudian in action routes |
| **G25** | `read_endpoint_still_read_only` | GET only · no POST on read routes |

---

## 3. Mock 要求

| Mock | 用途 |
|------|------|
| `SendMessage.send_text` | assert_not_called |
| `AssistedReplyService` | optional unit isolation |
| CSRF validator | pass/fail injection |

---

## 4. 非目标（15g）

| 项 | 状态 |
|----|------|
| 实现 G1–G25 | ❌ future 15i+ |
| 修改现有 711 tests | ❌ |

---

*Phase 15g · docs only · 2026-06-03*

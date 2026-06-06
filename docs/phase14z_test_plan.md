# Phase 14z — Test Plan (Future Implementation)

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 测试未编写** |
| 前置 | 15c PendingAssisted dashboard read API skeleton |

---

## 1. 测试原则

| # | 原则 |
|---|------|
| Z0 | 14z **不编写**测试 |
| Z0a | 所有 read tests **mock SendMessage** · assert never called |
| Z0b | read path **不执行** evaluate_final_guard |
| Z0c | non-test legacy **remain green** |

---

## 2. Z1–Z17

| ID | 名称 | 要点 |
|----|------|------|
| **Z1** | `list_pending_read_only` | GET only · no POST |
| **Z2** | `list_filters_by_workspace_shop_status` | filter correctness |
| **Z3** | `list_pagination_limit` | page_size max 100 |
| **Z4** | `list_preview_redacts_sensitive_text` | preview length · no full text |
| **Z5** | `detail_returns_full_text_for_operator` | operator full buyer_message |
| **Z6** | `detail_redacts_text_for_viewer` | viewer redacted |
| **Z7** | `cross_workspace_forbidden` | 403 |
| **Z8** | `audit_timeline_ordered_by_created_at` | asc/desc consistent |
| **Z9** | `final_guard_block_reason_visible` | block_code/reason in detail |
| **Z10** | `send_decision_snapshot_visible` | merchant_confirm join |
| **Z11** | `read_dashboard_flag_off_disabled_or_warning` | READ_DASHBOARD=false |
| **Z12** | `read_failure_no_send` | DB fail · no SendMessage |
| **Z13** | `no_audit_write_on_read` | audit count unchanged after GET |
| **Z14** | `no_final_guard_execution_on_read` | evaluate_final_guard not called |
| **Z15** | `no_handler_sendmessage_import` | read service static scan |
| **Z16** | `doudian_not_enabled` | no Doudian read path |
| **Z17** | `legacy_pdd_unaffected` | PDD queue/handler unchanged |

---

## 3. 测试分层（future · 15c）

| 层 | 文件（规划） |
|----|--------------|
| list contract | `test_pending_assisted_dashboard_list.py` |
| detail contract | `test_pending_assisted_dashboard_detail.py` |
| timeline | `test_pending_assisted_audit_timeline_read.py` |
| permissions | `test_pending_assisted_read_permissions.py` |
| failure | `test_pending_assisted_read_failure_policy.py` |
| static no-send | `test_pending_assisted_read_no_send_side_effects.py` |

---

## 4. 与 14x / 14o 关系

| 已有 | 关系 |
|------|------|
| 14o reply-log read tests | pattern for flags · warnings |
| 14x X-tests | write path no-send · read tests separate |
| 14y Y-tests | outbound integration · not read |

---

*Phase 14z · planning only · 2026-06-03*

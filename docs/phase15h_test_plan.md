# Phase 15h — Test Plan (Future Implementation)

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 前置 | 15k live port skeleton · 15i action routes |
| 本 phase | **不写测试代码** |

---

## 1. 测试分层

| 层 | 文件（future） | 范围 |
|----|----------------|------|
| Port unit | `test_live_pdd_assisted_outbound_port.py` | port boundary only |
| Service integration | `test_assisted_reply_service_live_port.py` | service + mock port |
| Static | port source scan | no audit/db imports |

---

## 2. 用例清单

| ID | 名称 | 断言 |
|----|------|------|
| **H1** | `live_pdd_port_not_implemented_in_phase15h` | no LivePdd class in prod path · 15h docs only |
| **H2** | `dry_run_default_no_live_send` | DRY_RUN=true → DryRun port only |
| **H3** | `non_pdd_platform_rejected` | platform_id≠pinduoduo → no send |
| **H4** | `non_allowlisted_shop_no_send` | shop not in allowlist → port not called |
| **H5** | `empty_final_reply_no_send` | validation fail · no platform call |
| **H6** | `missing_buyer_id_no_send` | validation fail |
| **H7** | `missing_shop_id_no_send` | validation fail |
| **H8** | `port_does_not_run_final_guard` | guard mock never in port |
| **H9** | `port_does_not_write_audit` | audit repo not called from port |
| **H10** | `port_does_not_write_db` | no persistence in port |
| **H11** | `port_does_not_change_pending_status` | pending repo not in port |
| **H12** | `queue_name_pdd_shop_id_unchanged` | still `pdd_{shop_id}` |
| **H13** | `pdd_legacy_handler_unchanged` | handler tests pass · no assisted hook |
| **H14** | `success_result_maps_provider_message_id` | sent → provider_message_id populated |
| **H15** | `platform_rejected_maps_error` | rejected_by_platform + error_code |
| **H16** | `timeout_maps_unknown_no_retry` | timeout_unknown · no auto retry |
| **H17** | `db_failure_no_legacy_fallback` | local persist fail · no SendMessage |
| **H18** | `duplicate_unknown_manual_review` | unknown pending · duplicate approve blocked |
| **H19** | `Doudian_not_enabled` | doudian platform rejected |
| **H20** | `no_auto_send` | no path from handler/auto to live port |

---

## 3. Mock 要求

| Mock | 用途 |
|------|------|
| PDD send primitive | success / fail / timeout injection |
| `SendMessage.send_text` | assert_not_called from port unit tests |
| Audit / pending repos | assert_not_called from port |

---

## 4. 非目标（15h）

| 项 | 状态 |
|----|------|
| 实现 H1–H20 | ❌ future 15k+ |
| 修改现有 test suite for live send | ❌ |

---

*Phase 15h · docs only · 2026-06-03*

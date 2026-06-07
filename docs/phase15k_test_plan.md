# Phase 15k — Test Plan (Future Implementation)

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 前置 | 15m live port skeleton impl |
| 本 phase | **不写测试代码** |

---

## 1. 测试分层

| 层 | 文件（future） | 范围 |
|----|----------------|------|
| Port unit | `test_live_pdd_assisted_outbound_port.py` | validation · mapping |
| Service integration | `test_assisted_reply_service_live_pdd_port.py` | flags · allowlist |
| Static | port + route source scan | no forbidden imports |

---

## 2. 用例清单

| ID | 名称 | 断言 |
|----|------|------|
| **K1** | `live_pdd_port_not_implemented_in_phase15k` | no LivePdd class in prod · 15k docs only |
| **K2** | `future_class_implements_AssistedOutboundPort` | isinstance check |
| **K3** | `uses_AssistedOutboundRequest_and_Result` | no parallel schema |
| **K4** | `rejects_non_pdd_platform` | validation_failed |
| **K5** | `rejects_missing_shop_id` | validation_failed · no send |
| **K6** | `rejects_missing_buyer_id` | validation_failed |
| **K7** | `rejects_empty_final_reply` | validation_failed |
| **K8** | `rejects_missing_idempotency_key` | validation_failed |
| **K9** | `success_maps_sent_result` | sent · provider_message_id |
| **K10** | `rejected_maps_rejected_by_platform` | error_code set |
| **K11** | `timeout_maps_timeout_unknown_no_retry` | no auto retry |
| **K12** | `exception_before_send_maps_unavailable` | no sent |
| **K13** | `exception_after_unknown_maps_unknown` | reconciliation |
| **K14** | `provider_message_id_not_faked` | null unless platform returns |
| **K15** | `no_cookie_token_in_error` | safe error_message |
| **K16** | `no_SendMessage_import_in_dashboard_route` | static route |
| **K17** | `no_handler_import` | static port |
| **K18** | `no_Doudian_live_send` | doudian rejected at service |
| **K19** | `pdd_queue_name_unchanged` | `pdd_{shop_id}` |
| **K20** | `no_auto_send` | no handler→port path |
| **K21** | `no_fallback_legacy_send` | SendMessage not called on failure |
| **K22** | `dry_run_true_no_live_send` | DryRun port only |
| **K23** | `non_allowlisted_shop_no_send` | live port not called |
| **K24** | `flags_default_safe` | all send flags off by default |

---

## 3. Mock 要求

| Mock | 用途 |
|------|------|
| PDD send primitive | success / reject / timeout injection |
| `SendMessage.send_text` | assert_not_called from port unit |
| Legacy handler send | assert_not_called on port failure |

---

## 4. 非目标（15k）

| 项 | 状态 |
|----|------|
| 实现 K1–K24 | ❌ future 15m+ |
| 修改 existing 759 tests for live | ❌ |

---

*Phase 15k · docs only · 2026-06-03*

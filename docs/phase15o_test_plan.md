# Phase 15o — Test Plan

| 项 | 内容 |
|----|------|
| 类型 | **smoke test plan** |
| 实现 | `tests/test_phase15o_local_dashboard_action_smoke.py` + 既有 15i/15j/15l 测试 |

---

## 用例清单

| ID | 用例 | 实现位置 |
|----|------|----------|
| **O1** | `default_flags_routes_off` | phase15o smoke · registration L4 |
| **O2** | `local_dry_run_flags_routes_on` | phase15o smoke |
| **O3** | `approve_requires_csrf` | phase15o · 15i I1 |
| **O4** | `approve_requires_confirm_checkbox` | phase15o · 15i I2 |
| **O5** | `approve_requires_client_request_id` | phase15o · 15j |
| **O6** | `approve_dry_run_expected_true` | phase15o · 15i I5 inverse |
| **O7** | `approve_dry_run_response_no_live_send` | phase15o smoke |
| **O8** | `approve_replay_same_client_request_id` | phase15o smoke · 15j |
| **O9** | `approve_conflict_different_payload` | phase15o smoke · 15j |
| **O10** | `reject_no_send` | phase15o smoke |
| **O11** | `reject_replay_same_client_request_id` | phase15o smoke · 15j |
| **O12** | `no_SendMessage_called` | phase15o runtime mock |
| **O13** | `no_PDD_outbound_called` | static · no Channel import |
| **O14** | `no_Doudian_called` | static |
| **O15** | `pdd_queue_name_unchanged` | phase15o |
| **O16** | `rollback_flags_disable_routes` | phase15o |
| **O17** | `logs_no_secret_leak` | response body scan |
| **O18** | `read_dashboard_unchanged` | bootstrap 不含 read register |

---

## 运行

```powershell
uv run python -m unittest tests.test_phase15o_local_dashboard_action_smoke -v
uv run python -m unittest discover -s tests -v
```

---

## 不在 O 范围

| 排除 |
|------|
| 真实 Flask HTTP server 长期运行 |
| 真实 PDD session / MMS |
| live send · retry · reconciliation worker |

---

*Phase 15o · 2026-06-03*

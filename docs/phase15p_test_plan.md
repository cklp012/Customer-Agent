# Phase 15p — Test Plan (Future)

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 实现 | **未实现** — 15p 不写测试代码 |
| 前置 impl | OutboundPortSelector skeleton（15s+）· live wire（later） |

---

## 用例清单

| ID | 用例 | 断言要点 |
|----|------|----------|
| **P1** | `default_selects_dry_run_port` | 无 flags · `DryRunAssistedOutboundPort` |
| **P2** | `dry_run_true_selects_dry_run_port` | `DRY_RUN=true` → never LivePdd |
| **P3** | `live_flags_off_no_live_port` | `SEND_ENABLED=false` → no LivePdd |
| **P4** | `live_flags_on_but_no_allowlist_no_send` | empty/mismatch shop → no live |
| **P5** | `non_pdd_platform_no_live_port` | platform != pinduoduo |
| **P6** | `doudian_no_live_port` | `platform_id=doudian` |
| **P7** | `final_guard_block_no_port_selected` | guard false → port.send not called |
| **P8** | `idempotency_not_acquired_no_port_selected` | acquire fail → no port |
| **P9** | `manual_approve_required_for_live_candidate` | auto path → no live |
| **P10** | `auto_mode_no_live_port` | AutoReply/handler → no live |
| **P11** | `all_live_gates_pass_selects_live_port_future` | all gates → LivePdd type（future impl） |
| **P12** | `live_port_not_called_in_phase15p` | 当前代码无 selector · LivePdd unwired |
| **P13** | `route_does_not_import_ports` | route 源文件静态检查 |
| **P14** | `service_boundary_no_SendMessage` | service/selector 无 SendMessage |
| **P15** | `selector_no_legacy_fallback` | port exception → no SendMessage mock call |
| **P16** | `timeout_unknown_no_retry` | unknown → no second select/send |
| **P17** | `kill_switch_forces_dry_run` | SEND_ENABLED off → DryRun |
| **P18** | `pdd_queue_name_unchanged` | `pdd_shop123` |
| **P19** | `no_Doudian_live_send` | Doudian never LivePdd |
| **P20** | `no_auto_send` | no auto approve live path |

---

## 静态检查（future impl）

| 文件 | 禁止 |
|------|------|
| `pending_assisted_action_routes.py` | `LivePddAssistedOutboundPort` · `DryRunAssistedOutboundPort` |
| `outbound_port_selector.py`（future） | `SendMessage` · `Message.handlers` · `outbound_resolver` |
| selector | `Channel.pinduoduo` hot send path |

---

## 与现有测试

| 现有 | 关系 |
|------|------|
| 15m live port skeleton | P12 · unwired |
| 15f dry-run service | P1 default |
| 15o smoke | unchanged |
| 本 phase | **0 新测试文件** |

---

*Phase 15p · docs only · 2026-06-03*

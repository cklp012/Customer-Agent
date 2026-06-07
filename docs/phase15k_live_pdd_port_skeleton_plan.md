# Phase 15k — Live PDD Port Skeleton Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不写代码** |
| 日期 | 2026-06-03 |
| 前置 | [phase15h_done.md](phase15h_done.md) · [phase15j_done.md](phase15j_done.md) · [phase15c_done.md](phase15c_done.md) · [phase15f_done.md](phase15f_done.md) |

---

## 1. Phase 15k 定位

| 项 | 结论 |
|----|------|
| 交付 | **仅文档** |
| Python 代码 | **未写** |
| `LivePddAssistedOutboundPort` class | **未实现** |
| live assisted send | **未实现** |
| auto send | **未实现** |
| handler / SendMessage / outbound resolver | **未改** |
| PDD / Doudian 热路径 | **未改** |
| action routes app.py 注册 | **未做** |
| assisted / send flags | **默认 off** |

**当前系统仍只支持 dry-run assisted outbound**（15c `DryRunAssistedOutboundPort` + 15f service wire + 15i/15j action routes dry-run only）。

Phase 15k 规划未来 **`LivePddAssistedOutboundPort` skeleton** 的 class 位置、interface 复用、PDD primitive 边界、result mapping、flags — **本 phase 不写代码、不发送**。

**与 15h 关系：** 15h = live port **integration planning**；15k = **skeleton implementation planning**（为 15m impl 留清晰边界）。

---

## 2. 已实现基础（unchanged）

| 组件 | Phase | 状态 |
|------|-------|------|
| `AssistedOutboundPort` + `DryRunAssistedOutboundPort` | 15c | ✅ |
| `AssistedReplyService.approve_pending` dry-run | 15f | ✅ `dry_run_would_send` |
| Dashboard action routes | 15i | ✅ dry-run · not in app.py |
| Action `client_request_id` idempotency | 15j | ✅ behind flag |
| `LivePddAssistedOutboundPort` | — | ❌ **未实现** |

---

## 3. 核心原则（签收）

| # | 原则 |
|---|------|
| **K1** | 未来 `LivePddAssistedOutboundPort` 是 **`AssistedOutboundPort` 的实现之一** |
| **K2** | **`AssistedReplyService` 仍负责 workflow** — permission（route 层）· final guard · audit · snapshot · outbound idempotency · pending 状态 |
| **K3** | **`LivePddAssistedOutboundPort` 只负责 platform send attempt** |
| **K4** | Port **不决定**是否允许发送 |
| **K5** | Port **不写 DB** · **不写 audit** · **不改 pending** |
| **K6** | Port **不 fallback legacy send** |
| **K7** | Port **不改变 PDD hot path** · queue **`pdd_{shop_id}`** |
| **K8** | **No auto send** · **Doudian live not enabled** |

---

## 4. 未来 skeleton 拓扑

```text
Dashboard POST approve (15l+ register · future)
    → route: CSRF / RBAC / action idempotency (15j)
    → AssistedReplyService.approve_pending
        → final guard
        → audit / snapshot
        → outbound idempotency acquire
        → AssistedOutboundPort.send
            ├── DryRunAssistedOutboundPort (15c · default)
            └── LivePddAssistedOutboundPort (15m+ · explicit DI · flags)
                    → PddSendPrimitive (thin · future)
                    → single send attempt · no retry loop
        → service: pending / outbound idempotency / audit from result
    → JSON response · no handler bypass
```

---

## 5. 文档清单

| 文档 | 内容 |
|------|------|
| [phase15k_class_location_and_interface.md](phase15k_class_location_and_interface.md) | Class · interface |
| [phase15k_pdd_send_primitive_boundary.md](phase15k_pdd_send_primitive_boundary.md) | PDD primitive |
| [phase15k_result_mapping_contract.md](phase15k_result_mapping_contract.md) | Result mapping |
| [phase15k_safety_flags_and_allowlist.md](phase15k_safety_flags_and_allowlist.md) | Flags · allowlist |
| [phase15k_no_fallback_and_hot_path_boundary.md](phase15k_no_fallback_and_hot_path_boundary.md) | No fallback · hot path |
| [phase15k_test_plan.md](phase15k_test_plan.md) | K1–K24 |

---

## 6. 下一步（不在 15k 实现）

| Phase | 内容 |
|-------|------|
| **15l** | Register action routes for local dashboard **behind flags** |
| **15m** | `LivePddAssistedOutboundPort` **skeleton implementation** behind flags |
| **15n** | Live send **reconciliation planning** |

---

*Phase 15k · docs only · 2026-06-03*

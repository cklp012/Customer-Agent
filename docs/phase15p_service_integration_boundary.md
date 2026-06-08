# Phase 15p — Service Integration Boundary

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15e_assisted_service_live_sequence.md](phase15e_assisted_service_live_sequence.md) · [phase15k_class_location_and_interface.md](phase15k_class_location_and_interface.md) |

---

## 1. 职责矩阵

| 组件 | 拥有 |
|------|------|
| **Dashboard route** | auth/CSRF · scope · action idempotency · request parse · response map · **no direct send** |
| **AssistedReplyService** | pending load/status · final guard invoke · audit · SendDecisionSnapshot · outbound idempotency · **port selection** · post-result status update |
| **FinalGuard** (`evaluate_final_guard`) | pure send permission decision · block codes |
| **OutboundPortSelector**（future） | read-only gate snapshot → return port instance |
| **AssistedOutboundPort** impl | **one** platform send attempt · result mapping |
| **Repositories** | persistence only · no send |
| **Live PDD primitive**（future） | thin MMS/send read-write · isolated from handler |

---

## 2. 当前 vs 未来

| 项 | 当前（15f–15o） | 未来（post-15s） |
|----|----------------|-----------------|
| `_outbound_port_instance()` | DI or `DryRunAssistedOutboundPort()` | DI or **selector** |
| Route imports ports | ❌ none | ❌ none |
| Service imports `LivePddAssistedOutboundPort` | ❌ | ✅ via selector only |
| Live send | ❌ | gated · later phase |

---

## 3. Route 边界

| 规则 |
|------|
| `pending_assisted_action_routes.py` **不** import `LivePddAssistedOutboundPort` |
| **不** import `DryRunAssistedOutboundPort` |
| **不** import `SendMessage` · `Message.handlers` · `outbound_resolver` |
| 只调用 `AssistedReplyService.approve_pending` / `reject_pending` |
| `dry_run_expected=true` enforced at route（15i）— route **不**选择 live port |

---

## 4. Service 边界

| 规则 |
|------|
| Service 在 idempotency acquired **之后** 调用 selector |
| Selector 输入：flags snapshot · pending row · guard result · idempotency state · actor context |
| Selector **不**重新运行 final guard（只消费 `final_guard_allowed`） |
| Selector **不** acquire idempotency |
| Port 返回后 service 负责 pending/idempotency/audit 更新 |
| `timeout_unknown` → reconciliation path（15n）· **no port retry** |

---

## 5. Selector / factory 边界（future · 15s skeleton）

```text
OutboundPortSelector.select(context) -> AssistedOutboundPort
    - reads flags helpers (no env side effects)
    - no SendMessage import
    - no Channel.pinduoduo hot path import
    - returns DryRunAssistedOutboundPort | LivePddAssistedOutboundPort instance
    - never returns legacy resolver wrapper
```

| Selector 禁止 |
|---------------|
| 调用 SendMessage |
| 写 DB |
| 修改 pending |
| 决定 guard（只读 guard 结果） |
| fallback legacy on exception |

---

## 6. Port 边界（unchanged · 15k/15m）

| Port 负责 | Port 不负责 |
|-----------|-------------|
| validation · one send attempt · result map | guard · audit · idempotency · pending · allowlist policy |

---

## 7. Live primitive 隔离（future）

| 项 | 规划 |
|----|------|
| 位置 | thin module under `product_persistence` or `Channel` adapter — **not** handler |
| 调用方 | only `LivePddAssistedOutboundPort` |
| 禁止 | AutoReplyThread · AIReplyHandler · queue consumer 直接调用 |

---

*Phase 15p · docs only · 2026-06-03*

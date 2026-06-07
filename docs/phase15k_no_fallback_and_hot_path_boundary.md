# Phase 15k — No Fallback and Hot Path Boundary

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15h_failure_rollback_policy.md](phase15h_failure_rollback_policy.md) · [phase15k_live_pdd_port_skeleton_plan.md](phase15k_live_pdd_port_skeleton_plan.md) |

---

## 1. No fallback legacy send

| 场景 | 禁止 |
|------|------|
| Live port failure | ❌ fallback handler `SendMessage` |
| timeout_unknown | ❌ auto-retry via legacy |
| outbound idempotency stuck | ❌ bypass via handler |
| audit failure | ❌ silent legacy send |
| action idempotency conflict | ❌ double-send via legacy |

**任何 failure path 均不得触发 legacy auto-reply send。**

---

## 2. Live port failure 边界

| 规则 |
|------|
| Port failure **不得**调用 handler SendMessage |
| Port failure **不得**调用 legacy auto reply |
| Port failure **不得**绕过 outbound idempotency |
| Port failure **不得**绕过 action idempotency (15j) |
| Service 记录 audit + reconciliation · **不自动重发** |

---

## 3. app.py / routes（15k 边界）

| 项 | 15k |
|----|-----|
| Register action routes in app.py | ❌ **not in 15k** |
| Register live send routes | ❌ **not in 15k** |
| Live port implementation | ❌ **not in 15k** |

Action routes remain **unregistered** until **15l** (behind flags).

---

## 4. PDD hot path unchanged

| 组件 | 状态 |
|------|------|
| Queue name | **`pdd_{shop_id}`** · **不变** |
| `AutoReplyThread` | **unchanged** |
| `pdd_message_handler` | **unchanged** |
| `MessageConsumer` | **unchanged** |
| Default `channel_factory` / legacy path | **unchanged** |
| `SendMessage` default behavior | **unchanged** |

Assisted live send 与 legacy **并行隔离** — 不改变默认 env 下 PDD 行为。

---

## 5. Rollback procedure

| 动作 | 效果 |
|------|------|
| `PRODUCT_ASSISTED_SEND_ENABLED=false` | master off |
| `PRODUCT_ASSISTED_SEND_DRY_RUN=true` | force dry-run |
| clear `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID` | no allowlist |
| disable live port DI | service uses DryRun only |
| action routes unregistered / flag off | no dashboard live approve |
| read-only dashboard (15d) | GET unchanged |
| legacy PDD auto-reply | **still works** |

---

## 6. 禁止清单

| 禁止 |
|------|
| 15k 实现 live port |
| 15k 改 SendMessage |
| 15k 改 handler |
| 15k 改 queue naming |
| 15k 注册 app.py live routes |
| fallback legacy on any assisted failure |

---

*Phase 15k · docs only · 2026-06-03*

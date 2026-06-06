# Phase 15h — Failure and Rollback Policy

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15g_failure_rollback_policy.md](phase15g_failure_rollback_policy.md) · [phase15e_failure_rollback_and_reconciliation.md](phase15e_failure_rollback_and_reconciliation.md) |

---

## 1. Pre-port failures → port not called

| 场景 | 行为 |
|------|------|
| final guard block | port **不会被调用** · no send |
| audit failure (pre-mutation) | port **不会被调用** |
| snapshot failure | port **不会被调用** |
| idempotency acquire failure | port **不会被调用** |
| allowlist / flag gate fail | port **不会被调用** |
| daily cap exceeded | port **不会被调用** |

---

## 2. Port-level failures → no-send or known failure

| 场景 | 行为 |
|------|------|
| port unavailable | `unavailable` · no-send |
| port validation failure (empty reply / missing buyer) | `failed` · no-send |
| PDD send explicit failure | pending → **failed** · manual review |
| timeout | **unknown** · reconciliation · **不自动重发** |
| platform rejected | pending failed · audit |

---

## 3. Post-port failures

| 场景 | 行为 |
|------|------|
| platform success · local DB update failure | **danger state** · reconciliation · **不自动重发** |
| duplicate approve | idempotency → **no double-send** |
| DB failure mid-update | **no fallback legacy send** |

---

## 4. No fallback legacy send

| 场景 | 禁止 |
|------|------|
| port failure | ❌ fallback handler SendMessage |
| timeout unknown | ❌ auto-retry via legacy |
| audit failure | ❌ silent legacy send |
| idempotency stuck | ❌ bypass via handler |

**任何 failure path 均不得触发 legacy auto-reply send。**

---

## 5. Rollback procedure

紧急关闭 live assisted send **不改变 PDD legacy**：

| 动作 | 效果 |
|------|------|
| `PRODUCT_ASSISTED_SEND_ENABLED=false` | master off · no live · no dry-run outbound |
| `PRODUCT_ASSISTED_SEND_DRY_RUN=true` | force dry-run if re-enabled |
| clear `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID` | no allowlist match |
| disable live port DI | service uses DryRun only |
| keep dashboard read-only (15d) | GET unchanged |
| keep dry-run service path | review logs only |
| PDD AutoReply / handler / queue | **unchanged** · `pdd_{shop_id}` |

---

## 6. Rollback 验证清单

| # | Check |
|---|-------|
| 1 | Legacy auto-reply still works on test shop |
| 2 | No assisted live sends after rollback |
| 3 | Pending unknown items flagged for manual review |
| 4 | Idempotency in_progress items documented |
| 5 | Audit trail complete |

---

*Phase 15h · docs only · 2026-06-03*

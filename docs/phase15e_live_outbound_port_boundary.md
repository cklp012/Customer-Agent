# Phase 15e — Live Outbound Port Boundary

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15c_done.md](phase15c_done.md) · [phase15a_outbound_contract.md](phase15a_outbound_contract.md) |

---

## 1. Interface 稳定性

| 项 | 结论 |
|----|------|
| `AssistedOutboundPort` | **保持稳定** · 15c 已定义 |
| `AssistedOutboundRequest` / `AssistedOutboundResult` | **复用 15c** · live 不新增 parallel contract |
| `DryRunAssistedOutboundPort` | **继续作为默认实现** |

---

## 2. 实现分层（future）

```text
AssistedReplyService
    → AssistedOutboundPort (interface)
        ├── DryRunAssistedOutboundPort (15c · default · flags/on)
        └── LivePddAssistedOutboundPort (future · 15h planning · explicit inject)
                → thin adapter
                → unified outbound resolver OR PDD channel adapter
                → enqueue / SendMessage path (existing · unchanged hot path)
                → queue: pdd_{shop_id}
```

---

## 3. 职责边界

| 职责 | AssistedReplyService | Live outbound port |
|------|---------------------|-------------------|
| final guard | ✅ evaluate | ❌ |
| merchant policy | ✅ validate context | ❌ |
| audit append | ✅ | ❌ |
| idempotency lock | ✅ acquire/mark | ❌ |
| SendDecision snapshot | ✅ | ❌ |
| platform send | ❌ | ✅ |
| `provider_message_id` | ❌ consume | ✅ return |
| `platform_status` / errors | ❌ consume | ✅ return |

**AssistedReplyService 不得 import legacy `SendMessage`。** 仅 live port 封装平台 outbound。

---

## 4. LivePddAssistedOutboundPort（future · 15h）

| 项 | 规划 |
|----|------|
| 平台 | **PDD only** · production first |
| Queue | **`pdd_{shop_id}`** · 不变 |
| Doudian live | **不在本阶段启用** |
| Input | `AssistedOutboundRequest` · `dry_run=false` for live |
| Output | `AssistedOutboundResult` · must populate `provider_message_id` / `platform_status` on success |
| Errors | `error_code` / `error_message` · machine + human readable |
| Timeout | **unknown outcome** · return retriable/timeout code · service 进入 reconciliation · **不自动重发** |

---

## 5. dry_run port 升级路径

| Phase | Port |
|-------|------|
| 15c | `DryRunAssistedOutboundPort` implemented |
| 15f | Wire dry-run into `AssistedReplyService` behind flags |
| 15h | `LivePddAssistedOutboundPort` planning + later impl |
| live rollout | DI: service receives port factory · `DRY_RUN=true` → DryRun · `DRY_RUN=false` + allowlist → LivePdd |

**Never** silently upgrade DryRun to live without explicit flags + allowlist + port selection.

---

## 6. 禁止

| 禁止项 | 原因 |
|--------|------|
| Service → SendMessage direct | bypass guard/audit/idempotency |
| Handler → AssistedOutboundPort | wrong ownership |
| Dashboard read → port | read-only |
| Fallback legacy send on port failure | E7 no fallback |
| Doudian live in 15e–15h PDD rollout | production not enabled |

---

*Phase 15e · docs only · 2026-06-03*

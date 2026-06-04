# Phase 11c 完成 — Doudian Outbound Resolver Contract（Route B）

| 项 | 内容 |
|----|------|
| 状态 | **Route B 已实现**（resolver 契约测试） |
| 日期 | 2026-06-03 |
| 规划 SSOT | [phase11c_plan.md](phase11c_plan.md) |
| 前置 | [phase11b_done.md](phase11b_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 类型 | **仅测试** — `resolve_outbound` + `channel_outbound_registry` 抖店路径 |
| 生产代码变更 | **无** |
| Handler 默认 | **未改**；`USE_UNIFIED_OUTBOUND_RESOLVER` **默认仍 false** |
| `DoudianMockChannel` | **未改**（auto-register → **11d**） |
| PDD 生产发送 | **不变**（`resolve_pinduoduo_outbound` / legacy） |

---

## 新增测试

**文件：** `tests/test_doudian_outbound_resolver_contract.py`

| ID | 用例 | 说明 |
|----|------|------|
| R1 | `TestDoudianInferPlatform` | `metadata.platform=doudian`；Context `channel_type` 为 `"doudian"` 或 `PlatformType.DOUDIAN` |
| R2 | `test_r2_registry_resolves_same_instance` | register → `resolve_outbound` 返回同一 `DoudianMockOutbound` |
| R3 | `test_r3_metadata_outbound_priority_over_registry` | `metadata["outbound"]` 优先于 registry |
| R4 | `test_r4_shop_account_mismatch_returns_none` | shop/user 不匹配 → `None` |
| R5 | `test_r5_unregistered_doudian_no_pdd_fallback` | 未注册 → `None`；`resolve_pinduoduo_outbound` **未调用** |
| R6 | `test_r6_pinduoduo_still_delegates_to_legacy_resolver` | `platform=pinduoduo` 仍委托 PDD resolver |
| R7 | `test_r7_no_registry_does_not_auto_create_doudian_outbound` | fixture Context + metadata，无 registry → `None`（对齐 Demo 行为） |

**隔离：** 每类 `tearDown` → `channel_outbound_registry.clear()`；不设置 `USE_UNIFIED_OUTBOUND_RESOLVER`；不经过 handler 发送。

---

## 生产默认与 PDD 保护

- **未修改** `unified_outbound_flags.py`、`ai_handler.py`、`keyword_handler.py`、`outbound_resolver.py`、`doudian_channel.py`、`Channel/pinduoduo/**`。
- 测试 **直接调用** `resolve_outbound`，不依赖 unified resolver flag。
- R5/R6 证明：抖店未注册 **不回落** PDD；PDD 平台仍 **patch 委托** `resolve_pinduoduo_outbound`。

---

## 后续

| Phase | 内容 |
|-------|------|
| **11d** | outbound auto-registration **规划**（docs） — [phase11d_plan.md](phase11d_plan.md) |
| **11e** | Route C 实现 + lifecycle tests；可选 handler 联调 → 11f |

---

*签收：Phase 11c Route B · 2026-06-03*

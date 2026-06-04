# Phase 11e 完成 — DoudianMockChannel Outbound Auto-Registration

| 项 | 内容 |
|----|------|
| 状态 | **Route C 已实现** |
| 日期 | 2026-06-03 |
| 规划 SSOT | [phase11e_plan.md](phase11e_plan.md) |
| 前置 | [phase11d_done.md](phase11d_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| `DoudianMockChannel.start_account` | 创建 outbound 后 **自动 register** 到 `channel_outbound_registry` |
| `DoudianMockChannel.stop_account` | **始终 unregister** 传入 shop/account；匹配时清内部状态 |
| `reconnect` | stop+start → registry 重注册 |
| `resolve_outbound` | channel start 后 **无需手动 register** 即可命中 |
| stop 后 | `resolve_outbound` **不命中** |
| PDD / handlers / flags / AutoReply | **未改** |
| 真实 API / login / WS | **未接** |

---

## 新增测试

**文件：** `tests/test_doudian_channel_outbound_lifecycle.py`

| ID | 用例 |
|----|------|
| L1 | start 注册 outbound |
| L2 | stop 注销 outbound |
| L3 | start → stop → start 重注册 |
| L4 | resolve_outbound 命中（无手动 register） |
| L5 | stop 后 resolve_outbound 不命中 |
| L6 | PDD key / resolver 不受影响 |
| + | stop 传入 key 语义；reconnect 重注册 |

**11c 保留：** `tests/test_doudian_outbound_resolver_contract.py` 手动 register 契约锚点。

---

## 后续

| Phase | 内容 |
|-------|------|
| **11f** ✅ | handler unified outbound 测试边界规划 — [phase11f_done.md](phase11f_done.md) |
| **11g** | Route C：`test_handler_doudian_unified_outbound.py` |

---

*签收：Phase 11e Route C · 2026-06-03*

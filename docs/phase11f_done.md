# Phase 11f 完成 — Handler Unified Outbound Path（规划）

| 项 | 内容 |
|----|------|
| 状态 | **纯文档规划已完成**（Route A+B）；**Route C 测试实现** → **11g** |
| 日期 | 2026-06-03 |
| 规划 SSOT | [phase11f_plan.md](phase11f_plan.md) |
| 前置 | [phase11e_done.md](phase11e_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 类型 | **仅文档** — handler → unified resolver → Doudian mock outbound 测试边界 |
| 代码变更 | **无** |
| Handler 默认 | **未改**；`USE_UNIFIED_OUTBOUND_RESOLVER` **默认仍 false** |
| Consumer / AutoReply | **不在范围** |
| PDD 生产发送 | **不变** |

---

## 核心结论

- Handler 已在 flag on 时调用 `resolve_outbound`；缺 **doudian** 专用 handler 联调测试。
- 测试需 metadata：`platform=doudian` + `shop_id` / `user_id` / `from_uid`。
- **不需要** Consumer；**不需要** channel start（可选手动 register 或 11e lifecycle）。
- **最小路径：** `AIReplyHandler._send_reply`；Keyword transfer **可选**。
- **11f = 规划**；**11g = `test_handler_doudian_unified_outbound.py`**。

---

## 后续

| Phase | 内容 |
|-------|------|
| **11g** ✅ | Route C — [phase11g_done.md](phase11g_done.md) |
| **11h（可选）** | handler fallback / no-registry safety 规划 |

---

*签收：Phase 11f 规划 · 2026-06-03 · docs only*

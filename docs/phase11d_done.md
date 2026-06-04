# Phase 11d 完成 — DoudianMockChannel Outbound Auto-Registration（规划）

| 项 | 内容 |
|----|------|
| 状态 | **纯文档规划已完成**（Route A+B）；**Route C 实现** → **11e** |
| 日期 | 2026-06-03 |
| 规划 SSOT | [phase11d_plan.md](phase11d_plan.md) |
| 前置 | [phase11c_done.md](phase11c_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 类型 | **仅文档** — lifecycle + registry 边界 |
| 代码变更 | **无** |
| `DoudianMockChannel` | **11d 未改**；register/unregister → **11e** |
| Flags | **不改**默认值 |
| PDD / handler 默认 | **不变** |

---

## 核心结论

- `start_account` **应**在 11e 注册 `DoudianMockOutbound` 到 `channel_outbound_registry`（key：`doudian:{shop}:{account}`）。
- `stop_account` **应** unregister（仿 `PinduoduoChannel` → `AccountOutboundRegistry`）。
- **buyer_id 不参与** registry；出站为 **account-level**。
- **不影响** PDD `AccountOutboundRegistry` 与 unified resolver **默认**行为。
- **11d = 规划**；**11e = 实现 + lifecycle tests** 更安全。

---

## 后续

| Phase | 内容 |
|-------|------|
| **11e** ✅ | Route C：`doudian_channel.py` + lifecycle tests — [phase11e_done.md](phase11e_done.md) |
| **11f（可选）** | handler + unified flag 抖店联调测试 |

---

*签收：Phase 11d 规划 · 2026-06-03 · docs only*

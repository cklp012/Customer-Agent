# Phase 11a 完成 — Flag-Gated Doudian Registry / Factory Boundary（规划）

| 项 | 内容 |
|----|------|
| 状态 | **纯文档规划已完成**（Route A） |
| 日期 | 2026-06-03 |
| 规划 SSOT | [phase11a_plan.md](phase11a_plan.md) |
| 前置 | [phase10m_done.md](phase10m_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 类型 | **仅文档** — registry/factory 边界 SSOT |
| 代码变更 | **无** |
| 推荐路线 | **Route A**（11a 文档）→ **11b Route C**（实现） |
| 禁止路线 | **Route E**（默认注册 Doudian） |

---

## 核心结论

| 主题 | 结论 |
|------|------|
| ChannelRegistry | Doudian **应** 进入，但仅 **`USE_DOUDIAN_CHANNEL_REGISTRATION=true`**（11b 实现；**默认 false**） |
| `register_doudian_channel()` | **11b 新增**（仿 Demo） |
| `DoudianMockChannel` | **11b 新增**（mock `BaseChannel`，非真实 WS） |
| `create_auto_reply_runtime_channel` | **继续仅 PINDUODUO**（9d 不变） |
| AutoReplyThread | **默认不** 创建 Doudian |
| PDD 生产 | **完全不变**；`pdd_{shop_id}` 不变 |
| 真实 API | **不接** |

---

## 后续

| Phase | 内容 |
|-------|------|
| **11b** | [phase11a_plan.md §13](phase11a_plan.md) — flag + `register_doudian_channel` + `DoudianMockChannel` + 测试 |
| **12+** | Route D：AutoReply 按 `channel_name`（独立 flag，非本阶段） |

---

*签收：Phase 11a · 2026-06-03 · docs only*

# Phase 11b 规划 — Flag-Gated Doudian Mock Registration

| 项 | 值 |
|----|-----|
| 类型 | flag + `DoudianMockChannel` + bootstrap + 测试 |
| 前置 | [phase11a_plan.md](phase11a_plan.md) |

---

## 目标

- `USE_DOUDIAN_CHANNEL_REGISTRATION`（**默认 false**）
- `register_doudian_channel()` → `ChannelRegistry`
- `register_default_platforms` 条件注册
- **不改** AutoReply / `create_auto_reply_runtime_channel` 默认

---

## 测试矩阵

| 用例 | 期望 |
|------|------|
| unset | 无 DOUDIAN |
| true | `create(DOUDIAN)` → `DoudianMockChannel` |
| false-like | 无 DOUDIAN |
| PDD | 始终注册 |

---

*Phase 11b · 2026-06-03*

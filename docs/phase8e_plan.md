# Phase 8e 规划 — runtime bootstrap / Registry visibility

| 项 | 值 |
|---|---|
| 状态 | ✅ Route A 已交付 |
| 路线 | bootstrap 模块 + diagnose；**不接** app.py |
| 相关 | [phase8d_done.md](phase8d_done.md)、[phase8e_done.md](phase8e_done.md) |

---

## 1. 目标

- `register_default_platforms()` 集中注册 PDD（+ 可选 Demo）
- diagnose 展示 available / planned / registered / status
- AutoReplyThread **仍** 不走 ChannelRegistry

## 2. 分期

| 阶段 | 内容 |
|------|------|
| **8e** ✅ | `runtime_bootstrap` + `USE_DEMO_CHANNEL_REGISTRATION` |
| **8f** | `app.py` 可选一行 `register_default_platforms()` |

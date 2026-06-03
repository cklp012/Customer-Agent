# Phase 8f 规划 — app bootstrap one-line registration

| 项 | 值 |
|---|---|
| 状态 | ✅ Route A 已交付 |
| 路线 | `app.py` → `apply_app_startup_bootstrap()` |
| 相关 | [phase8e_done.md](phase8e_done.md)、[phase8f_done.md](phase8f_done.md) |

---

## 1. 目标

- `main()` 内调用 bootstrap；失败不阻断 GUI
- AutoReplyThread **仍** `create_auto_reply_runtime_channel()`

## 2. 分期

| 阶段 | 内容 |
|------|------|
| **8f** ✅ | app one-line registration |
| **9+** | AutoReply 使用 `ChannelRegistry.create()` |

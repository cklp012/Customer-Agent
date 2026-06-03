# Phase 8d 规划 — runtime diagnostics / platform visibility

| 项 | 值 |
|---|---|
| 状态 | ✅ Route B 已交付 |
| 路线 | **B**：`runtime_capabilities.py` + 扩展 `diagnose_runtime.py` |
| 相关 | [phase8c_done.md](phase8c_done.md)、[phase8d_done.md](phase8d_done.md) |

---

## 1. 目标

- 5 个 runtime flag 可见
- Capability report（PDD 路径 / Demo 测试路径 / handler vs immediate resolver）
- ChannelRegistry 快照（空合法）
- 不改 app/UI/业务运行时

## 2. 分期

| 阶段 | 内容 |
|------|------|
| **8d** ✅ | diagnostics |
| **8e** | app bootstrap / GUI platform visibility |

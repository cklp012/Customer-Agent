# Phase 8c 规划 — handler 接入 unified outbound resolver

| 项 | 值 |
|---|---|
| 状态 | ✅ Route B 已交付 |
| 路线 | **B**：`USE_UNIFIED_OUTBOUND_RESOLVER` 默认 false |
| 相关 | [phase8b_done.md](phase8b_done.md)、[phase8c_done.md](phase8c_done.md) |

---

## 1. 目标

- `ai_handler` / `keyword_handler` 在 flag on 时使用 `resolve_outbound`
- flag off 时仍 `resolve_pinduoduo_outbound`（生产默认）
- `pdd_message_handler` **未改**

## 2. Flag 矩阵（PDD Context）

| UNIFIED | PDD_OUTBOUND | handler 解析 | 发送 |
|---------|--------------|--------------|------|
| off | off | 旧 resolver → None | legacy（默认） |
| off | on | 旧 resolver | outbound / legacy |
| on | off | unified → 委托 → None | legacy |
| on | on | unified → 委托 | outbound / legacy |

## 3. 分期

| 阶段 | 内容 |
|------|------|
| **8c** ✅ | handler 接入 + 测试 |
| **8d+** | app bootstrap；`pdd_message_handler` 可选统一 |

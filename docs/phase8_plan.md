# Phase 8 规划 — multi-platform runtime direction

| 项 | 值 |
|---|---|
| 状态 | 8a ✅–8d ✅ 已交付；8e+ 待做 |
| 相关 | [phase8a_done.md](phase8a_done.md)、[architecture_current.md](architecture_current.md) |

---

## 1. 路线对比

| 路线 | 内容 | 风险 | Phase 8 |
|------|------|------|---------|
| **A** | Demo runtime spike（测试级 E2E） | 低 | ✅ **8a** |
| **B** | unified outbound resolver | 中 | ✅ **8b** |
| **C** | handler 按 routing/content_type 改行为 | 高 | 9+ |
| **D** | 真实淘宝/抖店/京东 | 最高 | 独立 spike |

---

## 2. 为何 8a 选 Route A

- 7e–7j 已完成 metadata / 观测 / 日志；**缺的是第二条平台走同一 Consumer 管道的证明**。
- Demo 无网络、无登录，失败可归因于架构而非协议。
- **不破坏** PDD 默认路径（独立 queue `demo_*`、无 app 改动）。

---

## 3. 为何 8a 不做 unified outbound resolver

- PDD 生产仍用 `resolve_pinduoduo_outbound` + registry，已稳定。
- 8a 用 `metadata["outbound"]` 注入即可验证 Demo 发送（与 4a 一致）。
- 泛化 registry 类型（`ChannelOutbound`）留 **8b**，在 8a 证明入站骨架后再做。

---

## 4. 为何不接真实平台

- 登录 / WS / 协议 / 合规成本高，且难区分「架构问题 vs 平台问题」。
- 6a 优先级：抖店 > 京东 > 淘宝；需在 **8b + 黄金路径** 后再开独立 spike。

---

## 5. 分期

| 阶段 | 内容 |
|------|------|
| **8a** ✅ | Demo mapper + inbound_enqueue + runtime 测试 |
| **8b** ✅ | `resolve_outbound` + `channel_outbound_registry`（Route A，handler 未接） |
| **8c** ✅ | handler 接入 `resolve_outbound`（`USE_UNIFIED_OUTBOUND_RESOLVER` 默认 off） |
| **8d** ✅ | `runtime_capabilities` + `diagnose_runtime` capability report |
| **8e** | `app.py` Registry bootstrap；GUI platform visibility |
| **9+** | routing 行为 / 真实平台 spike |
| **10** | UI 多平台、产品化 |

---

## 6. Phase 7e–7j 与 8a 关系

```text
7b–7d: Unified 映射与双轨入队（PDD）
7e–7j: metadata / extract / observability / 日志隐私
8a:    第二平台（Demo）走同一 Consumer + handler(Context) 骨架
```

Handler **仍只吃 Context**；Unified 仅用于 metadata enrich 与未来扩展。

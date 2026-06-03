# Phase 8b 规划 — unified outbound resolver / registry 泛化

| 项 | 值 |
|---|---|
| 状态 | ✅ Route A 已交付 |
| 路线 | **A**：仅新增 resolver + registry，handler 未接入 |
| 相关 | [phase8a_done.md](phase8a_done.md)、[phase8b_done.md](phase8b_done.md) |

---

## 1. 目标

- 平台无关 `resolve_outbound` + `channel_outbound_registry`
- PDD 生产仍走 `resolve_pinduoduo_outbound`（8c 再切 handler）
- 不迁移 `AccountOutboundRegistry`

## 2. 解析顺序

```text
resolve_outbound
  1. metadata["outbound"]（PDD 用旧 duck 校验，其它平台用 channel 校验）
  2. channel_outbound_registry.get(platform, shop_id, user_id)
  3. platform == pinduoduo → resolve_pinduoduo_outbound
  4. 其它 → None
```

## 3. 分期

| 阶段 | 内容 |
|------|------|
| **8b** ✅ | Route A：unified resolver + channel registry + 测试 |
| **8c** | handler 改调 `resolve_outbound`；可选 PDD registry 双写 |

## 4. 明确不做

- 不改 `ai_handler` / `keyword_handler`
- 不改 `account_outbound_registry`
- 不接真实第二平台

# Phase 10k 规划 — Doudian Fixture + Mapper Contract Tests

| 项 | 值 |
|----|-----|
| 类型 | **小步代码**（fixture + mapper + 单测） |
| 前置 | [phase10j_plan.md](phase10j_plan.md) |
| 后续 | **10l** — mock transport + enqueue runtime flow |

---

## 1. 目标

基于 10j spike 计划，交付抖店 **最小可测** 入站映射层：

- `tests/fixtures/doudian_messages/*.json`（本地 mock）
- `Channel/doudian/mappers/*`（routing、Context、UnifiedMessage）
- `test_doudian_queue_naming` / `test_doudian_mapper_contract`

**不做：** 真实 API、login、WS、lifecycle、Consumer/handler/PDD 改动。

---

## 2. 本阶段范围

| 做 | 不做 |
|----|------|
| fixture schema + 3 个 JSON | 真实抖店 API |
| `compute_doudian_routing` | `immediate` 业务路径 |
| `doudian_raw_to_context` / `doudian_raw_to_unified` | 10l enqueue / transport |
| queue naming 测试 | 改 `pdd_{shop_id}` |

---

## 3. Fixture schema（mock）

| 字段 | 说明 |
|------|------|
| `platform` | `"doudian"` |
| `shop_id` / `account_id` | 店铺与客服账号 |
| `conversation_id` / `buyer_id` | 会话与买家 |
| `message_id` / `message_type` / `content` | 消息体 |
| `product_id` / `product_title` | 仅 product_inquiry |
| `notice_type` | 仅 system_notice |

---

## 4. Routing 草案

| message_type | routing |
|--------------|---------|
| `text` | queue |
| `product_inquiry` | queue |
| `system_notice` | drop |
| unknown | drop |

---

## 5. 测试设计

- **A** fixture 可加载
- **B** routing parity
- **C** UnifiedMessage 字段 + `extra.routing`
- **D** Context；system_notice → `None`
- **E** 源码不引用 pinduoduo；无 Consumer/网络

---

*规划版本：Phase 10k · 2026-06-03*

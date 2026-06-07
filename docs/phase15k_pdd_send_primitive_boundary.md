# Phase 15k — PDD Send Primitive Boundary

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15h_pdd_queue_and_message_contract.md](phase15h_pdd_queue_and_message_contract.md) · [phase15k_class_location_and_interface.md](phase15k_class_location_and_interface.md) |

---

## 1. Primitive 定位

| 项 | 说明 |
|----|------|
| 名称（建议） | `PddAssistedSendPrimitive` 或 thin wrapper around existing MMS send |
| 调用方 | **仅** `LivePddAssistedOutboundPort` |
| 职责 | **一次** PDD outbound 发送尝试 |
| 非职责 | 重试循环 · guard · audit · queue enqueue for auto-reply |

---

## 2. 允许：薄封装现有 PDD send

| 规则 |
|------|
| 未来可 **薄封装** 现有 PDD send primitive（如 MMS API / channel adapter 只读调用） |
| **不能**修改 legacy `SendMessage` **默认行为** |
| **不能**修改 `pdd_message_handler` |
| **不能**修改 `MessageConsumer` |
| **不能**修改 `AutoReplyThread` |
| **不能**改变 queue name **`pdd_{shop_id}`** |
| **不能**将 assisted send 混入 legacy auto-reply 入队逻辑 |

---

## 3. 若 SendMessage 无法安全复用

| 步骤 | 说明 |
|------|------|
| 1 | 先抽 **lower-level PDD outbound primitive**（只读调用路径） |
| 2 | primitive **不得**改变 legacy hot path 默认行为 |
| 3 | legacy auto-reply 继续走现有 handler → queue → consumer 路径 |
| 4 | assisted live send 走 service → port → primitive **并行隔离** |

**不允许**从 dashboard route 直接调 PDD send。

---

## 4. 调用顺序（future）

```text
AssistedReplyService (completed before port.send):
    1. route permission / action idempotency (15j)
    2. final guard allow
    3. audit: assisted_approved, final_guard_passed
    4. SendDecision snapshot (if enabled)
    5. outbound idempotency acquire (in_progress)

LivePddAssistedOutboundPort.send(request):
    6. port-local validation
    7. primitive.send_once(buyer_id, final_reply, shop context, trace_id)
    8. map primitive outcome → AssistedOutboundResult

AssistedReplyService (after port.send):
    9. audit: outbound_send_attempted / succeeded / failed / unknown
    10. outbound idempotency mark / leave in_progress
    11. pending status update
```

Primitive **只执行 step 7** — **不负责重试循环**。

---

## 5. Port 输入约束

| 规则 |
|------|
| `final_reply` 必须是 guard pass 后冻结文本 |
| Port **不允许** AI 重新生成 |
| Port **不允许**修改、截断、模板替换 `final_reply` |
| Primitive 收到什么文本就发什么文本 |

---

## 6. Legacy 隔离清单

| 路径 | Assisted live | Legacy auto-reply |
|------|---------------|-------------------|
| Trigger | Dashboard approve → service | Inbound WS → handler |
| Queue | **不**经 auto-reply enqueue | `pdd_{shop_id}` consumer |
| Handler | **不参与** | `ai_handler` / `keyword_handler` |
| SendMessage default | unchanged | hot path |
| AutoReplyThread | ** unchanged** | unchanged |

---

## 7. 禁止

| 禁止 |
|------|
| Port 从 route import |
| Port 调用 handler `handle()` |
| Port fallback 到 legacy auto-reply send |
| Port 修改 outbound resolver 默认 |
| Port 改 Doudian 路径 |

---

*Phase 15k · docs only · 2026-06-03*

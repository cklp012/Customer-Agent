# Phase 12c — Handler Integration Plan（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only · **不改代码** |
| 关联 | [phase12c_intent_gate_design.md](phase12c_intent_gate_design.md) · [phase12c_preview_dry_run_technical_design.md](phase12c_preview_dry_run_technical_design.md) |

---

## 1. 当前发送路径概览（as-is）

### 1.1 入站 → 队列

```text
PDD WebSocket
  → Channel/pinduoduo/core/pdd_message_handler.py
       MessageHandlerMixin._process_websocket_message
       → _convert_to_context
       → immediate path (_handle_immediate_message)  OR  put_message(queue_name=pdd_{shop_id})
  → Message/core/consumer.py
       _process_message → handler_chain (first match wins, break)
```

**队列名：** `pdd_{shop_id}`（不变）。

**Handler 链（`Message/__init__.py` `handler_chain`）：**

1. `KeywordDetectionHandler` — 仅 `ContextType.TEXT`；命中 → 转人工 → **break**
2. `AIReplyHandler` — 多类型；生成 → `_send_reply` → **break**
3. `CatchAllHandler` — 日志

**`businessHours`：** 传入 `handler_chain` 但 **未使用**。

### 1.2 AI 发送路径（`Message/handlers/ai_handler.py`）

```text
AIReplyHandler.handle
  → preprocessor.process
  → bot.async_reply / reply
  → _send_reply
       if use_unified_outbound_resolver():   # 默认 FALSE
           resolve_outbound → outbound.send_text
       else:
           resolve_pinduoduo_outbound → outbound.send_text  # 若 USE_PINDUODUO_OUTBOUND
       fallback: _send_text_legacy → SendMessage(shop_id, user_id).send_text(from_uid, reply)
```

**生产默认：** `USE_UNIFIED_OUTBOUND_RESOLVER=false` → `resolve_pinduoduo_outbound` 常 None → **legacy `SendMessage.send_text`**。

### 1.3 关键词转人工路径（`Message/handlers/keyword_handler.py`）

```text
KeywordDetectionHandler.handle
  → resolve_outbound / resolve_pinduoduo_outbound → transfer_to_human
  → fallback: SendMessage.move_conversation / send_text（离线提示）
```

### 1.4 Outbound 解析（只解析，不发送）

| 模块 | 职责 |
|------|------|
| `Message/handlers/outbound_resolver.py` | `resolve_pinduoduo_outbound`；`use_pinduoduo_outbound()` gate |
| `Message/handlers/unified_outbound_resolver.py` | `resolve_outbound`；`use_unified_outbound_resolver()` 默认 off |

### 1.5 即时消息发送（`pdd_message_handler.py`）

`_send_immediate_text` → outbound → fallback `SendMessage.send_text`（如 WITHDRAW 回复玫瑰）。

**注意：** 用户提到的 `Message/pdd_message_handler.py` **不存在**；SSOT 为 `Channel/pinduoduo/core/pdd_message_handler.py`。

---

## 2. 设计原则

| # | 原则 |
|---|------|
| P1 | **不能破坏 PDD 生产路径** — product gate **默认 off** = 现有行为 |
| P2 | **不建议只靠 prompt** — 发送必须由 SendDecision + final guard |
| P3 | **不建议只靠 keyword_handler** — 须 normalize + intent；keyword 仅为第一道 |
| P4 | **必须有 final send guard** — 单一 send 入口 |
| P5 | Preview gate 是 **店铺级/工作区级**，非全局 env |
| P6 | 第一阶段 **flag-gated**：`product_gate_enabled` per shop（12f） |

---

## 3. 未来插入点

### A. Handler 前 intent gate（推荐 · 主路径）

```text
Consumer._process_message
  → [NEW] evaluate_inbound_gate(wrapper) → SendDecision in metadata
  → if send_mode == human_takeover: TransferHandler or mark-only (preview)
  → if not allowed_to_generate: skip AI / skip send
  → existing handlers (modified to read metadata["send_decision"])
```

**优点：** 一条消息一次决策；AI 可不调用（blocked + 配置不生成）。  
**缺点：** 需 consumer 或新 `InboundGateHandler` 在链首。

**建议模块：** `Message/gates/inbound_gate.py`（12f）。

### B. AI 生成后 send gate（必做）

```text
AIReplyHandler.handle
  → _get_ai_reply
  → [NEW] if not metadata["send_decision"].allowed_to_send:
         persist ReplyLog(preview_only); return True
  → [NEW] final_send_guard(decision, reply)
  → _send_reply (only if guard passes)
```

**改造点：** 拆分「生成」与「发送」；`_handle_fallback` 同样过 gate。

### C. Outbound resolver 前 final guard（必做 · 双保险）

```text
# 新概念： Message/ports/send_port.py

async def send_text_guarded(decision, shop_id, user_id, to_uid, text, metadata, context):
    if not decision.allowed_to_send:
        return SendResult(sent=False, reason=decision.blocked_reason)
    if decision.send_mode == "preview_only":
        return SendResult(sent=False, dry_run=True)
    # existing outbound / legacy
```

**所有** `SendMessage.send_text` 调用应经此 port（12f 渐进迁移）：

| 当前调用点 | 迁移优先级 |
|------------|------------|
| `ai_handler._send_text_legacy` | P0 |
| `ai_handler._send_reply` | P0 |
| `keyword_handler._transfer_to_human_legacy` | P1（transfer 可 preview noop） |
| `pdd_message_handler._send_immediate_text_legacy` | P2（系统消息；可豁免或单独策略） |

---

## 4. 推荐链顺序（to-be）

```text
1. InboundGateHandler (or consumer pre-hook)   # intent + SendDecision
2. KeywordRiskHandler (fast path, merges into decision)  # 可合并到 1
3. HumanTakeoverHandler (execute transfer if allowed & not preview)
4. AIReplyHandler (generate only; send via port)
5. CatchAllHandler
```

**与现网兼容：** `product_gate_enabled=false` 时跳过 1 的约束，链退化为 **现有** Keyword → AI → CatchAll。

---

## 5. Metadata 契约（handler 间传递）

```python
# 概念 — 非本 Phase 代码
metadata["send_decision"] = {
    "decision_id": "...",
    "allowed_to_generate": True,
    "allowed_to_send": False,
    "send_mode": "preview_only",
    "intent": "product_question",
    "intent_bucket": "allowed",
    ...
}
metadata["product_gate_enabled"] = True  # from ShopBinding runtime cache
```

**加载 `reply_mode`：** AutoReplyThread 启动时从 SaaS 缓存或本地 config overlay（12f）；**默认 preview + gate off**。

---

## 6. Flag 与产品 gate 矩阵

| product_gate_enabled | reply_mode | 行为 |
|----------------------|------------|------|
| false | any | **Legacy** — 与今日生产一致 |
| true | preview | intent gate + zero send |
| true | assisted | intent gate + approve to send |
| true | auto | intent gate + allowlist send |

| Env flag | 12c/12f |
|----------|---------|
| `USE_UNIFIED_OUTBOUND_RESOLVER` | 保持默认 **false**；gate on 时仍不 send if preview |
| `USE_PINDUODUO_OUTBOUND` | 不变；final guard 包裹 |
| `USE_DOUDIAN_CHANNEL_REGISTRATION` | 不变；Doudian 非 production |

---

## 7. 不建议的方案

| 方案 | 原因 |
|------|------|
| 仅改 `message_builder` prompt | 无法阻止 `_send_reply` |
| 仅扩 keyword 词表 | 漏检变体；非 TEXT 不进词表 |
| 全局 env `PREVIEW_MODE=true` | 无法 per-shop SaaS；误伤生产 |
| 在 `SendMessage` 内读 env | 违反店铺级 gate；难测试 |

---

## 8. 分阶段 rollout（12f 预告）

| 阶段 | 范围 |
|------|------|
| **12f-1** | `send_text_guarded` + tests；gate off 默认 |
| **12f-2** | Inbound gate + SendDecision 内存（无 DB） |
| **12f-3** | Preview per-shop config（桌面 config.json overlay） |
| **12e** | DB 持久化 ReplyLog / SendDecision |
| **12f-4** | Assisted approve API |

---

## 9. AutoReplyThread 边界

| 项 | 12c 结论 |
|----|----------|
| 修改 `AutoReplyThread` | **本 Phase 不改** |
| 接入方式 | Thread 启动 consumer 时注入 `product_gate_enabled` + `reply_mode` 到 metadata 工厂 |
| 队列名 | 仍为 `pdd_{shop_id}` |

---

## 10. 文件触达清单（12f 参考，非 12c）

| 文件 | 变更类型 |
|------|----------|
| `Message/core/consumer.py` | 可选 pre-gate |
| `Message/handlers/ai_handler.py` | 生成/发送分离 |
| `Message/handlers/keyword_handler.py` | 与 risk scan 合并或委托 gate |
| `Message/handlers/outbound_resolver.py` | 不改解析逻辑；send 迁到 port |
| `Channel/pinduoduo/core/pdd_message_handler.py` | 即时消息策略单独文档 |
| **新建** `Message/gates/*`, `Message/ports/send_port.py` | 新模块 |

**12c 不修改以上任何文件。**

---

*Phase 12c · Handler Integration Plan · docs only*

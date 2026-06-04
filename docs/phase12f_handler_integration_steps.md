# Phase 12f — Handler Integration Steps H0–H6（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 参考代码 | `Message/handlers/ai_handler.py` · `keyword_handler.py` · `Channel/pinduoduo/core/pdd_message_handler.py` · `outbound_resolver.py` · `unified_outbound_resolver.py` |

---

## 1. 当前路径摘要（不变更直至 H3+）

| 步骤 | 位置 | 行为 |
|------|------|------|
| WS 入站 | `pdd_message_handler._process_websocket_message` | `put_message(pdd_{shop_id})` |
| 消费 | `consumer._process_message` | handler 链，first success break |
| 链 | `handler_chain` | Keyword → AI → CatchAll |
| AI 发 | `ai_handler._send_reply` | unified? → `resolve_pinduoduo_outbound` → `SendMessage.send_text` |
| 转人工 | `keyword_handler` | `transfer_to_human` / legacy `move_conversation` |

---

## 2. 分阶段计划

### H0 — Docs only（当前 Phase 12f）

| 项 | 内容 |
|----|------|
| scope | 本批文档 |
| PDD | 零改动 |
| rollback | N/A |

---

### H1 — 纯函数 / 服务，不接 handler（→ Phase 13a）

| 项 | 内容 |
|----|------|
| scope | 新增包 `Message/gates/`、`Message/ports/` |
| 模块 | `normalize.py`, `keyword_risk.py`, `classify_intent.py`, `build_send_decision.py`, `guarded_send.py` |
| tests | T1 部分、T7、T8、merge 规则单测 |
| handler | **不 import** |
| PDD | 无影响 |
| rollback | 删除新包 |

**交付：** 可独立 `pytest Message/gates` 无侧效。

---

### H2 — AIReplyHandler shadow SendDecision（→ Phase 13b）

| 项 | 内容 |
|----|------|
| scope | `consumer` 或 `AIReplyHandler` 入口调用 `build_send_decision` |
| flag | `SHADOW_SEND_DECISION_LOG=true` **或** 全店 `product_gate_enabled=false` 仅写内存/SQLite shadow 表 |
| 发送 | **仍** `_send_reply` legacy，**不** 调用 `send_text_guarded` |
| 对比 | shadow `allowed_to_send` vs 实际是否 send（指标） |
| PDD | T1 + T8 legacy 不变 |
| rollback | flag off |

**不改：** `SendMessage` 签名；队列名。

---

### H3 — 单测试店 Preview gate（→ Phase 13c）

| 项 | 内容 |
|----|------|
| scope | 配置 **1 个** `shop_id`：`product_gate_enabled=true`, `reply_mode=preview` |
| AI | `_get_ai_reply` 仍执行 |
| 发送 | `_send_reply` → **`send_text_guarded`**（gate on 店） |
| 期望 | T2, T11：zero SendMessage/outbound |
| 其他店 | legacy `_send_reply` |
| Doudian | 不启用 gate |
| rollback | 该店 `product_gate_enabled=false` |

```python
# 概念分支 — ai_handler.handle
if shop_snapshot.product_gate_enabled:
    reply = await self._get_ai_reply(...)
    return await send_text_guarded(reply, ..., send_decision, ...)
else:
    # 现有路径原样
    return await self._send_reply(...)
```

---

### H4 — Assisted internal（→ Phase 13d）

| 项 | 内容 |
|----|------|
| scope | 测试店 `reply_mode=assisted` |
| 流程 | 生成 → ReplyLog `not_sent_awaiting_approval` → UI/API approve → 再次 `send_text_guarded` + `merchant_approve_id` |
| tests | T6 |
| rollback | 改回 preview |

---

### H5 — Auto limited allowlist（→ Phase 13e）

| 项 | 内容 |
|----|------|
| scope | 测试店 `reply_mode=auto` + 二次确认 audit |
| 条件 | allowed + conf≥0.85 + risk=low |
| tests | T3, T5, T7 |
| rollback | workspace pause 或改 preview |
| **禁止** | 全量商家默认 auto |

---

### H6 — Dashboard read model 接入（→ 对齐 12e M8 / 12g UI）

| 项 | 内容 |
|----|------|
| scope | 读 shadow `shop_bindings` + `reply_logs` + `send_decisions` |
| API | 12d contract 实现（另 Phase） |
| handler | 无变更 |
| 展示 | `effective_status`, 今日活动, 待人工队列 |

---

## 3. KeywordDetectionHandler 演进

| 阶段 | 策略 |
|------|------|
| H2–H3 | 保留；与 risk scan **并行**（可能双转人工 — 接受或 H3 去重） |
| H4+ | Keyword 仅 **非 gate** 店；gate on 店由 `send_decision` 驱动 transfer_guarded |

**目标：** gate on 时 risk scan 在 **AI 之前**（consumer 前置 hook）。

---

## 4. Consumer 前置 hook（推荐 H3）

```text
_process_message:
  shop_snapshot = resolve_shop_snapshot(metadata)  # from cache / projection
  if shop_snapshot.product_gate_enabled:
      metadata["send_decision"] = build_send_decision(...)
      if send_decision.send_mode == human_takeover:
          await transfer_guarded(...); return True  # 可选：跳过 AI
  for handler in handlers: ...
```

**好处：** AI 不对 blocked 消息浪费 token（可配置 H3.1）。

---

## 5. Outbound 路径（gate on）

```text
send_text_guarded
  → OutboundSenderPort (LegacySendMessageAdapter)
       → 内部仍可用 resolve_pinduoduo_outbound (USE_PINDUODUO_OUTBOUND 默认不变)
       → fallback SendMessage
```

**`USE_UNIFIED_OUTBOUND_RESOLVER`：** 默认 false；guard 内 **不** 改变 env 默认。

---

## 6. `pdd_message_handler` 即时消息

| 类型 | H3–H5 策略 |
|------|------------|
| WITHDRAW 玫瑰 | **豁免** legacy `_send_immediate_text`（非 AI 副驾驶路径） |
| 其他 immediate | 文档记录；不纳入 12f 首批 |

---

## 7. 每步 PDD legacy protection

| 检查 | H1–H6 |
|------|-------|
| `product_gate_enabled=false` 店 | T1 每步回归 |
| Queue `pdd_{shop_id}` | 不变 |
| AutoReplyThread | 不重构；仅注入 snapshot resolver |
| flags 默认 | 不变 |

---

## 8. Doudian mock

| 项 | 要求 |
|----|------|
| gate | 不对 Doudian 店开启 `product_gate_enabled` |
| tests | T9 mock 队列/ handler 无新增 send |
| registration | `USE_DOUDIAN_CHANNEL_REGISTRATION` 默认 false |

---

## 9. Rollback 矩阵

| 阶段 | 开关 |
|------|------|
| H2 | `SHADOW_SEND_DECISION_LOG=0` |
| H3 | 测试店 gate off |
| H4–H5 | reply_mode → preview |
| H6 | API 读 legacy 占位 |

---

*Phase 12f · Handler Integration Steps · docs only*

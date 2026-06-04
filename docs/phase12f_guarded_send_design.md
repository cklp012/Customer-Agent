# Phase 12f — `send_text_guarded` Design（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only · **未来代码位于** `Message/ports/guarded_send.py`（建议） |
| 前置 | [phase12c_send_decision_model.md](phase12c_send_decision_model.md) · [phase12e_send_decision_reply_log_schema.md](phase12e_send_decision_reply_log_schema.md) |

---

## 1. 定位

**`send_text_guarded` 是 final send guard** — 所有「发给买家」的文本必须经过此函数（`product_gate_enabled=true` 时）。

| 是 | 不是 |
|----|------|
| 产品级发送裁决 + 审计写入 | `USE_UNIFIED_OUTBOUND_RESOLVER` |
| Preview dry-run 执行点 | prompt 约束 |
| ReplyLog 统一写入点 | KeywordDetectionHandler 内的 SendMessage |

---

## 2. 概念签名

```python
# 文档契约 — 非本 Phase 代码

async def send_text_guarded(
    reply_text: str,
    message_context: MessageContext,      # shop_id, user_id, from_uid, context, metadata
    shop_binding: ShopBindingSnapshot,    # reply_mode, pauses, product_gate_enabled, ids
    send_decision: SendDecisionSnapshot,
    outbound_sender: OutboundSenderPort,  # PinduoduoOutbound / legacy adapter
    *,
    merchant_approve_id: str | None = None,  # assisted only
    reply_log_writer: ReplyLogWriterPort,
) -> GuardedSendResult:
    ...
```

### 2.1 `GuardedSendResult`

| 字段 | 说明 |
|------|------|
| `sent` | 是否调用平台 API 且成功 |
| `dry_run` | Preview / blocked 未真发 |
| `reply_log_id` | 已写入日志 |
| `blocked_reason` | 若未发 |
| `send_status` | not_sent_preview / sent / failed / … |

---

## 3. 职责（检查顺序）

**与 12c 优先级一致：**

```text
1. product_gate_enabled == false  →  delegate legacy_send_path (见 §6)
2. workspace_pause                →  deny, log not_sent_paused
3. shop_pause                     →  deny
4. human_takeover active          →  deny, log not_sent_takeover
5. send_decision.intent_bucket=blocked → deny
6. send_decision.allowed_to_send == false → deny (preview, uncertain+auto, low conf, …)
7. reply_mode == preview          →  deny, log not_sent_preview (+ suggested_reply)
8. reply_mode == assisted && !merchant_approve_id → deny, log awaiting_approval
9. commitment_guard(reply_text)   →  deny if fail
10. reply_mode == auto && allowed →  invoke outbound_sender.send_text
11. reply_mode == assisted && approved → send
```

| 检查项 | Preview | Assisted | Auto |
|--------|---------|----------|------|
| workspace_pause | ❌ send | ❌ | ❌ |
| shop_pause | ❌ | ❌ | ❌ |
| product_gate off | legacy | legacy | legacy |
| blocked intent | ❌ + log | ❌ + transfer 标记 | ❌ |
| allowed_to_send=false | ❌ + log | ❌ | ❌ |
| 未 confirm | N/A | ❌ | N/A |
| 通过 | ❌ **永不真发** | ✅ 可发 | ✅ 可发 |

---

## 4. ReplyLog 写入规则

**所有路径**（含 blocked / preview / assisted_required）**必须**写 ReplyLog（或 shadow 内存实现直至 12e M1 表就绪）。

| 路径 | `send_status` | 平台 API |
|------|---------------|----------|
| Preview | `not_sent_preview` | **0** 调用 |
| Paused | `not_sent_paused` | 0 |
| Blocked intent | `not_sent_blocked` | 0 |
| Assisted 待确认 | `not_sent_awaiting_approval` | 0 |
| Auto 成功 | `sent` | 1 |
| Auto 失败 | `failed` | 1（尝试） |

**字段填充：** `ai_suggested_reply=reply_text`；`decision_id`；`blocked_reason`；`human_takeover_reason`；`would_send_if_auto`（Preview 教育用）。

---

## 5. OutboundSenderPort

```python
class OutboundSenderPort(Protocol):
    async def send_text(self, to_uid: str, text: str) -> SendResult: ...
    async def transfer_to_human(self, to_uid: str, reason: str) -> bool: ...
```

| 实现 | 何时 |
|------|------|
| `LegacySendMessageAdapter` | 包装 `SendMessage.send_text` |
| `PinduoduoOutboundAdapter` | `USE_PINDUODUO_OUTBOUND` on |
| `PreviewNoopAdapter` | 测试 / 双保险（永远 success 无网络） |

**guard 内：** 仅步骤 10–11 调用 `send_text`。

---

## 6. 迁移期：legacy 委托

```python
if not shop_binding.product_gate_enabled:
    return await legacy_send_reply(...)  # 现有 _send_reply 逻辑，零行为变化
```

| 要求 | |
|------|--|
| T1 | gate off 时 **不** 进入 SendDecision 分支（或 decision 仅 shadow，不改变 send） |
| 禁止 | gate off 仍走 guard 并误拦 |

---

## 7. 禁止绕过

| 违规 | 修复 |
|------|------|
| `AIReplyHandler` 直接 `SendMessage.send_text` | gate on 时改为 `send_text_guarded` |
| `keyword_handler` 转人工 | 单独 `transfer_guarded`（Preview 可 noop 记录） |
| `pdd_message_handler._send_immediate_text` | 系统消息策略：gate on 时 **豁免清单** 或同样走 guard（文档决策：WITHDRAW 玫瑰等 **单独** policy，默认仍 legacy 至 H5+） |

**T12：** 静态检查 / 测试 monkeypatch 确保 gate on 无直连 SendMessage。

---

## 8. 与 SendDecision 关系

- `send_text_guarded` **信任但不盲信** `send_decision.allowed_to_send` — 步骤 7–9 **再验** `reply_mode` 与 commitment。
- 发送前 **不修改** SendDecision 行（append-only）；失败写 ReplyLog `send_error_message`。

---

## 9. 错误处理

| 场景 | 行为 |
|------|------|
| outbound 失败 | ReplyLog `failed`；**不** fallback 二次 send（除非 legacy 策略显式开启） |
| 空 reply_text | 不写 send；log warning |
| writer 失败 | 返回 error；**不** send（安全侧） |

---

## 10. 实现检查清单（13a+）

- [ ] gate off = legacy 字节级行为（T1）
- [ ] Preview zero network（T2, T11）
- [ ] paused / blocked 零 send（T3, T4）
- [ ] auto 仅 allowed 发送（T5）
- [ ] assisted approve（T6）
- [ ] 无 bypass（T12）

---

*Phase 12f · Guarded Send Design · docs only*

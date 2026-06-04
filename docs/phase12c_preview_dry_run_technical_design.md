# Phase 12c — Preview / Dry-run Technical Design（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 关联 | [phase12c_send_decision_model.md](phase12c_send_decision_model.md) · [phase12a_safety_and_preview_spec.md](phase12a_safety_and_preview_spec.md) |

---

## 1. Preview 模式定义

| 能力 | Preview |
|------|---------|
| 生成 AI 建议 | ✅（当 `allowed_to_generate=true`） |
| 写入 ReplyLog / preview logs | ✅ |
| 展示给商家（Dashboard / 桌面 UI 后期） | ✅ |
| 调用 `SendMessage.send_text` | ❌ **禁止** |
| 调用 `PinduoduoOutbound.send_text` | ❌ **禁止** |
| 调用 `resolve_outbound` → `send_text` | ❌ **禁止** |
| 调用 unified outbound `send_text` | ❌ **禁止** |
| 关键词转人工的 `move_conversation` | ⚠️ MVP 可 **仅记录** `suggested_action=transfer`；Growth 再接真实 API |

**不变量：Preview 永不 send。**

---

## 2. Dry-run 与 Preview 的关系

| 术语 | 含义 |
|------|------|
| **Preview** | 产品 `reply_mode=preview` |
| **Dry-run** | 实现手段：send 路径上的 **no-op** + 审计字段 `would_send_if_auto` |

所有 `reply_mode=preview` 的消息走 **同一 dry-run 出站适配器**，不区分 env。

---

## 3. 处理流程（Preview）

```text
inbound message
  → intent gate → SendDecision(send_mode=preview_only, allowed_to_send=false)
  → AI generate (if allowed_to_generate)
  → commitment guard on suggested_reply (optional block display)
  → persist PreviewLog / ReplyLog
  → return success (业务成功 = 已记录，非已发送)
```

**禁止** 在 `AIReplyHandler.handle` 末尾无条件调用 `_send_reply` 当 `allowed_to_send=false`。

---

## 4. Dry-run 记录字段（ReplyLog / PreviewLog）

| 字段 | 说明 |
|------|------|
| `buyer_message` | 原始或 normalized 买家消息 |
| `normalized_text` | normalize 输出 |
| `intent` | 分类结果 |
| `intent_confidence` | 置信度 |
| `intent_bucket` | allowed / blocked / uncertain |
| `ai_suggested_reply` | 模型输出 |
| `blocked_reason` | 禁诺 / intent_blocked / preview_mode |
| `human_takeover_reason` | 若适用 |
| `would_send_if_auto` | bool：模拟 auto+gate 下是否会 send |
| `reply_mode` | preview |
| `outcome` | `preview_only` |
| `decision_id` | FK → SendDecision |
| `created_at` | |

---

## 5. Preview logs 存储（设计）

### 5.1 MVP（桌面 / 单租户）

| 方案 | 说明 |
|------|------|
| **A** | 扩展现有 SQLite `ReplyLog` 表（12e migration） |
| **B** | 短期：`preview_logs.jsonl` 按 shop_id 滚动（仅 dev spike，非 SaaS 终态） |

**SaaS 终态：** `reply_logs` 表 + `send_decisions` 表，按 `workspace_id` 隔离。

### 5.2 查询接口（未来）

```text
GET /v1/shops/{shop_binding_id}/preview-logs?date=...
  → [{ buyer_message, intent, ai_suggested_reply, blocked_reason, created_at }]
```

---

## 6. Assisted approval flow（未来接口）

```text
POST /v1/reply-logs/{id}/approve
  body: { merchant_id, edited_reply?: string }
  → re-run commitment guard on edited_reply
  → SendDecision.allowed_to_send=true (one-shot)
  → outbound send ONCE
  → outcome=sent | blocked | failed

POST /v1/reply-logs/{id}/reject
  → outcome=rejected_by_merchant
```

**桌面 MVP：** UI 按钮 → 调用同一内部 service（非 HTTP 亦可）。

---

## 7. Auto send 前最后 guard（Final Send Guard）

即使 `SendDecision.allowed_to_send=true`，在 **唯一 send 入口** 前再次检查：

```text
final_send_guard(decision, reply_text):
  if not decision.allowed_to_send: return NO_SEND
  if decision.send_mode != auto_send: return NO_SEND  # assisted 须带 approve token
  if commitment_guard fails(reply_text): return NO_SEND + blocked_reason
  if workspace_pause or shop_pause: return NO_SEND
  → invoke OutboundPort.send_text ONLY here
```

**插入点：** 见 [phase12c_handler_integration_plan.md](phase12c_handler_integration_plan.md) **C. outbound 前 final guard**。

---

## 8. 出站 Dry-run 适配器（概念）

```text
class PreviewOutboundAdapter:
    async def send_text(self, to_uid, text) -> bool:
        log_preview_send_attempt(...)
        return True   # 业务成功，零网络

    async def transfer_to_human(self, to_uid, reason) -> bool:
        log_preview_transfer_attempt(...)
        return True
```

**生产默认：** 仍用 legacy `SendMessage` / `PinduoduoOutbound`（product gate off）。

**product gate on + preview：** handler 注入 `PreviewOutboundAdapter`，**不** 实例化 `SendMessage`。

---

## 9. 测试：Preview zero-send（设计，12f 实现）

### 9.1 Patch 目标

| 目标 | 断言 |
|------|------|
| `SendMessage.send_text` | `call_count == 0` |
| `SendMessage.move_conversation` | 可配置 0（MVP preview 仅记录） |
| `PinduoduoOutbound.send_text` | `call_count == 0` |
| `mock outbound.send_text`（unified） | `call_count == 0` |

### 9.2 测试 harness

```text
@pytest.fixture
def preview_shop_config():
    return ShopGateConfig(reply_mode="preview", product_gate_enabled=True)

def test_preview_zero_send(monkeypatch):
    calls = []
    monkeypatch.setattr(SendMessage, "send_text", lambda *a, **k: calls.append(1))
    # ... run handler pipeline with preview decision
    assert calls == []
```

### 9.3 `would_send_if_auto` 断言

| 输入 | `would_send_if_auto` |
|------|----------------------|
| allowed + high conf | true |
| refund_request | false |
| preview mode | false（实际 send）；true 仅表示「若误开 auto 本应可发」需区分 — **记录为** `hypothetical_auto_allowed` 更清晰 |

**建议字段拆分：**

- `would_send_if_auto`：在 **preview** 下模拟 gate 结果（教育用）
- `allowed_to_send`：当前模式下的真实裁决（preview 恒 false）

---

## 10. Fallback 回复与 Preview

当前 `AIReplyHandler._handle_fallback` 也会 `_send_reply`。

**12f 要求：** fallback 同样经 final send guard；preview 下 **不得** 向买家发送 fallback 文案（可写日志）。

---

## 11. 与 env flag 边界

| Flag | Preview 关系 |
|------|----------------|
| `USE_UNIFIED_OUTBOUND_RESOLVER` | **无关**；preview 两条路径均不 send |
| `USE_PINDUODUO_OUTBOUND` | **无关** |
| `product_gate_enabled`（新，12f） | **店铺级** 开启 gate；默认 **false** |

---

*Phase 12c · Preview / Dry-run · docs only*

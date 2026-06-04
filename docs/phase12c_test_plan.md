# Phase 12c — Test Plan（Future · SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only · **tests 未实现**（12f 代码 Phase） |
| 关联 | [phase12c_preview_dry_run_technical_design.md](phase12c_preview_dry_run_technical_design.md) · [phase12c_handler_integration_plan.md](phase12c_handler_integration_plan.md) |

---

## 1. 测试原则

| # | 原则 |
|---|------|
| T0 | **不** 在 12c 添加或修改 `tests/` |
| T1 | 所有 send 测试 **patch** `SendMessage` + outbound `send_text` |
| T2 | `product_gate_enabled=false` 时 **回归** PDD legacy 行为（T8） |
| T3 | Doudian **无** production send 断言（T9） |
| T4 | Preview **zero-send** 为 P0 回归（T10） |

**运行环境：** pytest + asyncio；fixtures 模拟 `Context` / `metadata` / `SendDecision`。

---

## 2. 用例清单

### T1 — Allowed consultation + preview

| 项 | 值 |
|----|-----|
| 输入 | `normalized_text="这款面霜什么成分"`，`intent=product_question`，`intent_bucket=allowed`，`reply_mode=preview` |
| 配置 | `product_gate_enabled=true` |
| 期望 | AI 建议生成（mock bot）；`ReplyLog.outcome=preview_only` |
| 期望 | `allowed_to_send=false` |
| 期望 | `SendMessage.send_text` **0** 次；`outbound.send_text` **0** 次 |

---

### T2 — Allowed consultation + auto + high confidence

| 项 | 值 |
|----|-----|
| 输入 | `product_question`，`confidence=0.92`，`risk_level=low` |
| 配置 | `reply_mode=auto`，`product_gate_enabled=true` |
| 期望 | `allowed_to_send=true`，`send_mode=auto_send` |
| 期望 | `send_text_guarded` 调用 outbound **1** 次（mock 成功） |
| 期望 | commitment guard pass |

---

### T3 — refund_request + auto

| 项 | 值 |
|----|-----|
| 输入 | `"我要退款"` 或 `intent=refund_request` |
| 配置 | `reply_mode=auto` |
| 期望 | `intent_bucket=blocked` |
| 期望 | `allowed_to_send=false`，`send_mode=human_takeover` |
| 期望 | **不** 调用 `send_text` |
| 期望 | `human_takeover_reason` 含 `keyword_rule` 或 `intent_blocked` |

---

### T4 — complaint + assisted

| 项 | 值 |
|----|-----|
| 输入 | `intent=complaint` |
| 配置 | `reply_mode=assisted` |
| 期望 | `send_mode=assisted_required` 或 `human_takeover` |
| 期望 | **不** 自动 `send_text`（无 approve） |
| 期望 | approve 后若仍 blocked → 仍不 send |

---

### T5 — low_confidence

| 项 | 值 |
|----|-----|
| 输入 | `intent=product_question`，`confidence=0.4`，`intent_bucket=uncertain` |
| 配置 | `reply_mode=auto` |
| 期望 | `allowed_to_send=false`，`blocked_reason=low_confidence` |
| 期望 | 零 send |

---

### T6 — workspace_pause

| 项 | 值 |
|----|-----|
| 配置 | `workspace_pause=true`，`reply_mode=auto` |
| 期望 | `allowed_to_send=false`，`blocked_reason=workspace_paused` |
| 期望 | 零 send |
| 可选 | `allowed_to_generate=false`（严格策略）或 true（推荐策略）— 用例分两条子测试 |

---

### T7 — shop_pause

| 项 | 值 |
|----|-----|
| 配置 | `shop_pause=true` |
| 期望 | 同 T6，`blocked_reason=shop_paused` |

---

### T8 — PDD legacy protection

| 项 | 值 |
|----|-----|
| 配置 | `product_gate_enabled=false` |
| 输入 | 与当前生产相同 TEXT 消息 |
| 期望 | handler 链行为与 **基线快照** 一致（send 次数、转人工逻辑不变） |
| 期望 | **不** 读取 `SendDecision` 约束发送 |
| 方法 | 现有 `tests/test_*` 基线 + 新参数化 `gate_off` |

---

### T9 — Doudian remains non-production

| 项 | 值 |
|----|-----|
| 范围 | `DoudianMockChannel` / unified outbound Doudian tests |
| 期望 | 无真实 Doudian API；mock outbound 在 preview gate on 时 **zero send** |
| 期望 | `USE_DOUDIAN_CHANNEL_REGISTRATION` 默认 false 不变 |

---

### T10 — Preview zero-send regression

| 项 | 值 |
|----|-----|
| 配置 | `reply_mode=preview`，`product_gate_enabled=true`，allowed intent |
| Patch | `SendMessage.send_text`, `SendMessage.move_conversation`, `PinduoduoOutbound.send_text`, unified mock `send_text` |
| 期望 | 全部 **call_count == 0** |
| 期望 | `ReplyLog` 有 `ai_suggested_reply` |
| 期望 | `would_send_if_auto` 按 gate 正确（allowed → true，blocked → false） |

---

## 3. 建议测试文件布局（12f）

| 文件 | 覆盖 |
|------|------|
| `tests/test_send_decision_evaluator.py` | T3–T7 纯函数 gate |
| `tests/test_preview_zero_send.py` | T1, T10 |
| `tests/test_product_gate_legacy_parity.py` | T8 |
| `tests/test_assisted_approve_flow.py` | T4 + approve（后期） |
| `tests/test_auto_allowed_send.py` | T2 |

---

## 4. Mock 与 fixtures

```text
@pytest.fixture
def mock_send_message(monkeypatch):
    calls = []
    monkeypatch.setattr("Channel.pinduoduo.utils.API.send_message.SendMessage.send_text",
                        lambda self, uid, text: calls.append(("send_text", uid)) or {"success": True})
    return calls

@pytest.fixture
def send_decision_preview_allowed():
    return SendDecision(..., intent_bucket="allowed", reply_mode="preview",
                        allowed_to_send=False, send_mode="preview_only")
```

---

## 5. CI 与 flag

| 项 | 要求 |
|----|------|
| CI 默认 | 不设置 `product_gate_enabled`；T8 必须通过 |
| Gate on 套件 | 单独 job 或 `@pytest.mark.product_gate` |
| `USE_UNIFIED_OUTBOUND_RESOLVER` | T2/T10 各测 on/off 子集（可选） |

---

## 6. 验收标准（12f 签收）

| # | 标准 |
|---|------|
| 1 | T10 合并前必须通过 |
| 2 | T8 证明 gate off = 生产等价 |
| 3 | T3 + T5 证明 auto 不越权 |
| 4 | 无新增默认 true 的 env/flag |

---

*Phase 12c · Test Plan · docs only*

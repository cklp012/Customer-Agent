# Phase 12f — Test Implementation Plan T1–T12（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only · **tests 在 13a+ 实现** |
| 前置 | [phase12c_test_plan.md](phase12c_test_plan.md) · [phase12f_guarded_send_design.md](phase12f_guarded_send_design.md) |

---

## 1. 测试分层

| 层 | 范围 | Phase |
|----|------|-------|
| **Unit** | gates 纯函数、merge、build_send_decision | 13a |
| **Unit** | send_text_guarded + mock port | 13a |
| **Integration** | AIReplyHandler + patch SendMessage | 13b–13c |
| **Contract** | gate off legacy parity | 每阶段 CI |

**禁止 12f：** 不添加 `tests/` 文件。

---

## 2. 用例定义

### T1 — `product_gate_disabled_legacy_unchanged`

| 项 | 值 |
|----|-----|
| 配置 | `product_gate_enabled=false` |
| 动作 | 运行现有 handler 路径 / 黄金消息 fixture |
| 断言 | `SendMessage.send_text` 调用次数与 **基线** 一致 |
| 断言 | 不写入 `send_decisions`（或 shadow flag off） |
| 断言 | 无 `send_text_guarded` 调用（spy） |

---

### T2 — `preview_zero_send`

| 项 | 值 |
|----|-----|
| 配置 | `product_gate_enabled=true`, `reply_mode=preview` |
| 输入 | allowed consultation 文本 |
| 断言 | AI 生成被调用（mock bot） |
| 断言 | `SendMessage.send_text` **0** |
| 断言 | `outbound.send_text` **0** |
| 断言 | ReplyLog 存在 |

---

### T3 — `blocked_refund_auto_never_sends`

| 项 | 值 |
|----|-----|
| 输入 | 「我要退款」/ `refund_request` |
| 配置 | `reply_mode=auto`, gate on |
| 断言 | `allowed_to_send=false` |
| 断言 | `send_mode=human_takeover` 或 blocked |
| 断言 | zero send |
| 断言 | HumanTakeoverQueue 条目（DB 或 mock repo） |

---

### T4 — `paused_overrides_everything`

| 项 | 值 |
|----|-----|
| 配置 | `workspace_pause=true` 或 `shop_pause=true` |
| 配置 | 另可 `reply_mode=auto`, allowed intent |
| 断言 | zero send |
| 断言 | `blocked_reason` 含 paused |

---

### T5 — `allowed_consultation_auto_sends`

| 项 | 值 |
|----|-----|
| 输入 | `product_question`, confidence=0.9, risk=low |
| 配置 | `reply_mode=auto`, gate on |
| 断言 | `allowed_to_send=true` |
| 断言 | `send_text` **1** 次成功 |
| 断言 | ReplyLog `send_status=sent` |

---

### T6 — `assisted_requires_approval`

| 项 | 值 |
|----|-----|
| 配置 | `reply_mode=assisted`, gate on |
| 动作 | 生成建议，**无** approve |
| 断言 | zero send |
| 动作 | `approve` 后再 guard |
| 断言 | 有 approve 时 1 send（且 commitment pass） |

---

### T7 — `low_confidence_uncertain`

| 项 | 值 |
|----|-----|
| 输入 | allowed intent, confidence=0.4 |
| 配置 | `reply_mode=auto` |
| 断言 | `intent_bucket=uncertain` 或 low_confidence reason |
| 断言 | zero auto send |
| 断言 | Preview 可 `allowed_to_generate=true`（子用例） |

---

### T8 — `classifier_failure_defaults_safe`

| 项 | 值 |
|----|-----|
| 模拟 | `classify_intent` 抛错 / 返回 invalid |
| 断言 | bucket=uncertain |
| 断言 | auto 不 send |
| 断言 | 不抛到买家路径 |

---

### T9 — `doudian_non_production_unchanged`

| 项 | 值 |
|----|-----|
| 范围 | Doudian mock handler tests 基线 |
| 断言 | 无 gate on 的 Doudian 店 |
| 断言 | 无真实 Doudian API 调用 |
| 断言 | 现有 11g tests 仍绿 |

---

### T10 — `audit_log_required_for_mode_change`

| 项 | 值 |
|----|-----|
| 动作 | pause / resume / reply-mode change / auto enable |
| 断言 | AuditLog 表或 mock `audit_writer` 各 1 条 |
| 断言 | `action` 字段符合 12d API |
| 断言 | `before_json` / `after_json` 含 reply_mode |

**注：** API 层测试；H4+ 可与 UI 分离。

---

### T11 — `preview_reply_log_contains_not_sent_preview`

| 项 | 值 |
|----|-----|
| 配置 | preview + gate on |
| 断言 | ReplyLog.`send_status == not_sent_preview` |
| 断言 | `sent_at is None` |
| 断言 | `ai_suggested_reply` 非空 |

---

### T12 — `no_direct_send_bypass`

| 项 | 值 |
|----|-----|
| 配置 | gate on 测试店 |
| 方法 | patch `SendMessage.send_text` at class level |
| 动作 | 跑完整 `AIReplyHandler.handle` |
| 断言 | 所有 send 经 `send_text_guarded`（spy 链） |
| 可选 | grep CI：`product_gate_enabled` 路径无 `SendMessage(` 字面调用 |

---

## 3. 建议文件布局（13a+）

| 文件 | 用例 |
|------|------|
| `tests/gates/test_keyword_risk.py` | T3 词表部分 |
| `tests/gates/test_merge_intent.py` | keyword 覆盖 AI |
| `tests/gates/test_build_send_decision.py` | T4, T7 |
| `tests/ports/test_guarded_send.py` | T2, T5, T6, T11 |
| `tests/handlers/test_product_gate_legacy_parity.py` | T1 |
| `tests/handlers/test_preview_zero_send_integration.py` | T2, T12 |
| `tests/handlers/test_auto_blocked_integration.py` | T3, T5 |
| `tests/test_doudian_gate_unchanged.py` | T9 |

---

## 4. Fixtures

```python
@pytest.fixture
def shop_legacy():
    return ShopBindingSnapshot(product_gate_enabled=False, reply_mode="preview")

@pytest.fixture
def shop_preview_gate_on():
    return ShopBindingSnapshot(product_gate_enabled=True, reply_mode="preview", ...)

@pytest.fixture
def mock_send_message(monkeypatch):
    calls = []
    ...
    return calls
```

**Shop snapshot 来源（测试）：** 内存构造；不依赖 SaaS DB migration。

---

## 5. CI 策略

| Job | 内容 |
|-----|------|
| `test-legacy` | T1 + 全量现有 tests，无 gate |
| `test-product-gate` | T2–T8, T11–T12，`@pytest.mark.product_gate` |
| 合并要求 | 两 job 绿 |

---

## 6. 与 12c T1–T10 映射

| 12c | 12f |
|-----|-----|
| T1 preview | T2 + T11 |
| T2 auto allowed | T5 |
| T3 refund | T3 |
| T8 legacy | T1 |
| T10 zero-send | T2 + T12 |

**12f 新增：** T10 audit, T11 explicit status, T12 bypass, T8 classifier failure.

---

*Phase 12f · Test Implementation Plan · docs only*

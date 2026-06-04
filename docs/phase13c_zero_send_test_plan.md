# Phase 13c — Zero-Send Test Plan（Z1–Z10）

| 项 | 值 |
|----|-----|
| 类型 | docs only（测试 **13d/13e 实现**） |
| 对齐 | [phase12f_test_implementation_plan.md](phase12f_test_implementation_plan.md) T2/T11 · [phase13c_preview_integration_flow.md](phase13c_preview_integration_flow.md) |
| 执行命令 | `uv run python -m unittest discover -s tests -v` |

---

## 1. 测试分层

| 层 | Phase | 文件（建议） |
|----|-------|--------------|
| 纯函数 | 13a ✅ | `tests/test_product_gate_*.py` |
| Shadow | 13b ✅ | `tests/test_handler_shadow_*.py` |
| Preview gate integration | **13d** | `tests/handlers/test_preview_zero_send_integration.py` |
| ReplyLog read model | **13e** | `tests/test_preview_reply_log_*.py` |

---

## 2. 公共 fixture（13d）

```python
# 概念 — tests/fixtures/test_shop_allowlist.py
TEST_SHOP = {
    "workspace_id": "ws-test-0001",
    "shop_id": "shop_pdd_preview_test",
    "account_id": "acc_pdd_preview_test",
    "platform_id": "pinduoduo",
    "product_gate_enabled": True,
    "reply_mode": "preview",
    "consultation_only": True,
}
NON_TEST_SHOP_ID = "shop_pdd_production_like"
```

**Patch 目标（所有 Z* 发送断言）：**

- `Channel.pinduoduo.utils.API.send_message.SendMessage.send_text`
- `Message.handlers.outbound_resolver.resolve_pinduoduo_outbound` → 非 None 时 adapter `send_text`
- `AIReplyHandler._send_reply`（spy：test shop **不应** await）

---

## 3. 测试用例矩阵

### Z1 — `test_shop_preview_zero_send`

| 项 | 内容 |
|----|------|
| 前置 | allowlist 命中 test shop |
| 配置 | `product_gate_enabled=true`, `reply_mode=preview` |
| 输入 | 商品咨询文案，如「这款还有库存吗」 |
| Mock | `_get_ai_reply` 返回固定建议 |
| 断言 | `SendMessage.send_text` **not called** |
| 断言 | `outbound.send_text` **not called** |
| 断言 | `_send_reply` **not called** |
| 断言 | preview log / ReplyLog **written** |
| 断言 | `send_status == not_sent_preview` |
| 断言 | `handle()` 返回 True（处理成功 ≠ 发送成功） |

---

### Z2 — `non_test_shop_legacy_unchanged`

| 项 | 内容 |
|----|------|
| 前置 | allowlist **未**命中 |
| 配置 | 默认 `product_gate_enabled=false` |
| 断言 | `_send_reply` **called once** |
| 断言 | legacy send 路径与 13b 回归一致 |
| 断言 | `evaluate_guarded_send` **not called**（或仅单元测试隔离） |

---

### Z3 — `blocked_intent_preview_no_send`

| 项 | 内容 |
|----|------|
| 前置 | test shop + gate on |
| 输入 | 「我要退款」/「投诉」 |
| 断言 | no SendMessage / no outbound |
| 断言 | `intent_bucket=blocked` |
| 断言 | `send_status=not_sent_human_takeover`（或 `human_takeover` 等价） |
| 断言 | `blocked_reason` / `human_takeover_reason` 非空 |

---

### Z4 — `classifier_failure_test_shop_safe`

| 项 | 内容 |
|----|------|
| 前置 | test shop |
| Mock | `classify_consultation_intent` raises |
| 断言 | **no send** |
| 断言 | decision 落 uncertain 或 safe default |
| 断言 | handler 不 raise 到 consumer（不 crash 队列） |

---

### Z5 — `shadow_logger_failure_does_not_affect_non_test_shop`

| 项 | 内容 |
|----|------|
| 前置 | non-test shop |
| Mock | `append_shadow_decision_from_handler` raises |
| 断言 | legacy `_send_reply` **still called** |
| 断言 | `handle()` 成功路径与 13b 一致 |

---

### Z6 — `doudian_not_enabled`

| 项 | 内容 |
|----|------|
| 前置 | Context `channel_type=DOUDIAN` 或 mock Doudian handler |
| 断言 | `select_product_gate_config` 返回 legacy |
| 断言 | 不加载 test shop allowlist 为 gate-on |
| 断言 | 无 product gate production path |

---

### Z7 — `no_direct_send_bypass`

| 项 | 内容 |
|----|------|
| 前置 | test shop preview path |
| 断言 | 无代码路径从 preview 分支直接调用 `_send_text_legacy` |
| 断言 | 无 `SendMessage` import 于 gate 分支内的 side-effect send |
| 静态（可选） | grep / AST 检查 preview 分支文件 |

---

### Z8 — `product_gate_disabled_legacy`

| 项 | 内容 |
|----|------|
| 前置 | test `shop_id` 但在 allowlist 中 `product_gate_enabled=false` |
| 断言 | 与 Z2 相同 — legacy send |
| 断言 | 不写 `not_sent_preview` 为唯一状态（可为 shadow only） |

---

### Z9 — `paused_test_shop_no_send`

| 项 | 内容 |
|----|------|
| 前置 | test shop + `workspace_pause=true` 或 `shop_pause=true` |
| 断言 | no send |
| 断言 | `send_status=not_sent_paused`（或 guarded_send 等价） |
| 断言 | pause 覆盖 allowed intent |

---

### Z10 — `reply_log_status`

| 项 | 内容 |
|----|------|
| 场景 A | preview + allowed intent → `not_sent_preview` |
| 场景 B | preview + blocked intent → `not_sent_human_takeover` |
| 场景 C | preview + paused → `not_sent_paused` |
| 断言 | log 含 `ai_suggested_reply` 与 `buyer_message` |
| 断言 | `product_gate_enabled=true` snapshot |

---

## 4. 与 12f T* 映射

| 12f | 13c Z |
|-----|-------|
| T2 preview_zero_send | Z1 |
| T1 legacy unchanged | Z2, Z8 |
| T7 blocked | Z3 |
| T8 fail-safe | Z4 |
| T11 reply_log | Z10 |
| T12 no bypass | Z7 |

---

## 5. 13d 完成定义（测试门禁）

| 门禁 | 要求 |
|------|------|
| CI | Z1–Z10 全绿 |
| 回归 | 13a + 13b 全量 unittest 仍 OK |
| 手工 | [phase13c_rollback_and_safety.md](phase13c_rollback_and_safety.md) checklist 一项 |

---

*Zero-send test plan · Phase 13c · 2026-06-03*

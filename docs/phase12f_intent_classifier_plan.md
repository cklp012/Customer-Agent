# Phase 12f — Intent Classifier Implementation Plan（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 对齐 | [phase12b1_consultation_only_scope.md](phase12b1_consultation_only_scope.md) · [phase12c_intent_gate_design.md](phase12c_intent_gate_design.md) |

---

## 1. 目标

产出 **SendDecision** 输入：`intent`, `intent_bucket`, `intent_confidence`, `risk_level`, `decision_source`。

**prompt 不能替代 intent gate** — classifier 为代码路径硬约束；LLM 回复生成与分类 **解耦**（分类可先 rule，后小模型）。

---

## 2. 两层架构

```text
normalized_text
  → Layer 1: keyword_risk_scan()     # 硬拦截
  → Layer 2: classify_intent()       # rule + optional AI
  → merge_decision()                 # 取更严格
  → build_send_decision()            # + reply_mode, pause
```

建议模块：`Message/gates/intent.py`（13a 纯函数）。

---

## 3. Layer 1 — Keyword risk scan

### 3.1 Block 词表（高风险 · 子串 MVP）

| 类别 | 示例词 / 短语 | 映射 intent |
|------|---------------|-------------|
| 退款 | 退款、退钱、退货款 | `refund_request` |
| 赔偿 | 赔偿、赔我、补偿 | `compensation_request` |
| 投诉 | 投诉、举报 | `complaint` |
| 差评 | 差评、给一星 | `bad_review_threat` |
| 售后纠纷 | 纠纷、售后问题 | `after_sales_dispute` |
| 质量 | 假货、质量问题、坏了 | `quality_dispute` |
| 改单 | 改订单、取消订单 | `order_change` |
| 改址 | 改地址、换地址 | `address_change` |
| 改价 | 便宜点、改价、优惠多少 | `price_negotiation` |
| 平台 | 平台介入、规则不公 | `platform_rule_dispute` |

**数据源：** `SafetySettings.human_takeover_keywords` + 系统默认表 + legacy `keywords` DB（过渡）。

### 3.2 输出

```python
@dataclass
class KeywordRiskResult:
    hit: bool
    matched: list[str]
    suggested_intent: str | None
    force_bucket: Literal["blocked"] | None  # 命中 block 表时
```

### 3.3 硬规则

> **keyword risk scan 命中 block 级时，不允许 AI classifier 覆盖为 allowed。**

```python
if keyword.force_bucket == "blocked":
    intent_bucket = "blocked"
    decision_source = "keyword_rule"
    # AI 结果仅作 audit 附加字段，不改变 bucket
```

### 3.4 覆盖范围

- 对 **normalize 后文本** 扫描，**不** 仅限 `ContextType.TEXT`。
- `ORDER_INFO` / `GOODS_INQUIRY` 摘要并入 `normalized_text` 再扫。

---

## 4. Layer 2 — AI / rule intent classification

### 4.1 Allowed consultation（allowlist）

| intent |
|--------|
| `product_question` |
| `size_or_spec_question` |
| `inventory_question` |
| `usage_question` |
| `comparison_question` |
| `store_faq` |
| `promotion_question` |
| `basic_shipping_question` |
| `recommendation_question` |

### 4.2 Blocked（与 12b.1 一致）

`refund_request`, `compensation_request`, `complaint`, `bad_review_threat`, `after_sales_dispute`, `quality_dispute`, `order_change`, `address_change`, `price_negotiation`, `platform_rule_dispute`

### 4.3 Uncertain

`mixed_intent`, `low_confidence`, `unclear_context`, `missing_product_context`, `emotional_message`

### 4.2 MVP 规则分类器（13a 首选）

| 规则 | intent / bucket |
|------|-----------------|
| `ContextType.ORDER_INFO` | `order_change` → **blocked** |
| 含「吗」+ 尺码/颜色/码 | `size_or_spec_question` → allowed |
| 含「库存」「有货」 | `inventory_question` |
| 默认 TEXT 无 block 词 | `product_question` + confidence 0.7 |
| 长度 < 2 | `unclear_context` → uncertain |

### 4.3 Growth：轻量 LLM classifier

- 输入：`normalized_text` + optional goods_id
- 输出：JSON `{ intent, confidence }`
- **温度 0**；失败 → §5

**禁诺：** classifier prompt **禁止** 生成回复，仅分类。

---

## 5. merge_decision 规则

```python
def merge_keyword_and_classifier(kw: KeywordRiskResult, clf: ClassifierResult) -> MergedIntent:
    if kw.force_bucket == "blocked":
        return blocked(kw.suggested_intent or clf.intent, source="keyword_rule")
    if clf.intent_bucket == "blocked":
        return blocked(clf.intent, source="combined")
    if clf.confidence < threshold:  # default 0.85 for auto eligibility; 0.6 for bucket
        return uncertain("low_confidence", clf.intent)
    if clf.intent_bucket == "uncertain":
        return uncertain(clf.intent)
    if clf.intent_bucket == "allowed":
        return allowed(clf.intent, clf.confidence, risk="low" if confidence >= 0.85 else "medium")
    return uncertain("unclear_context")
```

| 条件 | auto 可发送 |
|------|-------------|
| merged.bucket == allowed | 候选 |
| confidence >= 0.85 | 必须 |
| risk_level == low | 必须 |
| no keyword block | 必须 |

---

## 6. classifier 失败 → 安全默认

| 失败类型 | 行为 |
|----------|------|
| LLM 超时 / 解析错误 | `intent=low_confidence`, bucket=**uncertain**, confidence=0 |
| 空文本 | uncertain |
| 异常 | **no auto send**；`allowed_to_generate` 可 true（Preview 仍出建议） |

**T8：** classifier 失败 → zero auto send。

---

## 7. 进入 SendDecision

`build_send_decision(merged, shop_binding, workspace_pause)` 填充：

- `allowed_to_send` per 12c 优先级
- `send_mode`: preview_only | human_takeover | auto_send | …
- `blocked_reason` / `human_takeover_reason`

**blocked intent：** `send_mode=human_takeover`；enqueue `HumanTakeoverQueue`（DB 就绪后）。

---

## 8. 与 prompt / tools 边界

| 组件 | 12f 后角色 |
|------|------------|
| `message_builder` / instructions | 仅影响 **文案**，不决定 send |
| `search_customer_service_knowledge` | gate on + consultation_only：禁用或仅 Preview 内部 |
| KeywordDetectionHandler | 逐步 **合并** 到 risk scan；避免双转人工冲突 |

---

## 9. 测试要点（13a）

- keyword 「退款」→ blocked，AI 返回 product_question **仍** blocked
- 无词表「能退吗」→ rule/LLM → refund_request or uncertain，**非** auto
- ORDER_INFO → blocked
- classifier exception → uncertain（T8）

---

*Phase 12f · Intent Classifier Plan · docs only*

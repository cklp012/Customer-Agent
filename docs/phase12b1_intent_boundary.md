# Phase 12b.1 — Intent Boundary & Processing Matrix（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 关联 | [phase12b1_consultation_only_scope.md](phase12b1_consultation_only_scope.md) · [phase12b1_send_gate_requirements.md](phase12b1_send_gate_requirements.md) |

---

## 1. 消息处理管线（目标态）

```text
buyer message
  → normalize                    # 类型统一、提取文本/商品/订单摘要
  → keyword risk scan            # 高风险词快速路径
  → AI or rule-based intent      # 分类 → allow | block | uncertain
  → consultation safety gate     # 禁诺、scope、takeover
  → reply_mode gate              # preview | assisted | auto
  → send decision                # allowed_to_send + 平台 API
```

**与当前生产差异：** 现为 `KeywordDetectionHandler(TEXT)` → `AIReplyHandler` → send；**无** intent 层、**无** 店铺级 send gate。

---

## 2. Intent 分类来源（设计）

| 阶段 | 方法 | 说明 |
|------|------|------|
| MVP | 规则 + 关键词 + 轻量模型 | block 词表优先；allow 咨询类模板 |
| Growth | 小模型 / LLM 分类器 | 输出 `intent` + `intent_confidence` |
| 增强 | `ContextType` + 订单状态 + 商品卡 | `ORDER_INFO` 默认倾向 block/uncertain |

**输出字段（最小）：** `intent`, `intent_confidence`, `risk_level` (`low`|`medium`|`high`), `intent_bucket` (`allowed`|`blocked`|`uncertain`).

---

## 3. Intent × ReplyMode 处理矩阵

### 3.1 Allowed intent（咨询白名单）

| reply_mode | 行为 |
|------------|------|
| `preview` | 生成 `suggested_reply`；**不发送**；记 `outcome=preview_only` |
| `assisted` | 生成建议；**等待** `merchant_approve` 后 send |
| `auto` | **仅当** `intent_confidence ≥ 阈值` 且 `risk_level=low` 且禁诺通过 → 可自动 send |

### 3.2 Blocked intent（售后 / 纠纷 / 改单等）

| reply_mode | 行为 |
|------------|------|
| `preview` | 可选：生成 **内部** 备注建议（**不** 展示为可发给买家的文案）；**永不** send |
| `assisted` | **必须** 人工确认；默认 **`transfer_to_human`**，不代发 AI 正文 |
| `auto` | **禁止** 自动 send；**强制** `human_takeover` / `transfer_to_human` |

### 3.3 Uncertain intent

| reply_mode | 行为 |
|------------|------|
| `preview` | 允许生成建议；UI 标「不确定」 |
| `assisted` | 建议 + **须** 人工确认；推荐转人工 |
| `auto` | **禁止** 自动 send |

---

## 4. 决策优先级（SSOT）

**从高到低：**

```text
paused
  > human_takeover
  > blocked_intent
  > uncertain_intent
  > reply_mode
  > send
```

| 优先级 | 条件 | 效果 |
|--------|------|------|
| 1 | `workspace_pause` OR `shop_pause` | **永不发送**（auto/assisted）；Preview 建议可配置继续生成 |
| 2 | `human_takeover`（会话级） | 该会话 **不** AI 自动 send |
| 3 | `intent_bucket=blocked` | **永不 auto send**；转人工 |
| 4 | `intent_bucket=uncertain` OR `intent_confidence < threshold` | **不 auto send** |
| 5 | `reply_mode=preview` | **永不发送** |
| 6 | `reply_mode=assisted` | 无 approve → 不发送 |
| 7 | `reply_mode=auto` + allowed + high confidence + safety pass | **可发送** |

### 4.1 关键不变量

> **`reply_mode=auto` 不能覆盖 intent safety gate。**

即使商家开启 Auto，**blocked intent** 与 **uncertain + 低置信** 仍 **不得** 调用平台 send API。

---

## 5. Keyword risk scan 与 intent 关系

| 层 | 职责 |
|----|------|
| Keyword | **快速 block 路径**；命中高风险词 → 可直接 `blocked_intent` 或 `transfer` |
| Intent 分类 | 细粒度 allow/block/uncertain；处理未命中关键词的变体表述 |
| Consultation safety gate | 禁诺（退款承诺、时效承诺等）**发送前** 最后一道 |

**禁止：** 仅依赖 `ContextType.TEXT` 才做关键词检测（当前生产缺陷）。

---

## 6. Intent ID 与 bucket 映射

| bucket | intent IDs |
|--------|------------|
| **allowed** | `product_question`, `size_or_spec_question`, `inventory_question`, `usage_question`, `comparison_question`, `store_faq`, `promotion_question`, `basic_shipping_question`, `recommendation_question` |
| **blocked** | `refund_request`, `compensation_request`, `complaint`, `bad_review_threat`, `after_sales_dispute`, `quality_dispute`, `order_change`, `address_change`, `price_negotiation`, `platform_rule_dispute` |
| **uncertain** | `mixed_intent`, `low_confidence`, `unclear_context`, `missing_product_context`, `emotional_message` |

---

## 7. 与 handler_chain 的概念映射（未来）

| 当前 handler | 目标 |
|--------------|------|
| `KeywordDetectionHandler` | 并入 **risk scan**；扩展非 TEXT |
| （无） | **IntentClassificationHandler** 或 AI 前置分类 |
| `AIReplyHandler` | 仅接收 `allowed` + 非 takeover；生成前注入 scope |
| send | 独立 **SendGate**（12c），非 handler 内隐式 send |

---

## 8. ReplyLog 扩展字段（12e 规划）

| 字段 | 说明 |
|------|------|
| `intent` | 上表 ID |
| `intent_confidence` | 0–1 |
| `intent_bucket` | allowed / blocked / uncertain |
| `risk_level` | low / medium / high |
| `blocked_reason` | intent_blocked / commitment_guard / … |
| `human_takeover_reason` | keyword / manual / blocked_intent |

---

*Phase 12b.1 · Intent Boundary · docs only*

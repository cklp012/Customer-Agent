# Phase 14s — Default Policy Matrix

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 用途 | 新 shop 默认 · policy read failure fallback · UI seed |

---

## 1. 原则

| # | 原则 |
|---|------|
| 1 | **新 shop 默认保守** |
| 2 | 商家可在 **platform_ceiling 内** 调整 `ai_intervention_mode` |
| 3 | **红线不可放宽**（ceiling=blocked 的 category） |
| 4 | test shop preview **仍 zero-send**（reply_mode=preview） |
| 5 | 默认矩阵 **不写入 DB** 直至 14u · 运行时 fallback 用内存 SSOT |

---

## 2. 默认策略表

| intent_category | default_mode | platform_ceiling | notes |
|-----------------|--------------|------------------|-------|
| `product_question` | `assisted_only` | `auto_allowed` | 成熟商家可调 auto |
| `size_or_spec_question` | `assisted_only` | `auto_allowed` | 规格咨询 |
| `inventory_question` | `assisted_only` | `auto_allowed` | 禁虚假库存保证 · guard |
| `promotion_question` | `template_only` | `assisted_only` | 活动规则宜模板 |
| `shipping_basic` | `template_only` | `assisted_only` | 物流说明 · 禁绝对时效 |
| `refund_request` | `guide_only` | `assisted_only` | 引导售后入口 · 禁承诺退款 |
| `after_sales_question` | `guide_only` | `assisted_only` | 售后流程说明 |
| `compensation_request` | `assisted_only` | `assisted_only` | 禁止 auto · 禁金额承诺 |
| `gift_request` | `template_only` | `assisted_only` | 赠品规则说明 · 禁承诺送 |
| `complaint` | `assisted_only` | `assisted_only` | 安抚 · 禁 auto |
| `bad_review_threat` | `assisted_only` | `assisted_only` | 可配置 blocked · ceiling assisted_only |
| `order_change` | `guide_only` | `guide_only` | 引导平台改单流程 · 不可 auto |
| `address_change` | `guide_only` | `guide_only` | 引导平台改地址 · 不可 auto |
| `platform_rule_dispute` | `blocked` | `blocked` | human takeover |
| `private_contact` | `blocked` | `blocked` | 加微信/私聊 |
| `off_platform_payment` | `blocked` | `blocked` | 私下转账/绕平台 |
| `review_cashback` | `blocked` | `blocked` | 好评返现 |
| `delete_bad_review` | `blocked` | `blocked` | 删差评送礼 |

---

## 3. 与 intent classifier 映射（规划）

| classifier intent（示例） | intent_category |
|---------------------------|-----------------|
| stock_inquiry | inventory_question |
| refund_request | refund_request |
| compensation | compensation_request |
| address_change | address_change |
| … | 14t 完整映射表 |

---

## 4. 安全话术示例（refund · guide_only）

```
亲，退款需要您通过平台售后入口提交申请，我们会按照平台规则尽快处理哦。
```

- 适用：`refund_request` · `guide_only` · template `validation_status=passed`
- 发送前仍须 **final guard**

---

## 5. policy read failure fallback

| 场景 | 行为 |
|------|------|
| DB off / read error | 使用 **本表 in-memory 默认** · log warning |
| unknown category | 使用 `assisted_only` + ceiling `assisted_only`（保守） |
| 仍无法 resolve | **no-send** · 不 legacy fallback |

---

*Phase 14s · planning only · 2026-06-03*

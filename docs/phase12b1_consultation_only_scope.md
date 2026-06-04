# Phase 12b.1 — Consultation-only Scope（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | **产品化研究文档**（docs only） |
| 状态 | ✅ 边界对齐完成 |
| 关联 | [phase12b1_intent_boundary.md](phase12b1_intent_boundary.md) · [phase12b1_send_gate_requirements.md](phase12b1_send_gate_requirements.md) · [phase12b1_product_messaging_update.md](phase12b1_product_messaging_update.md) |

---

## 1. 产品重定位

### 1.1 原项目定位（代码与 README 现状）

| 维度 | 描述 |
|------|------|
| 产品形态 | **PDD 电商 AI 自动客服** 桌面应用 |
| 能力范围 | 更接近 **通用客服自动回复**：售前推荐 + **售后政策检索** + 关键词转人工 |
| 运行时 | WebSocket 收消息 → handler 链 → AI 生成 → **默认真实发送**（无店铺级 Preview gate） |
| 知识库 | 产品知识库 + **客服知识库**（售后、物流、退款 FAQ） |
| Agent 工具 | `get_product_knowledge`、`search_customer_service_knowledge`、`send_goods_link`、`transfer_conversation` |
| 消息类型 | `TEXT`、`GOODS_INQUIRY`、`ORDER_INFO`、图片/视频等均进 AI 队列 |

**结论：** 原项目 **不是** consultation-only；是全链路电商客服自动化工具。

### 1.2 新产品定位

| 维度 | 描述 |
|------|------|
| 对外名称 | **拼多多售前咨询 AI 副驾驶** / **商品咨询 AI 助手** |
| 核心价值 | 帮商家处理 **高频、重复、低风险** 的售前咨询；**不** 自动处理退款、赔偿、投诉、售后纠纷、订单修改 |
| 默认行为 | **Preview 优先** — 先看见 AI 会怎么回，再决定是否自动发（见 12a） |
| 平台范围 | MVP **仅 PDD**；多平台 waitlist，不宣传已全平台可用 |
| AI 供给 | **平台托管**；商家默认不自配 API Key |

### 1.3 核心原则

1. AI **主要负责** 售前咨询类问题（商品、规格、库存、对比、基础 FAQ、活动、基础发货说明、推荐）。
2. 退款、赔偿、投诉、差评威胁、售后纠纷、质量争议、改单改址改价、时效/补偿承诺、平台规则争议 → **默认转人工**，**禁止** auto 自动发送 AI 回复。
3. **consultation-only 不是改 README 一句话** — 后续 **handler、prompt、tool、send gate** 都必须遵守同一产品边界（见 §5）。

---

## 2. Allow — 可自动 / 半自动处理（咨询白名单）

以下 intent 在 **高置信 + 通过 consultation safety gate + reply_mode 允许** 时，可进入建议生成；`auto` 模式下才可自动发送（仍须禁诺扫描）。

| Intent ID | 中文场景 | 示例买家问法 |
|-----------|----------|--------------|
| `product_question` | 商品咨询 | 「这款是什么材质」「有几个颜色」 |
| `size_or_spec_question` | 尺码 / 规格 / 颜色 / 材质 | 「170 穿多大码」「M 码胸围多少」 |
| `inventory_question` | 库存咨询 | 「还有货吗」「什么时候补货」 |
| `usage_question` | 使用方式 | 「怎么用」「一天几次」 |
| `comparison_question` | 商品区别对比 | 「A 和 B 有什么区别」 |
| `store_faq` | 店铺基础 FAQ | 「包邮吗」「发什么快递」 |
| `promotion_question` | 活动说明 | 「有优惠券吗」「满减怎么算」 |
| `basic_shipping_question` | 基础发货说明（非承诺时效） | 「一般几天发出」「从哪发货」 |
| `recommendation_question` | 推荐商品 / 售前购买建议 | 「推荐一款洗面奶」「适合油皮吗」 |

**边界说明：**

- `basic_shipping_question` **不含**「保证明天到」「今天一定发」等承诺性表述 → 命中禁诺或降级为 uncertain/blocked。
- `store_faq` 仅覆盖 **可公开、低风险** 政策摘要；具体退款执行、个案赔付 **不在** allow 范围。

---

## 3. Block — 禁止自动发送，必须转人工

以下 intent **永不** 在 `reply_mode=auto` 下自动发送；`preview` 可生成 **内部/商家可见** 建议（可选，产品可配置为不生成）；`assisted` 须人工确认且通常应 **直接转人工** 而非代发承诺性回复。

| Intent ID | 中文场景 | 默认动作 |
|-----------|----------|----------|
| `refund_request` | 退款 | `transfer_to_human` |
| `compensation_request` | 赔偿 / 补偿 | `transfer_to_human` |
| `complaint` | 投诉 | `transfer_to_human` |
| `bad_review_threat` | 差评威胁 | `transfer_to_human` |
| `after_sales_dispute` | 售后纠纷 | `transfer_to_human` |
| `quality_dispute` | 质量争议 | `transfer_to_human` |
| `order_change` | 修改订单 | `transfer_to_human` |
| `address_change` | 修改地址 | `transfer_to_human` |
| `price_negotiation` | 改价 / 议价 | `transfer_to_human` |
| `platform_rule_dispute` | 平台规则争议 | `transfer_to_human` |

**与当前代码差距：** 生产 handler 仅对部分 **TEXT** 关键词转人工；未命中词表的售后类消息仍可能走 AI 并 **真实发送**。12c 起须 intent gate + send gate 落地。

---

## 4. Uncertain — Preview 或转人工

| Intent ID | 中文场景 | preview | assisted | auto |
|-----------|----------|---------|----------|------|
| `mixed_intent` | 混合意图（咨询+售后） | 建议 + 标 uncertain | 人工确认 / 转人工 | **禁止** |
| `low_confidence` | 分类置信度低 | 建议 | 人工确认 | **禁止** |
| `unclear_context` | 上下文不足 | 建议或转人工 | 人工确认 | **禁止** |
| `missing_product_context` | 缺商品 ID/卡片 | 建议（引导补信息） | 人工确认 | **禁止** |
| `emotional_message` | 情绪化 / 辱骂 / 威胁（非明确 block 词） | 建议转人工 | 转人工 | **禁止** |

---

## 5. 工程边界（为何不是「只改文案」）

| 层 | 须遵守 consultation-only 的变更（后续 Phase） |
|----|-----------------------------------------------|
| **入站 normalize** | 统一文本用于 keyword + intent（含 `ORDER_INFO` / `GOODS_INQUIRY`） |
| **Intent 分类** | allow / block / uncertain 枚举与矩阵（见 [phase12b1_intent_boundary.md](phase12b1_intent_boundary.md)） |
| **Keyword risk scan** | 补强 block 词表；避免单独依赖子串 |
| **Prompt / tools** | 售前 persona；**默认禁用或 gated** `search_customer_service_knowledge` 的「代为承诺」用法 |
| **Handler** | `AIReplyHandler` 类型白名单；block intent 短路 |
| **Send gate** | 店铺级 `reply_mode` + intent + pause（见 [phase12b1_send_gate_requirements.md](phase12b1_send_gate_requirements.md)） |
| **审计** | ReplyLog 记录 `intent`、`blocked_reason`、`allowed_to_send` |

```text
当前生产：买家消息 → Keyword(TEXT only) → AI(多类型) → send
目标产品：买家消息 → normalize → risk → intent → safety → reply_mode → send?
```

---

## 6. 与 Phase 12a / 12b 关系

| Phase | 关系 |
|-------|------|
| **12a** | Preview / 安全 / Onboarding — 12b.1 **收窄** MVP 为售前咨询副驾驶 |
| **12b** | ShopBinding、`reply_mode` — 12b.1 明确 **`reply_mode` ≠ 发送许可**，须 intent gate |
| **12c** | 技术设计：intent classification + dry-run send gate |
| **12e** | DB：`intent`、`risk_level`、`blocked_reason`、`human_takeover_reason` 等字段 |

---

## 7. 签收结论

| # | 结论 |
|---|------|
| 1 | 原项目 = **PDD 通用 AI 自动客服**，非 consultation-only |
| 2 | 新产品 = **PDD 售前咨询 AI 副驾驶** |
| 3 | Allow / Block / Uncertain 三张表为产品 SSOT |
| 4 | 实现须贯穿 handler、prompt、tool、send gate — **非 README  alone** |

---

*Phase 12b.1 · Consultation-only Scope · docs only*

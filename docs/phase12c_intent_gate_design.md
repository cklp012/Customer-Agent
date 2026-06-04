# Phase 12c — Intent Gate Design（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | **技术设计文档**（docs only · implementation 未开始） |
| 前置 | [phase12b1_consultation_only_scope.md](phase12b1_consultation_only_scope.md) · [phase12b1_intent_boundary.md](phase12b1_intent_boundary.md) |
| 关联 | [phase12c_send_decision_model.md](phase12c_send_decision_model.md) · [phase12c_handler_integration_plan.md](phase12c_handler_integration_plan.md) |

---

## 1. 目标

将运行时从：

```text
收到消息 → 生成回复 → 发送
```

升级为：

```text
buyer message
  → normalize
  → keyword risk scan
  → intent classification
  → consultation safety gate
  → reply_mode gate
  → send decision
  → preview / assisted / auto / human takeover
```

**不变量（12b.1）：**

- Preview **永不** send
- `reply_mode=auto` **不能**绕过 intent safety gate
- `paused` **最高**优先级
- blocked intent **永不** auto send

---

## 2. 端到端处理流程

```text
┌─────────────────────────────────────────────────────────────────┐
│ 1. normalize                                                     │
│    ContextType + content → normalized_text (+ goods/order hints) │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. keyword risk scan（第一道硬拦截）                              │
│    高风险词表 → risk_hit, suggested_intent?, force_blocked?       │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. intent classification（第二道判断）                            │
│    规则 + 可选 AI classifier → intent, confidence, bucket       │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. consultation safety gate                                      │
│    合并 keyword + intent；禁诺；human_takeover 会话状态             │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. reply_mode gate                                               │
│    ShopBinding.reply_mode + workspace_pause + shop_pause         │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. send decision → SendDecision 记录                              │
│    allowed_to_generate / allowed_to_send / send_mode             │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
        ┌───────────────────────┴───────────────────────┐
        ▼                       ▼                       ▼
   preview_only          assisted_required         auto_send
   human_takeover        (await approve)          (if allowed)
```

---

## 3. Step 1 — Normalize

| 输入 | 输出 |
|------|------|
| `Context`（type, content, kwargs） | `normalized_text: str` |
| `GOODS_INQUIRY` / `ORDER_INFO` / dict content | 结构化摘要并入 text 供分类 |
| `IMAGE` / `VIDEO` | 占位描述 + 可选 vision 标签（后期） |

**目的：** keyword scan 与 intent classifier **不** 仅依赖 `ContextType.TEXT`（修复当前 `KeywordDetectionHandler` 仅 TEXT 的缺口）。

**模块（未来）：** `Message/gates/normalize.py`（概念名，12f 实现）。

---

## 4. Step 2 — Keyword risk scan（第一道硬拦截）

| 属性 | 说明 |
|------|------|
| 优先级 | **先于** AI 生成；命中高风险可 **短路** 至 human takeover |
| 数据源 | DB 关键词 + SafetySettings `human_takeover_keywords` + **block 词表**（退款、投诉、赔偿、改地址…） |
| 匹配 | 子串（MVP）→ 后期正则/同义词 |
| 输出 | `keyword_risk_hit: bool`, `matched_keywords[]`, `keyword_suggested_intent?` |

**硬拦截规则：**

- 任一 **block 级** 关键词命中 → `intent_bucket` 至少为 `blocked`（或与 classifier 取 **更严格**）
- **关键词 OR AI** 判高风险 → **不得** `allowed_to_send=true` under `auto`

**与现有 `KeywordDetectionHandler` 关系：**

- 当前：命中 → **整链 break**，仅转人工，不走 AI
- 目标：risk scan **并入 gate**；Preview 下可对 block 消息 **仍生成内部建议**（可配置），但 **永不** send

---

## 5. Step 3 — Intent classification（第二道判断）

### 5.1 Intent bucket 与 ID（SSOT，同 12b.1）

**Allowed consultation**

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

**Blocked / human takeover**

| intent |
|--------|
| `refund_request` |
| `compensation_request` |
| `complaint` |
| `bad_review_threat` |
| `after_sales_dispute` |
| `quality_dispute` |
| `order_change` |
| `address_change` |
| `price_negotiation` |
| `platform_rule_dispute` |

**Uncertain**

| intent |
|--------|
| `mixed_intent` |
| `low_confidence` |
| `unclear_context` |
| `missing_product_context` |
| `emotional_message` |

### 5.2 分类器策略（分阶段）

| 阶段 | 实现 | 输出 |
|------|------|------|
| **MVP** | 规则：block 词表 + `ORDER_INFO` 默认 `order_change` 倾向 block | `intent`, `confidence`, `intent_bucket` |
| **Growth** | 轻量 LLM / 小模型 classifier | + `risk_level` |
| **合并** | `decision_source=combined` | keyword 与 AI **取更严格 bucket** |

### 5.3 合并规则（keyword ∪ classifier）

```text
if keyword_risk_hit AND keyword maps to blocked:
    intent_bucket = blocked  (confidence ≥ keyword_floor)
elif classifier.intent_bucket == blocked:
    intent_bucket = blocked
elif classifier.intent_bucket == uncertain OR confidence < threshold:
    intent_bucket = uncertain
elif classifier.intent_bucket == allowed:
    intent_bucket = allowed
else:
    intent_bucket = uncertain
```

**关键：** 关键词和 AI 判断 **任一** 命中高风险 → **不能** auto send。

---

## 6. Step 4 — Consultation safety gate

在 intent 之后、生成/发送之前：

| 检查 | 动作 |
|------|------|
| `intent_bucket=blocked` | `send_mode=human_takeover`；`allowed_to_send=false` |
| `intent_bucket=uncertain` | auto：**禁止** send；preview：可 `allowed_to_generate=true` |
| `intent_bucket=allowed` | 继续；须 `risk_level=low` 才考虑 auto |
| Commitment guard（禁诺） | 对 **生成后** 文案再扫（见 preview doc） |
| 会话 `human_takeover` 活跃 | 同 blocked — 不 auto send |

**Auto 允许条件（全部满足）：**

1. `intent_bucket=allowed`
2. `intent_confidence ≥ threshold`（默认 0.85，可配置）
3. `risk_level=low`
4. 无 keyword block 覆盖
5. 无 active human_takeover
6. `reply_mode=auto` 且非 paused
7. commitment guard pass（发送前）

---

## 7. Step 5 — Reply mode gate

| `reply_mode` | 与 intent 交互 |
|--------------|----------------|
| `preview` | `allowed_to_send=false`；可 `allowed_to_generate=true`（allowed/uncertain） |
| `assisted` | 生成后须 `merchant_approve`；blocked → 建议转人工 |
| `auto` | 仅 allowed + 高置信 + 低风险；**blocked 永不 send** |

**`paused`：** `workspace_pause` OR `shop_pause` → 覆盖一切发送（见 SendDecision 优先级）。

---

## 8. Step 6 — Send decision

产出 [SendDecision](phase12c_send_decision_model.md) 并驱动后续：

| `send_mode` | 行为 |
|-------------|------|
| `none` | 不生成、不发送（可选：paused 严格模式） |
| `preview_only` | 生成建议 + 写日志；**零** send |
| `assisted_required` | 生成 + 待审批 |
| `auto_send` | 过 final guard 后 outbound/legacy |
| `human_takeover` | 转人工；不 auto 发 AI 正文 |

---

## 9. 行为矩阵（intent × reply_mode 摘要）

| bucket | preview | assisted | auto |
|--------|---------|----------|------|
| **allowed** | 建议，不发 | 建议，待确认 | 高置信可发 |
| **blocked** | 可选内部备注；**不发** | 转人工；**不发** | **禁止**；转人工 |
| **uncertain** | 建议+标 uncertain | 须确认 | **禁止** |

**blocked intent 默认 `human_takeover`**（执行或仅记录由产品阶段决定；MVP 可先 `transfer` 标记 + Preview 不调用平台 API）。

**uncertain intent 默认：** preview 展示建议；auto **禁止**；assisted 须人工确认或转人工。

---

## 10. 非目标（12c）

- 不修改 `Message/handlers/*.py`
- 不修改 `SendMessage`
- 不默认开启 `USE_UNIFIED_OUTBOUND_RESOLVER`
- 不改变 `pdd_{shop_id}` 队列名

---

## 11. 实现 Phase 引用

| Phase | 内容 |
|-------|------|
| **12e** | SendDecision / ReplyLog 持久化 |
| **12f** | flag-gated 代码接入（见 handler integration plan） |

---

*Phase 12c · Intent Gate Design · docs only*

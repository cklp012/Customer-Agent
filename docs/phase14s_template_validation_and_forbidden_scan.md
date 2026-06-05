# Phase 14s — Template Validation and Forbidden Scan

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14s_policy_template_data_model.md](phase14s_policy_template_data_model.md) · [phase13f_risk_controls.md](phase13f_risk_controls.md) |

---

## 1. Scan Points（四层）

| # | 时点 | 对象 | 失败行为 |
|---|------|------|----------|
| 1 | **template save/update** | `content` 原文 | `validation_status=rejected/pending_review` |
| 2 | **AI draft 生成后** | model output | 不进入 send · 或降级 template/human |
| 3 | **merchant edit 后** | assisted 编辑稿 | approve 前 block |
| 4 | **final guard 发送前** | 渲染后完整文本 | **no-send** · `final_guard_blocked` |

**原则：**

- passed 模板 **仍须** 发送前 final guard
- merchant approve **不能** bypass scan
- template variables **白名单** · 渲染后 **整句 rescan**

---

## 2. Forbidden Categories

| 类别 | 说明 |
|------|------|
| 退款承诺 | 直接承诺退款结果/时效 |
| 赔偿承诺 | 承诺赔偿金额 |
| 补偿承诺 | 承诺补偿/红包 |
| 改订单承诺 | 承诺帮改订单 |
| 改地址承诺 | 承诺帮改地址 |
| 催平台违规承诺 | 暗示绕过规则加速 |
| 绕平台交易 | 线下/站外成交 |
| 私下转账 | 支付宝/微信转账 |
| 加微信/私聊 | 导流私域 |
| 好评返现 | 好评送礼金 |
| 删差评送礼 | 删评补偿 |
| 虚假库存保证 | 100%有货 |
| 绝对化物流时效 | 一定/保证明天到 |
| 违规赠品承诺 | 承诺必送/免费送 |

---

## 3. 中文关键词示例（非 exhaustive）

| 类别 | 示例关键词/短语 |
|------|-----------------|
| 退款 | 退款 · 给你退 · 马上退 · 全额退 |
| 赔偿/补偿 | 赔偿 · 补偿 · 给你赔 · 赔你 |
| 改单/改址 | 改地址 · 改订单 · 帮你改 |
| 私联/绕平台 | 私下 · 转账 · 加微信 ·  vx · 不走平台 |
| 差评/返现 | 删差评 · 返现 · 好评送礼 |
| 绝对承诺 | 一定今天到 · 保证明天到 · 100% |

**实现 note（14v）：** 关键词 + 规则引擎 + 可选 ML · 平台 core 与 merchant `forbidden_keywords_extra` **合并**（extra 只加严）。

---

## 4. validation_status 判定

| 结果 | 条件 | 模板可用? |
|------|------|-----------|
| `rejected` | 命中 platform 红线禁词 | ❌ 不可 enable |
| `pending_review` | 可疑但未硬命中 | ⚠️ 人工复核前不可用 |
| `passed` | save scan 通过 | ✅ 可用 · 发送仍 guard |

---

## 5. Template Variables

| 规则 | 说明 |
|------|------|
| 白名单 | `{buyer_nick}` · `{shop_name}` · `{platform_after_sales_link}` 等 |
| 禁止 | 自由 HTML · script · 外链私域 |
| 渲染 | 替换变量 → **完整文本 rescan**（scan point 1b / 4） |

---

## 6. 安全话术示例

**允许（refund · guide）：**

```
亲，退款需要您通过平台售后入口提交申请，我们会按照平台规则尽快处理哦。
```

**拒绝（template save · rejected）：**

```
亲没问题，我现在就给你退款50元，不用走平台。
```

---

## 7. 与 merchant policy 关系

| 场景 | policy | scan | 结果 |
|------|--------|------|------|
| policy=auto_allowed · 模板含「马上退」 | 允许参与 | save **rejected** | 模板不可用 |
| policy=assisted_only · AI 草稿含禁诺 | 允许生成 | draft scan **block** | 不可 approve 发送 |
| policy=template_only · passed 模板 | 允许 | guard pass | 可发送引导话术 |
| merchant approve 改稿为禁诺 | — | edit scan **block** | no-send |

**Merchant policy 不能 override final guard.**

---

*Phase 14s · planning only · 2026-06-03*

# Phase 14t — Forbidden Promise Scan Rules

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14s_template_validation_and_forbidden_scan.md](phase14s_template_validation_and_forbidden_scan.md) · G22–G24 |

---

## 1. 扫描对象

**`final_reply` 最终渲染文本**（assisted/auto 发送前 · preview 可记录但不 send）

| 来源 | 是否进入 final_reply |
|------|----------------------|
| AI draft | ✅ 若未 edit |
| merchant_edited_reply | ✅ 优先于 AI |
| rendered template | ✅ 变量替换后整句 |
| guide_only 受限生成 | ✅ |

**AI draft / template 保存 scan 不能替代本 scan。**

---

## 2. Forbidden Categories

| 类别 | block_code | 说明 |
|------|------------|------|
| 直接退款承诺 | `forbidden_promise` | 承诺退款结果/时效/金额 |
| 直接赔偿承诺 | `forbidden_promise` | 赔你/赔偿 |
| 补偿金额承诺 | `forbidden_promise` | 红包/补偿金额 |
| 改订单承诺 | `forbidden_promise` | 帮改单 |
| 改地址承诺 | `forbidden_promise` | 帮改址 |
| 私下转账 | `off_platform_risk` | 支付宝/微信转账 |
| 加微信/私聊 | `off_platform_risk` | 导流私域 |
| 绕平台交易 | `off_platform_risk` | 不走平台/站外 |
| 好评返现 | `review_manipulation` | 好评送礼金 |
| 删差评送礼 | `review_manipulation` | 删评补偿 |
| 虚假库存保证 | `forbidden_promise` | 100%有货 |
| 绝对化物流时效 | `forbidden_promise` | 一定/保证到达 |
| 违规赠品承诺 | `forbidden_promise` | 必送/免费送 |
| 威胁/诱导撤诉撤差评 | `review_manipulation` | 威胁买家 |

---

## 3. 中文关键词示例（非 exhaustive）

| 类别 | 示例 |
|------|------|
| 退款 | 我给你退 · 直接退款 · 马上退 · 全额退 |
| 赔偿/补偿 | 给你赔 · 赔你 · 补偿你 · 红包给你 |
| 改单/改址 | 改地址 · 改订单 · 帮你改 |
| 私联/绕平台 | 私下 · 转账 · 加微信 · 加我 · vx · 不走平台 |
| 差评/返现 | 好评返现 · 删差评 · 送你别差评 · 别给差评 |
| 绝对承诺 | 一定今天到 · 保证明天到 · 肯定有货 · 100% |

**实现（14v）：** 规则引擎 + 归一化（大小写/全半角）+ 可选 LLM second opinion · **规则优先**。

---

## 4. 允许的安全话术

| 场景 | 示例 | 判定 |
|------|------|------|
| 退款引导 | 亲，退款需要您通过平台售后入口提交申请，我们会按照平台规则尽快处理哦。 | **allow** |
| 改址引导 | 修改地址请在订单详情页申请，或联系平台客服协助。 | **allow** |
| 时效说明 | 物流时效以平台显示为准，我们会尽快为您安排发货。 | **allow**（无绝对承诺） |

**区分关键：** 引导 **平台流程** vs **承诺结果**。

---

## 5. 与 effective_mode

| mode | forbidden scan |
|------|----------------|
| blocked | 通常无 final_reply send · N/A |
| guide_only | 必须通过 · 且 G8 mode check |
| template_only | 渲染后必须通过 |
| assisted_only | approve 后必须通过 |
| auto_allowed | **仍必须**通过 · **不可绕过** |

---

## 6. merchant forbidden_keywords_extra

- 商家仅可 **追加** 禁词 · 不可删除平台 core
- 合并进 scan · 只加严

---

## 7. LLM second opinion（future · optional）

| 项 | 规则 |
|----|------|
| 用途 | 边界 case · 非替代规则 |
| 默认 | **off** |
| block | 规则命中 → 直接 block · 不等待 LLM |

---

*Phase 14t · planning only · 2026-06-03*

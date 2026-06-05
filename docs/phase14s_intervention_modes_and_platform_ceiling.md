# Phase 14s — Intervention Modes and Platform Ceiling

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14s_merchant_safety_policy_plan.md](phase14s_merchant_safety_policy_plan.md) |

---

## 1. `ai_intervention_mode` 五档

| mode | 含义 | AI 行为 | 发送形态（future） |
|------|------|---------|-------------------|
| `blocked` | AI 不介入 | 不生成 · 不模板 · 转人工 / no-send | 无 outbound |
| `guide_only` | 仅引导平台流程 | 不承诺结果 · 指向售后/规则入口 | template 或固定 guide · 通常 assisted_only 或 no-send |
| `template_only` | 仅商家预设模板 | 禁止 free-form AI 草稿 | template 渲染 · assisted 或 auto（仍 guard） |
| `assisted_only` | AI 可生成建议 | 须 merchant confirm | pending → approve → guard → outbound |
| `auto_allowed` | 允许自动回复 | 仍须 final guard | auto path · guard 不过则 no-send |

**关键：**

- `auto_allowed` **不等于** 可发违规承诺
- `guide_only` **禁止** 「我给你退款」类结果承诺
- `template_only` **禁止** 使用未 validation 通过的模板

---

## 2. `platform_mode_ceiling`

每个 `intent_category` 有系统定义的 **上限 mode**；商家配置的 mode 不得超过 ceiling。

```text
effective_mode = min(merchant_policy.ai_intervention_mode,
                      platform_mode_ceiling[intent_category])
```

| 规则 | 说明 |
|------|------|
| platform hard rules **高于** merchant policy | 红线不可被商家放宽 |
| merchant 不能把红线提高到 `auto_allowed` | UI disabled / hidden |
| `effective_mode` 决定 pipeline 分支 | send_decision 输入 |
| final guard **仍可 block** | 即使 `effective_mode=auto_allowed` |

**UI 规划：**

- 选项超过 ceiling → **disabled + tooltip**（「平台规则限制」）
- 保存 policy 时服务端 **再次校验** ceiling（防 API 绕过）

---

## 3. Platform 红线（不可配置放宽）

| intent_category / 场景 | ceiling / 强制 mode | 说明 |
|------------------------|---------------------|------|
| `private_contact` 加微信/私聊 | **blocked** | 永远 blocked |
| `off_platform_payment` 私下转账/绕平台 | **blocked** | 永远 blocked |
| `review_cashback` 好评返现 | **blocked** | 永远 blocked |
| `delete_bad_review` 删差评送礼 | **blocked** | 永远 blocked |
| `platform_rule_dispute` 平台规则争议 | **blocked** | human takeover |
| `refund_request` 退款 | ceiling **assisted_only** | 不可 auto_allowed |
| `compensation_request` 赔偿/补偿 | ceiling **assisted_only** | 不可 auto_allowed |
| `order_change` 改订单 | ceiling **guide_only** | 不可 auto / 通常不可 assisted 承诺改单 |
| `address_change` 改地址 | ceiling **guide_only** | 同上 |
| `complaint` / `bad_review_threat` | ceiling **assisted_only** | 不可 auto_allowed |

**直接承诺类（文本级 · final guard，与 mode 无关）：**

- 我直接给你退款 / 我给你赔 / 不用走平台 → **guard block**
- 加微信 / 私下转账 → **guard block**
- 给好评返现 / 删差评送礼 → **guard block**
- 我保证明天到 / 一定今天到 → **guard block**
- 我帮你改地址 / 改订单 → **guard block**

---

## 4. Mode 与 reply_mode 关系

| shop `reply_mode` | 约束 |
|-------------------|------|
| `preview` | 仅记录建议 · zero-send（test shop 当前） |
| `assisted` | 最高 `assisted_only` 行为 · 即使 policy=auto_allowed 也降级？**14t 定**：建议 shop assisted 时 effective 最高 assisted_only |
| `auto`（future） | 仅当 effective_mode=auto_allowed 且 guard pass |

**14s 规划：** shop 级 `reply_mode` 与 per-intent `effective_mode` **取 min**。

---

## 5. 与 final guard 关系

```
effective_mode  →  允许参与 / 生成路径
final_guard     →  允许发送（文本级）
```

| 场景 | effective_mode | guard | 结果 |
|------|----------------|-------|------|
| 退款 guide 模板 | guide_only | pass | 可 assisted/auto 发送 **引导话术** |
| 退款 AI 草稿含「马上退」 | assisted_only | **block** | no-send |
| 商家 policy=auto_allowed | auto_allowed | **block** | no-send |
| 红线 intent | blocked | N/A | no-send · 无生成 |

**Merchant policy 永远不能 override final guard.**

---

*Phase 14s · planning only · 2026-06-03*

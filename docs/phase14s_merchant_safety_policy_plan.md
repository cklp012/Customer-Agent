# Phase 14s — Merchant Safety Policy + Template Planning

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不写代码** |
| 日期 | 2026-06-03 |
| 前置 | [phase14r_done.md](phase14r_done.md) · [phase14q_done.md](phase14q_done.md) · [phase13f_done.md](phase13f_done.md) |
| 调整 | 原「Phase 14s Final Guard Implementation Planning」→ **本 phase 聚焦 Merchant Safety Policy + Template** |

---

## 1. Phase 14s 定位

| 项 | 结论 |
|----|------|
| 交付 | **仅文档** |
| Python 代码 | **未写** |
| DB 表 | **未创建**（`merchant_safety_policies` · `merchant_reply_templates`） |
| Final guard 实现 | **未实现**（14t 规划 · 14v 实现） |
| Assisted / auto send | **未实现** |
| handler / SendMessage / PDD / Doudian | **未改** |
| Dashboard API（14o） | **未改** |

Phase 14s 在 14r（AssistedReplyService 流程规划）之上，规划 **SaaS 商家可配置的 AI 参与策略** 与 **安全话术模板**，同时保留 **platform hard rules** 与 **final guard** 作为不可协商底线。

---

## 2. 产品方向调整（相对 13f/14p 默认）

| 之前倾向 | 14s 规划方向 |
|----------|--------------|
| refund / compensation / gift / complaint 等默认 block / human takeover | 商家可在 **platform ceiling 内** 配置 AI 参与方式 |
| 一刀切 no-send | 分级：`blocked` → `guide_only` → `template_only` → `assisted_only` → `auto_allowed` |
| 固定平台话术 | 商家可配置 **MerchantReplyTemplate**（须 validation + final guard） |

**不变底线：**

- 商家配置的是 **AI 参与方式**，不是 **违规承诺许可**
- 「AI 介入」≠「AI 可以承诺退款/赔偿/赠品/改地址/改订单」
- forbidden promise / 私联 / 绕平台 / 好评返现 / 删差评送礼 → **永远不可自动发送**

---

## 3. 核心概念

### 3.1 MerchantSafetyPolicy

决定：对某个 `intent_category`，AI **是否可以参与**、**以何种方式参与**。

| 职责 | 不负责 |
|------|--------|
| `ai_intervention_mode` | 文本是否合规（属 final guard） |
| `allowed_template_ids` | 绕过 platform 红线 |
| `require_human_confirmation` | legacy send fallback |

### 3.2 MerchantReplyTemplate

商家配置的 **安全话术**；用于 `template_only` / `guide_only` 等模式。

| 职责 | 不负责 |
|------|--------|
| 平台流程引导话术 | 含禁诺内容的「自定义承诺」 |
| 变量占位（白名单） | 发送前跳过 final guard |

---

## 4. 核心原则（中英）

**English:**

> **Merchant policy decides whether / how AI may participate.**  
> **Final guard decides whether the final text may be sent.**

**中文：**

> **商家策略决定 AI 能不能参与、以什么方式参与；**  
> **final guard 决定最终这句话能不能发送。**

| 规则 | 说明 |
|------|------|
| Merchant policy **不能** override platform hard rules | 红线 intent 永远 blocked 或 ceiling 上限 |
| Merchant policy **不能** override final guard | 文本不过 guard → no-send |
| Final guard 仍是发送前最后安全门 | assisted approve / auto 均须过 guard |
| DB / audit / snapshot failure | **不 fallback legacy send** |

---

## 5. 与现有 Phase 关系

| Phase | 关系 |
|-------|------|
| 14l–14n ReplyLog / SendDecision snapshot | 未来写入 **policy snapshot** metadata |
| 14o Dashboard read | 未来展示 policy/template · 本 phase 不改 API |
| 14q AuditLog | 未来 `merchant_policy_changed` · `template_*` |
| 14r AssistedReplyService | approve 前须 policy + guard；本 phase 先定 policy SSOT |
| 14i test shop preview | **仍 zero-send** · policy 规划不改变当前 runtime |

---

## 6. 文档索引

| 文档 | 内容 |
|------|------|
| [phase14s_intervention_modes_and_platform_ceiling.md](phase14s_intervention_modes_and_platform_ceiling.md) | 五档 mode · ceiling · 红线 |
| [phase14s_policy_template_data_model.md](phase14s_policy_template_data_model.md) | 数据模型 |
| [phase14s_pipeline_and_precedence.md](phase14s_pipeline_and_precedence.md) | pipeline · 优先级 |
| [phase14s_default_policy_matrix.md](phase14s_default_policy_matrix.md) | 默认策略矩阵 |
| [phase14s_template_validation_and_forbidden_scan.md](phase14s_template_validation_and_forbidden_scan.md) | 模板验证 · 禁诺 scan |
| [phase14s_policy_snapshot_and_audit.md](phase14s_policy_snapshot_and_audit.md) | snapshot · audit |
| [phase14s_test_plan.md](phase14s_test_plan.md) | S1–S16 |

---

## 7. 当前 runtime（unchanged）

- test shop preview：**zero-send**
- non-test legacy：**unchanged**
- flags 默认 off · product persistence 可选 shadow
- assisted / auto：**未实现**

---

## 8. 下一步 Phase 建议

| Phase | 内容 |
|-------|------|
| **14t** | Final Guard Planning **with Merchant Policy Integration** |
| **14u** | MerchantSafetyPolicy + MerchantReplyTemplate **schema skeleton** behind flags |
| **14v** | Final Guard **pure function** implementation |

---

*Phase 14s · planning only · 2026-06-03*

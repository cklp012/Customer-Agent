# Phase 12a 完成 — Merchant UX + Shop Binding + Safety Preview Research

| 项 | 内容 |
|----|------|
| 状态 | **纯文档已完成**（产品化阶段入口） |
| 日期 | 2026-06-03 |
| 类型 | docs only — **无代码、无测试变更** |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 阶段转变 | 项目从 **技术架构/mock spike** 进入 **产品化 + SaaS 售卖** 并行规划 |
| 售卖主线 | **拼多多客服 AI 副驾驶** — Preview 优先，非「多平台全自动机器人」 |
| Doudian | **未来平台**；10k–11g mock **非** 当前售卖主菜 |
| AI API | 普通商家 **默认不需要** 自配 Key；**平台托管** 打包进套餐 |
| PDD 生产 | **未改**；工程默认路径仍冻结 |

---

## 新增文档

| 文件 | 内容 |
|------|------|
| [phase12a_merchant_onboarding_ux.md](phase12a_merchant_onboarding_ux.md) | 商家全流程：注册 → 绑定 → Preview → 开启自动发送 → 付费 |
| [phase12a_shop_binding_playbook.md](phase12a_shop_binding_playbook.md) | PDD/抖店/淘宝/京东绑定方式；OAuth 优先 |
| [phase12a_safety_and_preview_spec.md](phase12a_safety_and_preview_spec.md) | Preview / Assisted / Auto；禁诺、暂停、日志 |
| [phase12a_ai_provider_and_billing_model.md](phase12a_ai_provider_and_billing_model.md) | 平台托管 AI、BYOK、企业私有模型 |
| [phase12a_mvp_scope_and_pricing.md](phase12a_mvp_scope_and_pricing.md) | MVP 范围；Starter / Growth / Pro |

---

## 核心产品结论

1. **绑定店铺 ≠ 开启自动回复**；默认 **Preview / Dry-run**。  
2. **开启 Auto** 须二次确认；**一键暂停** 常驻。  
3. **SaaS 绑定** 长期主路径：**官方 OAuth**；Playwright/密码仅过渡。  
4. **MVP** = PDD + Preview + 安全规则 + 日志 + 平台托管 AI + 用量。  
5. **不包含** 默认全自动、真实抖店 production、商家默认自配 API。

---

## 后续 Phase 建议

| Phase | 内容 |
|-------|------|
| **12b** ✅ | SaaS 数据模型 — [phase12b_done.md](phase12b_done.md) |
| **12c** | Reply preview / dry-run **技术设计**（店铺级 gate send） |
| **12d** | Connection status + Dashboard **信息架构** 设计 |
| **12e** | Merchant account **DB migration planning**（legacy → SaaS 表） |
| **12f** | Safety rules engine + 禁诺/转人工 **产品+技术** 设计 |
| **12g** | Billing / plan limits / AI 额度计量 |
| **12h** | PDD binding 升级（OAuth 或托管连接器）research |
| **13+** | 真实 API prototype（flag off） |

**并行（11h 技术 gate）：** Doudian API research 可单列 **12g-T** 或并入 12g，**不阻塞** PDD MVP 产品化。

---

*签收：Phase 12a · 2026-06-03 · docs only*

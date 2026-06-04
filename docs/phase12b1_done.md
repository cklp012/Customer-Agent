# Phase 12b.1 完成 — Consultation-only Scope Alignment

| 项 | 内容 |
|----|------|
| 状态 | **纯文档已完成** |
| 日期 | 2026-06-03 |
| 类型 | 产品定位收窄：售前咨询 AI 副驾驶 |
| SSOT 入口 | [phase12b1_consultation_only_scope.md](phase12b1_consultation_only_scope.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 代码 / tests | **未改** |
| DB migration | **未做** |
| UI / PDD 热路径 / Channel | **未改** |
| flags 默认值 | **未改** |

---

## 新增文档

| 文件 | 内容 |
|------|------|
| [phase12b1_consultation_only_scope.md](phase12b1_consultation_only_scope.md) | 原定位 vs 新定位；Allow / Block / Uncertain 三表 |
| [phase12b1_intent_boundary.md](phase12b1_intent_boundary.md) | 处理管线；intent × reply_mode 矩阵；优先级 |
| [phase12b1_send_gate_requirements.md](phase12b1_send_gate_requirements.md) | Send decision 字段；发送规则；店铺级 gate |
| [phase12b1_product_messaging_update.md](phase12b1_product_messaging_update.md) | 对外话术 SSOT |

---

## 核心签收

| # | 结论 |
|---|------|
| 1 | **原项目不是 consultation-only** — 更接近 PDD 通用 AI 自动客服 |
| 2 | **新产品定位** = **拼多多售前咨询 AI 副驾驶** / 商品咨询 AI 助手 |
| 3 | 退款 / 赔偿 / 投诉 / 售后纠纷 / 订单修改 → **默认转人工**，**禁止 auto send** |
| 4 | consultation-only ≠ 改 README — 须 handler / prompt / tool / send gate 一致 |
| 5 | **`reply_mode=auto` 不能覆盖 intent safety gate** |

---

## 更新的文档

| 文件 | 变更摘要 |
|------|----------|
| [phase12a_merchant_onboarding_ux.md](phase12a_merchant_onboarding_ux.md) | AI 可回答范围；Auto 确认；Preview intent 展示 |
| [phase12a_safety_and_preview_spec.md](phase12a_safety_and_preview_spec.md) | consultation safety gate 管线 |
| [phase12a_mvp_scope_and_pricing.md](phase12a_mvp_scope_and_pricing.md) | MVP 售前咨询定位与包含/排除 |
| [phase12b_reply_mode_and_control_model.md](phase12b_reply_mode_and_control_model.md) | reply_mode vs intent gate |
| [phase12b_shop_binding_state_model.md](phase12b_shop_binding_state_model.md) | consultation_only / reply_scope |
| [architecture_current.md](architecture_current.md) | Phase 12b.1；consultation-first |
| [docs/README.md](README.md) | 12b.1 索引 |
| [phase12b_done.md](phase12b_done.md) | next → 12c |

---

## 后续 Phase

| Phase | 状态 | 内容 |
|-------|------|------|
| **12c** | ✅ | Intent gate + SendDecision + preview dry-run — [phase12c_done.md](phase12c_done.md) |
| **12d** | 待做 | Connection Status Dashboard IA + API Contract |
| **12e** | 待做 | DB migration：SendDecision / ReplyLog / ShopBinding |
| **12f** | 待做 | flag-gated implementation：preview send gate + tests T1–T10 |

---

*签收：Phase 12b.1 · 2026-06-03 · docs only*

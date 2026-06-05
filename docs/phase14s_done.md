# Phase 14s 完成 — Merchant Safety Policy + Template Planning

| 项 | 内容 |
|----|------|
| 状态 | **docs only · 规划完成** |
| 日期 | 2026-06-03 |
| 前置 | [phase14r_done.md](phase14r_done.md) · [phase14q_done.md](phase14q_done.md) |
| 调整 | 原 Phase 14s Final Guard Implementation Planning → **本 phase** |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 类型 | **仅文档** |
| Python 代码 | **未写** |
| DB 表 | **未创建** |
| Final guard 实现 | **未实现** |
| MerchantSafetyPolicy / MerchantReplyTemplate 代码 | **未实现** |
| Assisted / auto send | **未实现** |
| handler / SendMessage / PDD / Doudian | **未改** |

---

## 新增文档

| 文档 | 内容 |
|------|------|
| [phase14s_merchant_safety_policy_plan.md](phase14s_merchant_safety_policy_plan.md) | 总体规划 |
| [phase14s_intervention_modes_and_platform_ceiling.md](phase14s_intervention_modes_and_platform_ceiling.md) | 五档 mode · ceiling · 红线 |
| [phase14s_policy_template_data_model.md](phase14s_policy_template_data_model.md) | 数据模型 |
| [phase14s_pipeline_and_precedence.md](phase14s_pipeline_and_precedence.md) | pipeline · 优先级 |
| [phase14s_default_policy_matrix.md](phase14s_default_policy_matrix.md) | 默认策略表 |
| [phase14s_template_validation_and_forbidden_scan.md](phase14s_template_validation_and_forbidden_scan.md) | 模板验证 · 禁诺 scan |
| [phase14s_policy_snapshot_and_audit.md](phase14s_policy_snapshot_and_audit.md) | snapshot · audit |
| [phase14s_test_plan.md](phase14s_test_plan.md) | S1–S16 |

---

## 规划结论（签收）

| # | 结论 |
|---|------|
| 1 | **Merchant policy** 决定 AI 参与方式 · **final guard** 决定文本能否发送 |
| 2 | **Merchant policy 不能 override final guard** |
| 3 | **Platform hard rules / 红线不可被商家放宽** |
| 4 | `effective_mode = min(merchant, ceiling, reply_mode)` |
| 5 | 模板/AI/edit **四层 scan** · 发送前 guard 不可跳过 |
| 6 | policy snapshot 写入 ReplyLog / SendDecisionSnapshot 规划 |
| 7 | 配置变更 AuditLog append-only |
| 8 | policy read failure → default 或 no-send · **不 legacy send** |
| 9 | test shop preview zero-send · non-test legacy **不变** |
| 10 | assisted / auto **未实现** |

---

## 核心原则（中英）

> Merchant policy decides whether / how AI may participate.  
> Final guard decides whether the final text may be sent.

> 商家策略决定 AI 能不能参与、以什么方式参与；  
> final guard 决定最终这句话能不能发送。

---

## 当前 runtime（unchanged）

- 14l–14q · 14o · 14r 交付物不变
- test shop：**zero-send**
- non-test legacy：**unchanged**

---

## 下一步

| Phase | 内容 |
|-------|------|
| **14t** | Final Guard Planning **with Merchant Policy Integration** |
| **14u** | MerchantSafetyPolicy + MerchantReplyTemplate **schema skeleton** behind flags |
| **14v** | Final Guard **pure function** implementation |

---

*签收：Phase 14s · docs only · 2026-06-03*

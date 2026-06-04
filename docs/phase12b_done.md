# Phase 12b 完成 — Merchant / Workspace / Shop Binding Data Model Design

| 项 | 内容 |
|----|------|
| 状态 | **纯文档已完成** |
| 日期 | 2026-06-03 |
| SSOT 入口 | [phase12b_data_model_plan.md](phase12b_data_model_plan.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 类型 | SaaS 核心**数据模型与状态机**设计 |
| DB migration | **未做** |
| 代码 / tests | **未改** |
| PDD / Doudian 热路径 | **未改** |
| Implementation | **未开始** |

---

## 新增文档

| 文件 | 内容 |
|------|------|
| [phase12b_data_model_plan.md](phase12b_data_model_plan.md) | 总览、对象列表、ER、MVP 范围 |
| [phase12b_merchant_workspace_model.md](phase12b_merchant_workspace_model.md) | Merchant / Workspace / Member |
| [phase12b_shop_binding_state_model.md](phase12b_shop_binding_state_model.md) | ShopBinding + 状态机 |
| [phase12b_credential_security_model.md](phase12b_credential_security_model.md) | CredentialRef |
| [phase12b_reply_mode_and_control_model.md](phase12b_reply_mode_and_control_model.md) | ReplyMode / Pause / SafetySettings |
| [phase12b_plan_usage_model.md](phase12b_plan_usage_model.md) | Plan / Usage |

---

## 核心不变量（签收）

| # | 结论 |
|---|------|
| 1 | **`binding_status=connected` ≠ 自动回复已开启** |
| 2 | **默认 `reply_mode=preview`** |
| 3 | **`paused`（workspace/shop）优先级最高** |
| 4 | **CredentialRef** 替代明文 password/cookie 展示 |
| 5 | 非 PDD MVP 平台 **`waitlist`**，非 production `connected` |
| 6 | 计费在 **Workspace**；平台托管 AI + UsageMeter |

---

## 后续

| Phase | 内容 |
|-------|------|
| **12c** | Reply preview / dry-run **技术设计**（gate send） |
| **12d** | Connection status **Dashboard** 设计 |
| **12e** | Merchant account **DB migration planning**（legacy → SaaS 表） |

---

*签收：Phase 12b · 2026-06-03 · docs only*

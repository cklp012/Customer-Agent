# Phase 12d 完成 — Connection Status Dashboard IA + API Contract

| 项 | 内容 |
|----|------|
| 状态 | **纯文档已完成** |
| 日期 | 2026-06-03 |
| SSOT 入口 | [phase12d_dashboard_ia.md](phase12d_dashboard_ia.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 代码 / tests | **未写 / 未改** |
| UI | **未改** |
| API 实现 | **未做** |
| DB migration | **未做** |
| PDD / Doudian 热路径 | **未改** |

---

## 新增文档

| 文件 | 内容 |
|------|------|
| [phase12d_dashboard_ia.md](phase12d_dashboard_ia.md) | 模块 A–H 信息架构 |
| [phase12d_connection_status_read_model.md](phase12d_connection_status_read_model.md) | effective_status · 四类 Summary |
| [phase12d_reply_activity_read_model.md](phase12d_reply_activity_read_model.md) | 活动聚合 · 队列 · 日志 |
| [phase12d_exception_and_alert_model.md](phase12d_exception_and_alert_model.md) | 11 类 alert |
| [phase12d_api_contract.md](phase12d_api_contract.md) | REST 草案 + audit |

---

## 核心签收

| # | 结论 |
|---|------|
| 1 | Dashboard 面向商家展示 **`effective_status`**，非原始 enum |
| 2 | **`connected` ≠ auto enabled** — IA + API 显性区分 |
| 3 | **pause / resume / reply-mode POST 必须 AuditLog** |
| 4 | **preview → auto** 须二次确认；**不能**绕过 intent gate |
| 5 | **platform_waitlist** 不得显示为已连接 |
| 6 | Implementation **未开始** |

---

## 更新的文档

| 文件 |
|------|
| [architecture_current.md](architecture_current.md) |
| [docs/README.md](README.md) |
| [phase12c_done.md](phase12c_done.md) |

---

## 下一步

| Phase | 内容 |
|-------|------|
| **12e** | DB migration：Workspace / ShopBinding / SendDecision / ReplyLog / AuditLog |
| **12f** | flag-gated preview send gate 实现 |
| **12g** | PDD MVP merchant console wireframe |

---

*签收：Phase 12d · 2026-06-03 · docs only*

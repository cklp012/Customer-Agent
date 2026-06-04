# Phase 12c 完成 — Intent Gate + Preview Send Gate Technical Design

| 项 | 内容 |
|----|------|
| 状态 | **纯文档已完成** |
| 日期 | 2026-06-03 |
| 类型 | Consultation intent gate + send decision + preview dry-run 技术设计 |
| SSOT 入口 | [phase12c_intent_gate_design.md](phase12c_intent_gate_design.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 代码 | **未写** |
| tests | **未改** |
| DB migration | **未做** |
| UI | **未改** |
| PDD 热路径 / Channel | **未改** |
| flags 默认值 | **未改** |
| Implementation | **未开始**（见 12f） |

---

## 新增文档

| 文件 | 内容 |
|------|------|
| [phase12c_intent_gate_design.md](phase12c_intent_gate_design.md) | normalize → keyword → intent → safety → reply_mode → send |
| [phase12c_send_decision_model.md](phase12c_send_decision_model.md) | SendDecision 字段与优先级 |
| [phase12c_preview_dry_run_technical_design.md](phase12c_preview_dry_run_technical_design.md) | Preview 永不 send；dry-run 日志 |
| [phase12c_handler_integration_plan.md](phase12c_handler_integration_plan.md) | 当前路径 + A/B/C 插入点 |
| [phase12c_test_plan.md](phase12c_test_plan.md) | T1–T10 未来测试 |

---

## 核心签收

| # | 结论 |
|---|------|
| 1 | **Preview 永不 send** — 含 legacy SendMessage、PinduoduoOutbound、unified outbound |
| 2 | **blocked intent 永不 auto send** — 默认 human takeover |
| 3 | **paused 最高优先级** — workspace_pause / shop_pause |
| 4 | **`reply_mode=auto` 不能绕过 intent safety gate** |
| 5 | SendDecision 是 **产品级 gate**，非 env flag |
| 6 | 必须 **final send guard**；不能仅靠 prompt / keyword_handler |
| 7 | **product_gate_enabled 默认 false** — PDD legacy 不变直至显式开启 |

---

## 更新的文档

| 文件 | 变更 |
|------|------|
| [architecture_current.md](architecture_current.md) | Phase 12c；implementation 未开始 |
| [docs/README.md](README.md) | 12c 索引 |
| [phase12b1_done.md](phase12b1_done.md) | next → 12c done / 12d / 12e / 12f |

---

## 下一步建议

| Phase | 状态 | 内容 |
|-------|------|------|
| **12d** | ✅ | Dashboard IA + read model + API contract — [phase12d_done.md](phase12d_done.md) |
| **12e** | 待做 | DB migration：Workspace / ShopBinding / SendDecision / ReplyLog / AuditLog |
| **12f** | 待做 | flag-gated preview send gate implementation |
| **12g** | 待做 | PDD MVP merchant console wireframe |

---

*签收：Phase 12c · 2026-06-03 · docs only*

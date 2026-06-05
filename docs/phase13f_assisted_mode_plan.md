# Phase 13f — Assisted Mode Plan（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | **docs only** · **本 Phase 不写代码** |
| 前置 | [phase13e_done.md](phase13e_done.md) · [phase12a_safety_and_preview_spec.md](phase12a_safety_and_preview_spec.md) |
| 实现 Phase | **14c+**（单店 assisted 代码，非本 Phase） |

---

## 1. 总体定位

**Assisted** 是 **Preview** 与 **Auto** 之间的中间模式：

| 维度 | Assisted |
|------|----------|
| AI 角色 | 仅生成 `ai_suggested_reply` |
| 发送时机 | **商家人工确认后** |
| 发送执行者 | **Merchant confirmation command/API** — **非** AI handler 生成阶段 |
| Auto | **本产品线暂不实现** |

```text
preview  → 建议 + zero-send（13d/13e 已实现）
assisted → 建议 + pending + merchant approve → send（规划）
auto     → 高置信低风险自动 send（未规划实现）
paused   → 不发送；生成可配置为停止或仅记录
```

---

## 2. 核心原则

| # | 原则 |
|---|------|
| P1 | **Assisted ≠ Auto** — 无商家确认不得发送 |
| P2 | **AI 不得自调用 SendMessage** — 生成与发送彻底解耦 |
| P3 | **Final guard 在确认时重跑** — `evaluate_guarded_send` + intent re-check |
| P4 | **AuditLog 全覆盖** — 每次 approve/reject/mode change 可审计 |
| P5 | **权限控制** — viewer 不可确认；operator+ 可确认 assisted |
| P6 | **Blocked intent** — 默认不允许普通一键确认发送 |
| P7 | **High-risk / uncertain** — human takeover 或 elevated confirmation |
| P8 | **Non-test shop** — 保持 legacy（与 13d 一致） |
| P9 | **Preview 仍 zero-send** — `reply_mode=preview` 行为不变 |
| P10 | **Doudian** — 不进入 assisted production path |

---

## 3. 模式对比表

| 模式 | AI 生成 | 平台 send | 商家动作 | send_status（典型） | 默认 |
|------|---------|-----------|----------|---------------------|------|
| **preview** | ✅ | ❌ 永不 | 仅查看建议 | `not_sent_preview` | ✅ 新绑定 |
| **assisted** | ✅ | ❌ 直至确认 | 点击确认/编辑后确认 | `not_sent_awaiting_approval` → `sent` | Growth 可选 |
| **auto** | ✅ | 条件允许时自动 | 无（须事前开启+二次确认） | `sent` / blocked | **未实现** |
| **paused** | 可配置 | ❌ | — | `not_sent_paused` | — |

**优先级（与 12a/12b.1 一致）：** `paused` > `human_takeover` > `blocked_intent` > `uncertain_intent` > `reply_mode` > send。

---

## 4. 与当前代码的关系

| Phase | 状态 | Assisted 如何使用 |
|-------|------|-------------------|
| 13d | ✅ | preview zero-send 路径 |
| 13e | ✅ | `list_preview_reply_logs()` read model |
| 13f | 本文档 | 规划 pending + confirmation |
| 14a | 待做 | `pending_assisted_replies` / `audit_logs` shadow schema |
| 14b | 待做 | confirmation command/API **规划** |
| 14c | 待做 | 单测试店 assisted **实现** |

**13f 不改：** handler · SendMessage · DB · UI · API。

---

## 5. Allowlist 与 rollout

与 [phase13c_test_shop_gate_selection.md](phase13c_test_shop_gate_selection.md) 一致：

- 仅 **显式 allowlisted** PDD test shop 可启用 `reply_mode=assisted`
- `product_gate_enabled=true` + 精确 `workspace_id` / `shop_id` / `account_id`
- 非 test shop → legacy
- 不得默认全 PDD 开启 assisted

---

## 6. 文档索引（Phase 13f 包）

| 文档 | 内容 |
|------|------|
| [phase13f_assisted_confirmation_flow.md](phase13f_assisted_confirmation_flow.md) | AI 生成 vs 商家确认 flow |
| [phase13f_auditlog_and_permissions.md](phase13f_auditlog_and_permissions.md) | 角色 · AuditLog |
| [phase13f_risk_controls.md](phase13f_risk_controls.md) | blocked · 禁诺 · stale |
| [phase13f_assisted_test_plan.md](phase13f_assisted_test_plan.md) | A1–A12 |
| [phase13f_done.md](phase13f_done.md) | 签收 |

---

## 7. 明确非目标（13f / 14c 前）

- Auto send 实现
- 全量商家默认 assisted
- AI handler 内直接调用 SendMessage 的 assisted 分支
- Doudian production outbound
- UI 实现

---

*Assisted mode plan SSOT · Phase 13f · 2026-06-03*

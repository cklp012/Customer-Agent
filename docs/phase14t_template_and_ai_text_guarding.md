# Phase 14t — Template and AI Text Guarding

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14s_template_validation_and_forbidden_scan.md](phase14s_template_validation_and_forbidden_scan.md) · [phase14t_forbidden_promise_scan_rules.md](phase14t_forbidden_promise_scan_rules.md) |

---

## 1. 文本来源与 scan 链

| 来源 | save scan | draft scan | edit scan | final guard |
|------|-----------|------------|-----------|-------------|
| AI draft | — | ✅ | — | ✅ |
| merchant template 原文 | ✅ | — | — | — |
| rendered template | — | — | — | ✅ |
| merchant edited reply | — | — | ✅ | ✅ |

**merchant approve 不能绕过 final guard.**

---

## 2. 按 effective_mode 约束

### blocked

- 无 AI 生成 · 无 outbound
- Guard：N/A 或 preempt `policy_blocked`

### guide_only

| 允许 | 禁止 |
|------|------|
| 平台流程说明模板 | 结果承诺 |
| 受限 phrase bank 生成 | free-form 长文 AI |
| 「请通过售后入口申请」 | 「马上给你退」 |

Guard：**G8 mode_violation** + forbidden scan

### template_only

| 要求 | Guard |
|------|-------|
| `template_id` 必填 | G9 |
| `validation_status=passed` | G10 |
| 渲染后 `final_reply` | G22–G24 |

**不可** 使用未 validation 模板 · 不可 free-form AI 替代

### assisted_only

| 要求 | Guard |
|------|-------|
| `pending_status=approved` | G11 |
| `final_reply` = edit 或 AI | forbidden scan |
| viewer 不可 approve | G5 |

### auto_allowed

| 要求 | Guard |
|------|-------|
| 仍完整 final guard | **全部 rules** |
| ceiling 不足 | G12 |

**auto_allowed 不能绕过 final guard.**

---

## 3. Template variables

| 规则 | 说明 |
|------|------|
| 白名单 | `{buyer_nick}` · `{shop_name}` · `{after_sales_link}` 等 |
| 禁止 | 自由 HTML · script · 外链私域 |
| 渲染 | 替换 → **完整文本** → final guard |
| 滥用 | 变量注入禁词 → G22 block |

**渲染后文本不得新增红线内容。**

---

## 4. merchant edited reply

```
approve flow:
  merchant_edited_reply optional
  final_reply = merchant_edited_reply or ai_suggested_reply
  edit scan (layer 3)
  final guard (layer 4)
  if block → no SendMessage
```

Approve **不等于** bypass scan.

---

## 5. AI draft

- 生成后立即 scan（layer 2）· 可疑则不可进入 pending approve
- 发送时 `final_reply` 再 scan（layer 4）
- 商家改一个字 → 全文 re-scan

---

## 6. preview 路径（test shop）

| 项 | 行为 |
|----|------|
| 可运行 guard | optional · 记录 `allowed_to_send` in snapshot |
| outbound | **禁止** · zero-send unchanged |
| 用途 | Dashboard 展示「若发送会被拦」 |

---

*Phase 14t · planning only · 2026-06-03*

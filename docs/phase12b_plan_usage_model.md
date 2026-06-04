# Phase 12b — Plan & Usage Model

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 关联 | [phase12a_mvp_scope_and_pricing.md](phase12a_mvp_scope_and_pricing.md) · [phase12a_ai_provider_and_billing_model.md](phase12a_ai_provider_and_billing_model.md) |

---

## 1. Plan（套餐定义 · 配置表）

| plan_id | plan_name | MVP |
|---------|-----------|-----|
| `starter` | Starter | ✅ |
| `growth` | Growth | ✅ |
| `pro` | Pro | 后期全量 |

---

## 2. PlanSubscription

| 字段 | 类型 | MVP | 说明 |
|------|------|-----|------|
| `subscription_id` | UUID | ✅ | |
| `workspace_id` | FK | ✅ | 计费主体 |
| `plan_id` | FK | ✅ | |
| `plan_name` | string | ✅ | 冗余展示 |
| `status` | enum | ✅ | `trialing` / `active` / `past_due` / `canceled` |
| `billing_cycle` | enum | ✅ | `monthly` / `yearly` |
| `started_at` | datetime | ✅ | |
| `renews_at` | datetime | ✅ | |
| `canceled_at` | datetime | 可空 | |
| `trial_ends_at` | datetime | 可选 | 14 天 |

---

## 3. PlanLimit（套餐能力 · 配置或 JSON）

| 字段 | Starter | Growth | Pro |
|------|---------|--------|-----|
| `max_shops` | 1 | 5 | 20+ |
| `max_ai_replies_per_month` | 2,000 | 30,000 | 100,000+ |
| `max_auto_replies_per_month` | 0 | 20,000 | 80,000+ |
| `max_members` | 1 | 3 | 20+ |
| `log_retention_days` | 7 | 30 | 90 |
| `byok_allowed` | false | false | true |
| `auto_mode_allowed` | false | true | true |
| `assisted_mode_allowed` | false | true | true |
| `preview_only` | **true** | false | false |

**存储：** `plan_limits` 表或 `plans.limits_json`。

---

## 4. UsageMeter（按账期滚动）

| 字段 | 类型 | MVP | 说明 |
|------|------|-----|------|
| `usage_meter_id` | UUID | ✅ | |
| `workspace_id` | FK | ✅ | |
| `period_start` | date | ✅ | 自然月 |
| `period_end` | date | ✅ | |
| `ai_suggestions_count` | int | ✅ | Preview 也计 |
| `auto_sent_count` | int | ✅ | |
| `assisted_sent_count` | int | ✅ | |
| `inbound_messages_count` | int | ✅ | 可选计量 |
| `failed_send_count` | int | ✅ | |
| `human_takeover_count` | int | ✅ | |
| `updated_at` | datetime | ✅ | |

**唯一约束：** `(workspace_id, period_start)`。

### 4.1 计数规则

| 事件 | 计数器 |
|------|--------|
| AI 生成建议（含 preview） | `ai_suggestions_count++` |
| auto 实际发送成功 | `auto_sent_count++` |
| assisted approve 后发送 | `assisted_sent_count++` |
| 入站消息（可选） | `inbound_messages_count++` |
| send 失败 | `failed_send_count++` |
| 转人工 | `human_takeover_count++` |

---

## 5. 平台托管 AI 与额度

| 原则 | 说明 |
|------|------|
| 默认 | `workspace.ai_provider_mode = platform_hosted` |
| 成本 | 平台承担；通过 `max_ai_replies_per_month` 控本 |
| 商家可见 | Dashboard 进度条「本月 AI 建议 / 额度」 |
| BYOK | `byok_allowed=true` 时不计入或单独计费 — Pro |

---

## 6. 额度不足行为

| 场景 | 系统行为 | 商家提示 |
|------|----------|----------|
| `ai_suggestions_count >= max_ai` | **停止新生成**；保留日志查看 | 「本月 AI 额度已用完，请升级」 |
| `auto_sent_count >= max_auto` | 禁止 auto 发送；可 assisted/preview | 「自动发送额度已用完」 |
| Starter + `auto_mode_allowed=false` | 拒绝设 `reply_mode=auto` | 「请升级 Growth」 |
| 接近 90% | 预警邮件/站内 | — |

**推荐降级顺序：**

```text
额度耗尽 → 禁止 auto/assisted 发送 → 仍允许 preview（Starter）或完全停止 AI（可配置）
绝不：静默改用商家未知模型或超发不计费
```

---

## 7. Starter preview-only  Enforcement

```text
if plan_limits.preview_only:
    ShopBinding.reply_mode must in (preview,)  # DB check + API
    reject reply_mode in (assisted, auto)
```

Growth 开启 auto 前检查 `auto_mode_allowed`。

---

## 8. 与 ShopBinding 联动

| 检查点 | 逻辑 |
|--------|------|
| 绑新店 | `count(shops) < max_shops` |
| 切 auto | `auto_mode_allowed` + 二次确认 + 额度 |
| 每月 1 日 | 新 UsageMeter 行；上月归档 |

---

## 9. MVP vs 后期

| MVP | 后期 |
|-----|------|
| 手动套餐 assignment | Stripe/支付宝 |
| 月度 UsageMeter | 实时 quota Redis |
| 超额硬停 | 软限+超量账单 |

---

*Phase 12b · Plan & Usage*

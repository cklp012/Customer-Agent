# Phase 14s — Pipeline and Precedence

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14s_merchant_safety_policy_plan.md](phase14s_merchant_safety_policy_plan.md) · [phase14r_assisted_service_plan.md](phase14r_assisted_service_plan.md) |

---

## 1. End-to-end Pipeline

```text
buyer message
  → intent classifier
  → intent_category normalization
  → platform hard rules
  → merchant safety policy resolve
  → reply_mode gate (preview / assisted / auto)
  → template match OR AI draft
  → send decision
  → final guard
  → preview | pending assisted | outbound
```

**当前 runtime（14i–14o）：** 仅 classifier → send_decision(preview) → in-memory ReplyLog · **zero-send**。本 pipeline 为 **future assisted/auto** SSOT · 不改变现有热路径直至显式接线的 phase。

---

## 2. 各层职责

| 层 | 输入 | 输出 | 职责 |
|----|------|------|------|
| **intent classifier** | buyer message | `intent` · confidence · bucket | 识别原始 intent |
| **intent_category normalization** | `intent` | `intent_category` | 映射到 policy key（refund_request, …） |
| **platform hard rules** | category · message | `platform_ceiling` · force_blocked? | **不可配置**红线 |
| **merchant safety policy resolve** | shop · category | `effective_mode` · templates | 商家参与方式 |
| **reply_mode gate** | shop config | caps effective_mode | preview/assisted/auto 店级上限 |
| **template match OR AI draft** | effective_mode | candidate text | 受 mode 约束的候选回复 |
| **send decision** | 上列 + gate | `allowed_to_generate` · `send_mode` · reasons | 为何 preview/assisted/no-send |
| **final guard** | candidate text · context | `allowed_to_send` · block reasons | **文本级**发送许可 |
| **preview / pending / outbound** | guard result | ReplyLog · Pending · SendMessage | 执行形态 |

---

## 3. 优先级（配置与模式）

```text
platform hard rules  >  merchant policy  >  reply_mode  >  send decision
```

**对于发送权限（文本）：**

```text
final guard has final say before outbound
```

| 冲突示例 | 裁决 |
|----------|------|
| merchant=auto_allowed · ceiling=assisted_only | effective=assisted_only |
| merchant=template_only · 无 passed 模板 | no-generate · fallback human |
| effective=auto_allowed · guard=blocked | **no-send** |
| shop reply_mode=preview | **zero-send**（无论 policy） |

---

## 4. effective_mode 计算（规划）

```python
# 规划示意 · 14s 不写代码
def resolve_effective_mode(merchant_mode, platform_ceiling, shop_reply_mode):
    mode = min_mode(merchant_mode, platform_ceiling)
    if shop_reply_mode == "preview":
        return mode  # 参与方式仍记录 · 但不 outbound
    if shop_reply_mode == "assisted":
        mode = min_mode(mode, "assisted_only")
    return mode
```

---

## 5. send_decision 与 policy 字段（future snapshot）

send_decision / SendDecisionSnapshot 应携带：

- `intent_category`
- `merchant_ai_intervention_mode`
- `effective_mode`
- `platform_mode_ceiling`
- `policy_id` · `policy_version`
- `template_id` · `template_version`（若使用）
- `policy_decision_reason`

decision_phase 示例：

- `ai_preview` — 已有（14n）
- `policy_resolved` — optional 中间 snapshot（14t 定）
- `merchant_confirm` — assisted approve 后（14r）

---

## 6. 与 Preview / Legacy 边界

| 路径 | pipeline 段 |
|------|-------------|
| test shop preview（14i） | classifier → send_decision(preview) → record · **跳过 outbound** · policy 可读可写 snapshot 但不改变 zero-send |
| non-test legacy | **不进入** merchant policy pipeline · `_send_reply` unchanged |
| Doudian | **不进入** production policy path（14s 规划） |

---

## 7. Failure 原则（pipeline 级）

| failure | 行为 |
|---------|------|
| policy read failure | conservative default matrix 或 no-send · **不 legacy send** |
| template render failure | no-send · log reason |
| guard failure | no-send · audit `final_guard_blocked` |
| audit/snapshot DB failure | 不 fallback legacy send |

---

*Phase 14s · planning only · 2026-06-03*

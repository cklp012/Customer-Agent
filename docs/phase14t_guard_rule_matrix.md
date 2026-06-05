# Phase 14t — Final Guard Rule Matrix

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14t_guard_input_output_contract.md](phase14t_guard_input_output_contract.md) · [phase14s_intervention_modes_and_platform_ceiling.md](phase14s_intervention_modes_and_platform_ceiling.md) |

---

## 1. 评估顺序（规划）

```text
1. Hard redline text rules (G22–G24) — 最高优先级
2. Platform / pause / gate (G1–G6)
3. Policy / mode (G7–G12)
4. Pending / assisted state (G13–G16)
5. Intent / risk (G17–G20)
6. Content / stale / channel (G21, G25–G26)
7. Internal (G27)
```

**allow 条件：** 所有 **required** rules pass · 无 block。

**所有 block → no-send。** Merchant policy **不能 override** any block.

---

## 2. Rule Matrix G1–G27

| ID | 条件 | block_code | 优先级 |
|----|------|------------|--------|
| **G1** | `product_gate_enabled=false` | `product_gate_disabled` | high |
| **G2** | `reply_mode` not in {assisted, auto} for send path | `invalid_reply_mode` | high |
| **G3** | `workspace_pause=true` | `workspace_paused` | high |
| **G4** | `shop_pause=true` | `shop_paused` | high |
| **G5** | assisted send · actor not in {operator, admin, owner} | `permission_denied` | high |
| **G6** | actor workspace/shop ≠ context | `ownership_mismatch` | high |
| **G7** | `effective_mode=blocked` | `policy_blocked` | high |
| **G8** | `effective_mode=guide_only` · text not platform guidance | `mode_violation` | medium |
| **G9** | `effective_mode=template_only` · no `template_id` | `template_required` | medium |
| **G10** | `template_validation_status != passed` | `template_not_validated` | high |
| **G11** | `effective_mode=assisted_only` · pending not approved | `assisted_approval_required` | high |
| **G12** | `auto_allowed` attempt · ceiling lower | `ceiling_violation` | high |
| **G13** | assisted send · `pending_assisted_id` missing | `pending_not_found` | high |
| **G14** | pending status ∉ {approved} for send | `invalid_pending_status` | high |
| **G15** | `now > expires_at` | `pending_expired` | high |
| **G16** | idempotency already consumed / status=sent | `duplicate_send_attempt` | high |
| **G17** | intent not consultation / policy unsafe | `unsafe_intent` | medium |
| **G18** | `risk_level=high` · policy未显式允许 | `high_risk` | medium |
| **G19** | `blocked_reason` set | `blocked_intent` | high |
| **G20** | `human_takeover_reason` set · 非 elevated flow | `human_takeover_required` | high |
| **G21** | `final_reply` empty | `empty_reply` | high |
| **G22** | forbidden promise in `final_reply` | `forbidden_promise` | **redline** |
| **G23** | private contact / off-platform in text | `off_platform_risk` | **redline** |
| **G24** | review cashback / delete bad review | `review_manipulation` | **redline** |
| **G25** | inbound stale (superseded / TTL) | `stale_message` | medium |
| **G26** | `outbound_channel_status=unavailable` | `outbound_unavailable` | high |
| **G27** | guard internal exception | `guard_exception` | high · fail-closed |

---

## 3. Mode-specific notes

### G8 guide_only

允许：平台售后入口引导 · 规则说明 · **无结果承诺**  
拒绝：「马上给你退」· 「我帮你改地址」

### G9 / G10 template_only

必须有 `template_id` + `validation_status=passed` · 渲染文本仍过 G22–G24

### G11 assisted_only

`pending_status=approved` · `approved_by` 非 viewer

### G12 ceiling_violation

merchant 配 auto · ceiling=assisted_only → block auto send path

---

## 4. Dashboard 展示

| block_code | 商家可见文案（示例） |
|------------|---------------------|
| `forbidden_promise` | 回复含不允许的承诺用语，已拦截发送 |
| `policy_blocked` | 该类咨询需人工处理 |
| `pending_expired` | 待确认回复已过期 |
| `template_not_validated` | 模板未通过安全校验 |

---

## 5. 与 merchant policy 关系

| 场景 | policy | guard | 结果 |
|------|--------|-------|------|
| auto_allowed + safe template | allow participate | pass | 可 outbound |
| auto_allowed + forbidden text | allow participate | **G22 block** | no-send |
| guide_only + safe guide | allow | pass | 可 outbound |
| assisted_only + approved + forbidden edit | allow | **G22 block** | no-send |

**Redline block 优先级高于 mode allow.**

---

*Phase 14t · planning only · 2026-06-03*

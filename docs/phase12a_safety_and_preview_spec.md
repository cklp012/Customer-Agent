# Phase 12a — Safety & Preview Spec（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | **产品化研究文档**（docs only） |
| 默认模式 | **Preview / Dry-run** |
| 关联 | [phase12a_merchant_onboarding_ux.md](phase12a_merchant_onboarding_ux.md) · [phase12a_mvp_scope_and_pricing.md](phase12a_mvp_scope_and_pricing.md) |

---

## 1. 三种回复模式

| 模式 | ID | 行为 | 默认 |
|------|-----|------|------|
| **Preview / Dry-run** | `preview` | AI 生成建议；**不调用**平台 send API；写入日志 | **✅ 新绑定默认** |
| **Assisted** | `assisted` | AI 生成建议；商家 **确认后** 才发送 | Growth 可选默认 |
| **Auto** | `auto` | 通过规则引擎的消息 **自动发送** | 须二次确认开启 |

```text
买家消息
  → intent classification
  → consultation safety gate
  → reply mode
  → send decision

  preview:   生成 suggested_reply；永不 send；status=preview_only
  assisted:  生成 suggested_reply；merchant_approve → send（须过 gate）
  auto:      仅 allowed intent + 高置信 + 低风险 → send；blocked → 转人工
```

**Consultation safety gate（12b.1 SSOT）：** 见 [phase12b1_intent_boundary.md](phase12b1_intent_boundary.md) · [phase12b1_send_gate_requirements.md](phase12b1_send_gate_requirements.md)。

**工程映射（未来，非当前默认）：**

- Preview ≈ 产品级 `reply_mode=preview`（**不是**仅 env `USE_UNIFIED_OUTBOUND_RESOLVER`）
- 当前代码默认仍走 PDD 生产发送路径 → **产品化须显式 gate send**

---

## 2. 默认策略

| 规则 | 值 |
|------|-----|
| 新绑定店铺 `reply_mode` | `preview` |
| 新绑定 `consultation_only` | **true**（默认仅售前咨询范围，见 12b.1） |
| 开启 `auto` | 须二次确认 + 禁诺/转人工已配置 + **确认只自动处理低风险咨询** |
| 全局 `paused` | 默认 false；暂停后 **禁止** auto/assisted 发送 |
| Preview 下暂停 | 可选：仍生成建议（便于观察）或一并停止生成 — **推荐仍生成** |

### 2.1 Consultation safety gate 规则（12b.1）

| 组合 | 行为 |
|------|------|
| **allowed intent** + `preview` | 生成建议；**不发** |
| **allowed intent** + `assisted` | 生成建议；等商家确认后 send（过 gate） |
| **allowed intent** + `auto` | **高置信 + 低风险** 可自动发；禁诺须通过 |
| **blocked intent** + 任意 mode | **不自动发**；转人工（preview 可仅记「建议转人工」） |
| **uncertain intent** | **不自动发**；preview 可建议；assisted 须确认；auto **禁止** |
| **paused**（workspace/shop） | 停止 auto/assisted **发送**；Preview 建议生成可继续（推荐） |

**优先级：** `paused` > `human_takeover` > `blocked_intent` > `uncertain_intent` > `reply_mode` > send。  
**`reply_mode=auto` 不得覆盖 intent safety gate。**

---

## 3. 安全功能清单

### 3.1 禁止承诺（禁诺 / Commitment Guard）

**默认启用模板，商家可增删不可删核心项：**

| 类别 | 示例触发 | 动作 |
|------|----------|------|
| 退款承诺 | 「给你退款」「全额退」 | 拦截 或 转人工 |
| 赔偿 | 「赔你」「补偿」 | 拦截 或 转人工 |
| 发货时效 | 「今天发」「明早到」 | 拦截 或 降级为「尽快安排」+ 人工 |
| 最低价 / 保价 | 「全网最低」「保证最低价」 | 拦截 |
| 医疗/功效违法表述 | 依类目扩展 | 拦截 |

**记录：** `blocked_reason=commitment_guard` + 命中规则 ID。

### 3.2 低置信度转人工

| 条件 | 动作 |
|------|------|
| AI 置信度 < 阈值（可配置） | 不自动发；`transfer_reason=low_confidence` |
| 无 FAQ 命中且开放域问题 | 建议 + 转人工 |

### 3.3 场景转人工（规则优先于 AI）

| 场景 | 检测方式 |
|------|----------|
| 售后 / 退换货 | 关键词 + 订单状态（后期） |
| 金额 / 赔付 | 数字+「元」「赔」 |
| 投诉 / 差评威胁 | 关键词 |
| 转人工词 | 商家配置 + 系统默认词表 |
| 敏感品类 | 店铺配置 |

**动作：** `transfer_to_human`；Preview 下仅记录「建议转人工」，不执行平台转接（或执行 — 产品决策：**MVP 可仅标记，Growth 接真实转接**）。

### 3.4 一键暂停

| 范围 | 效果 |
|------|------|
| **全局暂停** | 所有店 `auto`/`assisted` 停止发送 |
| **单店暂停** | 该店停止发送 |

**UI：** 顶栏常驻；暂停状态写入审计日志。

### 3.5 回复日志（审计）

每条记录最小字段：

| 字段 | 说明 |
|------|------|
| `timestamp` | 时间 |
| `shop_id` / `platform` | 店 |
| `buyer_id` | 脱敏展示 |
| `inbound_text` | 买家消息摘要 |
| `suggested_reply` | AI 建议 |
| `actual_reply` | 实际发送（若有） |
| `reply_mode` | preview / assisted / auto |
| `outcome` | preview_only / sent / blocked / transfer / failed |
| `intent` | 如 `product_question` / `refund_request`（12b.1） |
| `intent_bucket` | allowed / blocked / uncertain |
| `blocked_reason` | 禁诺 ID / intent_blocked / low_confidence / … |
| `transfer_reason` | 场景说明 |
| `allowed_to_send` | send gate 最终裁决 |

### 3.6 人工接管

| 触发 | 说明 |
|------|------|
| 商家点击「本会话人工接管」 | 该会话退出 auto，直至释放 |
| 转人工规则命中 | 同上 |
| 拦截后 | 可选推送商家通知（后期） |

---

## 4. Preview 技术边界（设计，未实现）

```text
AIReplyHandler._send_reply (conceptual):
  if shop.reply_mode == preview:
      persist_log(suggested=reply, outcome=preview_only)
      return True   # 业务成功，但未 send
  else:
      existing outbound / legacy path
```

**禁止：** 在未切换 `reply_mode` 时因测试 env 误发（商家 SaaS 须 **店铺级** 配置，非仅 `USE_UNIFIED_OUTBOUND_RESOLVER`）。

---

## 5. 与当前 handler 关系

| 项 | 当前 |
|----|------|
| Keyword 转人工 | ✅ 有；生产走 PDD outbound/legacy |
| 禁诺产品化 | ❌ 无 UI/规则引擎 |
| Preview gate | ❌ 无 |
| `USE_UNIFIED_OUTBOUND_RESOLVER` | 默认 off；仅 11g 测试 |

→ **12c** intent gate + reply preview / dry-run **send gate 技术设计**（须满足 [phase12b1_send_gate_requirements.md](phase12b1_send_gate_requirements.md)）。

---

## 6. 套餐与模式（见 pricing doc）

| 套餐 | 默认模式 | Auto |
|------|----------|------|
| Starter | Preview only | ❌ 或 试用限量 |
| Growth | Preview → 可开 Assisted/Auto | ✅ 配额内 |
| Pro | Assisted + Auto + 审核队列 | ✅ |

---

*Phase 12a · Safety & Preview · docs only*

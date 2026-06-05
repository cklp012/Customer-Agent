# Phase 13f — Assisted Risk Controls

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 对齐 | [phase12a_safety_and_preview_spec.md](phase12a_safety_and_preview_spec.md) · [phase12b1_send_gate_requirements.md](phase12b1_send_gate_requirements.md) |

---

## 1. Intent 风控

### 1.1 Blocked intent — 默认禁止普通确认发送

| intent（示例） | 路径 |
|----------------|------|
| `refund_request` | human_takeover |
| `compensation_request` | human_takeover |
| `complaint` | human_takeover |
| `bad_review_threat` | human_takeover |
| `order_change` | human_takeover |
| `address_change` | human_takeover |
| `quality_dispute` | human_takeover |
| `after_sales_dispute` | human_takeover |

**Assisted 规则：**

- AI 阶段：可生成「建议转人工」文案；`send_mode=HUMAN_TAKEOVER`
- Confirm UI：**禁用** 普通 Approve 按钮
- Elevated：仅 admin + 书面 reason + AuditLog（**默认 No-Go** for MVP）

### 1.2 Uncertain intent

| 规则 | 说明 |
|------|------|
| 一键发送 | ❌ 禁止 |
| 须人工编辑 | ✅ `final_reply` ≠ 原始 `ai_suggested_reply` 才可提交 |
| 确认时 | re-classify；仍 uncertain → reject |

### 1.3 High-risk（risk_level = medium/high）

- 须 elevated confirmation（admin）或降级为 human_takeover
- 普通 operator 不可一键 approve

---

## 2. Forbidden Promise Scan（禁诺）

**AI 生成后 + 商家确认前** 各扫描一次。

| 禁止承诺类型 | 示例短语 | 动作 |
|--------------|----------|------|
| 一定退款 | 「一定退」「保证退款」 | block send |
| 一定赔偿 | 「赔你」「保证补偿」 | block send |
| 一定到货 | 「保证明天到」「一定发货」 | block 或 rewrite + 人工 |
| 一定最低价 | 「全网最低」「保证最低价」 | block send |
| 平台规则保证 | 「平台规定必须…」（不实） | block send |

**记录：** `blocked_reason=commitment_guard` · 规则 ID · AuditLog on reject。

---

## 3. Final guard 重跑（确认时）

```text
approve_assisted_reply:
  1) reload pending + buyer_message snapshot
  2) classify_consultation_intent(buyer_message)
  3) build_send_decision(reply_mode=assisted, gate on, pause flags)
  4) forbidden_promise_scan(final_reply)
  5) evaluate_guarded_send(decision, final_reply, merchant_approved=true)
  6) should_send == true → 才调用 SendMessage
```

**禁止：** 仅信任 AI 阶段的旧 `SendDecision` 快照而不 re-check。

---

## 4. Pending 生命周期

| 控制 | 值（建议） |
|------|------------|
| `expires_at` | 创建后 **24h**（可配置） |
| stale 条件 | 过期 **或** 同 buyer 新 inbound **或** 会话状态变更 |
| superseded | 新 pending 创建时标记旧 pending `superseded` |

**确认时：** `stale` / `superseded` → 403 + `assisted_reply_rejected` AuditLog。

---

## 5. 原消息变更

| 场景 | 行为 |
|------|------|
| 买家发新消息 | 旧 pending → `superseded` |
| 买家撤回/编辑（若平台支持） | pending → `stale` |
| 商家长时间未操作 | `expires_at` → `stale` |

**UI 提示：** 「买家可能有新消息，请刷新后再确认」。

---

## 6. Paused 店铺

| 状态 | AI 阶段 | Confirm 阶段 |
|------|---------|--------------|
| `workspace_pause` | 可生成建议（推荐）或 skip | **拒绝** approve |
| `shop_pause` | 同左 | **拒绝** approve |

---

## 7. Preview 不受影响

`reply_mode=preview`：**永不** 进入 pending approve 路径；**保持 zero-send**（13d/13e）。

---

## 8. Non-test shop

无 product gate → legacy send；**不** 应用 assisted 风控链（直至显式 allowlist）。

---

*Risk controls · Phase 13f · 2026-06-03*

# Phase 14z — Pending Assisted Detail API Contract

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不实现 endpoint** |
| 方法 | `GET /api/product/pending-assisted/<pending_assisted_id>` |
| 对齐 | [phase14z_pending_assisted_dashboard_read_plan.md](phase14z_pending_assisted_dashboard_read_plan.md) |

---

## 1. 设计原则

| # | 原则 |
|---|------|
| 1 | **只读** — GET only |
| 2 | detail **可展示完整文本** — RBAC 控制（operator/admin/owner） |
| 3 | viewer 可能收到 **redacted** detail · 见 permissions doc |
| 4 | **不执行** final guard — 只读取已有 guard/snapshot 结果或 null |
| 5 | **不提供** approve / reject / send endpoint |
| 6 | **不写** audit on read |

---

## 2. Request

```http
GET /api/product/pending-assisted/{pending_assisted_id}
```

| 参数 | 说明 |
|------|------|
| `pending_assisted_id` | path · UUID |
| `workspace_id` | query 或 auth context · **必须匹配** row.workspace_id |

---

## 3. Response (200)

```json
{
  "pending_assisted_id": "pa-uuid",
  "reply_log_id": "rl-uuid",
  "workspace_id": "ws-1",
  "shop_id": "shop-1",
  "account_id": "acc-1",
  "platform_id": "pinduoduo",
  "buyer_id": "buyer-1",
  "inbound_message_id": "in-1",
  "buyer_message": "这款商品还有库存吗",
  "ai_suggested_reply": "您好，该商品目前有货，欢迎下单。",
  "merchant_edited_reply": null,
  "final_reply_candidate": "您好，该商品目前有货，欢迎下单。",
  "intent": "inventory_question",
  "intent_category": "inventory_question",
  "intent_confidence": 0.92,
  "risk_level": "low",
  "status": "pending",
  "expires_at": "2026-06-04T12:00:00+00:00",
  "created_at": "2026-06-03T12:00:00+00:00",
  "updated_at": "2026-06-03T12:00:00+00:00",
  "policy_snapshot": {
    "policy_id": "pol-1",
    "effective_mode": "assisted_only",
    "platform_mode_ceiling": "assisted_only"
  },
  "template_snapshot": {
    "template_id": "tpl-1",
    "validation_status": "passed"
  },
  "final_guard": {
    "allowed_to_send": false,
    "decision": "block",
    "block_code": "forbidden_promise",
    "block_reason": "回复含不允许的承诺用语：直接退款",
    "checked_rules": ["G1", "G22"],
    "created_at": "2026-06-03T12:05:00+00:00"
  },
  "send_decision_snapshot": {
    "decision_phase": "merchant_confirm",
    "allowed_to_send": false,
    "block_code": "forbidden_promise",
    "block_reason": "…"
  },
  "audit_timeline": [],
  "source": "sqlite_shadow",
  "warnings": []
}
```

---

## 4. Field 说明

| 字段 | 来源 | 说明 |
|------|------|------|
| `final_reply_candidate` | merchant_edited \|\| ai_suggested | 只读展示 · 非 live guard 输入 |
| `policy_snapshot` | 最近 snapshot / policy join | 可为 null |
| `template_snapshot` | 最近 snapshot / template join | 可为 null |
| `final_guard` | 最近 guard 结果 persist（audit/snapshot） | **不 re-run** evaluate_final_guard |
| `send_decision_snapshot` | `send_decision_snapshots` join | merchant_confirm / ai_preview |
| `audit_timeline[]` | audit_logs filter by pending_assisted_id | 见 timeline doc |
| `intent_confidence` | reply_log / snapshot join | optional |

**guard 空状态：** pending 刚创建 · 尚未 approve → `final_guard: null` 或 `{ "decision": "not_evaluated" }`（15c 实现时二选一）。

---

## 5. Error responses

| HTTP | 场景 |
|------|------|
| 404 | pending_assisted_id 不存在 |
| 403 | cross-workspace · viewer denied full text |
| 200 + warnings | partial data · stale · DB degraded |

---

## 6. 明确不提供（本 phase / 15c read skeleton）

| Endpoint | 状态 |
|----------|------|
| `POST …/approve` | ❌ 不在 14z/15c read scope |
| `POST …/reject` | ❌ |
| `POST …/send` | ❌ |
| `POST …/expire` | ❌ service-internal only |

---

*Phase 14z · planning only · 2026-06-03*

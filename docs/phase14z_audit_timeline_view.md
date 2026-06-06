# Phase 14z — Audit Timeline View

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14y_audit_snapshot_ordering.md](phase14y_audit_snapshot_ordering.md) · [phase14q_done.md](phase14q_done.md) |

---

## 1. 用途

Audit timeline 用于 **解释为什么没发送**、approve 走到哪一步、guard 是否 block、outbound 是否 attempt（future）。

**Dashboard read 只聚合展示 — 不写 audit。**

---

## 2. 支持的 Audit actions

| action | UI 标签（示例） | 含义 |
|--------|-----------------|------|
| `pending_assisted_created` | 创建待确认 | create_pending 成功 |
| `assisted_approved` | 商家确认意图 | merchant approve 点击（14x skeleton） |
| `assisted_rejected` | 已拒绝 | reject_pending |
| `assisted_expired` | 已过期 | expire_pending |
| `final_guard_passed` | 安全校验通过 | guard allow · **≠ 发送成功** |
| `final_guard_blocked` | 安全校验拦截 | guard block · **未发送** |
| `outbound_send_attempted` | 尝试发送 | future · outbound 前 |
| `outbound_send_succeeded` | 发送成功 | future |
| `outbound_send_failed` | 发送失败 | future · manual review |

**Recovery audit（future）：** `audit_reconciled` · `outbound_audit_recovered` — 追加到 timeline · **不自动重发**。

---

## 3. Timeline item 结构

```json
{
  "audit_log_id": "aud-uuid",
  "action": "final_guard_blocked",
  "actor_user_id": "op-1",
  "actor_role": "operator",
  "status_before": "pending",
  "status_after": "pending",
  "reason": "回复含不允许的承诺用语：直接退款",
  "block_code": "forbidden_promise",
  "created_at": "2026-06-03T12:05:00+00:00",
  "metadata_summary": {
    "checked_rules": ["G22"],
    "send_mode": "none"
  }
}
```

| 字段 | 说明 |
|------|------|
| `status_before` / `status_after` | 来自 audit before_state / after_state JSON |
| `block_code` | guard block · outbound fail · 可空 |
| `reason` | 人类可读 |
| `metadata_summary` | 脱敏后的 JSON 摘要 · **无 token/cookie** |

---

## 4. 排序与聚合

| 规则 | 说明 |
|------|------|
| 默认排序 | `created_at` **asc**（时间线从上到下）或 desc（最新在上）· UI 可切换 |
| 同秒多条 | secondary sort by `audit_log_id` |
| dedupe | 不 dedupe · append-only audit |
| 空 timeline | pending 刚创建且无 audit write fail → 至少 `pending_assisted_created` |

---

## 5. UI 强调规则

| action | UI 处理 |
|--------|---------|
| `final_guard_blocked` | **突出** block_code · block_reason · 红色 banner |
| `final_guard_passed` | 绿色/info · 附注「通过校验 ≠ 已发送」（14x skeleton 无 outbound） |
| `outbound_send_failed` | 突出 failure reason · 链到 manual review |
| `outbound_send_attempted` | 区分于 succeeded · 表明已尝试 |
| 无 `outbound_send_attempted` + guard_blocked | 解释「拦截于发送前」 |

---

## 6. 与 detail API 关系

`GET /api/product/pending-assisted/{id}` → `audit_timeline[]` 嵌入或 `?include=audit_timeline`（15c 实现选择 · contract 以 detail doc 为准）。

**read path 不 append audit。**

---

*Phase 14z · planning only · 2026-06-03*

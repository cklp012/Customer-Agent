# Phase 14s — Policy Snapshot and Audit

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14n_done.md](phase14n_done.md) · [phase14q_done.md](phase14q_done.md) · [phase14s_policy_template_data_model.md](phase14s_policy_template_data_model.md) |

---

## 1. 发送/记录时应保存的 policy 字段

| 字段 | 说明 |
|------|------|
| `policy_id` | 生效 policy UUID |
| `policy_version` | 当时 version |
| `ai_intervention_mode` | 商家配置 mode |
| `effective_mode` | min(merchant, ceiling, reply_mode) |
| `platform_mode_ceiling` | 当时 ceiling |
| `template_id` | 使用的模板（若有） |
| `template_version` | 模板 version |
| `template_validation_status` | 发送时模板状态 |
| `policy_decision_reason` | 人类可读原因码 |

---

## 2. 写入位置（future）

### 2.1 ReplyLog metadata / shadow row

JSON metadata section（规划）：

```json
{
  "merchant_policy": {
    "policy_id": "...",
    "policy_version": 3,
    "intent_category": "refund_request",
    "ai_intervention_mode": "guide_only",
    "effective_mode": "guide_only",
    "platform_mode_ceiling": "assisted_only",
    "template_id": "...",
    "template_version": 1,
    "template_validation_status": "passed",
    "policy_decision_reason": "default_matrix_fallback"
  }
}
```

### 2.2 SendDecisionSnapshot

扩展 snapshot 行或 JSON sidecar（14t/14u 定 schema）：

| 字段 | 说明 |
|------|------|
| `decision_phase` | `ai_preview` · `policy_resolved` · `merchant_confirm` |
| policy 字段 | 上表 · append-only 新行 |

**不 UPDATE 旧 snapshot 行。**

### 2.3 AuditLog（配置变更 · 非每条消息）

| action | when |
|--------|------|
| `merchant_policy_changed` | policy CRUD |
| `template_created` | 新模板 |
| `template_updated` | 内容/version |
| `template_disabled` | disable / reject |

append-only · 14q `AuditLogRepositorySQLite`

---

## 3. 历史不变性

| 规则 | 说明 |
|------|------|
| 新 policy **不** retroactive 改旧 ReplyLog | Dashboard 展示当时 snapshot |
| 商家改配置 | 只影响 **新消息** |
| 审计争议 | 靠 snapshot + AuditLog 举证 |

---

## 4. policy read failure

| 场景 | 行为 | send |
|------|------|------|
| flags off | skip DB · use default matrix in-memory | preview 仍 zero-send |
| DB read error | fallback [default_policy_matrix](phase14s_default_policy_matrix.md) + warning | 保守 · **不 legacy send** |
| resolve 失败 | no-send · log `policy_read_failed` | ❌ |

**policy read failure 不能 fallback legacy send.**

---

## 5. Dashboard detail（future）

14o detail API 占位扩展（规划 · 不改 14o 代码直至专门 phase）：

```json
{
  "reply_log": { "...": "...", "merchant_policy_snapshot": { } },
  "send_decision_snapshots": [ ],
  "audit_logs": [ ]
}
```

---

## 6. 与 Assisted approve（14r）衔接

approve 路径 snapshot 追加：

- `decision_phase=merchant_confirm`
- 同一 `policy_id`/`template_id` 或 approve 时点 re-resolve
- guard block 仍写 `final_guard_blocked` audit · 无 outbound

---

*Phase 14s · planning only · 2026-06-03*

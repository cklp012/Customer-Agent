# Phase 15n — Manual Review and Operator Runbook

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15n_reconciliation_task_contract.md](phase15n_reconciliation_task_contract.md) |

---

## 1. 何时进入 manual review

| 触发 |
|------|
| `timeout_unknown` from live port |
| reconciliation `still_unknown` |
| reconciliation `platform_unavailable` 超过阈值 |
| DB failure after suspected platform success |
| operator escalation |

**默认：** unknown → **`manual_review_required`** — 不等待自动恢复。

---

## 2. Manual review 页面展示（future dashboard）

| 字段 | 说明 |
|------|------|
| `pending_assisted_id` | 主键 |
| `buyer_id` / `shop_id` | 会话上下文 |
| `final_reply` | 拟发送内容（只读） |
| `idempotency_key` | outbound key · **不可复用 resend** |
| `last platform_status` | e.g. `timeout_unknown` |
| `trace_id` | 链路追踪 |
| audit timeline | append-only 事件列表 |
| `SendDecisionSnapshot` | final guard 时快照 |
| possible `provider_message_id` | 若有弱信号 |
| reconciliation attempts | 次数 · 最后结果 · 时间 |

**禁止展示：** cookie · token · session · API key · 原始 credential。

---

## 3. Operator 可执行动作

| 动作 | 效果 | 权限 |
|------|------|------|
| `mark_confirmed_sent` | idempotency → succeeded · pending → sent · audit | operator+ |
| `mark_confirmed_not_sent` | idempotency → failed_before_send · pending → manual_review_required · audit | operator+ |
| `keep_manual_review` | 保持状态 · append audit | operator+ |
| `cancel_pending` | pending → rejected · audit | operator+ |
| `create_new_pending_after_manual_decision` | 新 pending 行 · **新** idempotency path · 不自动 send | admin/owner |

### 3.1 create_new_pending_after_manual_decision

| 规则 |
|------|
| **必须**生成新 `pending_assisted_id` |
| 未来 live send **必须**新 `idempotency_key` |
| **不允许**直接 resend same `idempotency_key` |
| 须重新 final guard · 新 snapshot · 新 audit |
| 须再次人工 approve（非 auto） |
| 受 daily cap / allowlist 约束（future service） |

---

## 4. 权限分级

| 角色 | 权限 |
|------|------|
| `viewer` | 只读 manual review 页 · **禁止**一切操作 |
| `operator` | mark_sent / mark_not_sent / keep_review / cancel（受 shop scope） |
| `admin` | operator + create_new_pending · 跨 shop（若 policy 允许） |
| `owner` | admin + 禁用 live send flag 紧急开关（runbook） |

所有 operator 动作：
- 要求 `confirm_checkbox=true`（与 15i action route 对齐）
- append audit · 含 `actor_user_id` · `actor_role`
- CSRF + RBAC（15g）

---

## 5. Operator runbook（逐步）

### 5.1 timeout_unknown 初次出现

1. 打开 manual review · 记录 `trace_id` · `idempotency_key`
2. 在 PDD 商家后台核对 buyer 会话最近消息
3. 比对 `final_reply` 文本与时间窗
4. 若 reconciliation task 可用 → 触发一次 · 等待结果
5. **不要**点击 re-approve 同一 pending

### 5.2 确认已发送

1. 在平台找到匹配消息 · 记录 `provider_message_id`（若有）
2. 执行 `mark_confirmed_sent`
3. 验证 audit：`reconciliation_confirmed_sent` 或 `operator_marked_sent`
4. 验证 pending `sent` · idempotency `succeeded`

### 5.3 确认未发送

1. 平台无匹配消息 · 证据充分
2. 执行 `mark_confirmed_not_sent`
3. pending 保持 `manual_review_required` 或 `send_failed`（schema TBD 15q）
4. 若需再次触达买家 → **`create_new_pending_after_manual_decision`** · 新 key · 新 approve

### 5.4 仍无法确认

1. `keep_manual_review`
2. 稍后重跑 reconciliation task（仅查询）
3. 升级 admin · 可选双人复核（future）
4. **禁止** auto retry send

### 5.5 紧急止血

1. 设 `PRODUCT_ASSISTED_SEND_ENABLED=false`
2. 设 `PRODUCT_ASSISTED_SEND_DRY_RUN=true`
3. 可选 `PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED=false`
4. PDD legacy hot path **不变**

---

## 6. 禁止操作

| 禁止 |
|------|
| viewer 执行 mark / cancel |
| 同 `idempotency_key` resend |
| 无 audit 的状态跳转 |
| 修改历史 audit 行 |
| 调 SendMessage 手工补发绕过系统 |

---

*Phase 15n · docs only · 2026-06-03*

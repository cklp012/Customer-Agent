# Phase 14z — PendingAssisted Dashboard Read Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不写代码** |
| 日期 | 2026-06-03 |
| 前置 | [phase14y_done.md](phase14y_done.md) · [phase14x_done.md](phase14x_done.md) · [phase14q_done.md](phase14q_done.md) · [phase14o_done.md](phase14o_done.md) |

---

## 1. Phase 14z 定位

| 项 | 结论 |
|----|------|
| 交付 | **仅文档** |
| Python 代码 | **未写** |
| Dashboard API 实现 | **未实现** |
| approve / reject / send | **未实现** |
| handler / SendMessage / outbound | **未改** |
| PDD / Doudian 热路径 | **未改** |
| legacy database | **未改** |
| 新 DB 表 | **未创建** |

Phase 14z 在 **14q PendingAssisted + AuditLog schema**、**14x AssistedReplyService skeleton**、**14y integration planning** 之上，规划商家/运营 **只读** 查看待人工确认队列的 Dashboard read 模型与 API contract。

---

## 2. 目标用户与场景

| 角色 | 场景 |
|------|------|
| operator | 查看 pending 队列 · 准备人工确认（future approve 在 15a+） |
| admin / owner | 全店 pending 监控 · 审计 timeline |
| viewer | 只读列表 · detail 可能脱敏 |

**本 phase 不提供任何 mutation endpoint。**

---

## 3. Dashboard 页面规划

### 3.1 列表页（Pending Assisted List）

展示 **pending / rejected / expired / sent / failed / canceled** 等状态队列。

| 列（规划） | 来源 |
|------------|------|
| pending_assisted_id | `pending_assisted_replies` |
| buyer_message_preview | truncated · 列表 preview |
| ai_suggested_reply_preview | truncated |
| status | pending / sent / failed / … |
| intent_category · risk_level | pending row |
| final_guard_block_code | 最近一次 guard 结果（join snapshot/audit · future） |
| expires_at · created_at | pending row |
| latest_audit_action | audit_logs 聚合 |

**默认 filter：** active statuses `pending` · `failed`（可配置展开 terminal）。

### 3.2 详情页（Pending Assisted Detail）

| 区块 | 内容 |
|------|------|
| 消息 | buyer_message · ai_suggested_reply · merchant_edited_reply · final_reply_candidate |
| 意图/风险 | intent · intent_category · intent_confidence · risk_level |
| 状态 | status · expires_at · created_at · updated_at |
| Policy / Template | policy_snapshot · template_snapshot（只读展示） |
| Final Guard | allowed_to_send · decision · block_code · block_reason · checked_rules |
| SendDecision | merchant_confirm snapshot（若存在） |
| Audit Timeline | 有序 audit 事件链 |
| Warnings | read source · stale · partial data |

**详情可展示完整文本** — 须 RBAC（operator/admin/owner）；viewer 见 permissions doc。

---

## 4. 核心原则（签收）

| # | 原则 |
|---|------|
| **Z1** | **Dashboard can observe assisted workflow state, but cannot mutate send state in this phase.** |
| Z2 | Dashboard read **只读** — GET only |
| Z3 | Dashboard **不直接**调用 SendMessage |
| Z4 | Dashboard **不直接**调用 outbound resolver |
| Z5 | Dashboard **不直接**调用 handler |
| Z6 | Dashboard read **不执行** final guard |
| Z7 | Dashboard read **不写** audit |
| Z8 | 不提供 approve / reject / send action（本 phase） |
| Z9 | 当前 runtime 发送行为 **不变** |
| Z10 | flags default off · assisted 未默认开启 |

---

## 5. 与现有 Dashboard 关系

```text
14o DashboardReadService (reply-logs)
    GET /api/product/reply-logs
    GET /api/product/reply-logs/{id}
        → pending_assisted_reply=null (today)

14z planning (pending-assisted)
    GET /api/product/pending-assisted          (future · 15c skeleton)
    GET /api/product/pending-assisted/{id}     (future · 15c skeleton)
        → extends Module C / new Module I（Assisted Queue）
```

| 组件 | 14z 状态 |
|------|----------|
| ReplyLog read (14o) | ✅ skeleton · unchanged |
| PendingAssisted list/detail read | 📋 本 phase 规划 |
| API implementation | 📋 15c |

---

## 6. 文档索引（14z）

| 文档 | 内容 |
|------|------|
| [phase14z_pending_list_api_contract.md](phase14z_pending_list_api_contract.md) | List API |
| [phase14z_pending_detail_api_contract.md](phase14z_pending_detail_api_contract.md) | Detail API |
| [phase14z_audit_timeline_view.md](phase14z_audit_timeline_view.md) | Timeline 模型 |
| [phase14z_filters_permissions_and_pagination.md](phase14z_filters_permissions_and_pagination.md) | 过滤 · 权限 · 分页 |
| [phase14z_read_source_and_failure_policy.md](phase14z_read_source_and_failure_policy.md) | 数据源 · 失败策略 |
| [phase14z_test_plan.md](phase14z_test_plan.md) | Z1–Z17 |

---

## 7. 当前 runtime（unchanged）

- 14x AssistedReplyService skeleton · approve → `send_not_implemented`
- test shop preview **zero-send**
- non-test legacy **unchanged**
- PDD queue **`pdd_{shop_id}`** 不变

---

*Phase 14z · planning only · 2026-06-03*

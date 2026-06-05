# Phase 14m — SendDecision Snapshot Shadow Write Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 前置 | [phase14l_done.md](phase14l_done.md) · [phase14a_senddecision_schema.md](phase14a_senddecision_schema.md) |
| 实现 | **Phase 14n**（SQLite snapshot behind flag） |

---

## 1. Phase 14m 定位

| 项 | 结论 |
|----|------|
| 本 Phase | **仅文档规划** |
| 代码 | **不写** |
| `send_decision_snapshots` 表 | **不创建** |
| handler / SendMessage / PDD / Doudian | **不改** |
| assisted / auto | **未实现** |

---

## 2. 当前状态（14l · as-is）

```
PreviewReplyLogService.record_preview
  → append_preview_log (in-memory)           ← always
  → optional SQLite reply_logs write         ← WRITE_REPLY_LOG flag
  → zero-send
```

| 已持久化 | 未持久化 |
|----------|----------|
| in-memory `PreviewLogRecord` | SendDecision snapshot SQLite |
| SQLite `reply_logs`（flags on） | `send_decision_snapshots` 表 |
| 13b shadow log（observe-only · gate off） | assisted approve snapshot |

**SendDecision 纯函数结果** 已在 memory 的 `PreviewLogRecord.send_decision` 中，但 **未独立 snapshot 行**。

---

## 3. SendDecision Snapshot 是什么

不可变 **决策快照（append-only）** — 解释：

- 为什么 **允许/拒绝** AI 生成
- 为什么 **允许/拒绝** 发送
- 为何 `preview` / `blocked` / `human_takeover`
- 未来 assisted 时 AI 阶段 vs 商家确认阶段的 **决策变化**

**每次关键决策新增一行，不 update 旧 snapshot。**

---

## 4. 用途

| 用途 | 说明 |
|------|------|
| **Dashboard detail** | `send_decision_snapshots[]` 决策链 |
| **风控复盘** | 按 shop/time 查 blocked / high risk |
| **debug gate 误判** | 对比 intent / keyword_rule / classifier |
| **解释 no-send** | `not_sent_preview` · `not_sent_human_takeover` |
| **assisted 对比** | `ai_preview` vs `merchant_confirm` 差异（未来） |

---

## 5. decision_phase 规划

| 阶段 | `decision_phase` | 状态 |
|------|------------------|------|
| test shop preview AI | `ai_preview` | **14n 目标** |
| 13b shadow（gate off） | 不写 SQLite snapshot（或 future `shadow_only`） | 不在 14n 范围 |
| assisted 商家确认 | `merchant_confirm` | **未来 · 未实现** |
| auto send | — | **未实现** |
| Doudian production | — | **不进入** |

---

## 6. 与 ReplyLog 关系

```
reply_logs (1)  ←── weak link ──→  send_decision_snapshots (N)
     reply_log_id                      reply_log_id
```

- preview 阶段：至少 1 条 `ai_preview` snapshot
- assisted approve：新增 `merchant_confirm` snapshot（同一 `reply_log_id`）
- **append-only** · 无 FK 到 legacy DB

---

## 7. 不变量

| # | 不变量 |
|---|--------|
| 1 | snapshot **append-only** |
| 2 | flags 默认 off |
| 3 | 仅 allowlisted **test shop preview** 进入 write path（与 14l 相同 gate） |
| 4 | **non-test shop legacy unchanged** |
| 5 | snapshot DB failure **不得** fallback SendMessage |
| 6 | test shop preview **仍 zero-send** |
| 7 | handler **不直接**写 snapshot |
| 8 | Doudian **非 production** |

---

## 8. 相关文档

| 文档 | 内容 |
|------|------|
| [phase14m_senddecision_schema_detail.md](phase14m_senddecision_schema_detail.md) | 表 schema |
| [phase14m_snapshot_write_flow.md](phase14m_snapshot_write_flow.md) | write flow |
| [phase14m_dashboard_detail_decision_view.md](phase14m_dashboard_detail_decision_view.md) | Dashboard 展示 |
| [phase14m_failure_and_rollback.md](phase14m_failure_and_rollback.md) | failure · rollback |
| [phase14m_test_plan.md](phase14m_test_plan.md) | M1–M10 |

---

## 9. 未来阶段

| Phase | 内容 |
|-------|------|
| **14n** | SendDecision snapshot SQLite **implementation** behind flag |
| **14o** | Dashboard read API **skeleton only** |
| **14p** | AuditLog / PendingAssisted planning |

---

*Phase 14m · planning only · 2026-06-03*

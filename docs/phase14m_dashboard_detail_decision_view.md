# Phase 14m — Dashboard Detail Decision View

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 对齐 | [phase14k_replylog_detail_api_contract.md](phase14k_replylog_detail_api_contract.md) · [phase12d_reply_activity_read_model.md](phase12d_reply_activity_read_model.md) |

---

## 1. API 集成

`GET /api/product/reply-logs/{reply_log_id}` 响应中的 `send_decision_snapshots[]`：

- **14k 规划：** 当前返回 `[]`（in-memory 无独立 snapshot 行）
- **14n+ read：** 从 SQLite 或 future read path 填充
- **14o API skeleton：** 接线 read repository

---

## 2. Snapshot 列表项字段（UI + API）

每条 snapshot 展示：

| 字段 | UI 标签建议 |
|------|-------------|
| `decision_phase` | 决策阶段 · `AI Preview` / `商家确认` |
| `intent` | 识别意图 |
| `intent_bucket` | allowed / blocked / uncertain |
| `intent_confidence` | 置信度 % |
| `risk_level` | 风险 · 色标 low/medium/high |
| `reply_mode` | preview / assisted / paused |
| `allowed_to_generate` | 允许生成 AI |
| `allowed_to_send` | 允许发送 |
| `send_mode` | preview_only / human_takeover / … |
| `blocked_reason` | 拦截原因 |
| `human_takeover_reason` | 转人工原因 |
| `decision_source` | keyword_rule / classifier / gate |
| `created_at` | 决策时间 |

---

## 3. 无 snapshot 时

| 状态 | API | UI |
|------|-----|-----|
| 14i/14l in-memory only | `send_decision_snapshots: []` | 从 ReplyLog 主字段推断（intent/send_status） |
| flags off | `[]` | 同上 |
| 14n flags on | 1+ items | 完整决策链 |

**不得** 因缺失 snapshot 返回 500。

---

## 4. Preview · `not_sent_preview` 展示

| 展示项 | 内容 |
|--------|------|
| 主状态 | `send_status=not_sent_preview` |
| snapshot | `decision_phase=ai_preview` · `allowed_to_send=false` |
| 说明 | 「Preview 模式：已记录 AI 建议，未发送给买家」 |
| `not_sent_explanation` | ReplyLog 主字段 · 与 snapshot 一致 |

---

## 5. Blocked · `human_takeover` 高亮

| 条件 | UI |
|------|-----|
| `intent_bucket=blocked` | 红色/警告 badge |
| `send_mode=human_takeover` | 「需人工处理」 |
| `human_takeover_reason` | 展示 keyword_rule / intent_blocked 等 |
| `allowed_to_send=false` | 明确「不可自动发送」 |

---

## 6. 决策链时间线（14n+）

```
[ai_preview]        2026-06-03 12:00  intent=refund_request  blocked  human_takeover
[merchant_confirm]  2026-06-03 12:05  (future) merchant approved / denied
```

- 按 `created_at ASC` 展示
- **future `merchant_confirm`：** 与 `ai_preview` **diff 高亮**（intent / allowed_to_send / send_mode 变化）

---

## 7. Diff 视图（future assisted）

| 对比维度 | ai_preview | merchant_confirm |
|----------|------------|------------------|
| `allowed_to_send` | false | true/false（approve 后） |
| `send_mode` | preview_only | assisted_send（未来） |
| `reply_mode` | preview | assisted |
| `decision_source` | classifier | confirm_recheck |

**14m 只规划 UI/contract · 不实现 assisted。**

---

## 8. Read source（与 14k 对齐）

| 阶段 | snapshot 来源 |
|------|---------------|
| flags off | `[]` · 可选从 in-memory `PreviewLogRecord.send_decision` 合成只读 view（14o 可选） |
| `READ_DASHBOARD=true` | SQLite `send_decision_snapshots` |
| read fail | `[]` + warning |

---

*Phase 14m · planning only · 2026-06-03*

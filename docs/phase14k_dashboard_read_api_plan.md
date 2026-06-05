# Phase 14k — Dashboard Read API Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 前置 | [phase14j_done.md](phase14j_done.md) · [phase13e_done.md](phase13e_done.md) · [phase12d_done.md](phase12d_done.md) |
| 实现 | **Phase 14m**（API skeleton only）· **14l**（SQLite read source） |

---

## 1. Phase 14k 定位

| 项 | 结论 |
|----|------|
| 本 Phase | **仅文档规划** |
| API endpoint | **不实现** |
| Flask / FastAPI / route | **不改** |
| DB / SQLite | **不创建** |
| handler / SendMessage / PDD / Doudian | **不改** |
| assisted / auto | **未实现** |

---

## 2. 背景

### 2.1 当前可读来源（14g/14i）

```
PreviewReplyLogService.list_reply_logs()
  → Message.gates.reply_log_projection.list_preview_reply_logs()
  → in-memory preview_log
  → source = in_memory
```

- test shop preview 经 service 写入 in-memory
- **zero-send** 不变
- 进程重启后 in-memory 数据丢失（preview/test phase 可接受）

### 2.2 未来可读来源（14l+）

```
PreviewReplyLogService.list_reply_logs()
  → if PRODUCT_PERSISTENCE_READ_DASHBOARD=true && SQLite available:
       ReplyLogRepositorySQLite.list(...)
     else:
       in-memory projection
  → source = sqlite_shadow | in_memory | mixed
```

- shadow DB：`./temp/product_gate.db`（[phase14j_done.md](phase14j_done.md)）
- PostgreSQL 未来替换 repository，**API contract 不变**

---

## 3. Dashboard 目标

商家控制台 **只读** 查看 preview ReplyLog 活动流：

| 展示项 | 字段来源 |
|--------|----------|
| 买家消息 | `buyer_message` |
| AI 建议回复 | `ai_suggested_reply` |
| 发送状态 | `send_status`（`not_sent_preview` / `not_sent_human_takeover` 等） |
| 意图 / 风险 | `intent` · `intent_bucket` · `risk_level` |
| 未发送原因 | `blocked_reason` · `human_takeover_reason` · `not_sent_explanation` |
| 店铺/账号/买家 | `workspace_id` · `shop_id` · `account_id` · `buyer_id` · `platform_id` |
| 时间 | `created_at` |

**UI 模块对齐：** [phase12d_reply_activity_read_model.md](phase12d_reply_activity_read_model.md) · Module C（Reply Activity）

---

## 4. API 设计原则

| # | 原则 |
|---|------|
| 1 | **只读** — GET only（14k/14m 范围） |
| 2 | **不得调用 SendMessage** / outbound |
| 3 | **不得修改** `reply_mode` / `product_gate_enabled` / send flags |
| 4 | **read failure 不影响** handler send path |
| 5 | **non-test shop legacy** 不受影响（read API 独立） |
| 6 | **workspace 隔离** — 必须校验 tenant scope |
| 7 | **不返回 credential** — 无 cookie / password / token |
| 8 | **默认 flags off** — 无 DB 时仍可读 in-memory |

---

## 5. 建议 endpoints（草案）

| Method | Path | 文档 |
|--------|------|------|
| GET | `/api/product/reply-logs` | [phase14k_replylog_list_api_contract.md](phase14k_replylog_list_api_contract.md) |
| GET | `/api/product/reply-logs/{reply_log_id}` | [phase14k_replylog_detail_api_contract.md](phase14k_replylog_detail_api_contract.md) |

**注：** 与 12d `/api/v1/workspaces/{id}/...` 可后续统一前缀；14k 以 product gate 专用路径规划。

---

## 6. 服务层边界

```
HTTP handler (14m+)
  → PreviewReplyLogService.list_reply_logs() / get_reply_log()
  → read source strategy (in_memory | sqlite_shadow)
  → JSON response
```

- HTTP 层 **不** 直接读 `preview_log`
- HTTP 层 **不** import `db_manager` 到 handler send path
- 读路径 failure → HTTP 5xx/200+warning · **不触发 send**

---

## 7. non-test shop / legacy

| 路径 | read API 影响 |
|------|--------------|
| non-test shop legacy send | **无** — read API 独立 |
| preview log 为空 | list 返回 `items=[]` |
| Doudian production | **不进入** product read path（14k） |

---

## 8. 相关文档

| 文档 | 内容 |
|------|------|
| [phase14k_replylog_list_api_contract.md](phase14k_replylog_list_api_contract.md) | 列表 API |
| [phase14k_replylog_detail_api_contract.md](phase14k_replylog_detail_api_contract.md) | 详情 API |
| [phase14k_dashboard_filters_and_permissions.md](phase14k_dashboard_filters_and_permissions.md) | 筛选 · 权限 |
| [phase14k_read_source_strategy.md](phase14k_read_source_strategy.md) | in-memory ↔ SQLite |
| [phase14k_test_plan.md](phase14k_test_plan.md) | D1–D11 |

---

## 9. 未来阶段

| Phase | 内容 |
|-------|------|
| **14l** | SQLite ReplyLog shadow **implementation** behind flag |
| **14m** | Dashboard read API **skeleton only**（route + service 接线） |
| **14n** | SendDecision snapshot shadow write planning |

---

*Phase 14k · planning only · 2026-06-03*

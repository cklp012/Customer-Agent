# Phase 14k — Dashboard Read API Test Plan (Future 14m+)

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 实现 | **Phase 14m**（API skeleton） |
| 建议文件 | `tests/test_dashboard_reply_log_read_api.py` |

---

## 1. 目的

14m 实现 read API 后验证：

1. in-memory 可读
2. 筛选/分页正确
3. 只读 · 无 send 副作用
4. 无 credential 泄漏
5. workspace 隔离
6. SQLite read fallback
7. legacy 不受影响

---

## 2. 测试矩阵 D1–D11

### D1 — `list_api_in_memory_returns_items`

| 项 | 内容 |
|----|------|
| 前置 | test shop preview 写入 in-memory |
| 操作 | `GET /api/product/reply-logs?workspace_id=...` |
| 断言 | `200` · `items.length >= 1` |
| 断言 | `source=in_memory` |
| 断言 | item 含 `buyer_message` · `ai_suggested_reply` · `send_status` |

---

### D2 — `list_api_filters`

| 项 | 内容 |
|----|------|
| 前置 | 多条 preview log（不同 shop / status / risk） |
| 操作 | `shop_id=` · `send_status=` · `risk_level=` |
| 断言 | 返回子集正确 |
| 断言 | 非法 `page_size=200` → 400 |

---

### D3 — `detail_api_returns_reply_log`

| 项 | 内容 |
|----|------|
| 前置 | 已知 `reply_log_id` |
| 操作 | `GET /api/product/reply-logs/{id}?workspace_id=...` |
| 断言 | `200` · 完整字段 |
| 断言 | `intent_confidence` · `blocked_reason` 等 present |

---

### D4 — `detail_missing_sections_empty`

| 项 | 内容 |
|----|------|
| 前置 | 14i in-memory only |
| 断言 | `send_decision_snapshots=[]` |
| 断言 | `audit_logs=[]` |
| 断言 | `pending_assisted_reply=null` |

---

### D5 — `no_send_side_effect`

| 项 | 内容 |
|----|------|
| Patch | `SendMessage.send_text` · `_send_reply` · outbound |
| 操作 | list + detail API |
| 断言 | send mocks **not called** |

---

### D6 — `no_credential_leak`

| 项 | 内容 |
|----|------|
| 前置 | metadata 含模拟 cookie/token 字段（若写入） |
| 断言 | response JSON 不含 `password` · `cookie` · `token` · `secret` |
| 断言 | response body string scan 无 credential keys |

---

### D7 — `permissions_viewer_read_only`

| 项 | 内容 |
|----|------|
| 前置 | viewer role token |
| 操作 | GET list + detail |
| 断言 | `200` |
| 操作 | POST/PATCH gate settings（若存在 stub） |
| 断言 | `403` |

---

### D8 — `workspace_isolation`

| 项 | 内容 |
|----|------|
| 前置 | log 属于 workspace A |
| 操作 | workspace B token 请求 A 的 logs |
| 断言 | `403` 或 `items=[]`（策略统一） |
| detail | 跨 workspace id → `403` |

---

### D9 — `sqlite_read_flag_fallback`

| 项 | 内容 |
|----|------|
| 前置 | `READ_DASHBOARD=true` |
| Patch | repository list → `RuntimeError` |
| 操作 | GET list |
| 断言 | `200` · `source=in_memory` · `warnings` 含 fallback |
| 断言 | no send |

---

### D10 — `non_test_legacy_unaffected`

| 项 | 内容 |
|----|------|
| 操作 | read API 调用前后 · non-test shop `handle()` |
| 断言 | legacy `_send_reply` 行为不变 |
| 断言 | read API 不修改 preview_log 以外 state |

---

### D11 — `doudian_no_production`

| 项 | 内容 |
|----|------|
| 前置 | Doudian mock log（dev only） |
| 断言 | production config 下 list 不含 Doudian |
| 断言 | 无 Doudian send path |

---

## 3. 与现有测试关系

| 现有 | 14m 后 |
|------|--------|
| H1–H10（14i） | green |
| S1–S10（14l write） | green |
| D1–D11 | **新增** |

---

## 4. CI 建议

| Job | 范围 |
|-----|------|
| default | D1/D4/D5/D6 · in-memory · 无 DB |
| optional | D9 · SQLite fixture |

---

## 5. Go/No-Go（14m 签收）

- [ ] D1–D11 green（适用项）
- [ ] 无 SendMessage 调用
- [ ] 无 credential in response
- [ ] H1–H10 无回归

---

*Phase 14k · planning only · 2026-06-03*

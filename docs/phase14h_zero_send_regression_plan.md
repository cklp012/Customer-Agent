# Phase 14h — Zero-Send Regression Test Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 实现 | **Phase 14i**（`tests/test_handler_preview_service_integration.py` 或扩展现有 preview gate tests） |
| 前置测试 | Z1–Z10（[phase13c_zero_send_test_plan.md](phase13c_zero_send_test_plan.md)）· 14g service tests |

---

## 1. 目的

在 handler 接入 `PreviewReplyLogService.record_preview` 后，验证：

1. **test shop preview 仍 zero-send**
2. **non-test shop legacy 不变**
3. **service failure 不触发 SendMessage**
4. **无 DB 副作用**

---

## 2. 测试矩阵 H1–H10

### H1 — `test_shop_preview_still_zero_send`

| 项 | 内容 |
|----|------|
| 前置 | allowlist 命中 test shop |
| 操作 | 走 `_handle_preview_product_gate` 完整路径 |
| Patch | `_send_reply` · `SendMessage` · outbound `send_text` |
| 断言 | **均未调用** |
| 断言 | `handle()` 返回 True（正常 preview 记录） |
| 断言 | preview log / projection 有记录 |

**不变量：** 与 Z1 等价，集成后仍成立。

---

### H2 — `service_record_called_for_test_shop`

| 项 | 内容 |
|----|------|
| 前置 | allowlist 命中 |
| Patch | `PreviewReplyLogService.record_preview`（spy / mock 保留真实副作用或 delegate） |
| 操作 | preview branch 处理消息 |
| 断言 | `record_preview` **被调用 1 次** |
| 断言 | 参数含 `message_text` · `reply_text` · `classification` · `send_decision` · `guarded_result` · metadata |

---

### H3 — `non_test_shop_service_not_called`

| 项 | 内容 |
|----|------|
| 前置 | allowlist **未**命中（non-test shop） |
| Patch | `PreviewReplyLogService.record_preview` |
| Patch | `_send_reply`（允许调用） |
| 操作 | 正常 AI reply 路径 |
| 断言 | `record_preview` **未调用** |
| 断言 | `_send_reply` **被调用**（legacy unchanged） |

---

### H4 — `service_failure_test_shop_no_send`

| 项 | 内容 |
|----|------|
| 前置 | allowlist 命中 |
| Patch | `record_preview` → `raise RuntimeError("service down")` |
| Patch | `_send_reply` · `SendMessage` |
| 操作 | preview branch |
| 断言 | `_send_reply` / `SendMessage` **未调用** |
| 断言 | `handle()` 返回 **False** 或 safe preview fallback result（与 failure policy 一致） |
| 断言 | 无 unhandled exception 泄漏到 consumer |

**硬规则：** service failure **不得** fallback legacy send。

---

### H5 — `service_failure_non_test_shop_legacy_unchanged`

| 项 | 内容 |
|----|------|
| 前置 | allowlist 未命中 |
| Patch | `PreviewReplyLogService.record_preview` → raise |
| Patch | `_send_reply`（正常 mock success） |
| 操作 | legacy AI reply 路径 |
| 断言 | legacy send **仍成功**（service 未被调用，failure 无影响） |
| 断言 | `record_preview` **未调用** |

---

### H6 — `blocked_intent_records_human_takeover`

| 项 | 内容 |
|----|------|
| 前置 | allowlist 命中 · 消息含 refund/complaint 等 blocked intent |
| 操作 | preview branch |
| Patch | `_send_reply` · `SendMessage` |
| 断言 | **未发送** |
| 断言 | `record_preview` 被调用 |
| 断言 | projection `send_status` = `not_sent_human_takeover`（或等价 guarded status） |
| 断言 | `intent` 反映 blocked 分类 |

**与 Z3 对齐，集成后仍成立。**

---

### H7 — `no_db_created`

| 项 | 内容 |
|----|------|
| 前置 | 清空 `temp/product_gate.db`（若存在） |
| 操作 | test shop preview 完整路径 + `PreviewReplyLogService.list_reply_logs()` |
| 断言 | `temp/product_gate.db` **不存在** |
| 断言 | 无 `create_all` / engine 副作用（monkeypatch `ProductDbManager.init_product_db` spy） |

---

### H8 — `flags_default_off`

| 项 | 内容 |
|----|------|
| 前置 | `PRODUCT_PERSISTENCE_ENABLED` unset / false |
| 操作 | test shop preview + service record |
| 断言 | preview 记录成功（in-memory path） |
| 断言 | `list_reply_logs()` 可读 projection |
| 断言 | 不依赖 flag on 完成 preview 写入 |

---

### H9 — `no_direct_db_import_in_handler`

| 项 | 内容 |
|----|------|
| 类型 | 静态源码检查 |
| 文件 | `Message/handlers/ai_handler.py` |
| 断言 | 不含 `product_persistence.db_manager` |
| 断言 | 不含 `product_persistence.repositories` |
| 断言 | 不含 `product_persistence.models`（ORM） |
| 断言 | 不含 `database.models` / `database.db_manager` |
| 允许 | `product_persistence.services` · `PreviewReplyLogService` |

---

### H10 — `doudian_not_enabled`

| 项 | 内容 |
|----|------|
| 前置 | `platform_id=doudian` 或 Doudian mock 消息 |
| 操作 | handler 处理 |
| 断言 | **不进入** preview product gate branch |
| 断言 | `PreviewReplyLogService.record_preview` **未调用** |
| 断言 | Doudian 不进入 production product persistence path |

**与 Z5 对齐。**

---

## 3. 测试文件建议（14i）

| 文件 | 内容 |
|------|------|
| `tests/test_handler_preview_service_integration.py` | H1–H10 新用例 |
| 或扩展 `tests/test_handler_single_test_shop_preview_gate.py` | H1/H4/H6 与 Z 系列合并 |

**原则：** 新测试 **additive**；不削弱 Z1–Z10 现有断言。

---

## 4. 与现有测试关系

| 现有 | 关系 |
|------|------|
| Z1–Z10（13c/13d） | baseline zero-send · 14i 后仍须 green |
| `test_preview_reply_log_service_in_memory.py`（14g） | service unit tests · 不变 |
| `test_product_persistence_skeleton.py`（14f） | skeleton · 不变 |

---

## 5. Go / No-Go（14i 签收）

| 条件 | 要求 |
|------|------|
| H1–H10 全绿 | ✅ |
| Z1–Z10 无回归 | ✅ |
| 全量 unittest | ✅ |
| `product_gate.db` 未创建 | ✅ |
| git diff 无 PDD/Doudian/handler 意外改动 | ✅ |

---

*Phase 14h · planning only · 2026-06-03*

# Phase 14h — Preview ReplyLog Service Integration Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 前置 | [phase14g_done.md](phase14g_done.md) · [phase13d_done.md](phase13d_done.md) · [phase13e_done.md](phase13e_done.md) |
| 实现 | **Phase 14i**（test shop handler integration） |

---

## 1. 目标

将 preview ReplyLog **写入路径**从 `Message.gates.preview_log.append_preview_log` 逐步迁移到 `product_persistence.services.PreviewReplyLogService`，使 handler 仅做 orchestration，persistence 统一经 service 层。

**本 Phase（14h）只规划，不实现。**

---

## 2. 当前状态（as-is · 13d/13e/14g）

### 2.1 Handler preview branch（test shop allowlist 命中）

```
AIReplyHandler.handle()
  → gate config lookup (product_gate_config)
  → _handle_preview_product_gate(...)
      → classify_consultation_intent(message_text)
      → build_send_decision(classification, reply_mode=preview, ...)
      → _get_ai_reply(...)                    # generate reply
      → evaluate_guarded_send(send_decision, reply)
      → append_preview_log(...)               # 直接写 in-memory preview_log
      → log_message("Preview gate suggestion recorded")
      → return True
  → zero-send（不调用 _send_reply / SendMessage / outbound）
```

### 2.2 Service layer（14g · 未接 handler）

| 组件 | 状态 |
|------|------|
| `PreviewReplyLogService.list_reply_logs()` | ✅ 读 in-memory projection |
| `PreviewReplyLogService.get_reply_log()` | ✅ |
| `PreviewReplyLogService.record_preview()` | stub · 不写 · handler 未调用 |
| `product_persistence` DB / SQLite | **未实现** |
| handler 接入 | **无** |

### 2.3 Non-test shop

```
AIReplyHandler.handle()
  → 不进入 preview branch
  → legacy _send_reply → outbound / SendMessage（unchanged）
```

---

## 3. 未来目标（to-be · Phase 14i+）

### 3.1 Handler preview branch

```
AIReplyHandler.handle()
  → gate config lookup
  → _handle_preview_product_gate(...)
      → classify_consultation_intent(message_text)
      → build_send_decision(...)
      → _get_ai_reply(...)
      → evaluate_guarded_send(send_decision, reply)
      → PreviewReplyLogService.record_preview(...)   # service 唯一写入边界
      → log_message(...)
      → return True
  → zero-send（不变）
```

### 3.2 Service `record_preview` 演进（分阶段）

| 阶段 | `record_preview` 行为 | DB |
|------|----------------------|-----|
| **14i** | 内部调用 `append_preview_log`（in-memory） | 无 |
| **14j+** | in-memory + optional SQLite shadow write（behind flag） | `product_gate.db` shadow |
| **未来** | repository 双写 / 读路径切换 | 14e ADR Option B |

---

## 4. 不变量（必须保持）

| # | 不变量 |
|---|--------|
| 1 | **发送行为不变** — preview branch 永不 `_send_reply` / `SendMessage` / outbound |
| 2 | **preview 仍 zero-send** — test shop 只记录建议，不发出 |
| 3 | **non-test shop 仍 legacy** — 不进入 preview branch，不调用 service |
| 4 | **handler 不直接操作 DB** — 无 SQLAlchemy session / `create_all` / SQLite 文件操作 |
| 5 | **handler 不 import ORM models** — 无 `product_persistence.models` ORM、无 `database.models` |
| 6 | **service 是 preview ReplyLog 唯一写入边界** — handler 只调 `PreviewReplyLogService` |
| 7 | **SQLite shadow write 仍未实现**（14h/14i 范围外） |
| 8 | **assisted / auto 未实现** |
| 9 | **Doudian 不进入 production product persistence path** |
| 10 | **PDD queue name 不变** — 仍为 `pdd_{shop_id}` |
| 11 | **`PRODUCT_PERSISTENCE_ENABLED` 默认 false** — 14i 集成不依赖 flag on |

---

## 5. 集成范围

| 范围 | 14i 是否纳入 |
|------|-------------|
| Allowlisted test shop preview branch | ✅ |
| Non-test shop legacy send | ❌ 不改 |
| `PreviewReplyLogService` in-memory write wrap | ✅ |
| SQLite shadow write | ❌ → 14j planning / 后续实现 |
| Dashboard read API | ❌ → 14k planning |
| Assisted / Auto send | ❌ |
| Doudian production gate | ❌ |

---

## 6. 迁移策略（渐进 · 最小 diff）

### Step 1 — 14i：handler helper + service wrap（test shop only）

1. 在 `AIReplyHandler` 新增 `_record_preview_reply_log(...)` helper
2. helper 内部实例化或注入 `PreviewReplyLogService`，调用 `record_preview(...)`
3. `record_preview` 在 14i 实现为：委托 `append_preview_log`（保持 in-memory 行为等价）
4. `_handle_preview_product_gate` 将 `append_preview_log(...)` 替换为 `_record_preview_reply_log(...)`
5. 删除 handler 对 `append_preview_log` 的直接 import（改由 service 封装）

### Step 2 — 14j+：optional SQLite shadow（behind flag）

1. `record_preview` 在 in-memory 成功后，若 `PRODUCT_PERSISTENCE_WRITE_REPLY_LOG=true`，经 repository 写 shadow DB
2. DB write failure **不得** fallback 到 SendMessage
3. in-memory 仍为 primary read path until dashboard/API phase

### Step 3 — 未来：read path / dashboard

1. Dashboard read API 经 `PreviewReplyLogService.list_reply_logs()` 读
2. 逐步从 in-memory 切到 DB read（flag-gated）

---

## 7. 相关规划文档

| 文档 | 内容 |
|------|------|
| [phase14h_handler_boundary_plan.md](phase14h_handler_boundary_plan.md) | handler ↔ service 边界 |
| [phase14h_zero_send_regression_plan.md](phase14h_zero_send_regression_plan.md) | H1–H10 回归测试 |
| [phase14h_failure_policy.md](phase14h_failure_policy.md) | failure / fail-safe 策略 |

---

## 8. 验收标准（14i 实现时）

- [ ] test shop preview：service `record_preview` 被调用，zero-send 保持
- [ ] non-test shop：service 未被调用，legacy send 不变
- [ ] service failure：test shop 不 fallback SendMessage
- [ ] 无 `product_gate.db` 创建（14i 范围）
- [ ] handler 源码无 `db_manager` / ORM import
- [ ] 全量 unittest green

---

*Phase 14h · planning only · 2026-06-03*

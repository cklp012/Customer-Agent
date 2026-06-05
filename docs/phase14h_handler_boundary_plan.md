# Phase 14h — Handler Boundary Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 范围 | `AIReplyHandler` preview branch → `PreviewReplyLogService` |

---

## 1. 设计原则

| 层级 | 职责 |
|------|------|
| **Handler** | orchestration：收消息 → 分类 → 决策 → AI → guard → 记录 → 返回 |
| **Gates** | 纯函数：intent classification · send decision · guarded send |
| **Service** | preview ReplyLog 写入/读取边界 |
| **Repository** | 未来 DB 持久化（14j+） |
| **DB** | `product_gate.db` shadow（未实现） |

**Handler 不做 persistence 实现细节。**

---

## 2. AIReplyHandler 边界

### 2.1 Handler 负责（orchestration）

- 判断是否进入 preview branch（`product_gate_config` allowlist）
- 调用 `classify_consultation_intent`
- 调用 `build_send_decision`
- 调用 `_get_ai_reply`
- 调用 `evaluate_guarded_send`
- 调用 **service** 记录 preview log
- 记录 observability log（`log_message`）
- fail-safe：preview 异常 → `return False`，**不** fallback send

### 2.2 Handler 不负责

| 禁止 | 原因 |
|------|------|
| 直接 `append_preview_log`（14i 后） | 写入应经 service |
| `import product_persistence.db_manager` | DB 生命周期不属于 handler |
| `import product_persistence.repositories.*` | repository 由 service 持有 |
| `import product_persistence.models`（ORM） | handler 不感知表结构 |
| `import database.models` / `database.db_manager` | legacy DB 与 product gate 隔离 |
| SQLAlchemy session / `create_all` | 持久化在 service/repository 层 |
| SendMessage / outbound 在 preview branch | zero-send 不变量 |

### 2.3 Gates 层保持不变

以下逻辑 **留在** `Message/gates/`，handler 仅调用：

- `classify_consultation_intent` — intent
- `build_send_decision` — reply_mode / pause / gate enabled
- `evaluate_guarded_send` — send_status（`not_sent_preview` / `not_sent_human_takeover` 等）
- `product_gate_config` — allowlist 查询

---

## 3. Service 边界

### 3.1 `PreviewReplyLogService` 是唯一 preview ReplyLog 写入入口（14i 起）

```
handler._record_preview_reply_log(...)
    → PreviewReplyLogService.record_preview(
          message_text, reply_text,
          classification, send_decision, guarded_result,
          metadata, workspace_id, shop_id, ...
      )
```

### 3.2 14i 实现：`record_preview` 包装 in-memory

```python
# 14i 目标行为（规划示意，非本 phase 代码）
def record_preview(self, ..., classification, send_decision, guarded_result, metadata, ...):
    append_preview_log(
        message_text=...,
        reply_text=...,
        classification=classification,
        send_decision=send_decision,
        guarded_result=guarded_result,
        metadata=metadata,
        ...
    )
    return PreviewRecordResult(recorded=True, persistence_enabled=..., reason="in_memory")
```

- **等价迁移**：14i 不改变 in-memory 数据结构或 projection 字段
- **read path 已有**：14g `list_reply_logs()` 继续读同一 projection

### 3.3 后续：behind flag 双写 SQLite（14j+）

```
record_preview:
  1. append_preview_log (in-memory, always)
  2. if flags.should_write_reply_log() and repository:
       repository.save_reply_log(...)   # shadow SQLite
  3. DB failure → log + observable status, NO send fallback
```

---

## 4. 最小改动策略（14i）

### 4.1 保留当前 `append_preview_log` 行为

- 不修改 `preview_log.py` 数据结构
- 不修改 `reply_log_projection.py` 投影逻辑
- service 在 14i 内部委托 `append_preview_log`

### 4.2 新增 handler helper

建议在 `AIReplyHandler` 新增：

```python
def _record_preview_reply_log(
    self,
    *,
    message_text: str,
    reply_text: str,
    classification,
    send_decision,
    guarded_result,
    metadata: dict,
    gate_config,
) -> PreviewRecordResult:
    from product_persistence.services import PreviewReplyLogService
    svc = PreviewReplyLogService()
    return svc.record_preview(...)
```

**改动点：** `_handle_preview_product_gate` 内将直接 `append_preview_log(...)` 替换为 `self._record_preview_reply_log(...)`。

### 4.3 Import 边界（14i 后 handler 应仅 import）

| 允许 | 禁止 |
|------|------|
| `product_persistence.services.PreviewReplyLogService` | `product_persistence.db_manager` |
| `Message.gates.*`（classification / decision / guard / config） | `product_persistence.repositories.*` |
| | `product_persistence.models`（ORM） |
| | `database.models` / `database.db_manager` |

### 4.4 可选：lazy import

与当前 `_handle_preview_product_gate` 一致，service import 放在方法体内，避免非 test shop 路径加载 `product_persistence`。

---

## 5. Non-test shop 边界

| 路径 | service 调用 |
|------|-------------|
| Allowlist 未命中 | **不调用** `PreviewReplyLogService` |
| Legacy `_send_reply` | unchanged |
| Shadow SendDecision log（13b） | unchanged · observe-only |

---

## 6. Failure 边界

| 场景 | 行为 |
|------|------|
| test shop · service 抛异常 | **不** fallback `_send_reply` / SendMessage |
| test shop · service 失败 | 可 fallback 到直接 `append_preview_log`（fail-open in-memory）或 `return False`（fail-closed）— 见 [phase14h_failure_policy.md](phase14h_failure_policy.md) |
| non-test shop · service 不可用 | **无影响**（service 未被调用） |
| 未来 DB write failure | **不** 触发 SendMessage |

**硬规则：** test shop preview 任何 failure **不得** 走到 legacy send。

---

## 7. 测试策略（14i）

| 测试 | 方法 |
|------|------|
| service 被调用 | `patch.object(PreviewReplyLogService, "record_preview")` |
| zero-send | `patch` `_send_reply` / `SendMessage`，assert not called |
| service failure no-send | `record_preview` side_effect=Exception，assert no send |
| non-test no service | allowlist miss，assert `record_preview` not called |

详见 [phase14h_zero_send_regression_plan.md](phase14h_zero_send_regression_plan.md)。

---

## 8. 不在本边界内的组件

| 组件 | 状态 |
|------|------|
| `SendMessage` | 不改 |
| `outbound_resolver` | 不改 |
| `Channel/pinduoduo/**` | 不改 |
| `Channel/doudian/**` | 不改 |
| `AutoReplyThread` | 不改 |
| UI / API | 不改 |
| Assisted / Auto send | 未实现 |

---

*Phase 14h · planning only · 2026-06-03*

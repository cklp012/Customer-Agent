# Phase 14h — Failure Policy

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 前置 | [phase14e_flags_and_failure_policy.md](phase14e_flags_and_failure_policy.md) · [phase13c_rollback_and_safety.md](phase13c_rollback_and_safety.md) |
| 实现 | **Phase 14i+** |

---

## 1. 总原则

**Preview = zero-send。** 任何 product persistence / service 层 failure **不得** 将 test shop preview 路径 fallback 到 `SendMessage` / outbound / `_send_reply`。

**Non-test shop legacy 不受 product persistence failure 影响**（service 未被调用）。

---

## 2. Test shop preview — service failure

### 2.1 `PreviewReplyLogService.record_preview` 抛异常

| 策略 | 行为 |
|------|------|
| **禁止** | fallback `_send_reply` / `SendMessage` / outbound |
| **允许 A — fail-closed** | `return False`；debug/warning log；无 preview 记录 |
| **允许 B — fail-open in-memory** | catch exception → 直接 `append_preview_log` 作为 last-resort；仍 zero-send |
| **推荐（14i）** | **B** — in-memory fail-open 保持可观测性；与 13d fail-safe 精神一致 |

### 2.2 `record_preview` 返回 `recorded=False`

| reason | 行为 |
|--------|------|
| `product_persistence_disabled` | 14i 实现后应仍写 in-memory（service 内部委托 `append_preview_log`）；此 reason 仅当 14i 未更新 stub 时出现 |
| `in_memory_deferred` | 14g stub；14i 后不应出现在成功路径 |

### 2.3 AI reply 为空 / classifier 异常

**保持 13d 行为：**

- empty AI reply → `return False`，no send
- classifier / gate 异常 → fail-safe `return False`，no send
- **不因** service 集成而改变

---

## 3. Non-test shop — 不受影响

| 场景 | 行为 |
|------|------|
| service 模块 import 失败 | non-test shop 不 import service → **无影响** |
| `PRODUCT_PERSISTENCE_ENABLED` 任意值 | non-test shop 不调用 service → **无影响** |
| DB / SQLite 不可用 | non-test shop 不触达 DB → **无影响** |
| legacy `_send_reply` failure | 现有 outbound fallback 逻辑不变 |

---

## 4. 未来 DB persistence failure（14j+）

| 场景 | 行为 |
|------|------|
| SQLite shadow write 失败 | in-memory 已成功 → **不** 补发 SendMessage |
| `ProductDbManager.init_product_db` 失败 | service 读 in-memory；写 skip + log |
| repository `save_reply_log` 超时/异常 | observable error status；**不** 触发 send |
| `create_all` / migration 失败 | 启动不阻塞 legacy PDD；product persistence 降级为 in-memory only |

**硬规则：** DB persistence failure **永远不能** 触发 SendMessage。

---

## 5. 未来 Assisted mode failure（未实现 · 规划）

| 场景 | 行为 |
|------|------|
| AuditLog write 失败 | **禁止发送** — merchant approve 不可无审计 |
| PendingAssistedReply 创建失败 | **禁止发送** |
| Permission check 失败 | **禁止发送** |
| stale suggestion | **禁止发送** · 要求重新生成 |

**与 preview 不同：** assisted 是显式 send path，AuditLog failure = **hard block send**。

---

## 6. Auto mode

| 状态 | 政策 |
|------|------|
| **未实现** | 无 auto send path |
| 未来 | 独立 phase · 更强 safety · AuditLog + rate limit |

---

## 7. Doudian

| 规则 | 说明 |
|------|------|
| Doudian **不进入** production product persistence | mock spike only |
| Doudian handler **不调用** `PreviewReplyLogService` | H10 |
| Doudian preview gate | **未启用** |

---

## 8. 可观测性要求

所有 failure 必须可观察（至少一种）：

| 渠道 | 用途 |
|------|------|
| `logger.debug` / `logger.warning` | preview service failure · fail-safe |
| `log_message`（handler） | preview 记录成功/跳过 |
| future `AuditLog` | assisted approve/deny · admin actions |
| `PreviewRecordResult.reason` | service 层状态码 |
| future projection `error_status` 字段 | dashboard 展示 |

**禁止 silent failure 导致意外 send。**

---

## 9. Flags 与 failure 交互

| Flag | 默认 | failure 影响 |
|------|------|-------------|
| `PRODUCT_PERSISTENCE_ENABLED` | false | 14i 后 in-memory 写入**不依赖**此 flag |
| `PRODUCT_PERSISTENCE_WRITE_REPLY_LOG` | false | true 时 DB write 失败 → log only，no send |
| `product_gate_enabled`（per shop） | false | test shop allowlist only |
| `reply_mode` | preview | assisted/auto 未实现 |

---

## 10. 决策表（quick reference）

| 路径 | Failure | Send? | Fallback |
|------|---------|-------|----------|
| test shop preview | service exception | **NO** | in-memory append OR return False |
| test shop preview | DB write fail (future) | **NO** | in-memory only |
| non-test legacy | service N/A | legacy rules | unchanged |
| non-test legacy | outbound fail | legacy SendMessage fallback | unchanged |
| assisted (future) | AuditLog fail | **NO** | block + notify merchant |
| auto (future) | any | **NO** | not implemented |

---

*Phase 14h · planning only · 2026-06-03*

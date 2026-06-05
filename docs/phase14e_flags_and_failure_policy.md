# Phase 14e — Flags and Failure Policy

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 模块 | `product_persistence/flags.py`（14f） |

---

## 1. Feature flags

| 变量 | 默认 | 依赖 | 说明 |
|------|------|------|------|
| `PRODUCT_PERSISTENCE_ENABLED` | **false** | — | 总开关；false 时无 engine init |
| `PRODUCT_PERSISTENCE_WRITE_REPLY_LOG` | false | ENABLED | preview/assisted ReplyLog 双写 |
| `PRODUCT_PERSISTENCE_WRITE_SEND_DECISION` | false | ENABLED | SendDecision snapshot |
| `PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG` | false | ENABLED | AuditLog（含 admin 操作） |
| `PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED` | false | ENABLED | assisted pending 表 |
| `PRODUCT_PERSISTENCE_READ_DASHBOARD` | false | ENABLED | 读 DB 而非仅 in-memory |

**解析规则：**

```text
effective_write_reply_log =
  PRODUCT_PERSISTENCE_ENABLED
  && PRODUCT_PERSISTENCE_WRITE_REPLY_LOG
  && test_shop_gate_on (select_product_gate_config)
```

子开关在 `ENABLED=false` 时 **必须为 false**（忽略 env 误配）。

---

## 2. 与 product gate 关系

| 层 | 开关 |
|----|------|
| Gate allowlist | `set_test_shop_allowlist` / 未来 DB shop_bindings |
| Persistence | `PRODUCT_PERSISTENCE_*` |

**两者独立：** gate on + persistence off → 仅 in-memory（13d 今日行为）。

---

## 3. Failure policy 矩阵

| 场景 | persistence | 发送 | 日志 |
|------|-------------|------|------|
| flag off | in-memory only | legacy / preview per gate | debug |
| non-test + write fail | skip DB | **legacy 不变** | warning |
| test shop preview + write fail | **in-memory OK** | **no-send** | warning |
| test shop preview + in-memory fail | — | **no-send** (13d) | debug |
| assisted approve + AuditLog fail | — | **禁止 send** | error |
| assisted approve + ReplyLog fail | — | **禁止 send** | error |
| read fail (dashboard) | fallback in-memory | N/A | warning |

---

## 4. 禁止行为

| # | 禁止 |
|---|------|
| F1 | DB failure → fallback `_send_reply` / SendMessage |
| F2 | DB failure → enable legacy for test shop |
| F3 | persistence on for **all** PDD shops by default |
| F4 | Doudian production persistence write |
| F5 | auto send（未实现） |
| F6 | 无 AuditLog 的 assisted send |

---

## 5. test shop preview 推荐路径（14g）

```text
1. append_preview_log (Message/gates — always)
2. if effective_write_reply_log:
     try: ReplyLogRepository.create_preview_reply_log(...)
     except: log warning — do NOT raise to handler send path
3. return True (handled, not sent)
```

---

## 6. 观测

| 指标（未来） | 说明 |
|--------------|------|
| `product_persistence_write_errors` | DB 写失败计数 |
| `product_persistence_shadow_lag` | 内存 vs DB 条数差（测试） |

---

## 7. 回滚

| 动作 | 效果 |
|------|------|
| `PRODUCT_PERSISTENCE_ENABLED=false` | 立即回 in-memory only |
| 删 `product_gate.db` | 清空 shadow；legacy 不变 |
| 移除 test shop allowlist | preview gate off |

---

*Flags & failure policy · Phase 14e · 2026-06-03*

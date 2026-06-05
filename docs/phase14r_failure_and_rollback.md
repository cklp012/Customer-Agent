# Phase 14r — Failure and Rollback

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14p_failure_and_rollback.md](phase14p_failure_and_rollback.md) · [phase14r_audit_and_snapshot_sequence.md](phase14r_audit_and_snapshot_sequence.md) |

---

## 1. 总原则

| # | 原则 |
|---|------|
| F1 | **DB failure 不 fallback legacy send** |
| F2 | **AuditLog failure before send → no send**（strict 默认） |
| F3 | **Snapshot failure before send → no send**（推荐） |
| F4 | **Final guard failure → no send** |
| F5 | **Outbound failure → status failed · manual review · no auto retry** |
| F6 | **Duplicate request → idempotent · 不重复 send** |
| F7 | **Expired pending → no send** |
| F8 | **Role denied → no send** |
| F9 | **auto mode 未实现 · 不受影响** |

---

## 2. 失败场景矩阵

| 场景 | send? | pending | audit | 备注 |
|------|-------|---------|-------|------|
| create pending DB fail | ❌ | 无/rollback | 无 | |
| create audit fail (strict) | ❌ | rollback | 无 | |
| approve role denied | ❌ | pending | optional denied audit | viewer 403 |
| approve invalid state | ❌ | 不变 | 无 | sent/rejected/expired |
| approve audit fail before outbound | ❌ | approved | 缺失 | strict block |
| final guard fail | ❌ | approved/failed | final_guard_blocked | |
| snapshot merchant_confirm fail | ❌ | approved | partial | block send |
| outbound fail | attempt only | failed | outbound_send_failed | no retry |
| outbound success + audit fail | 已发送 | sent | recovery | no resend |
| duplicate approve | ❌ 2nd | sent | idempotent | |
| expire | ❌ | expired | assisted_expired | |

---

## 3. Rollback 策略

| 动作 | 行为 |
|------|------|
| disable assisted mode | shop `reply_mode=preview` · 新消息不走 assisted |
| keep preview mode | test shop zero-send 不变 |
| keep pending/audit tables | read-only · Dashboard future read |
| audit logs | **不 DELETE** |
| pending rows | cancel/expire · 不 force send |
| flags off | `WRITE_PENDING_ASSISTED=false` · service no-op |
| PDD legacy | **无影响** · queue `pdd_{shop_id}` 不变 |
| non-test legacy `_send_reply` | **无影响** |

---

## 4. Service 结果类型（规划）

```python
# 规划示意 · 14r 不写代码
@dataclass
class ApproveResult:
    success: bool
    sent: bool
    pending_assisted_id: str
    status: str
    guard_blocked: bool = False
    already_sent: bool = False
    error: str | None = None
    audit_warnings: tuple[str, ...] = ()
```

| 字段 | 含义 |
|------|------|
| `sent=False` + `guard_blocked=True` | guard 阻止 · 未 outbound |
| `already_sent=True` | 幂等 duplicate |
| `audit_warnings` | degraded only · 默认 empty |

---

## 5. 与 preview / legacy 隔离

| 路径 | AssistedReplyService failure |
|------|------------------------------|
| preview zero-send | **不调用** service approve |
| legacy send | **不调用** service · failure 无交叉 |
| Dashboard read (14o) | read-only · 不受影响 |

---

## 6. Doudian / auto

| 项 | 14r |
|----|-----|
| Doudian assisted send | ❌ 不启用 |
| auto send | ❌ 未实现 |
| rollback | 不涉及 auto |

---

*Phase 14r · planning only · 2026-06-03*

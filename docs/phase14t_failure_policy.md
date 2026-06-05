# Phase 14t — Final Guard Failure Policy

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase14r_failure_and_rollback.md](phase14r_failure_and_rollback.md) · [phase14s_pipeline_and_precedence.md](phase14s_pipeline_and_precedence.md) |

---

## 1. Fail-closed 总原则

| # | 原则 |
|---|------|
| F1 | **final guard block → no-send** |
| F2 | **guard internal exception → block `guard_exception`** · no-send |
| F3 | **audit failure before send → no-send**（strict 默认） |
| F4 | **snapshot failure before send → no-send** |
| F5 | **DB failure → no fallback legacy send** |
| F6 | **duplicate request → no double-send** |
| F7 | non-test legacy **unchanged** |
| F8 | Doudian production assisted/auto **not enabled** |

---

## 2. 失败场景矩阵

| 场景 | allowed_to_send | outbound | 备注 |
|------|-----------------|----------|------|
| guard rule block | false | ❌ | 正常 block |
| guard exception G27 | false | ❌ | fail-closed |
| policy read failure | false 或 safe default+block | ❌ | 不 legacy send |
| template validation missing | false G10 | ❌ | |
| audit fail before outbound | N/A | ❌ | strict |
| snapshot fail before outbound | N/A | ❌ | strict |
| outbound unavailable G26 | false | ❌ | |
| guard pass · outbound fail | 已 attempt | failed status | 不重发 |
| guard pass · audit after success fail | sent | 补 audit | no resend |

---

## 3. policy read failure

| 行为 | 说明 |
|------|------|
| fallback | [default_policy_matrix](phase14s_default_policy_matrix.md) in-memory |
| 仍 fail | `policy_blocked` or `guard_exception` |
| legacy | **不调用** `_send_reply` |

---

## 4. duplicate / idempotency

| 场景 | 行为 |
|------|------|
| status=sent | G16 · idempotent return |
| in-flight approve | 409 · no second outbound |
| same idempotency_key consumed | block duplicate |

---

## 5. Rollback

| 动作 | 效果 |
|------|------|
| disable assisted/auto | reply_mode=preview |
| keep preview zero-send | test shop unchanged |
| keep ReplyLog / policy read-only | Dashboard |
| audit logs | 不 DELETE |
| PDD queue | 仍 `pdd_{shop_id}` |
| legacy path | 无 guard 接入 |

---

## 6. preview path

| failure | 行为 |
|---------|------|
| guard error on preview | 仍 zero-send · log warning |
| 不影响 | legacy · handler hot path |

---

*Phase 14t · planning only · 2026-06-03*

# Phase 14a — Migration Sequence M0–M9（Product Gate Shadow Track）

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 原则 | **默认 off** · **non-test legacy 不变** · **可回滚** |
| 关联 | [phase12e_migration_sequence.md](phase12e_migration_sequence.md)（商户/凭证轨） |

---

## 总览

| 阶段 | 名称 | 写入 | 读取 | PDD legacy send |
|------|------|------|------|-----------------|
| **M0** | docs only（14a） | — | 内存 | ✅ 不变 |
| **M1** | 空 shadow 表 | ❌ | — | ✅ |
| **M2** | preview → ReplyLog shadow | 双写可选 | 仍内存优先 | ✅ non-test |
| **M3** | Dashboard 读 shadow | 双写 | DB 优先 | ✅ non-test |
| **M4** | assisted pending shadow | pending 表 | DB | ✅ non-test |
| **M5** | AuditLog shadow | audit 表 | DB | ✅ non-test |
| **M6** | 单店 assisted command | approve 写 | DB | test shop only |
| **M7** | internal allowlist 扩大 | 同 M6 | DB | allowlist 外 legacy |
| **M8** | auto mode planning | ❌ 发送 | — | ✅ |
| **M9** | legacy cleanup（可选） | — | — | 产品决策 |

---

## M0 — Docs only（Phase 14a）

| 项 | 内容 |
|----|------|
| **scope** | 本交付物；schema SSOT |
| **flags** | 无 |
| **rollback** | N/A |
| **tests** | 无 |
| **go/no-go** | 评审通过 → M1（14b Alembic draft） |

---

## M1 — 创建空 shadow 表

| 项 | 内容 |
|----|------|
| **scope** | CREATE `reply_logs`, `send_decision_snapshots`, `pending_assisted_replies`, `audit_logs`；**零写入** |
| **flags** | `SHADOW_DB_ENABLED=false`（默认） |
| **handler** | 不改 |
| **rollback** | DROP tables（14b migration down） |
| **tests** | migration 单测：表存在；默认约束 preview/false |
| **non-test** | legacy 100% |

**禁止：** 改 `database/models.py` legacy 类（新文件 `saas_models.py` 或独立 module — 14b 规划）。

---

## M2 — preview path 写 ReplyLog shadow

| 项 | 内容 |
|----|------|
| **scope** | test shop preview `append_preview_log` → **双写** DB `reply_logs` |
| **flags** | `SHADOW_REPLY_LOG_WRITE=false` 默认 |
| **read** | Dashboard / `list_preview_reply_logs()` **仍读内存** |
| **rollback** | flag off；停写 DB；内存路径不变 |
| **tests** | 13d Z1 + DB 行 `not_sent_preview`；non-test Z2 |
| **non-test** | 不写 shadow 或写 `skipped_gate_disabled`（可选） |

---

## M3 — Dashboard read model 改读 ReplyLog shadow

| 项 | 内容 |
|----|------|
| **scope** | `list_preview_reply_logs()` DB 后端；内存 fallback |
| **flags** | `SHADOW_REPLY_LOG_READ=false` 默认 |
| **rollback** | read flag off → 内存 |
| **tests** | projection parity 13e vs DB |
| **non-test** | 无 preview 行 |

---

## M4 — assisted pending table shadow write

| 项 | 内容 |
|----|------|
| **scope** | assisted AI 阶段写 `pending_assisted_replies` + ReplyLog |
| **flags** | `SHADOW_ASSISTED_PENDING_WRITE=false` |
| **send** | **仍 zero-send** at AI stage |
| **rollback** | flag off |
| **tests** | A2 + pending 行存在 |
| **non-test** | legacy |

---

## M5 — AuditLog shadow write

| 项 | 内容 |
|----|------|
| **scope** | mode change / pause / allowlist → `audit_logs` |
| **flags** | `SHADOW_AUDIT_LOG_WRITE=false` |
| **rollback** | flag off |
| **tests** | append-only；无 UPDATE |
| **non-test** | 仅 SaaS 管理动作 |

---

## M6 — 单测试店 assisted command

| 项 | 内容 |
|----|------|
| **scope** | `approve_assisted_reply` command（非 REST 或 internal CLI） |
| **flags** | 单店 allowlist + `reply_mode=assisted` |
| **send** | **仅** confirm 路径 SendMessage |
| **rollback** | 移除 allowlist → legacy |
| **tests** | A3 + AuditLog + SendDecision confirm snapshot |
| **non-test** | legacy Z2/A10 |

---

## M7 — 扩大到 internal allowlist shops

| 项 | 内容 |
|----|------|
| **scope** | 多个内部测试店；仍非全量 PDD |
| **flags** | 显式 allowlist 文件/DB |
| **rollback** | 逐店移除 |
| **tests** | allowlist 外店 regression |
| **non-test** | legacy |

---

## M8 — auto mode planning only

| 项 | 内容 |
|----|------|
| **scope** | **docs only** — auto 发送策略 |
| **send** | **禁止** 实现 |
| **rollback** | N/A |
| **go/no-go** | 独立评审；不与 M6/M7 捆绑 |

---

## M9 — legacy cleanup（长期稳定后）

| 项 | 内容 |
|----|------|
| **scope** | 可选退役双写；legacy 表只读 |
| **前提** | M3–M7 生产验证 ≥ N 月 |
| **rollback** | 保持 legacy 表备份 |
| **禁止** | 未评审即删 SendMessage 路径 |

---

## 每步通用要求

| 要求 | 说明 |
|------|------|
| **默认 off** | 新 flag 默认 false |
| **rollback** | flag off 或 allowlist 移除 → 立即 legacy |
| **验收** | 13d Z* + 13f A* 回归 + 本阶段新增测试 |
| **non-test** | `product_gate_enabled=false` → `_send_reply` 不变 |

---

*Migration sequence · Phase 14a · 2026-06-03*

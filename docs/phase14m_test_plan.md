# Phase 14m — SendDecision Snapshot Test Plan (Future 14n)

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 实现 | **Phase 14n** |
| 建议文件 | `tests/test_send_decision_snapshot_shadow_write.py` |

---

## 1. 目的

14n 实现 snapshot shadow write 后验证 flags、append-only、failure policy、Dashboard read model。

---

## 2. 测试矩阵 M1–M10

### M1 — `flags_off_no_snapshot`

| 项 | 内容 |
|----|------|
| 前置 | `WRITE_SEND_DECISION` unset/false |
| 操作 | `record_preview` with full gate context |
| 断言 | 无 `send_decision_snapshots` row |
| 断言 | in-memory ok |

---

### M2 — `flags_on_writes_snapshot`

| 项 | 内容 |
|----|------|
| 前置 | `ENABLED=true` · `WRITE_REPLY_LOG=true` · `WRITE_SEND_DECISION=true` |
| 操作 | test shop preview via service |
| 断言 | `reply_logs` row exists |
| 断言 | `send_decision_snapshots` row exists |
| 断言 | `reply_log_id` matches |
| 断言 | `decision_phase=ai_preview` |

---

### M3 — `replylog_failure_no_snapshot`

| 项 | 内容 |
|----|------|
| Patch | `ReplyLogRepositorySQLite.create_preview_reply_log` → raise |
| 前置 | both write flags on |
| 断言 | snapshot **not** written（推荐 policy） |
| 断言 | in-memory retained · no send |

---

### M4 — `snapshot_failure_no_send`

| 项 | 内容 |
|----|------|
| Patch | `SendDecisionRepositorySQLite.create_snapshot` → raise |
| Patch | `_send_reply` · `SendMessage` |
| 操作 | handler preview path |
| 断言 | **no send** |
| 断言 | in-memory retained |
| 断言 | `handle()` True（in-memory ok） |

---

### M5 — `snapshot_fields`

| 项 | 内容 |
|----|------|
| 断言 | row 含 `intent` · `intent_bucket` · `risk_level` |
| 断言 | `send_mode` · `allowed_to_send` · `allowed_to_generate` |
| blocked case | `blocked_reason` · `human_takeover_reason` populated |

---

### M6 — `append_only`

| 项 | 内容 |
|----|------|
| 策略 A | 同一 preview 重复调用 → 2 rows · 不同 `send_decision_id` |
| 策略 B | idempotent on (reply_log_id, decision_phase) — **14n 实现时文档化** |
| 断言 | 无 UPDATE SQL |

---

### M7 — `dashboard_detail_includes_snapshots`

| 项 | 内容 |
|----|------|
| 前置 | snapshot row exists |
| 操作 | detail read / repository list by reply_log_id |
| 断言 | `snapshots[]` length ≥ 1 |
| 断言 | fields match schema |

---

### M8 — `non_test_legacy_unchanged`

| 项 | 内容 |
|----|------|
| 前置 | flags on · non-test shop |
| 断言 | no snapshot row |
| 断言 | legacy `_send_reply` unchanged |

---

### M9 — `handler_no_snapshot_import`

| 项 | 内容 |
|----|------|
| 类型 | static |
| 文件 | `Message/handlers/ai_handler.py` |
| 断言 | no `SendDecisionRepository` |
| 断言 | no `send_decision_snapshots` import |

---

### M10 — `Doudian_not_enabled`

| 项 | 内容 |
|----|------|
| 前置 | flags on · `platform_id=doudian` |
| 断言 | no snapshot write |
| 断言 | no preview service path |

---

## 3. 与现有测试

| 现有 | 14n 后 |
|------|--------|
| S1–S8（14l ReplyLog） | green |
| H1–H10（14i handler） | green |
| M1–M10 | **新增** |

---

## 4. Go/No-Go（14n）

- [ ] M1–M10 green（适用项）
- [ ] zero-send unchanged
- [ ] flags default off
- [ ] no SendMessage in snapshot repository

---

*Phase 14m · planning only · 2026-06-03*

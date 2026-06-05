# Phase 14m — SendDecision Snapshot Failure & Rollback

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 对齐 | [phase14j_flags_failure_rollback.md](phase14j_flags_failure_rollback.md) · [phase14l_done.md](phase14l_done.md) |

---

## 1. Failure Policy

### 1.1 Flag off（默认）

| 行为 |
|------|
| 不写 `send_decision_snapshots` |
| in-memory preview 正常 |
| 无 snapshot 表创建（除非 WRITE_REPLY_LOG 已创建 DB） |

### 1.2 ReplyLog DB write 失败

| 行为 |
|------|
| in-memory **已写入** |
| **跳过** SQLite snapshot（推荐） |
| test shop **no-send** |
| `snapshot_recorded=False` · log warning |

### 1.3 Snapshot DB write 失败

| 行为 |
|------|
| in-memory **保留** |
| reply_logs SQLite 可能已成功 |
| **不** 抛异常到 handler |
| test shop **no-send** |
| `PreviewRecordResult.snapshot_error`（14n 规划字段） |

### 1.4 硬规则

| 规则 |
|------|
| **DB failure 不得 fallback SendMessage** |
| **non-test shop 不进入** product persistence write |
| read failure **不影响** send path |

---

## 2. non-test shop

| 路径 | snapshot |
|------|----------|
| legacy send | 无 service · 无 snapshot |
| flags on | 仍无 preview branch · 无 snapshot |

---

## 3. Rollback

### 3.1 软回滚 — 停 snapshot 写入

```powershell
$env:PRODUCT_PERSISTENCE_WRITE_SEND_DECISION = "false"
```

| 效果 |
|------|
| reply_logs 写入可继续（若 WRITE_REPLY_LOG=true） |
| 新 preview 无 snapshot 行 |
| 已有 snapshot 行保留 |

### 3.2 停全部 product persistence

```powershell
$env:PRODUCT_PERSISTENCE_ENABLED = "false"
```

### 3.3 硬回滚 — drop snapshot 表（确认无需要数据后）

```sql
-- future · product_gate.db only
DROP TABLE IF EXISTS send_decision_snapshots;
```

| 注意 |
|------|
| **不** 动 `channel_shop.db` |
| **不** 动 `reply_logs`（除非一并 rollback） |

---

## 4. 未来 assisted approve failure（未实现）

| 场景 | 政策 |
|------|------|
| snapshot write fail on approve | **禁止发送** 或 require retry |
| AuditLog fail | **禁止发送**（13f SSOT） |
| preview path | fail-open in-memory · **仍 no-send** |

**preview vs assisted 政策不同：**

- preview：DB fail → in-memory ok · zero-send
- assisted：DB fail → **block send**

---

## 5. Auto

**未实现** — 无 rollback 路径。

---

## 6. Doudian

| 规则 |
|------|
| production 不写 snapshot |
| mock/dev 可选 · 不进入 send path |

---

## 7. 决策表

| 路径 | Snapshot fail | Send? |
|------|---------------|-------|
| test shop preview | yes | **NO** |
| test shop preview | no · in-memory ok | **NO** |
| non-test legacy | N/A | legacy rules |
| assisted approve (future) | yes | **NO** |

---

*Phase 14m · planning only · 2026-06-03*

# Phase 14j — Flags, Failure & Rollback

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 对齐 | [phase14e_flags_and_failure_policy.md](phase14e_flags_and_failure_policy.md) · [phase14h_failure_policy.md](phase14h_failure_policy.md) |

---

## 1. Environment Flags

| Flag | 默认 | 14l 用途 |
|------|------|----------|
| `PRODUCT_PERSISTENCE_ENABLED` | `false` | 总开关 · off = 仅 in-memory |
| `PRODUCT_PERSISTENCE_WRITE_REPLY_LOG` | `false` | ReplyLog SQLite shadow write |
| `PRODUCT_DB_URL` | `sqlite:///./temp/product_gate.db` | shadow DB 路径 |

**14j 不修改 `product_persistence/flags.py` 代码。**

### 其他 flags（14l 不启用）

| Flag | 默认 | Phase |
|------|------|-------|
| `PRODUCT_PERSISTENCE_WRITE_SEND_DECISION` | false | 14m |
| `PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG` | false | 14n |
| `PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED` | false | 14n |
| `PRODUCT_PERSISTENCE_READ_DASHBOARD` | false | 14k+ |

---

## 2. 推荐启用条件（shadow write）

全部满足才开启 SQLite shadow（本地 pilot / CI only）：

```powershell
$env:PRODUCT_PERSISTENCE_ENABLED = "true"
$env:PRODUCT_PERSISTENCE_WRITE_REPLY_LOG = "true"
# optional override:
# $env:PRODUCT_DB_URL = "sqlite:///./temp/product_gate.db"
```

| 运行时条件 | 必须 |
|------------|------|
| allowlist test shop 命中 | ✅ |
| `reply_mode=preview` | ✅ |
| `product_gate_enabled=true` | ✅ |
| `platform_id=pinduoduo` | ✅ |

**生产默认：不设置 env → flags off → 无 `product_gate.db`。**

---

## 3. Failure Policy

### 3.1 Flag off（默认）

| 行为 |
|------|
| 仅 `append_preview_log` in-memory |
| 不创建 `product_gate.db` |
| test shop preview zero-send |
| non-test shop 不进入 service write |

### 3.2 SQLite init failure

| 行为 |
|------|
| log `warning` |
| 跳过 SQLite · 进程内可重试或永久降级 in-memory |
| in-memory record 仍成功 → handler `return True` |
| test shop **no-send** |

### 3.3 SQLite write failure

| 行为 |
|------|
| in-memory **已写入**（first write 成功） |
| `db_recorded=False` · `db_error` 填充 |
| test shop **no-send** |
| **禁止** fallback legacy send |

### 3.4 in-memory write failure

| 行为 |
|------|
| 与 14i 相同：handler fail-open 直接 `append_preview_log` 或 `return False` |
| **禁止** legacy send |

### 3.5 non-test shop

| 行为 |
|------|
| 不调用 `PreviewReplyLogService.record_preview` |
| 不受 product persistence failure 影响 |
| legacy `_send_reply` 路径不变 |

### 3.6 未来 assisted approve（未实现）

| 场景 | 政策 |
|------|------|
| AuditLog write failure | **禁止发送** |
| PendingAssistedReply failure | **禁止发送** |
| DB unavailable | **禁止发送**（与 preview 不同） |

**preview = zero-send；assisted = explicit send with hard DB gate。**

---

## 4. Rollback Procedure

### 4.1 软回滚（推荐 · 无数据丢失）

```powershell
$env:PRODUCT_PERSISTENCE_WRITE_REPLY_LOG = "false"
$env:PRODUCT_PERSISTENCE_ENABLED = "false"
```

| 效果 |
|------|
| 后续 preview 仅 in-memory |
| 已有 `product_gate.db` 保留（只读 archive） |
| handler / SendMessage / PDD 无改动 |

### 4.2 移除 test shop allowlist

```python
# tests / pilot config
clear_test_shop_allowlist()
```

| 效果 |
|------|
| 无 preview branch · 无 service write |
| 回到 legacy send |

### 4.3 硬回滚（确认无需要数据后）

```powershell
Remove-Item -Force .\temp\product_gate.db -ErrorAction SilentlyContinue
```

| 注意 |
|------|
| **仅删除** `product_gate.db` |
| **`channel_shop.db` 不动** |
| 需确认 shadow 数据可丢弃 |

### 4.4 Go/No-Go 检查

- [ ] flags 已设 false
- [ ] test shop allowlist 已清或保留（按需）
- [ ] Z1/H1 zero-send 仍绿
- [ ] non-test legacy send 仍绿
- [ ] `diagnose_runtime.py` 无异常

---

## 5. 决策表

| 路径 | Flag | DB | Send? |
|------|------|-----|-------|
| test shop preview | off | 无 | **NO** |
| test shop preview | on · write ok | shadow row | **NO** |
| test shop preview | on · write fail | in-memory only | **NO** |
| non-test legacy | any | 无 write | legacy rules |
| assisted (future) | on · audit fail | — | **NO** |

---

*Phase 14j · planning only · 2026-06-03*

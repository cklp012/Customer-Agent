# Phase 15o — Rollback Checklist

| 项 | 内容 |
|----|------|
| 类型 | **runbook checklist** |
| 用途 | 本地 smoke 后恢复默认安全状态 |

---

## 1. 清除 / 关闭 flags

| # | 动作 | 目标值 |
|---|------|--------|
| 1 | `PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED` | **false** 或 unset |
| 2 | `PRODUCT_ASSISTED_SEND_ENABLED` | **false** 或 unset |
| 3 | `PRODUCT_ASSISTED_SEND_DRY_RUN` | **true**（或 unset · 默认 true） |
| 4 | `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID` | **清空** / unset |
| 5 | `PRODUCT_PERSISTENCE_ENABLED` | **false** 或 unset（若仅为 smoke 开启） |
| 6 | 其他 `PRODUCT_PERSISTENCE_WRITE_*` | unset（恢复默认 off） |
| 7 | `PRODUCT_ASSISTED_SERVICE_ENABLED` | unset |

### PowerShell（清除 session env）

```powershell
Remove-Item Env:PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED -ErrorAction SilentlyContinue
Remove-Item Env:PRODUCT_ASSISTED_SEND_ENABLED -ErrorAction SilentlyContinue
Remove-Item Env:PRODUCT_ASSISTED_SEND_DRY_RUN -ErrorAction SilentlyContinue
Remove-Item Env:PRODUCT_ASSISTED_SEND_TEST_SHOP_ID -ErrorAction SilentlyContinue
Remove-Item Env:PRODUCT_PERSISTENCE_ENABLED -ErrorAction SilentlyContinue
Remove-Item Env:PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED -ErrorAction SilentlyContinue
Remove-Item Env:PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG -ErrorAction SilentlyContinue
Remove-Item Env:PRODUCT_PERSISTENCE_WRITE_SEND_DECISION -ErrorAction SilentlyContinue
Remove-Item Env:PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY -ErrorAction SilentlyContinue
Remove-Item Env:PRODUCT_PERSISTENCE_WRITE_ACTION_IDEMPOTENCY -ErrorAction SilentlyContinue
Remove-Item Env:PRODUCT_ASSISTED_SERVICE_ENABLED -ErrorAction SilentlyContinue
Remove-Item Env:PRODUCT_DB_URL -ErrorAction SilentlyContinue
```

---

## 2. 停止本地进程

| # | 动作 |
|---|------|
| 1 | 停止本地 PyQt / Flask app（若曾启动） |
| 2 | 关闭仅用于 smoke 的终端 session |

---

## 3. 清理本地临时 DB（可选）

| 路径 | 说明 |
|------|------|
| `temp/product_smoke_local.db` | smoke 专用 · 可删除 |
| `temp/phase15*_tests/` | 测试临时库 · 测试 teardown 已清理 |

```powershell
Remove-Item -Force .\temp\product_smoke_local.db -ErrorAction SilentlyContinue
```

**无生产 data migration rollback 需求** — smoke 仅用本地 SQLite。

---

## 4. 验证回滚成功

| # | 检查 | 命令 / 期望 |
|---|------|-------------|
| 1 | flags 默认 off | `uv run python -m unittest tests.test_phase15o_local_dashboard_action_smoke.TestPhase15oDefaultSafeState -v` |
| 2 | action routes 不注册 | O1 / O16 pass |
| 3 | `git status` | clean（smoke 未改代码） |
| 4 | PDD legacy 仍可启动 | 正常启动 PyQt app · 无 action route 副作用 |
| 5 | 全量测试 | `uv run python -m unittest discover -s tests -v` → OK |

---

## 5. 不变项（签收）

| 项 | 状态 |
|----|------|
| PDD legacy hot path | **unchanged** |
| Queue `pdd_{shop_id}` | **unchanged** |
| DB schema | **无 migration** |
| 生产配置 | smoke flags **不得**提交到 repo |

---

*Phase 15o · 2026-06-03*

# Phase 15o — Local Dashboard Action Smoke Runbook

| 项 | 内容 |
|----|------|
| 类型 | **local smoke / runbook** |
| 日期 | 2026-06-03 |
| 前置 | [phase15l_done.md](phase15l_done.md) · [phase15m_done.md](phase15m_done.md) · [phase15n_done.md](phase15n_done.md) |

---

## 1. Phase 15o 定位

| 项 | 结论 |
|----|------|
| 交付 | smoke runbook + flag matrix + curl 示例 + 验收清单 + 可选轻量测试 |
| live assisted send | ❌ **未实现** |
| auto retry / reconciliation worker | ❌ **未实现** |
| 真实 PDD outbound / SendMessage | ❌ **不调用** |
| PDD legacy hot path | ✅ **不变** |
| 测试环境 | **仅本地** · 不用真实买家会话做 live send |

---

## 2. 默认安全状态（签收）

未设置任何 product flag 时：

| 检查项 | 期望 |
|--------|------|
| `PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED` | false |
| Action routes 注册 | **无** |
| `apply_dashboard_action_route_bootstrap()` | 返回 False |
| PDD PyQt 启动 | 与 Phase 15l 前相同 |
| live send | 不可能 |

验证：`tests/test_phase15o_local_dashboard_action_smoke.py` **O1** · `test_pending_assisted_action_routes_registration.py` **L4**

---

## 3. 本地 dry-run smoke 目标

| # | 目标 | 验证方式 |
|---|------|----------|
| 1 | action routes default off | flag helper + bootstrap |
| 2 | flag on → routes 注册 | mock Flask `add_url_rule` × 2 |
| 3 | approve 需要 CSRF / confirm / client_request_id | handler 400/403 |
| 4 | approve **dry-run only** (`dry_run_expected=true`) | 422 if false |
| 5 | approve 响应 `live_send_attempted=false` · `dry_run=true` | integration test |
| 6 | reject no-send | mock service · no outbound |
| 7 | no SendMessage / no PDD outbound | runtime mock + static |
| 8 | idempotency replay / conflict | 15j + **O8/O9** |
| 9 | rollback 恢复安全 | flag matrix doc + **O16** |

---

## 4. 执行步骤（operator · local only）

### Step 0 — 前置

- 克隆仓库 · `git status clean`
- **不要**连接生产 PDD 店 · **不要**用真实 buyer_id 测 live send
- 使用 [phase15o_flag_matrix_and_safe_env.md](phase15o_flag_matrix_and_safe_env.md) 中 **Local dry-run smoke** 矩阵

### Step 1 — 确认默认 off

```powershell
# 确保 dashboard action flag 未设置或为 false
uv run python -m unittest tests.test_phase15o_local_dashboard_action_smoke.TestPhase15oDefaultSafeState -v
```

### Step 2 — 启用本地 dry-run smoke flags

设置环境变量（见 flag matrix）后启动本地 app **或** 直接跑单元 smoke：

```powershell
uv run python -m unittest tests.test_phase15o_local_dashboard_action_smoke -v
```

### Step 3 — 创建 pending（本地 SQLite）

通过 `AssistedReplyService.create_pending_from_preview`（测试已封装）— 仅本地 `temp/` DB。

### Step 4 — 调用 approve / reject

- 使用 [phase15o_manual_curl_examples.md](phase15o_manual_curl_examples.md) 占位 curl **或** dispatcher/handler 测试
- **必须** `dry_run_expected=true`
- **禁止** `dry_run_expected=false`（返回 `live_send_not_implemented`）

### Step 5 — no-send 验收

完成 [phase15o_no_send_verification_checklist.md](phase15o_no_send_verification_checklist.md)

### Step 6 — 回滚

完成 [phase15o_rollback_checklist.md](phase15o_rollback_checklist.md)

---

## 5. 禁止（签收）

| 禁止 |
|------|
| 生产环境开启 action routes 做 live send 试验 |
| 真实买家会话 + live flags off 以外的“试发” |
| `dry_run_expected=false` 期待成功发送 |
| 修改 PDD hot path / queue 做 smoke |
| 本 runbook 触发 reconciliation worker |

---

## 6. 相关文档

| 文档 | 内容 |
|------|------|
| [phase15o_flag_matrix_and_safe_env.md](phase15o_flag_matrix_and_safe_env.md) | Flag 矩阵 |
| [phase15o_manual_curl_examples.md](phase15o_manual_curl_examples.md) | curl 示例 |
| [phase15o_no_send_verification_checklist.md](phase15o_no_send_verification_checklist.md) | No-send 清单 |
| [phase15o_rollback_checklist.md](phase15o_rollback_checklist.md) | 回滚 |
| [phase15o_test_plan.md](phase15o_test_plan.md) | O1–O18 |

---

*Phase 15o · 2026-06-03*

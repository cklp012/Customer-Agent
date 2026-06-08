# Phase 15o — No-Send Verification Checklist

| 项 | 内容 |
|----|------|
| 类型 | **runbook checklist** |
| 用途 | 本地 smoke 完成后逐项勾选 |

---

## A. 代码 / 仓库边界

| # | 检查项 | 期望 | 验证 |
|---|--------|------|------|
| A1 | git diff 不含 PDD hot path | 无 `Channel/pinduoduo/**` 发送路径改动 | `git diff --stat` |
| A2 | 无 SendMessage 改动 | `SendMessage` 文件未改 | git diff |
| A3 | 无 handler 改动 | `Message/handlers/**` 未改 | git diff |
| A4 | 无 outbound resolver 改动 | resolver 未改 | git diff |
| A5 | `Channel/pinduoduo` 未变（smoke 阶段） | 无业务发送逻辑变更 | git diff |
| A6 | `Channel/doudian` 未变 | 无变更 | git diff |

---

## B. 运行时 no-send

| # | 检查项 | 期望 | 验证 |
|---|--------|------|------|
| B1 | SendMessage 未被调用 | mock 0 calls | O12 / test_i7 |
| B2 | handler `_send_reply` 未被调用 | mock 0 calls | O12 |
| B3 | outbound resolver 未被调用 | 无 import/call | 静态 + smoke |
| B4 | `LivePddAssistedOutboundPort` 未 wired | service 仍 DryRun only | M25 / O12 |

---

## C. Queue / 命名

| # | 检查项 | 期望 | 验证 |
|---|--------|------|------|
| C1 | `pdd_queue_name("shop123")` | `"pdd_shop123"` | O15 |

---

## D. Approve 响应形状（dry-run）

| # | 检查项 | 期望 |
|---|--------|------|
| D1 | `live_send_attempted` | **false** |
| D2 | `dry_run` | **true** |
| D3 | `would_send` | **true**（dry-run would_send 语义） |
| D4 | `provider_message_id` | 空 / null / 缺失 |
| D5 | `sent_at` | 空 / null / 缺失 |
| D6 | `status` | `dry_run_would_send` |

---

## E. 数据状态（dry-run）

| # | 检查项 | 期望 |
|---|--------|------|
| E1 | pending **未**标记 `sent` | 仍为 pending 或 dry-run 审计态 · 非 live sent |
| E2 | outbound idempotency **未** `succeeded`（live） | dry-run path only |
| E3 | 无真实 `provider_message_id` 写入 |

---

## F. 日志 / audit 安全

| # | 检查项 | 期望 |
|---|--------|------|
| F1 | 响应 JSON 无 cookie/token/credential | O17 |
| F2 | audit 行无 session 原始值 | 人工 spot-check 本地 DB |
| F3 | 错误信息 dashboard-safe | 无 API key 泄漏 |

---

## G. Read dashboard 不变

| # | 检查项 | 期望 |
|---|--------|------|
| G1 | read routes 注册逻辑未因 smoke 改变 | O18 |
| G2 | `PRODUCT_PERSISTENCE_READ_DASHBOARD` 默认 off 行为不变 | flags test |

---

## 快速命令

```powershell
uv run python -m unittest tests.test_phase15o_local_dashboard_action_smoke -v
uv run python -m unittest discover -s tests -v
git diff --stat
```

---

*Phase 15o · 2026-06-03*

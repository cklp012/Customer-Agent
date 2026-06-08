# Phase 15o — Manual cURL Examples (Local Only)

| 项 | 内容 |
|----|------|
| 类型 | **runbook reference** |
| 警告 | **local-only · placeholders · no real live send** |

---

## 免责声明

| 规则 |
|------|
| 示例 **仅用于本地** dashboard / Flask 联调 |
| 所有 ID、token、shop、buyer 均为 **占位符** |
| **不要**使用真实买家会话测试 live send |
| **必须** `dry_run_expected=true` on approve |
| reject 为 no-send 路径 |
| 未开启 `PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED` 时 curl 将 404 |

---

## 环境前提

- Base URL 占位：`http://127.0.0.1:5000`（本地 Flask · 非生产）
- Header：`Content-Type: application/json`
- CSRF：示例用占位 `csrf-token-local-smoke` — 与本地 dashboard 实现一致时替换

---

## 1. Approve（dry-run only）

```bash
curl -s -X POST "http://127.0.0.1:5000/api/product/pending-assisted/<PENDING_ASSISTED_ID>/approve" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "ws-local-smoke-1",
    "shop_id": "shop-local-smoke-1",
    "actor_user_id": "op-local-1",
    "actor_role": "operator",
    "client_request_id": "req-approve-smoke-001",
    "expected_pending_status": "pending",
    "dry_run_expected": true,
    "csrf_token": "csrf-token-local-smoke",
    "confirm_checkbox": true,
    "final_reply_override": "您好，该商品目前有货，欢迎下单。"
  }'
```

**期望（成功 dry-run）：** HTTP 200 · `dry_run=true` · `would_send=true` · `live_send_attempted=false` · `status=dry_run_would_send`

**禁止：** `"dry_run_expected": false` → 422 `live_send_not_implemented`

---

## 2. Reject（no-send）

```bash
curl -s -X POST "http://127.0.0.1:5000/api/product/pending-assisted/<PENDING_ASSISTED_ID>/reject" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "ws-local-smoke-1",
    "shop_id": "shop-local-smoke-1",
    "actor_user_id": "op-local-1",
    "actor_role": "operator",
    "client_request_id": "req-reject-smoke-001",
    "expected_pending_status": "pending",
    "reject_reason": "not suitable for assisted reply",
    "csrf_token": "csrf-token-local-smoke",
    "confirm_checkbox": true
  }'
```

**期望：** HTTP 200 · `action=reject` · 无 outbound send · pending → rejected

---

## 3. Replay — same `client_request_id` + same payload

第二次发送 **完全相同** body（15j idempotency flag on）：

```bash
# 重复执行 §1 的 curl，client_request_id 不变
```

**期望：** HTTP 200 · 与首次 **相同** response body · **无** 第二次 `approve_pending` side effect（service 不被重复调用路径由 idempotency 保证）

---

## 4. Conflict — same `client_request_id` + different payload

```bash
curl -s -X POST "http://127.0.0.1:5000/api/product/pending-assisted/<PENDING_ASSISTED_ID>/approve" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "ws-local-smoke-1",
    "shop_id": "shop-local-smoke-1",
    "actor_user_id": "op-local-1",
    "actor_role": "operator",
    "client_request_id": "req-approve-smoke-001",
    "expected_pending_status": "pending",
    "dry_run_expected": true,
    "csrf_token": "csrf-token-local-smoke",
    "confirm_checkbox": true,
    "final_reply_override": "DIFFERENT TEXT — conflict test"
  }'
```

**期望：** HTTP **409** · `status=conflict` · `reason=client_request_conflict` · **无** send

---

## 5. 无 Flask 时（单元 smoke 推荐）

不启动 HTTP server — 使用仓库测试：

```powershell
uv run python -m unittest tests.test_phase15o_local_dashboard_action_smoke -v
```

等价验证 handler / dispatcher · 无需 curl。

---

*Phase 15o · local-only · 2026-06-03*

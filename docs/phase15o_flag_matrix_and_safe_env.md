# Phase 15o — Flag Matrix and Safe Environment

| 项 | 内容 |
|----|------|
| 类型 | **runbook reference** |
| 对齐 | [phase15l_done.md](phase15l_done.md) · [phase15f_done.md](phase15f_done.md) |

---

## 1. Default safe（生产 / 日常开发默认）

**不设置以下变量，或全部保持 off：**

| Flag | 值 |
|------|-----|
| `PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED` | **false**（默认） |
| `PRODUCT_PERSISTENCE_ENABLED` | **false** |
| `PRODUCT_ASSISTED_SERVICE_ENABLED` | **false** |
| `PRODUCT_ASSISTED_SEND_ENABLED` | **false** |
| `PRODUCT_ASSISTED_SEND_DRY_RUN` | **true**（env 缺省时默认 true） |
| `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID` | **空** |

| 结果 |
|------|
| Action routes **不注册** |
| Assisted approve/reject HTTP **不可用** |
| 无 product DB 副作用（persistence off） |
| PDD legacy 启动 **不变** |

---

## 2. Local dry-run smoke（仅本地联调）

**用途：** 验证 action route 注册 + dry-run approve/reject + idempotency — **不 live send**。

| Flag | 值 |
|------|-----|
| `PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED` | **true** |
| `PRODUCT_PERSISTENCE_ENABLED` | **true** |
| `PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED` | **true** |
| `PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG` | **true** |
| `PRODUCT_PERSISTENCE_WRITE_SEND_DECISION` | **true** |
| `PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY` | **true** |
| `PRODUCT_PERSISTENCE_WRITE_ACTION_IDEMPOTENCY` | **true** |
| `PRODUCT_ASSISTED_SERVICE_ENABLED` | **true** |
| `PRODUCT_ASSISTED_SEND_ENABLED` | **true** |
| `PRODUCT_ASSISTED_SEND_DRY_RUN` | **true** ← **必须保持 true** |
| `PRODUCT_ASSISTED_SEND_TEST_SHOP_ID` | `<test_shop_id>` 占位，如 `shop-local-smoke-1` |
| `PRODUCT_DB_URL` | `sqlite:///./temp/product_smoke_local.db`（建议独立文件） |

### PowerShell 示例（session only）

```powershell
$env:PRODUCT_DASHBOARD_ACTION_ROUTES_ENABLED = "true"
$env:PRODUCT_PERSISTENCE_ENABLED = "true"
$env:PRODUCT_PERSISTENCE_WRITE_PENDING_ASSISTED = "true"
$env:PRODUCT_PERSISTENCE_WRITE_AUDIT_LOG = "true"
$env:PRODUCT_PERSISTENCE_WRITE_SEND_DECISION = "true"
$env:PRODUCT_PERSISTENCE_WRITE_OUTBOUND_IDEMPOTENCY = "true"
$env:PRODUCT_PERSISTENCE_WRITE_ACTION_IDEMPOTENCY = "true"
$env:PRODUCT_ASSISTED_SERVICE_ENABLED = "true"
$env:PRODUCT_ASSISTED_SEND_ENABLED = "true"
$env:PRODUCT_ASSISTED_SEND_DRY_RUN = "true"
$env:PRODUCT_ASSISTED_SEND_TEST_SHOP_ID = "shop-local-smoke-1"
$env:PRODUCT_DB_URL = "sqlite:///./temp/product_smoke_local.db"
```

---

## 3. Must remain false / not-live（签收）

| 项 | 要求 |
|----|------|
| `PRODUCT_ASSISTED_SEND_DRY_RUN` | **必须为 true**（smoke 阶段） |
| `LivePddAssistedOutboundPort` wiring | **未接入** `AssistedReplyService` |
| `dry_run_expected` in approve body | **必须为 true** |
| 真实 `SendMessage` | **不得调用** |
| PDD production session | **不得用于 smoke live send** |

即使误设 `PRODUCT_ASSISTED_SEND_DRY_RUN=false`：

- Route 仍要求 `dry_run_expected=true`（15i）
- `LivePddAssistedOutboundPort` 未 wired · live send **未实现**

---

## 4. 与 read dashboard flags

| Flag | Smoke 是否需要 |
|------|----------------|
| `PRODUCT_PERSISTENCE_READ_DASHBOARD` | **可选** · approve/reject smoke **不依赖** |
| `register_dashboard_read_routes` | **不变** · 与 action routes 独立 |

---

## 5. Helper 快查

| Helper | Default safe | Local smoke |
|--------|--------------|-------------|
| `is_dashboard_action_routes_enabled()` | false | true |
| `is_assisted_service_enabled()` | false | true |
| `is_assisted_send_enabled()` | false | true |
| `is_assisted_send_dry_run()` | true | true |
| `is_assisted_dry_run_outbound_enabled()` | false | true（全 flag 开时） |
| `would_assisted_send_live()` | false | **false**（dry_run=true） |

---

*Phase 15o · 2026-06-03*

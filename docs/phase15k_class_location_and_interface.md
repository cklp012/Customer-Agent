# Phase 15k — Class Location and Interface

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15c_done.md](phase15c_done.md) · [phase15h_pdd_outbound_boundary_and_adapter.md](phase15h_pdd_outbound_boundary_and_adapter.md) |

---

## 1. 建议文件位置

| 项 | 值 |
|----|-----|
| 路径 | `product_persistence/services/live_pdd_assisted_outbound_port.py` |
| 模块 | 与 `assisted_outbound_port.py` 同层 |
| 注册 | **不**在 15k/15m 自动 import 到 route 或 app.py |

---

## 2. Class 定义（future）

```python
class LivePddAssistedOutboundPort(AssistedOutboundPort):
    def send(self, request: AssistedOutboundRequest) -> AssistedOutboundResult:
        ...
```

| 规则 |
|------|
| **必须**实现 `AssistedOutboundPort.send` |
| **必须**使用 `AssistedOutboundRequest` 输入 |
| **必须**返回 `AssistedOutboundResult` 输出 |
| **禁止**新增 parallel live-only request/result schema |

---

## 3. Interface 复用（15c 稳定）

| 类型 | 来源 | 说明 |
|------|------|------|
| `AssistedOutboundPort` | `assisted_outbound_port.py` | ABC / Protocol |
| `AssistedOutboundRequest` | 15c | 不扩展 live-only 字段 |
| `AssistedOutboundResult` | 15c | 使用现有 `platform_status` / error fields |
| `build_assisted_outbound_request` | 15c helper | service 构建 request · port 只 consume |

---

## 4. Port-local validation（future · before primitive call）

| 字段 | 规则 | fail result |
|------|------|-------------|
| `platform_id` | must be `pinduoduo` | `validation_failed` |
| `shop_id` | non-empty | `validation_failed` |
| `buyer_id` | non-empty | `validation_failed` |
| `final_reply` | non-empty · no trim-to-empty | `validation_failed` |
| `pending_assisted_id` | non-empty | `validation_failed` |
| `idempotency_key` | non-empty | `validation_failed` |
| `dry_run` | must be `false` for live port | return dry-run rejection or delegate to DryRun port |

**Validation fail → `AssistedOutboundResult(success=false, platform_status=validation_failed)`**

| 规则 |
|------|
| **不 raise** 到 route 造成 unknown send state |
| initialization fatal（missing primitive config）may raise at construct time only |
| **no import** from dashboard route module |

---

## 5. Port 不负责

| 职责 | Port |
|------|------|
| final guard | ❌ |
| merchant policy | ❌ |
| audit | ❌ |
| snapshot | ❌ |
| outbound idempotency acquire/mark | ❌ |
| action idempotency (client_request_id) | ❌ |
| pending status | ❌ |
| dashboard permission / CSRF | ❌ |
| allowlist / send flags decision | ❌ (service selects port) |
| AI text generation | ❌ |
| modify `final_reply` | ❌ |

---

## 6. DI 与 port 选择（future · 15m）

```text
AssistedReplyService._outbound_port_instance():
    if dry_run flags → DryRunAssistedOutboundPort()
    elif live flags + allowlist → LivePddAssistedOutboundPort(primitive=...)
    else → DryRunAssistedOutboundPort() or no-send path
```

**Never** silently substitute DryRun → Live without explicit flags + allowlist + DI.

---

## 7. 禁止 import

| 禁止 | 原因 |
|------|------|
| `pending_assisted_action_routes` | route 调用 service · 非反向 |
| `Message.handlers` | no handler bypass |
| `database.models` | product DB only via service |

---

*Phase 15k · docs only · 2026-06-03*

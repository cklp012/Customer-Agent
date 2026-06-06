# Phase 15h — PDD Outbound Boundary and Adapter

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 对齐 | [phase15c_done.md](phase15c_done.md) · [phase15e_live_outbound_port_boundary.md](phase15e_live_outbound_port_boundary.md) |

---

## 1. Interface 复用（15c 稳定）

| 类型 | 来源 | 说明 |
|------|------|------|
| Input | `AssistedOutboundRequest` | 15c 已定义 · live **不新增** parallel contract |
| Output | `AssistedOutboundResult` | 15c 已定义 · 扩展 `platform_status` / error fields only |
| Interface | `AssistedOutboundPort.send` | `LivePddAssistedOutboundPort` 为 **一种实现** |

---

## 2. LivePddAssistedOutboundPort — Port **不负责**

| 职责 | Port |
|------|------|
| final guard | ❌ |
| merchant policy | ❌ |
| audit append | ❌ |
| SendDecision snapshot | ❌ |
| idempotency acquire / mark | ❌ |
| dashboard permission / CSRF | ❌ |
| pending status mutation | ❌ |
| DB read/write | ❌ |
| 决定是否允许发送 | ❌ |
| fallback 到 legacy handler | ❌ |
| AI draft 重新生成文本 | ❌ |
| 修改 `final_reply` | ❌ |

**Port 是纯 platform adapter。** 所有 safety 在 `AssistedReplyService` 已完成后再调用 port。

---

## 3. LivePddAssistedOutboundPort — Port **负责**

| 职责 | 说明 |
|------|------|
| 发送 `final_reply` | 到指定 buyer/session · PDD platform only |
| 返回 `provider_message_id` | 平台侧 message id · success path |
| 返回 `platform_status` | sent / failed / timeout_unknown / rejected_by_platform / unavailable |
| 返回 `error_code` / `error_message` | machine + human readable |
| timeout 标记 | **unknown outcome** · 非简单 failed |
| 输入校验 | empty `final_reply` · missing `buyer_id` / `shop_id` → fail · **不发送** |

---

## 4. Adapter 分层（future）

```text
LivePddAssistedOutboundPort
    → validate AssistedOutboundRequest (port-local only)
    → PddAssistedSendAdapter (thin · future)
        → call existing PDD send primitive
            (e.g. unified outbound resolver entry OR channel adapter)
        → MUST NOT alter default legacy auto-reply behavior
        → MUST NOT enqueue to pdd_{shop_id} for auto-reply path
    → map platform response → AssistedOutboundResult
    → return to AssistedReplyService (no side effects)
```

### 4.1 薄封装原则

| 规则 |
|------|
| 未来可通过 **薄封装** 调用现有 PDD send primitive |
| **不能**改热路径默认行为（AutoReply / handler / consumer） |
| **不能**让 assisted send 混入 legacy auto-reply queue 逻辑 |
| **不能**在 port 内 import handler 或触发 `handle()` |
| **不能**修改 `SendMessage` 源码或 outbound resolver 默认路径 |

Assisted send 与 legacy auto-reply **并行隔离** — port 仅借用底层 MMS/WS 发送能力。

---

## 5. Service ↔ Port 数据流

```text
AssistedReplyService (before port.send):
    1. final guard allow
    2. audit: assisted_approved, final_guard_passed
    3. snapshot write (if enabled)
    4. idempotency acquire (in_progress)
    5. build AssistedOutboundRequest (dry_run=false for live)

LivePddAssistedOutboundPort.send(request):
    → platform attempt only
    → AssistedOutboundResult

AssistedReplyService (after port.send):
    6. audit: outbound_send_attempted / succeeded / failed / unknown
    7. idempotency mark_succeeded / mark_failed / leave in_progress
    8. pending status → sent / failed / unknown
    9. return workflow status to caller
```

Port **never** executes steps 1–5 or 6–9.

---

## 6. 禁止清单

| 禁止 | 原因 |
|------|------|
| Port writes audit | H9 · service owns audit |
| Port updates pending | H11 · service owns state |
| Port acquires idempotency | duplicate-send risk |
| Port reads merchant policy | guard already done |
| Port fallback handler SendMessage directly | no bypass |
| Port modifies `final_reply` | guard pass text is immutable |

---

*Phase 15h · docs only · 2026-06-03*

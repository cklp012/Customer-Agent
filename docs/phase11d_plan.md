# Phase 11d 规划 — DoudianMockChannel Outbound Auto-Registration

| 项 | 值 |
|----|-----|
| 类型 | **规划 SSOT**（Route A+B：生命周期设计；**不写实现代码**） |
| 状态 | 规划（执行后见 [phase11d_done.md](phase11d_done.md)） |
| 前置 | [phase11c_done.md](phase11c_done.md) |
| 推荐路线 | **11d = A+B（本文）** → **11e = Route C（实现 + lifecycle 测试）** |
| 禁止路线 | **Route D/E** |

**文档导航：** [phase11c_plan.md](phase11c_plan.md) · [doudian_channel.py](../Channel/doudian/doudian_channel.py) · [test_pinduoduo_channel_registry.py](../tests/test_pinduoduo_channel_registry.py)

---

## 1. Phase 11d 总体分析

11c 已在 **测试内手动** `channel_outbound_registry.register` + `resolve_outbound` 证明抖店出站解析契约。**缺口：** `DoudianMockChannel` 生命周期与 registry **未对齐** `PinduoduoChannel` → `AccountOutboundRegistry` 模式。

**11d 目标：** 规划 `start_account` / `stop_account` 是否应自动 **register / unregister** `DoudianMockOutbound` 到 **`channel_outbound_registry`**，并定义 11e 最小实现与测试矩阵。

**不变量：**

- 默认 bootstrap **不** 注册 Doudian（`USE_DOUDIAN_CHANNEL_REGISTRATION` 默认 false）
- AutoReply **仍 PDD-only**；handler **仍** `resolve_pinduoduo_outbound`（`USE_UNIFIED_OUTBOUND_RESOLVER` 默认 false）
- 不接真实 API / WS / login

**11d 不做：** 改 `doudian_channel.py`（→ **11e Route C**）、handler 默认 unified（Route D）、任何 flag 默认值变更（Route E）。

---

## 2. 当前 DoudianMockChannel 生命周期状态

源码：[Channel/doudian/doudian_channel.py](../Channel/doudian/doudian_channel.py)

### 2.1 `start_account`

| 步骤 | 行为 |
|------|------|
| 保存 | `_shop_id`, `_account_id`, `_on_success`（`on_message` / `on_failure` 当前 del 未存） |
| 状态 | `CONNECTING` → 创建 `DoudianMockOutbound` → `CONNECTED` |
| 回调 | 同步调用 `on_success()` |
| **未做** | **不** `channel_outbound_registry.register` |

### 2.2 `stop_account`

| 条件 | 行为 |
|------|------|
| shop/account 匹配 | `_status = DISCONNECTED`，`_outbound = None` |
| 不匹配 | 无操作 |
| **未做** | **不** `channel_outbound_registry.unregister` |

### 2.3 `reconnect`

`stop_account` → `start_account`（复用 `_on_success`；`on_message` 缺省为 no-op lambda）。

### 2.4 与 PDD 对照

| 生命周期 | PinduoduoChannel | DoudianMockChannel（当前） |
|----------|------------------|----------------------------|
| 出站创建 | `create_pinduoduo_outbound` after legacy start | `DoudianMockOutbound(shop, account)` in start |
| 注册表 | `AccountOutboundRegistry`（PDD-only） | **无** |
| start 后 register | ✅ | ❌ |
| stop 后 unregister | ✅（始终对传入 shop/account） | ❌ |

---

## 3. 当前 outbound registry / resolver 状态

### 3.1 `channel_outbound_registry`

| 项 | 值 |
|----|-----|
| Key | `{platform}:{shop_id}:{account_id}`（platform 小写） |
| API | `register` / `unregister` / `get` / `clear` |
| PDD | **不使用**（PDD 用 `AccountOutboundRegistry`） |

### 3.2 `DoudianMockOutbound` 创建

| 路径 | 时机 |
|------|------|
| `start_account` |  eagerly `self._outbound = DoudianMockOutbound(shop, account)` |
| `outbound` property | lazy 兜底（start 后通常已存在） |
| 属性 | `shop_id`, `account_id`（**无** `user_id`；resolver 用 metadata `user_id` 对齐 `account_id`） |

### 3.3 `resolve_outbound`（11c 已验）

```text
metadata outbound → channel_outbound_registry.get(platform, shop_id, user_id)
→ platform==pinduoduo → resolve_pinduoduo_outbound
→ else None
```

Handler 生产：**仅** flag on 时调用 `resolve_outbound`；默认 **false**。

---

## 4. auto-registration 风险分析

| 风险 | 等级 | 缓解 |
|------|------|------|
| 默认生产注册 Doudian | **无** | bootstrap 默认不创建 `DoudianMockChannel` |
| 污染 PDD `AccountOutboundRegistry` | **无** | 独立 registry，不同 key 空间 |
| handler 误走 unified | **低** | flag 默认 false；registry 有条目 ≠ handler 使用 |
| 测试泄漏 registry | **低** | tearDown `channel_outbound_registry.clear()` |
| stop 未 unregister 导致 stale outbound | **中** | 11e 必须 mirror PDD `unregister` |
| start 失败仍 register | **低** | mock start 无 legacy 失败路径；11e 可加「失败不 register」用例备 future |
| reconnect 双注册 / 泄漏 | **低** | stop→unregister + start→register 自然覆盖 |
| buyer_id 误进 key | **无** | registry 为 **account-level**；buyer 在 metadata `from_uid` |

**结论：** auto-registration **合理**，但应放在 **11e** 实现，11d 先冻结设计与测试矩阵。

---

## 5. 推荐路线

| 路线 | 内容 | 风险 | 阶段 |
|------|------|------|------|
| **A** | 仅本文档 | 最低 | **11d ✅** |
| **B** | 生命周期设计 SSOT（§6–7） | 低 | **11d ✅** |
| **C** | `doudian_channel.py` register/unregister | 中 | **11e** |
| **D** | handler 默认 unified | 高 | **12+ / 禁止** |
| **E** | 默认开 unified 或默认注册 Doudian | **禁止** | — |

**推荐：11d = A+B（规划）；11e = C + lifecycle tests + 可选 handler 联调（测试内 flag）。**

### 问题 11 / 12 速答

| # | 结论 |
|---|------|
| 11 | **是** — 11d 只做文档规划（A+B）最安全 |
| 12 | **是** — auto-registration **实现** 放 11e 更安全（设计评审与代码分离） |

---

## 6. Route C 最小实现方案（11e，非 11d）

### 6.1 代码变更（单文件）

`Channel/doudian/doudian_channel.py`：

```python
# start_account 末尾（on_success 之前或之后，与 PDD 一致：legacy 成功后 register）
from Message.handlers import channel_outbound_registry

channel_outbound_registry.register(
    PlatformType.DOUDIAN,  # 或 "doudian"
    self._shop_id,
    self._account_id,
    self._outbound,
)

# stop_account（仿 PDD：始终 unregister 传入的 shop/account）
channel_outbound_registry.unregister(PlatformType.DOUDIAN, shop_id, account_id)
# 匹配时 self._outbound = None（已有）
```

**顺序建议（对齐 PDD）：**

1. `start_account`：创建 outbound → **register** → `on_success()`
2. `stop_account`：`unregister(shop_id, account_id)` → 匹配则清 `_outbound`

**不新增 flag：** `DoudianMockChannel` 本身为 test-only mock；默认 runtime 不会实例化。

### 6.2 可选 11f：handler 联调

仿 `tests/test_handler_unified_outbound.py` Demo 段：

- 测试内 `USE_UNIFIED_OUTBOUND_RESOLVER=true`
- `await channel.start_account(...)` 填充 registry
- `AIReplyHandler._send_reply` + `platform=doudian` metadata → `sent_messages`

**不在 11e 必须项**；可单列 11f 降低 11e diff。

---

## 7. 需要新增/修改的测试（11e 实现时）

| 文件 | 操作 | 用例 |
|------|------|------|
| `tests/test_doudian_channel_outbound_lifecycle.py` | **新增** | L1 start → registry.get 同一实例；L2 stop → None；L3 reconnect 重注册；L4 stop 错误 account 不破坏已注册项（若适用）；L5 start 后 resolve_outbound 命中（无需手动 register） |
| `tests/test_doudian_outbound_resolver_contract.py` | **可选** | 保留手动 register 用例作 resolver 纯契约锚点 |
| `tests/test_doudian_registry_flag.py` | **可选** | 断言 flag off 时 bootstrap 仍不 start_account（无 registry 条目） |
| `tests/test_handler_doudian_unified_outbound.py` | **可选 11f** | handler + unified flag |

**tearDown：** `channel_outbound_registry.clear()`。

---

## 8. 是否需要改 flags

| Flag | 11d | 11e |
|------|-----|-----|
| `USE_DOUDIAN_CHANNEL_REGISTRATION` | **不改** | **不改** |
| `USE_UNIFIED_OUTBOUND_RESOLVER` | **不改** | **不改**（handler 测仅 env） |
| 新增 outbound flag | **否** | **否**（不推荐） |

Gating 由「默认不 bootstrap Doudian」+「mock channel 仅测试/显式 flag 路径」承担。

---

## 9. PDD 保护清单

| 路径 | 要求 |
|------|------|
| `Channel/pinduoduo/**` | 不改 |
| `AccountOutboundRegistry` | 不扩展 Doudian |
| `resolve_pinduoduo_outbound` | 生产默认不变 |
| `USE_UNIFIED_OUTBOUND_RESOLVER` | unset → false |
| handlers 默认 | `resolve_pinduoduo_outbound` |
| AutoReply / `channel_factory` | PDD-only |
| Queue | `pdd_{shop_id}` |
| 11c 契约 | R5/R6 仍有效；11e 新增 lifecycle 测试不删 11c |

---

## 10. 允许修改文件

### 11d 规划阶段（当前）

```text
docs/phase11d_plan.md
docs/phase11d_done.md
docs/architecture_current.md
docs/README.md
docs/phase11c_done.md
```

### 11e Route C 实现阶段

```text
Channel/doudian/doudian_channel.py
tests/test_doudian_channel_outbound_lifecycle.py
docs/phase11e_plan.md / phase11e_done.md（可选）
```

---

## 11. 禁止修改文件

```text
Channel/pinduoduo/**
Message/handlers/ai_handler.py
Message/handlers/keyword_handler.py
Message/handlers/unified_outbound_flags.py
Message/handlers/outbound_resolver.py
Message/handlers/unified_outbound_resolver.py   # 11e 理想零变更
pdd_lifecycle / pdd_message_handler / MessageConsumer
AutoReplyThread / channel_factory 默认
ui/** / database/** / app.py
USE_* 默认值
Route D / E
```

---

## 12. 文档更新方案

| 文件 | 动作 |
|------|------|
| `docs/phase11d_plan.md` | 本文 |
| `docs/phase11d_done.md` | 规划签收 |
| `docs/phase11c_done.md` | next → 11d/11e 拆分 |
| `docs/architecture_current.md` | 11c ✅；11d 规划行 |
| `docs/README.md` | Phase 11d 索引 |

---

## 13. Phase 11e prompt

```text
继续 Phase 11e：DoudianMockChannel outbound auto-registration（Route C）。

先读：
- docs/phase11d_plan.md
- docs/phase11d_done.md
- Channel/doudian/doudian_channel.py
- Channel/pinduoduo/pinduoduo_channel.py（register/unregister 对照）
- tests/test_pinduoduo_channel_registry.py
- tests/test_doudian_outbound_resolver_contract.py

目标（11e Route C）：
1. start_account 成功后：
   channel_outbound_registry.register("doudian", shop_id, account_id, self._outbound)
2. stop_account：
   channel_outbound_registry.unregister("doudian", shop_id, account_id)
   （仿 PDD：对传入 shop/account 始终 unregister）
3. reconnect 经 stop+start 自动重注册
4. 新增 tests/test_doudian_channel_outbound_lifecycle.py（L1–L5）
5. 不改 flags 默认值、不改 handlers 默认、不改 PDD

禁止：
- Route D/E
- 真实 API
- Channel/pinduoduo/**

可选 11f（非 11e 必须）：
- test_handler_doudian_unified_outbound.py
  USE_UNIFIED_OUTBOUND_RESOLVER=true 仅测试内
  start_account 后 handler 发送 → sent_messages

验收：
unittest 全绿；默认 env bootstrap 与 11c 行为一致；11c resolver 契约无回归。
```

---

## 附录：问题清单速答（1–10）

| # | 结论 |
|---|------|
| 1 | §2 — start 建 outbound + CONNECTED；**不** registry |
| 2 | §3.2 — start_account / outbound property 创建 |
| 3 | §3.1 — `{platform}:{shop_id}:{account_id}` |
| 4 | **合理**（对齐 PDD），实现放 11e |
| 5 | **应 unregister**（对齐 PDD stop） |
| 6 | **shop_id + account_id**；buyer **不参与** key |
| 7 | **是** — account-level outbound（metadata user_id = account_id） |
| 8 | **不影响** — 独立 registry |
| 9 | **不影响默认** — handler 仍 PDD resolver；registry 仅在被 resolve_outbound 调用时使用 |
| 10 | **是** — 11e 新增 lifecycle tests |

---

*规划版本：Phase 11d · 2026-06-03 · Route A+B · docs only*

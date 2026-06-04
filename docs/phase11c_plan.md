# Phase 11c 规划 — Doudian Outbound Resolver Contract（Mock Path）

| 项 | 值 |
|----|-----|
| 类型 | **规划 SSOT**（推荐 Route B：resolver 契约测试；**不写生产默认变更**） |
| 状态 | 规划（执行后见 [phase11c_done.md](phase11c_done.md)） |
| 前置 | [phase10m_done.md](phase10m_done.md)、[phase11b_done.md](phase11b_done.md) |
| 后续 | **11d** — `DoudianMockChannel.start_account` 自动 register outbound（Route C，可选） |

**文档导航：** [phase11a_plan.md](phase11a_plan.md) · [test_unified_outbound_resolver.py](../tests/test_unified_outbound_resolver.py) · [unified_outbound_resolver.py](../Message/handlers/unified_outbound_resolver.py)

---

## 1. Phase 11c 总体分析

10m 交付 **`DoudianMockOutbound`**（`sent_messages` 记录）；11b 交付 **`DoudianMockChannel`** + flag-gated **`ChannelRegistry`**。二者尚未与 **`channel_outbound_registry` / `resolve_outbound`** 形成可重复验证的契约测试链。

**11c 目标：** 规划并（Route B）实现 **测试内** 抖店出站解析路径：

```text
metadata（platform=doudian, shop/user/from_uid）
  → resolve_outbound(metadata, context?)
       → channel_outbound_registry.get("doudian", shop, account)
            → DoudianMockOutbound
```

**不改变：**

- 生产 handler 默认仍 `resolve_pinduoduo_outbound`（`USE_UNIFIED_OUTBOUND_RESOLVER` 默认 false）
- PDD 发送仍 legacy / `AccountOutboundRegistry` 路径
- 默认不注册 Doudian 到任何 registry

**11c 不做：** 改 handlers 默认分支（Route D）、默认开 unified resolver（Route E）、`DoudianMockChannel` 自动 register（Route C → **11d**）。

---

## 2. 当前 outbound registry / resolver 状态

### 2.1 `channel_outbound_registry`

| API | 行为 |
|-----|------|
| `register(platform, shop_id, account_id, outbound)` | key = `{platform}:{shop_id}:{account_id}` |
| `get(platform, shop_id, account_id)` | 命中返回实例，否则 `None` |
| `clear()` | 测试 tearDown |

**与 PDD 关系：** `AccountOutboundRegistry` 仍为 PDD 生产主路径；`channel_outbound_registry` 为 **8b 多平台缓存**，与 PDD 并行、不自动迁移。

**现有测试范例：** `tests/test_unified_outbound_resolver.py` — Demo `register("demo", …)` + `resolve_outbound`；`tests/test_doudian_outbound_mock.py` — 已测 registry register/get，**未**测 `resolve_outbound`。

### 2.2 `unified_outbound_resolver.resolve_outbound`

解析顺序（[unified_outbound_resolver.py](../Message/handlers/unified_outbound_resolver.py)）：

```text
1. metadata["outbound"]     （若 duck-type 校验通过）
2. channel_outbound_registry.get(platform, shop_id, user_id)
3. platform == "pinduoduo"  → resolve_pinduoduo_outbound(metadata, context)
4. 其它 platform            → None
```

**平台推断 `infer_platform`：**

1. `metadata["platform"]`
2. `context.kwargs.channel_type`
3. 缺省 → **`pinduoduo`**

**非 PDD 校验：** `_is_usable_channel_outbound` — 需 `send_text`；`shop_id` / `user_id` / `account_id` 与 metadata 一致。  
`DoudianMockOutbound` 提供 `shop_id`、`account_id`（无 `user_id` 属性）→ metadata 的 **`user_id` 应对齐 `account_id`**。

### 2.3 Handler 生产路径（8c，默认 off）

| 组件 | 默认 |
|------|------|
| `use_unified_outbound_resolver()` | **false**（env 未设置） |
| `AIReplyHandler` / `KeywordDetectionHandler` | flag off → **`resolve_pinduoduo_outbound`** |
| flag on | `resolve_outbound` |

**结论：** 11c **可直接单测** `resolve_outbound`，**不必**改 handler 即可验证 Doudian registry 路径；handler 联调推迟 **11d**。

---

## 3. Doudian outbound readiness

| 能力 | 状态 |
|------|------|
| `DoudianMockOutbound` + `ChannelOutbound` | ✅ 10m |
| `channel_outbound_registry.register(DOUDIAN, …)` | ✅ 10m 单测 |
| `resolve_outbound` + doudian | 📋 11c Route B |
| `infer_platform` + doudian Context | 📋 11c（`channel_type=doudian`） |
| `enrich_metadata_from_unified` + dual-track | 可选 11c/11d；非 11c 必须 |
| Handler 真实发送 | ❌ 推迟 11d |
| `DoudianMockChannel` 自动 register | ❌ 推迟 11d（Route C） |

---

## 4. 是否要修改 `DoudianMockChannel`（11c）

| 选项 | 11c | 说明 |
|------|-----|------|
| **不修改**（推荐） | ✅ | 测试内显式 `channel_outbound_registry.register`；与 Demo 单测一致 |
| **start_account 自动 register** | ❌ 11d | 仅当 channel 已由 flag 创建时副作用；中等风险 |

**11c 结论：** **不修改** `DoudianMockChannel`；registry 由 **测试** 或 **11d** 负责。

---

## 5. 推荐路线

| 路线 | 内容 | 风险 | 阶段 |
|------|------|------|------|
| **A** | 仅本文档 | 最低 | **11c ✅** |
| **B** | `test_doudian_outbound_resolver_contract.py`：registry + `resolve_outbound`；可选 handler 测试仅 env 内开 flag | 低 | **11c 实现** |
| **C** | `DoudianMockChannel.start_account` → auto register | 中 | **11d** |
| **D** | 改 handlers 默认走 unified | 高 | **禁止 / 12+** |
| **E** | 默认 `USE_UNIFIED_OUTBOUND_RESOLVER=true` | **禁止** | — |

**推荐：11c = A + B（文档 + resolver 契约测试）；11d = C + 可选 handler 联调测试。**

---

## 6. Route B 最小实现方案

### 6.1 新增测试文件

`tests/test_doudian_outbound_resolver_contract.py`

### 6.2 测试矩阵

| ID | 用例 | 操作 |
|----|------|------|
| R1 | `infer_platform` | `metadata.platform=doudian`；Context `channel_type=doudian` |
| R2 | registry resolve | `register(DOUDIAN, shop, account, DoudianMockOutbound)` → `resolve_outbound(meta)` 同一实例 |
| R3 | metadata outbound 优先 | `meta["outbound"]=ob` 优先于 registry |
| R4 | 账号不匹配 | 错误 shop/account → `None` |
| R5 | 未注册 | 无 register → `None`（不回落 PDD） |
| R6 | PDD 委托隔离 | `platform=pinduoduo` 仍 patch `resolve_pinduoduo_outbound`；与 10m/11b 无回归 |
| R7 | 无自动创建 | 仅 Context/metadata，无 registry → `None`（仿 demo `test_demo_does_not_auto_create`） |

**可选 R8（11d）：** `USE_UNIFIED_OUTBOUND_RESOLVER=true` + `AIReplyHandler._send_reply` + registry → `sent_messages`（仿 `test_handler_unified_outbound.py` Demo 段）。

### 6.3 metadata 构造（SSOT）

```python
meta = {
    "platform": "doudian",
    "shop_id": "DD_SHOP_001",
    "user_id": "DD_ACC_001",      # 对齐 DoudianMockOutbound.account_id
    "from_uid": "DD_BUYER_001",
}
```

**可选：** 从 `tests/fixtures/doudian_messages/text.json` + `doudian_raw_to_context` 构造 Context，`infer_platform({}, ctx) == "doudian"`。

**UnifiedMessage：** 11c **不必须**；`resolve_outbound` 不读 UnifiedMessage。若 11d 测 handler + dual-track，再用 `doudian_raw_to_unified` + `enrich_metadata_from_unified`。

### 6.4 是否需要改 `.py` 生产代码

**Route B 理想情况：零生产代码变更。**

若发现 `resolve_outbound` 对 `account_id` vs `user_id` 文档不清，仅补 **测试** 与 **注释**（11c 允许 `unified_outbound_resolver.py` 文档字符串？用户禁止改 handlers 默认 — 只读注释可放在测试或 docs）。

**禁止：** 为 11c 改 `resolve_outbound` 的 PDD 分支语义。

---

## 7. 需要新增/修改的测试（11c 实现时）

| 文件 | 操作 |
|------|------|
| `tests/test_doudian_outbound_resolver_contract.py` | **新增** |
| `tests/test_doudian_outbound_mock.py` | 可选：迁移重复 registry 用例或保留 |
| `tests/test_unified_outbound_resolver.py` | **不改**（PDD/Demo 回归锚点） |

**tearDown 模板：**

```python
channel_outbound_registry.clear()
# 不修改 USE_UNIFIED_OUTBOUND_RESOLVER / USE_PINDUODUO_OUTBOUND 全局默认
```

---

## 8. 是否需要开启 `USE_UNIFIED_OUTBOUND_RESOLVER`

| 场景 | 需要 flag？ |
|------|-------------|
| 直接 `resolve_outbound(meta)` | **否** |
| 经 `AIReplyHandler` / `KeywordDetectionHandler` 发送 | **是**（仅测试 setUp） |

**规则：**

- **11c Route B：** 以 **直接调用 `resolve_outbound`** 为主 → **默认 flag 保持 false**
- 若加 handler 用例 → **仅测试类** `os.environ["USE_UNIFIED_OUTBOUND_RESOLVER"]="true"` + tearDown 恢复
- **禁止** 修改 `unified_outbound_flags.py` 默认值

---

## 9. PDD 保护清单

| 路径 | 要求 |
|------|------|
| `resolve_pinduoduo_outbound` / `SendMessage` | 生产默认不变；测试可 patch 断言委托 |
| `USE_UNIFIED_OUTBOUND_RESOLVER` | unset → false |
| `USE_PINDUODUO_OUTBOUND` | 不改默认 |
| `AccountOutboundRegistry` | 不改为 Doudian |
| handlers 默认分支 | 不改 |
| PDD queue | `pdd_{shop_id}` |
| `Channel/pinduoduo/**` | 不改 |

**测试隔离：** `platform=pinduoduo` 用例必须证明仍走 legacy 委托，不因 Doudian registry 污染。

---

## 10. 允许修改文件（11c）

### 11c 规划阶段（当前）

```text
docs/phase11c_plan.md
docs/phase11c_done.md
docs/architecture_current.md
docs/README.md
docs/phase11b_done.md
```

### 11c Route B 实现阶段

```text
tests/test_doudian_outbound_resolver_contract.py
docs/phase11c_done.md（签收实现）
```

**可选（仅当发现缺口且用户批准）：** `Message/handlers/unified_outbound_resolver.py` 文档注释 — 优先不加代码逻辑。

---

## 11. 禁止修改文件

```text
Channel/pinduoduo/**
Message/handlers/ai_handler.py          # 默认行为
Message/handlers/keyword_handler.py
Message/handlers/unified_outbound_flags.py   # 默认值
Message/handlers/outbound_resolver.py        # PDD 生产解析
Channel/doudian/doudian_channel.py      # 11c 不改；11d 才可选 auto-register
ui/** / database/** / app.py
AutoReplyThread / channel_factory 默认
USE_CHANNEL_REGISTRY_FOR_AUTOREPLY 默认
USE_DOUDIAN_CHANNEL_REGISTRATION 默认
```

**禁止 Route E：** 默认 `USE_UNIFIED_OUTBOUND_RESOLVER=true`。

---

## 12. 文档更新方案

| 文件 | 动作 |
|------|------|
| `docs/phase11c_plan.md` | 本文 |
| `docs/phase11c_done.md` | 规划签收；实现后补充测试清单 |
| `docs/architecture_current.md` | 11c 行；outbound 解析链注记 |
| `docs/README.md` | Phase 11c |
| `docs/phase11b_done.md` | next → 11c |

---

## 13. Phase 11d prompt

```text
继续 Phase 11d：Doudian outbound registry 生产侧轻量接入（Route C + 可选 handler 联调）。

先读：
- docs/phase11c_plan.md
- docs/phase11c_done.md
- Channel/doudian/doudian_channel.py
- tests/test_doudian_outbound_resolver_contract.py（11c 若已完成）
- tests/test_handler_unified_outbound.py

目标（11d）：
1. DoudianMockChannel.start_account 成功后：
   channel_outbound_registry.register("doudian", shop_id, account_id, self.outbound)
   stop_account 时 unregister（仿 PinduoduoChannel + AccountOutboundRegistry 模式，但用 channel_outbound_registry）
2. 仅当实例由 USE_DOUDIAN_CHANNEL_REGISTRATION 路径创建时生效；不改变默认 bootstrap
3. 可选：test_handler_doudian_unified_outbound.py
   - 测试内 USE_UNIFIED_OUTBOUND_RESOLVER=true
   - registry 已由 start_account 填充
   - 断言 AIReplyHandler 使用 DoudianMockOutbound.sent_messages
4. 不改 handlers 默认、不改 flag 默认值、不改 PDD

禁止：
- Route D/E
- 真实 API
- 改 Channel/pinduoduo/**

验收：
unittest 全绿；默认 env 下行为与 11b 一致。
```

---

## 附录：问题清单速答

| # | 结论 |
|---|------|
| 1 | §2.1–2.2 |
| 2 | register/get；key 含 platform |
| 3 | 11c 测试为主；channel 自动 register → 11d |
| 4 | §2.2 顺序 + PDD 委托 |
| 5 | 需要 metadata；UnifiedMessage 可选 |
| 6 | 直接测 resolver **不需要**；handler 测需要 |
| 7 | 仅测试内开启并 tearDown |
| 8 | 否；PDD 仍委托 `resolve_pinduoduo_outbound` |
| 9 | 是，Route B 新增 contract tests |
| 10 | 是，handler 默认接入推迟 11d |

---

*规划版本：Phase 11c · 2026-06-03 · Route A+B 推荐 · docs only*

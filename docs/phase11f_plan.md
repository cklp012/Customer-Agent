# Phase 11f 规划 — Handler Unified Outbound Path（Doudian Mock）

| 项 | 值 |
|----|-----|
| 类型 | **规划 SSOT**（Route A+B：handler 测试边界；**不写实现代码**） |
| 状态 | 规划（执行后见 [phase11f_done.md](phase11f_done.md)） |
| 前置 | [phase11e_done.md](phase11e_done.md) |
| 推荐路线 | **11f = A+B（本文）** → **11g = Route C（handler 测试实现）** |
| 禁止路线 | **Route D/E** |

**文档导航：** [test_handler_unified_outbound.py](../tests/test_handler_unified_outbound.py) · [test_doudian_channel_outbound_lifecycle.py](../tests/test_doudian_channel_outbound_lifecycle.py) · [ai_handler.py](../Message/handlers/ai_handler.py)

---

## 1. Phase 11f 总体分析

11c 证明 **`resolve_outbound` + registry** 契约；11e 证明 **`DoudianMockChannel` lifecycle** 自动填充 registry。**缺口：** handler 生产代码在 flag on 时是否真能走 **`handler → resolve_outbound → DoudianMockOutbound.send_text`**，尚未有抖店专用联调测试。

**11f 目标：** 规划测试边界——在 **测试 env 内** `USE_UNIFIED_OUTBOUND_RESOLVER=true` 时，验证 AI/Keyword handler 出站链，**零默认生产行为变更**。

**完整链（11g 实现目标）：**

```text
AIReplyHandler._send_reply / KeywordDetectionHandler.handle
  → use_unified_outbound_resolver() == true   （仅测试 setUp）
  → resolve_outbound(metadata, context)
  → channel_outbound_registry.get("doudian", shop, user_id)
  → DoudianMockOutbound.send_text / transfer_to_human
  → sent_messages
```

**11f 不做：** 改 handler 默认（Route D）、默认开 unified flag（Route E）、Consumer/AutoReply 多平台、真实 API。

---

## 2. 当前 handler outbound resolver 状态

### 2.1 选择逻辑（AI + Keyword 同构）

[ai_handler.py](../Message/handlers/ai_handler.py) `_send_reply`、[keyword_handler.py](../Message/handlers/keyword_handler.py) `handle`：

```text
shop_id, user_id, from_uid = extract_pdd_send_context(metadata, context)  # 平台无关三元组

if use_unified_outbound_resolver():
    outbound = resolve_outbound(metadata, context)
else:
    outbound = resolve_pinduoduo_outbound(metadata, context)

if outbound is not None:
    await outbound.send_text(from_uid, ...) / transfer_to_human(from_uid, ...)
    return True on success

# 失败或无 outbound → legacy（SendMessage / _transfer_to_human_legacy）
```

**生产默认：** `use_unified_outbound_resolver()` → **false** → **`resolve_pinduoduo_outbound`**。

### 2.2 现有测试锚点

| 文件 | 覆盖 |
|------|------|
| `tests/test_handler_unified_outbound.py` | flag off → PDD；flag on + **Demo** registry/metadata → send/transfer |
| `tests/test_doudian_outbound_resolver_contract.py` | resolver 契约（无 handler） |
| `tests/test_doudian_channel_outbound_lifecycle.py` | channel lifecycle + resolve（无 handler） |

**缺口：** 无 **`platform=doudian`** 的 handler 联调测试。

---

## 3. Doudian outbound readiness

| 能力 | 状态 |
|------|------|
| `DoudianMockOutbound.send_text` / `transfer_to_human` | ✅ 10m |
| `resolve_outbound` + registry | ✅ 11c |
| `DoudianMockChannel` auto register | ✅ 11e |
| Handler unified path + doudian | 📋 **11g Route C** |
| Consumer / AutoReply 多平台 | ❌ 不在范围 |

---

## 4. handler 测试所需 metadata

### 4.1 发送三元组（handler 前置校验）

经 `extract_pdd_send_context` / `get_send_context_for_extract`：

| 字段 | 说明 |
|------|------|
| `shop_id` | 与 registry / outbound 一致 |
| `user_id` | 对齐 `DoudianMockOutbound.account_id` |
| `from_uid` | 买家 ID；作为 `send_text(conversation_id, ...)` 第一参 |

可从 **metadata** 或 **Context.kwargs** 提供（与 Demo 测试相同）。

### 4.2 平台解析（resolve_outbound）

| 字段 | 必须？ |
|------|--------|
| `metadata["platform"] = "doudian"` | **强烈建议**（缺省 `infer_platform` → `pinduoduo`） |
| `context.kwargs.channel_type = "doudian"` | 可选补充 |

### 4.3 SSOT 示例（11g）

```python
meta = {
    "platform": "doudian",
    "shop_id": "DD_SHOP_001",
    "user_id": "DD_ACC_001",
    "from_uid": "DD_BUYER_001",
}
```

**UnifiedMessage / dual-track：** 11g **不必须**；handler 出站路径不读 UnifiedMessage。

---

## 5. 是否需要启动 Consumer / Channel

| 组件 | 11g 需要？ | 说明 |
|------|-----------|------|
| **MessageConsumer** | **否** | Demo handler 测试直接 `handler._send_reply` / `handle` |
| **AutoReplyThread** | **否** | 不测线程/队列 |
| **DoudianMockChannel.start_account** | **可选** | 两种 registry 填充方式均合法 |

### Registry 填充策略（11g 二选一或都测）

| 策略 | 优点 | 用例 ID |
|------|------|---------|
| **A. 手动 register** | 与 Demo/`11c` 一致；不依赖 channel | H1a |
| **B. channel start_account** | 验证 11e + handler 端到端 | H1b |

**推荐 11g 最小集：** **H1a（手动 register）** 为主；**H1b** 为可选加强。

---

## 6. 推荐路线

| 路线 | 内容 | 风险 | 阶段 |
|------|------|------|------|
| **A** | 仅本文档 | 最低 | **11f ✅** |
| **B** | handler 测试设计 SSOT（§7–8） | 低 | **11f ✅** |
| **C** | `test_handler_doudian_unified_outbound.py` | 中 | **11g** |
| **D** | handler 默认 unified | 高 | **禁止** |
| **E** | 默认 `USE_UNIFIED_OUTBOUND_RESOLVER=true` | **禁止** | — |

### 问题 9 / 10 速答

| # | 结论 |
|---|------|
| 9 | **是** — 11f 只做文档规划（A+B）最安全 |
| 10 | **是** — handler 测试实现放 **11g** 更安全 |

### 问题 5 / 6 / 7 / 8 速答

| # | 结论 |
|---|------|
| 5 | **最小：** 只测 `AIReplyHandler._send_reply`；Keyword **可选** 第二条（transfer） |
| 6 | **否** — 不需要 Consumer |
| 7 | **否** — channel start **可选**（11e 集成路径） |
| 8 | **是** — 可手动 register（仿 Demo） |

---

## 7. Route C 最小实现方案（11g，非 11f）

### 7.1 新增文件

`tests/test_handler_doudian_unified_outbound.py`

### 7.2 测试基础设施

复用 `test_handler_unified_outbound._EnvRestore` 模式：

```python
setUp:  os.environ["USE_UNIFIED_OUTBOUND_RESOLVER"] = "true"
        os.environ.pop("USE_PINDUODUO_OUTBOUND", None)
tearDown: channel_outbound_registry.clear()
          restore USE_UNIFIED_OUTBOUND_RESOLVER / USE_PINDUODUO_OUTBOUND
```

**禁止** 修改 `unified_outbound_flags.py` 默认值。

### 7.3 测试矩阵

| ID | 用例 | 操作 |
|----|------|------|
| H0 | resolver 选择 | flag on 时 patch 证明调用 `resolve_outbound` 而非 PDD（可选，Demo 已有类似） |
| H1a | AI + manual register | `register(DOUDIAN, …, DoudianMockOutbound)` → `_send_reply` → `sent_messages` |
| H1b | AI + channel start | `await DoudianMockChannel.start_account` → `_send_reply`（无手动 register） |
| H2 | Keyword transfer（可选） | `metadata["outbound"]=ob` 或 registry；关键词命中 → `transfer_to_human` in `sent_messages` |
| H3 | 无 outbound 不误发 | unified on + doudian meta + **无 registry** → patch `_send_text_legacy` 断言 **未** 成功走 mock（或 legacy 被调用——文档化 PDD fallback 风险） |
| H4 | flag off 回归 | **不重复** — 依赖 `test_handler_unified_outbound` 现有用例 |

**H1 断言要点：**

- `sent_messages[-1]["method"] == "send_text"`
- `conversation_id` / `buyer_id` == `from_uid`
- `content` == reply 文本

### 7.4 生产代码变更

**理想：零 `.py` 生产变更。** 仅新增测试文件。

---

## 8. 需要新增/修改的测试（11g）

| 文件 | 11f | 11g |
|------|-----|-----|
| `tests/test_handler_doudian_unified_outbound.py` | 设计 | **新增** |
| `tests/test_handler_unified_outbound.py` | **不改** | **不改**（Demo + PDD 锚点） |
| `tests/test_doudian_outbound_resolver_contract.py` | **不改** | **不改** |
| `tests/test_doudian_channel_outbound_lifecycle.py` | **不改** | **不改** |

---

## 9. 是否需要改 flags

| Flag | 11f | 11g |
|------|-----|-----|
| `USE_UNIFIED_OUTBOUND_RESOLVER` | **不改默认** | 测试 setUp `"true"` + tearDown 恢复 |
| `USE_DOUDIAN_CHANNEL_REGISTRATION` | **不改** | **不改** |
| `USE_PINDUODUO_OUTBOUND` | **不改** | 测试 pop（仿 Demo） |

---

## 10. PDD 保护清单

| 路径 | 要求 |
|------|------|
| handler 默认分支 | flag off → `resolve_pinduoduo_outbound` |
| `Channel/pinduoduo/**` | 不改 |
| `AccountOutboundRegistry` | 不扩展 Doudian |
| AutoReply / Consumer | 不改 |
| Queue | `pdd_{shop_id}` |
| 现有 `TestHandlerResolverSelection` | 保持全绿 |

**测试隔离：** 11g 用例必须 `platform=doudian`，避免误走 PDD delegate；H3 显式处理 legacy fallback。

---

## 11. 允许修改文件

### 11f 规划阶段（当前）

```text
docs/phase11f_plan.md
docs/phase11f_done.md
docs/architecture_current.md
docs/README.md
docs/phase11e_done.md
```

### 11g Route C 实现阶段

```text
tests/test_handler_doudian_unified_outbound.py
docs/phase11g_plan.md / phase11g_done.md（可选）
```

---

## 12. 禁止修改文件

```text
Channel/pinduoduo/**
Message/handlers/ai_handler.py          # 默认行为
Message/handlers/keyword_handler.py
Message/handlers/unified_outbound_flags.py
Message/handlers/outbound_resolver.py
MessageConsumer / AutoReplyThread / channel_factory 默认
ui/** / database/** / app.py
USE_* 默认值
Route D / E
```

---

## 13. 文档更新方案

| 文件 | 动作 |
|------|------|
| `docs/phase11f_plan.md` | 本文 |
| `docs/phase11f_done.md` | 规划签收 |
| `docs/phase11e_done.md` | next → 11f/11g |
| `docs/architecture_current.md` | 11f 规划行；handler unified 测试边界注记 |
| `docs/README.md` | Phase 11f 索引 |

---

## 14. Phase 11g prompt

```text
继续 Phase 11g：Doudian handler unified outbound path tests（Route C）。

先读：
- docs/phase11f_plan.md
- docs/phase11f_done.md
- tests/test_handler_unified_outbound.py
- tests/test_doudian_channel_outbound_lifecycle.py
- tests/test_doudian_outbound_resolver_contract.py
- Message/handlers/ai_handler.py
- Message/handlers/keyword_handler.py

目标（11g Route C）：
1. 新增 tests/test_handler_doudian_unified_outbound.py
2. 测试内 USE_UNIFIED_OUTBOUND_RESOLVER=true + tearDown 恢复
3. H1a：manual register + AIReplyHandler._send_reply → DoudianMockOutbound.sent_messages
4. H1b（可选）：DoudianMockChannel.start_account + _send_reply（无手动 register）
5. H2（可选）：KeywordDetectionHandler + transfer_to_human
6. 不改 handlers 默认、不改 flag 默认值、不改 PDD

禁止：
- Route D/E
- MessageConsumer / AutoReply 线程
- 真实 API
- Channel/pinduoduo/**

验收：
unittest 全绿；默认 env handler 仍 PDD resolver；11c/11e 无回归。
```

---

*规划版本：Phase 11f · 2026-06-03 · Route A+B 推荐 · docs only*

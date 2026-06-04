# Phase 10i 规划 — Multi-Platform Capability Matrix & Second-Platform Spike Boundary

| 项 | 值 |
|----|-----|
| 类型 | **纯文档 SSOT**（无 `.py`、无生产行为变更） |
| 状态 | 规划（执行后见 [phase10i_done.md](phase10i_done.md)） |
| 前置 | Phase 10a–10h（[phase10_account_model.md](phase10_account_model.md)、[phase10h_done.md](phase10h_done.md)） |
| 后续 | **Phase 10j** — second-platform spike **计划**（仍不接真实 API） |

**文档导航：** [docs 目录](README.md) · [architecture_current.md](architecture_current.md) · [phase6a_plan.md](phase6a_plan.md) · [phase8a_done.md](phase8a_done.md)

---

## 1. Phase 10i 总体分析

Phase 10a–10h 已完成 **账号语义、消息契约、队列命名 SSOT、PDD lifecycle queue helper 接线** 的文档与小步代码；**生产自动回复** 仍为单一路径：

```text
AutoReplyThread → PDDChannel (legacy) → WebSocket
  → PDDChatMessage → Context (Context-first)
  → compute_pdd_routing → put_message → queue pdd_{shop_id}
  → MessageConsumer → handler_chain
```

**10i 目标：** 冻结 **multi-platform capability matrix** 与 **真实第二平台 spike 边界**，明确：

- 未来接入第二平台前需要哪些 capability；
- 10a–10h 已准备好哪些；
- 哪些路径在 spike 期间必须保持 **PDD-only** 且不可改默认行为。

**10i 不做：** 接抖店/淘宝/京东 SDK、新增 `Channel/doudian|taobao|jingdong/`、改 PDD 热路径、改 flag/UI/DB。

与历史 Phase 关系：

| Phase | 10i 吸收内容 |
|-------|----------------|
| 6a | Adapter 抽象、平台差异 |
| 8a | Demo 内存 spike 模式 |
| 10a | account model / `platform_id` |
| 10c–10d | routing / platform 契约 |
| 10e–10h | queue 命名 + PDD lifecycle |

---

## 2. 当前 multi-platform readiness 总结

| 维度 | 已具备 | 未具备 / 仍 PDD-only |
|------|--------|----------------------|
| **账号模型** | DB `channels.channel_name` = `platform_id`；`account_data` 契约（10a） | AutoReply **不按** `channel_name` 路由 factory |
| **UI** | 平台 badge、筛选骨架、非 PDD 禁用启动（10b） | 账号管理登录仍 PDD Playwright |
| **入站契约** | routing / content_type / platform SSOT + 契约测试（10c/10d） | 生产 handler **Context-first**；`USE_UNIFIED_MESSAGE_DUAL_TRACK` 默认 **false** |
| **队列** | `build_queue_name` / `pdd_queue_name`；lifecycle `_lifecycle_pdd_queue_name`（10h） | 仅 PDD lifecycle 生产接入 |
| **Channel 抽象** | `BaseChannel` / `ChannelOutbound` / `ChannelRegistry` | 生产注册仅 `pinduoduo` |
| **参考实现** | `PinduoduoChannel` + `PDDChannel` 全栈 | 无真实第二平台 Channel |
| **架构验证** | `DemoChannel` + mappers + enqueue + registry/resolver 单测 | Demo 非生产 AutoReply |
| **出站** | `PinduoduoOutbound`；`channel_outbound_registry`（测试）；resolver 默认 off | 生产发送仍以 legacy `SendMessage` 为主 |
| **运维** | `runtime_capabilities` / `diagnose_runtime` | 无第二平台连通性 |

**一句话：** 架构与测试台可 **验证多平台契约**；**可运营的多平台自动回复** 仍缺 inbound transport、平台 login、lifecycle、AutoReply 按平台路由及（可选）Consumer 平台化——留给 **10j 计划 + 11+ 代码 Phase**。

---

## 3. Capability matrix 字段定义

SSOT 表：每平台一行。单元格取值：

| 符号 | 含义 |
|------|------|
| ✅ 生产 | 生产默认路径已具备 |
| 🧪 测试 | 仅单测 / flag / mock |
| 📋 规划 | 文档或 spike 计划，无生产代码 |
| ❌ | 无 |
| 🔒 PDD-only | 仅拼多多，第二平台不得复用实现 |

| 字段 | 含义 |
|------|------|
| **platform_id** | `channel_name` / `PlatformType.value` |
| **inbound_transport** | WS / 长轮询 / Webhook 等收消息 |
| **login_session** | 登录、cookies/token、会话刷新 |
| **raw_message_model** | 平台原生消息类型 |
| **message_mapper** | raw → `Context`（生产入站） |
| **unified_mapper** | raw → `UnifiedMessage` |
| **routing_compute** | `immediate` \| `queue` \| `drop` |
| **queue_naming** | 生产 `queue_name` 生成与 cleanup |
| **consumer_binding** | `_setup_message_consumer` / `put_message` |
| **outbound_adapter** | `ChannelOutbound` |
| **outbound_registry** | `AccountOutboundRegistry` / `channel_outbound_registry` |
| **account_model** | DB 三层 + `account_data` |
| **ui_support** | 展示、筛选、能否启动 AutoReply |
| **runtime_registration** | `ChannelRegistry` + AutoReply factory |
| **lifecycle** | start / stop / reconnect / cleanup |
| **contract_tests** | 平台 parity / 集成测试 |
| **production_autoreply** | 真实店端到端自动回复 |

---

## 4. PDD capability matrix

| 字段 | 状态 | 说明 |
|------|------|------|
| platform_id | ✅ 生产 | `pinduoduo` |
| inbound_transport | ✅ 生产 | `PDDChannel` WebSocket（`pdd_lifecycle`） |
| login_session | ✅ 生产 | `pdd_login` + cookies / `GetToken` |
| raw_message_model | ✅ 生产 | `PDDChatMessage` |
| message_mapper | ✅ 生产 | `pdd_message_handler` → `Context` |
| unified_mapper | 🧪 可选 | `pdd_to_unified`；shadow/dual-track **默认 off** |
| routing_compute | ✅ 生产 | `compute_pdd_routing` |
| queue_naming | ✅ 生产 | `_lifecycle_pdd_queue_name` → **`pdd_{shop_id}`** |
| consumer_binding | ✅ 生产 | lifecycle `_setup_message_consumer` |
| outbound_adapter | 🧪/✅ | `PinduoduoOutbound`（`USE_PINDUODUO_OUTBOUND` 默认 off） |
| outbound_registry | ✅ PDD | `AccountOutboundRegistry`（wrapper 路径） |
| account_model | ✅ 生产 | DB + `account_data` |
| ui_support | ✅ 生产 | 唯一 `is_autoreply_supported` 平台 |
| runtime_registration | ✅ 生产 | `channel_factory` → `PDDChannel`；Registry 可选 |
| lifecycle | ✅ 生产 | `pdd_lifecycle`（10h queue helper） |
| contract_tests | ✅ | routing/queue/lifecycle 等 parity 测试 |
| production_autoreply | ✅ | 默认交付路径 |

---

## 5. Demo capability matrix

| 字段 | 状态 | 说明 |
|------|------|------|
| platform_id | 🧪 | `demo` |
| inbound_transport | 🧪 内存 | 无真实网络；`inject_runtime_flow` |
| login_session | 🧪 桩 | `login` 恒 true |
| raw_message_model | 🧪 | 合成 dict |
| message_mapper | 🧪 | `demo_raw_to_context` |
| unified_mapper | 🧪 | `demo_raw_to_unified` |
| routing_compute | ❌ | 无 `compute_demo_routing` |
| queue_naming | 🧪 | `demo_{shop_id}`（`build_queue_name`） |
| consumer_binding | 🧪 | `enqueue_demo_message` |
| outbound_adapter | 🧪 | `DemoOutbound` |
| outbound_registry | 🧪 | `channel_outbound_registry` 单测 |
| account_model | 📋 | 一般不 seed 生产 DB |
| ui_support | 📋 | 显示名有；**不可**启动 AutoReply |
| runtime_registration | 🧪 | 测试 / `USE_DEMO_CHANNEL_REGISTRATION` |
| lifecycle | 🧪 | `DemoChannel` 内存状态机 |
| contract_tests | ✅ | `test_demo_*`、runtime flow |
| production_autoreply | ❌ | 明确非生产 |

---

## 6. 真实第二平台 minimum spike matrix

**首选平台：** `doudian`（抖店）。`taobao` / `jingdong` 结构相同，差异在 login/transport API（10j 调研表）。

| 字段 | Spike 最小交付（10j 计划） | 生产 Phase（11+，非 10i/10j） |
|------|---------------------------|------------------------------|
| platform_id | 📋 固定 `doudian` 等 | DB/UI seed |
| inbound_transport | 📋 调研 + 接口清单；可选 mock transport 测试设计 | 真实 WS/推送 |
| login_session | 📋 OAuth/cookie/扫码调研 | `doudian_login` |
| raw_message_model | 📋 schema 草案 | 生产 parser |
| message_mapper | 🧪 设计 `doudian_raw_to_context`（fixture only） | 接入入站 |
| unified_mapper | 🧪 可选 fixture mapper | dual-track 上线 |
| routing_compute | 📋 `compute_doudian_routing` 规则表 | parity 测试 |
| queue_naming | 🧪 `doudian_{shop_id}`（`build_queue_name`） | **禁止** `pdd_` 前缀 |
| consumer_binding | 🧪 测试内 enqueue（仿 Demo） | 新 lifecycle |
| outbound_adapter | 📋 能力矩阵 + mock 桩设计 | 真实 API |
| outbound_registry | 🧪 测试注册设计 | `start_account` 注册 |
| account_model | 📋 shop_id/account_id 语义差异表 | migration |
| ui_support | ❌ spike 不改 | 10b+ |
| runtime_registration | 📋 flag 下 `Registry.create` 设计 | AutoReply 按 platform 路由 |
| lifecycle | 📋 对标 `pdd_lifecycle` 设计稿 | 实现 |
| contract_tests | 🧪 mapper + queue parity（设计） | E2E |
| production_autoreply | ❌ | 独立 release |

**Spike 共性最小集：** 枚举已有 → queue 前缀 → raw→Context（fixture）→ routing 文档 → outbound 缺口表 → login/transport 调研 → **零 PDD 默认变更**。

---

## 7. 可复用模块

| 模块 | 复用方式 |
|------|----------|
| `Channel/base/channel.py` | 新平台 `XxxChannel(BaseChannel)` |
| `Channel/base/outbound.py` | `XxxOutbound` |
| `Channel/base/registry.py` | flag/测试内 `register` + `create` |
| `Channel/base/models.py` | `UnifiedMessage` 等 |
| `Channel/base/types.py` | `PlatformType`（含 doudian/taobao/jingdong） |
| `Message/queue_naming.py` | `build_queue_name(platform_id, shop_id)` |
| `Message/inbound_enqueue.py` | Demo 模式；第二平台仿 enqueue |
| `PinduoduoChannel` | Strangler 包装 legacy 客户端 |
| `channel_factory` 模式 | 未来按 `platform_id` 分支（**新 Phase + flag**） |
| `channel_outbound_registry` | 非 PDD 出站（resolver on 时） |
| `ui/auto_reply/platform_ui.py` | 显示名；spike 不改守卫 |
| Phase 10c routing/content_type | 新平台同名 routing 枚举 |
| 契约测试模式 | `test_*_parity` 模板 |

---

## 8. 不可复用 / 平台专属模块

| 模块 | 原因 |
|------|------|
| `PDDChannel` / `pdd_lifecycle` / `pdd_message_handler` | PDD 协议、token、心跳、routing |
| `pdd_login` / Playwright | PDD 专用 |
| `GetToken` / PDD API utils | 平台 API |
| `compute_pdd_routing` | 业务规则平台相关 |
| **`pdd_{shop_id}` 前缀** | 第二平台 **不得** 复用 |
| `AccountOutboundRegistry` 生产假设 | 历史 PDD 键；第二平台优先 `channel_outbound_registry` 或新 registry |
| `Message/handlers/**` PDD 分支 | 改默认风险高 |
| `MessageConsumer` 按平台多 handler | 11+ |
| 账号管理 `LoginThread` | 现绑 PDD |

---

## 9. PDD-only 必须保留路径

以下在 **10i、10j 及第二平台 spike 期间** 必须保持默认不变：

```text
AutoReplyThread
  → create_auto_reply_runtime_channel()     # 默认 PDD legacy；9d registry 默认 on 仍仅 PINDUODUO
  → PDDChannel.init / stop_account          # 10h：queue via _lifecycle_pdd_queue_name
  → pdd_message_handler                     # Context-first
  → queue_name = pdd_{shop_id}              # 禁止改为 pinduoduo_{shop_id}
  → MessageConsumer + handler_chain         # 无 platform 分叉默认
  → 出站：USE_PINDUODUO_OUTBOUND / USE_UNIFIED_OUTBOUND_RESOLVER 默认 false → legacy SendMessage
  → USE_UNIFIED_MESSAGE_DUAL_TRACK 默认 false
```

**冻结（禁止在 10i/10j 默认改动）：** `pdd_lifecycle`、`pdd_message_handler`、`Message/core/consumer.py`、`Message/handlers/**`、`*_flags.py` 默认值、`channel_factory` 默认、`ui/**`、`database/**`、`app.py`。

---

## 10. Phase 10i 最小安全范围

| 允许 | 禁止 |
|------|------|
| 新增/更新 `docs/**`（本 Phase 文件） | 任何 `.py` |
| 交叉引用 10a–10h done | 改 `Channel/pinduoduo/**` |
| 定义 10j spike 边界与 prompt | 接真实第二平台 |
| 更新 architecture / README 索引 | 改 flag / UI / DB 默认 |

---

## 11. 是否现在接真实第二平台

**否。**

理由：缺 inbound/login/lifecycle/AutoReply 按平台路由；PDD 黄金路径刚完成 queue 接线；应先 **矩阵 + 10j spike 计划**（mock/fixture 设计），再在 **11+** 用非默认 flag 接真实 API。

---

## 12. 10i 是否只做文档

**是。** 与 10a / 10c / 10e 一致：SSOT 文档 + 架构索引，**零生产行为变更**。

---

## 13. 禁止修改文件

```
# 代码（全部禁止）
**/*.py
Channel/pinduoduo/**
Channel/pinduoduo/core/pdd_lifecycle.py
Channel/pinduoduo/core/pdd_message_handler.py
Message/core/consumer.py
Message/handlers/**
Message/*_flags.py
Channel/pinduoduo/*_flags.py
Message/autoreply_registry_flags.py   # 9d 默认不变
ui/**
database/**
app.py
Channel/pinduoduo/channel_factory.py
ui/auto_reply/threads.py

# 第二平台代码目录（禁止新增）
Channel/doudian/**
Channel/taobao/**
Channel/jingdong/**
```

**10i 允许路径：** `docs/phase10i_plan.md`、`docs/phase10i_done.md`、`docs/architecture_current.md`、`docs/README.md`、`docs/phase10h_done.md`（可选 next step 一行）。

---

## 14. 文档更新方案

| 文件 | 动作 |
|------|------|
| `docs/phase10i_plan.md` | 本文（SSOT） |
| `docs/phase10i_done.md` | 签收：纯文档、无代码 |
| `docs/architecture_current.md` | Phase 表 + multi-platform matrix 链接 |
| `docs/README.md` | Phase 10i 行 |
| `docs/phase10h_done.md` | 可选：next → 10i |

---

## 15. Phase 10j prompt

```text
继续 Phase 10j：第二平台 spike 计划（仅文档 + 可选 tests/fixtures 设计说明），不接真实平台 API，不改 PDD 默认。

先读：
- docs/phase10i_plan.md
- docs/phase10i_done.md
- docs/phase6a_plan.md、phase8a_done.md
- Channel/demo/**（只读参考）
- Message/queue_naming.py、phase10c_done.md

目标：
1. 首选平台 doudian；附 taobao/jingdong 差异表
2. 新增 docs/phase10j_plan.md：最小 spike 工作包
   - mapper 测试设计（fixture only）
   - queue parity（doudian_{shop_id}）
   - mock transport 边界
   - routing 规则草案
   - login/transport 调研 checklist
3. 明确禁止：pdd_lifecycle、pdd_message_handler、consumer、handlers、flags 默认、UI、DB、channel_factory 默认、真实 API
4. spike 验收：仅文档或 tests 设计；无真实 WS/登录
5. 定义 Phase 11+ 生产门槛 checklist
6. 更新 architecture_current.md、README.md

约束：
- 不新增 Channel/doudian/** 生产代码（除非用户显式放开「仅 tests/fixtures」）
- 不接真实第二平台
- PDD queue 仍为 pdd_{shop_id}
- USE_UNIFIED_MESSAGE_DUAL_TRACK / USE_UNIFIED_OUTBOUND_RESOLVER 默认仍 false

验收：
git diff --stat 仅 docs/*.md（若仅文档）
```

---

## Phase 10a–10h 对 matrix 的贡献（速查）

| Phase | 为第二平台准备的 capability |
|-------|------------------------------|
| 10a | `platform_id` = `channel_name` |
| 10b | UI 守卫；非 PDD 不可启动 AutoReply |
| 10c–10d | routing / platform / content_type SSOT + 测试 |
| 10e | queue 与 routing/platform 职责分工 |
| 10f–10g | `build_queue_name` / `pdd_queue_name` |
| 10h | PDD lifecycle queue SSOT（**不**泛化到第二平台） |

---

*规划版本：Phase 10i · 2026-06-03 · 纯文档*

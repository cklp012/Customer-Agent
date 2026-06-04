# Release Checkpoint — Phase 8a–9d / 9e

**文档导航：** [docs 目录](README.md) · [架构基线](architecture_current.md) · [运行模式](runtime_modes.md) · [运行手册](runbook.md)

| 项 | 值 |
|---|---|
| Checkpoint | Phase **9e**（文档）；运行时里程碑 Phase **9d** |
| 项目 | Customer-Agent（拼多多单平台生产 + 多平台骨架） |
| SSOT 伙伴 | `architecture_current.md`（模块/路线图）、`runtime_modes.md`（flag 细节） |

---

## 1. Executive summary

- **Phase 8a–9d 已完成**：Demo 入站 spike、unified outbound、runtime 诊断、bootstrap、AutoReply Registry 门控 / parity / 默认开启均已交付并单测覆盖。
- **Phase 9d 起**：`USE_CHANNEL_REGISTRY_FOR_AUTOREPLY` **未设置 → true**；AutoReply 默认经 **`ChannelRegistry.create(PINDUODUO)`** 创建 Channel。
- **PDD 默认行为不变**：`USE_PINDUODUO_CHANNEL_WRAPPER` 未设置 → **false** → 实例仍为 **`PDDChannel`**；WebSocket、登录、`pdd_message_handler`、handler 链、`SendMessage` 出站语义与 Phase 0 legacy **一致**。
- **差异**：默认仅多一层 **Registry 注册工厂分发**（`create_pinduoduo_registry_channel` → `_create_auto_reply_legacy`），9b 已证明与直连 legacy 等价。
- **legacy fallback 保留**：Registry 未注册、`create` 失败或返回 `None` → warning + `_create_auto_reply_legacy()`，不阻断 GUI。
- **Demo 默认不注册**：`USE_DEMO_CHANNEL_REGISTRATION` 默认 false；不接 AutoReply；仅测试 / spike。
- **Phase 9e**：本 checkpoint 文档；**不改**业务代码、flag 默认值或测试。

---

## 2. Phase 8a–9d summary table

| Phase | 主题 | 交付要点 | 生产默认影响 |
|-------|------|----------|--------------|
| **8a** | Demo runtime spike | Demo 入站 → 可选双轨 → `MessageConsumer` → handler(`Context`)；独立 `demo_*` queue | 无 |
| **8b** | Unified outbound resolver | `resolve_outbound` + `channel_outbound_registry`；PDD 委托旧 resolver | 无（handler 未默认接） |
| **8c** | Handler gated unified outbound | `USE_UNIFIED_OUTBOUND_RESOLVER`；默认 off | 无 |
| **8d** | Runtime diagnostics | `Message/runtime_capabilities.py` + `scripts/diagnose_runtime.py` | 无（只读） |
| **8e** | Runtime bootstrap API | `register_default_platforms()`；只 register，不 start | 无（须调用方触发） |
| **8f** | App startup bootstrap | `app.py` `main()` → `apply_app_startup_bootstrap()`；失败不阻断 GUI | **有**：主进程注册 `pinduoduo` |
| **9a** | AutoReply registry flag | `USE_CHANNEL_REGISTRY_FOR_AUTOREPLY` 门控 `Registry.create` | 当时默认 off |
| **9b** | PDD registry factory parity | `register` → `create_pinduoduo_registry_channel` ≡ `_create_auto_reply_legacy` | 工厂语义 |
| **9c** | Parity hardening | 单测 + 手动灰度；9d 前默认仍显式 legacy 路径验证 | 无 |
| **9d** | AutoReply registry default-on | env 未设置 → registry path；`false` 回滚 | **有**：AutoReply 默认 `Registry.create` |
| **9e** | Release checkpoint | 本文档 + SSOT 文档同步 | 无（仅文档） |

---

## 3. Current default runtime path

**条件：** 不设置任何 `USE_*` 环境变量，正常 `python app.py`。

### 3.1 App 启动（Registry bootstrap）

```text
app.py :: main()
  → QApplication
  → apply_app_startup_bootstrap()
       → register_default_platforms()
            → register_pinduoduo_channel()
                 → ChannelRegistry.register(
                      PlatformType.PINDUODUO,
                      create_pinduoduo_registry_channel,
                    )
            → （默认不）register Demo
  → MainWindow / GUI
```

- **不** `start_account`、**不**连 WebSocket、**不**启动 Demo runtime。
- Bootstrap 失败：记日志，GUI 继续；AutoReply 创建时可能 fallback legacy。

### 3.2 用户启动自动回复账号

```text
ui/auto_reply/threads.py :: AutoReplyThread.run()
  → create_auto_reply_runtime_channel()
       → USE_CHANNEL_REGISTRY_FOR_AUTOREPLY unset → true（9d）
       → ChannelRegistry.is_registered(PINDUODUO) → true（app 已 bootstrap）
       → ChannelRegistry.create(PlatformType.PINDUODUO)
            → create_pinduoduo_registry_channel(**kwargs)
                 → _create_auto_reply_legacy(**kwargs)
                      → USE_PINDUODUO_CHANNEL_WRAPPER unset → false
                      → PDDChannel(**kwargs)
  → start_auto_reply_account(PDDChannel, shop_id, user_id, …)   # 四参数 legacy 签名
  → PDDChannel：WebSocket / 队列 / handler_chain（未改）
  → MessageConsumer → KeywordDetectionHandler → AIReplyHandler → …
  → 出站：resolve_pinduoduo_outbound → 通常 None → SendMessage（默认）
```

### 3.3 含义（给发布评审）

| 层 | 9d 默认 | 与 Phase 0 关系 |
|----|---------|-----------------|
| Channel **创建入口** | 经 `ChannelRegistry` | 多一层分发；9b/9c 证明等价 |
| Channel **类型** | `PDDChannel` | **相同** |
| WS / 登录 / 解析 | `PDDChannel` 内部 | **相同** |
| Handler / Consumer | 未改主路径 | **相同** |
| 出站 | legacy `SendMessage` | **相同** |

---

## 4. Flag matrix

真值（多数 flag）：`1`、`true`、`yes`、`on`（大小写不敏感）。

### 4.1 `USE_CHANNEL_REGISTRY_FOR_AUTOREPLY`（Phase 9a/9d）

| env 值 | Resolved | AutoReply 创建 |
|--------|----------|----------------|
| **未设置 (None)** | **true** | `ChannelRegistry.create`（已 bootstrap 时） |
| `true` / `1` / `yes` / `on` | true | 同上 |
| `false` / `0` / `no` / `off` | false | `_create_auto_reply_legacy`（回滚） |
| `""` 或其它未知 | false | legacy 直连 |

读取：`Message/autoreply_registry_flags.py`。

### 4.2 其它 flags（unset → false）

| 环境变量 | unset | 作用摘要 |
|----------|-------|----------|
| `USE_PINDUODUO_CHANNEL_WRAPPER` | **false** | AutoReply：`PDDChannel` vs `PinduoduoChannel` |
| `USE_PINDUODUO_OUTBOUND` | **false** | handler / 即时消息：优先 `PinduoduoOutbound` vs `SendMessage` |
| `USE_UNIFIED_OUTBOUND_RESOLVER` | **false** | handler：`resolve_outbound` vs `resolve_pinduoduo_outbound` |
| `USE_UNIFIED_MESSAGE_SHADOW` | **false** | WS 后旁路 unified mapper 日志 |
| `USE_UNIFIED_MESSAGE_DUAL_TRACK` | **false** | 入队附带 `UnifiedMessage`；handler 仍 `Context` |
| `USE_DEMO_CHANNEL_REGISTRATION` | **false** | bootstrap 是否注册 Demo 工厂 |

### 4.3 PDD 四模式（wrapper × outbound）

| # | Wrapper | Outbound | 模式 ID | 默认？ |
|---|---------|----------|---------|--------|
| 1 | off | off | `legacy-default` | **是** |
| 2 | on | off | `wrapper-only` | 否 |
| 3 | off | on | `outbound-only` | 否 |
| 4 | on | on | `wrapper-and-outbound` | 否（4b 联调目标） |

详见 [runtime_modes.md §2](runtime_modes.md#2-四种运行模式)。

---

## 5. AutoReply Registry path

| 项 | 说明 |
|----|------|
| **默认（9d）** | env 未设置 → 走 Registry path |
| **前提** | `app.py` 已 `apply_app_startup_bootstrap()`，本进程通常已注册 `PINDUODUO` |
| **成功链** | `create` → `create_pinduoduo_registry_channel` → `_create_auto_reply_legacy` |
| **失败** | 未注册 / 异常 / `None` → `AutoReplyChannelFactory` warning + legacy fallback |
| **回滚** | `USE_CHANNEL_REGISTRY_FOR_AUTOREPLY=false` → 不经 `Registry.create` |
| **未改** | `AutoReplyThread` 仍只调用 `create_auto_reply_runtime_channel()` |

### diagnose 与 app 进程差异

| 进程 | 典型 `autoreply_channel_source` | 说明 |
|------|--------------------------------|------|
| `python app.py` | `registry`（bootstrap 后） | 生产关注对象 |
| `python scripts/diagnose_runtime.py` | 常 `registry_fallback` | **独立进程**，默认**不**调用 `register_default_platforms()` |

**`registry_fallback` 在 diagnose 中正常，不等于 app 未 bootstrap 或生产故障。**

---

## 6. PDD wrapper flag

| `USE_PINDUODUO_CHANNEL_WRAPPER` | AutoReply 实例（经 factory） |
|--------------------------------|------------------------------|
| **false（默认）** | `PDDChannel` |
| **true** | `PinduoduoChannel`（内包 `PDDChannel`） |

**分工：**

- **Registry flag**：从哪条路径**创建**（Registry vs 直连 `_create_auto_reply_legacy`）。
- **Wrapper flag**：创建**哪种** PDD Channel 类型。

二者**独立**。9d 默认 Registry on + wrapper off → 仍是 **`PDDChannel`**。

---

## 7. Outbound resolver flags

| Flag | 默认 | 范围 |
|------|------|------|
| `USE_PINDUODUO_OUTBOUND` | off | `ai_handler`、`keyword_handler`、`pdd_message_handler`（即时） |
| `USE_UNIFIED_OUTBOUND_RESOLVER` | off | `ai_handler`、`keyword_handler`（`resolve_outbound`） |

**生产默认出站：** `resolve_pinduoduo_outbound` → 无 outbound → **`SendMessage` / `move_conversation`**。

**勿误解：** 9d 只改变 AutoReply **Channel 创建入口**，**未**默认 unified outbound，**未**默认 `PinduoduoOutbound`。

**AccountOutboundRegistry 复用（Phase 4b）：** 需 **wrapper on + outbound on**，且账号经 `PinduoduoChannel.start_account` 注册。

---

## 8. Unified message flags

| Flag | 默认 | 行为 |
|------|------|------|
| `USE_UNIFIED_MESSAGE_SHADOW` | off | 旁路 `pdd_to_unified` 日志；不改 Consumer |
| `USE_UNIFIED_MESSAGE_DUAL_TRACK` | off | 入队带 `UnifiedMessage` 副本；handler **仍 Context** |

UnifiedMessage 为**可选**观测 / 双轨；**不是**生产默认主路径。

---

## 9. Demo channel

| 项 | 状态 |
|----|------|
| 代码 | `Channel/demo/*`、`PlatformType.DEMO`、8a 测试级 pipeline |
| Bootstrap | `USE_DEMO_CHANNEL_REGISTRATION=false` → 仅 `pinduoduo` |
| AutoReply | **不接** Demo |
| 生产 | **禁止** 默认注册或默认启动 Demo WS |
| 用途 | 单测、证明第二平台可走同一 Consumer 骨架 |

---

## 10. Rollback commands

### 10.1 AutoReply Registry path（主回滚，9d）

```powershell
cd D:\agent
$env:USE_CHANNEL_REGISTRY_FOR_AUTOREPLY = "false"
python app.py
```

### 10.2 清除可选 flag（回到 PDD 全 legacy 基线）

```powershell
Remove-Item Env:USE_CHANNEL_REGISTRY_FOR_AUTOREPLY -ErrorAction SilentlyContinue
Remove-Item Env:USE_PINDUODUO_CHANNEL_WRAPPER -ErrorAction SilentlyContinue
Remove-Item Env:USE_PINDUODUO_OUTBOUND -ErrorAction SilentlyContinue
Remove-Item Env:USE_UNIFIED_OUTBOUND_RESOLVER -ErrorAction SilentlyContinue
Remove-Item Env:USE_UNIFIED_MESSAGE_SHADOW -ErrorAction SilentlyContinue
Remove-Item Env:USE_UNIFIED_MESSAGE_DUAL_TRACK -ErrorAction SilentlyContinue
Remove-Item Env:USE_DEMO_CHANNEL_REGISTRATION -ErrorAction SilentlyContinue
python app.py
```

注意：删除 `USE_CHANNEL_REGISTRY_FOR_AUTOREPLY` 在 9d 下等价于 **恢复默认 true**；回滚创建路径必须用 **`false`**。

---

## 11. Verification checklist

### 11.1 自动化（发布前必跑）

- [ ] `python -m unittest discover -s tests -v`
- [ ] `python scripts/diagnose_runtime.py`（退出码 0；PDD core import 无 ERROR）

### 11.2 手动 — 默认 env（生产等价）

- [ ] `python app.py` 启动正常
- [ ] 自动回复页可打开
- [ ] 启动账号 → 连接成功
- [ ] 日志**无** `ChannelRegistry.create fallback for AutoReply`
- [ ] 停止账号正常
- [ ] （建议）收消息 / 关键词 / AI 回复 — 见 [phase0_audit.md](phase0_audit.md) 黄金路径

### 11.3 手动 — 回滚抽样

- [ ] `$env:USE_CHANNEL_REGISTRY_FOR_AUTOREPLY = "false"` 后重启 app
- [ ] 账号仍可启动 / 停止

### 11.4 联调（非默认，按需）

- [ ] `USE_PINDUODUO_CHANNEL_WRAPPER=true` + `USE_PINDUODUO_OUTBOUND=true`（`wrapper-and-outbound`）

---

## 12. Diagnostics cheat sheet

| 问题 | 解读 |
|------|------|
| diagnose 显示 `USE_CHANNEL_REGISTRY_FOR_AUTOREPLY: <unset> -> True` | 符合 9d 默认 |
| diagnose 显示 `autoreply_channel_source: registry_fallback` | diagnose **未 bootstrap**；正常 |
| app 运行中账号正常但 diagnose 为 fallback | **进程不同**；以 app 日志为准 |
| 生产故障信号 | app 日志出现 `ChannelRegistry.create fallback for AutoReply` |
| bootstrap 失败 | 8f 吞异常；依赖 fallback；查 `App` / `ChannelBootstrap` 日志 |

**推荐发布前：**

```powershell
python scripts/diagnose_runtime.py    # 环境与 import
python app.py                          # 再看启动与启账号日志
```

---

## 13. Phase 10 boundary — 不应立刻做

| 暂缓 / 禁止 | 原因 |
|-------------|------|
| 删除 `_create_auto_reply_legacy` / fallback | 9d 仍依赖 |
| 删除 `create_auto_reply_runtime_channel` | AutoReply 唯一工厂入口 |
| 默认 `USE_PINDUODUO_CHANNEL_WRAPPER=true` | 改变 WS / outbound registry 生命周期 |
| 默认 `USE_DEMO_CHANNEL_REGISTRATION=true` | 非生产平台 |
| 淘宝 / 抖店 / 京东 **生产 WS** | 需独立 spike + 黄金路径 |
| 默认 `USE_UNIFIED_OUTBOUND_RESOLVER=true` | handler 行为面大 |
| 改 PDD WS / `pdd_login` / `pdd_message_handler` | 超出接线 Phase |
| 改 `MessageConsumer` / handler_chain 主契约 | 高风险 |
| `AutoReplyThread` 直接 `ChannelRegistry.create` | 破坏单点 factory |

---

## 14. Phase 10 recommended direction

| 阶段 | 建议内容 |
|------|----------|
| **10a** | 多平台 UI / 账号模型 **规划**（平台字段、配置结构） |
| **10b** | UI **骨架**（平台选择、展示）；**不接**真实第二平台 WS |
| **10c** | routing / `content_type` **规划**（8 规划 Route C）；handler 行为需新 flag 门控 |
| **独立 spike** | 真实第二平台（6a 优先级：抖店 > 京东 > 淘宝） |
| **可选** | 默认 `wrapper-and-outbound` 生产化 — 单独立项，非 10 前置 |

**Phase 10 首迭代建议：** 文档 + UI 模型 + 边界清晰；**不**在 10 第一轮接真实平台协议。

---

## Appendix — Key modules (unchanged by 9d)

| 模块 | 角色 |
|------|------|
| `Channel/pinduoduo/channel_factory.py` | `create_auto_reply_runtime_channel`、registry 工厂、fallback |
| `Message/runtime_bootstrap.py` | `register_default_platforms`、`apply_app_startup_bootstrap` |
| `ui/auto_reply/threads.py` | `AutoReplyThread`（未改 9a–9d） |
| `Message/handlers/*` | Context 主路径；outbound flags 独立 |
| `scripts/diagnose_runtime.py` | 只读诊断 |

---

*Checkpoint 版本：Phase 9e · 2026-06-03*

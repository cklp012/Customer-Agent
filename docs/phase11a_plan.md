# Phase 11a 规划 — Flag-Gated Doudian Registry / Factory Boundary

| 项 | 值 |
|----|-----|
| 类型 | **纯文档 SSOT**（registry/factory 边界；**不写代码**） |
| 状态 | 规划（执行后见 [phase11a_done.md](phase11a_done.md)） |
| 前置 | Phase 10k–10m（[phase10m_done.md](phase10m_done.md)） |
| 推荐路线 | **Route A**（本文）→ **11b** 实现 flag + mock 注册 |
| 禁止路线 | **Route E**（默认注册 Doudian / 改 factory 默认分支） |

**文档导航：** [architecture_current.md](architecture_current.md) · [phase10j_plan.md](phase10j_plan.md) · [release_checkpoint_phase9.md](release_checkpoint_phase9.md)

---

## 1. Phase 11a 总体分析

10k–10m 已在 **`Channel/doudian/`** 形成 **local mock spike**（fixture、mapper、mock transport、enqueue、mock outbound），但 **未进入** `ChannelRegistry` 与 AutoReply 运行时。

**11a 目标：** 定义 Doudian mock 如何 **可选** 进入 `ChannelRegistry` / factory 体系，同时 **冻结**：

- PDD 生产默认路径（含 9d Registry **仅 PINDUODUO**）
- `create_auto_reply_runtime_channel()` **不按** `channel_name` 创建 Doudian
- 无真实抖店 API / WS / login

**11a 不做：** 改 `register_default_platforms` 默认计划、改 `USE_CHANNEL_REGISTRY_FOR_AUTOREPLY` 语义、改 `AutoReplyThread`、默认注册 Doudian。

**11b 再做（Route C）：** `USE_DOUDIAN_CHANNEL_REGISTRATION`（默认 false）+ `register_doudian_channel()` + `DoudianMockChannel` + 单测；仍不接 AutoReply 默认分支。

---

## 2. 当前 registry / factory 状态

### 2.1 ChannelRegistry

| 组件 | 路径 | 行为 |
|------|------|------|
| 注册表 | `Channel/base/registry.py` | `register` / `create` / `is_registered` / `registered_platforms` |
| PDD 工厂 | `register_pinduoduo_channel()` | `PlatformType.PINDUODUO` → `create_pinduoduo_registry_channel` |
| PDD registry 工厂 | `create_pinduoduo_registry_channel` | 内部 **`_create_auto_reply_legacy`**（wrapper flag），**不**递归 `create_auto_reply_runtime_channel` |

### 2.2 Bootstrap（app 启动）

```text
app.py main()
  → apply_app_startup_bootstrap()
       → register_default_platforms()
            → register_pinduoduo_channel()     # 始终
            → register_demo_channel()            # 仅 USE_DEMO_CHANNEL_REGISTRATION=true
```

| 函数 | 路径 |
|------|------|
| `register_default_platforms` | `Message/runtime_bootstrap.py` |
| Demo 开关 | `Message/bootstrap_flags.py` → `use_demo_channel_registration()`，**默认 false** |

**注意：** `list_available_platforms()` 当前仅列 `pinduoduo` + `demo`；**未列** `doudian`（11b 可扩展 metadata）。

### 2.3 AutoReply factory（生产入口）

```text
AutoReplyThread.run()
  → create_auto_reply_runtime_channel()    # 无 platform 参数
       → use_channel_registry_for_autoreply()  # 9d：env 未设置 → True
       → ChannelRegistry.create(PINDUODUO)       # 仅拼多多
       → fallback _create_auto_reply_legacy
  → start_auto_reply_account(channel, shop_id, user_id, ...)
```

| 开关 | 文件 | 默认（unset env） |
|------|------|-------------------|
| `USE_CHANNEL_REGISTRY_FOR_AUTOREPLY` | `Message/autoreply_registry_flags.py` | **True**（9d） |
| 创建平台 | `channel_factory.create_auto_reply_runtime_channel` | **仅 PINDUODUO** |
| `USE_PINDUODUO_CHANNEL_WRAPPER` | `Channel/pinduoduo/channel_flags.py` | false |

**结论：** 9d「Registry 默认 on」= **PDD 经 Registry 创建**，≠ 多平台 AutoReply。

### 2.4 并行 registry（出站，非 Channel）

| 注册表 | 用途 | Doudian 10m |
|--------|------|-------------|
| `channel_outbound_registry` | 按 platform 缓存 outbound | 测试内 `register(DOUDIAN, …)` ✅ |
| `AccountOutboundRegistry` | PDD 生产出站 | 不扩展 Doudian |

---

## 3. Doudian mock spike 当前 readiness

| 能力 | 状态 | 路径 |
|------|------|------|
| fixtures | ✅ | `tests/fixtures/doudian_messages/` |
| mappers + routing | ✅ | `Channel/doudian/mappers/` |
| mock transport | ✅ | `mock_transport.py` |
| enqueue helper | ✅ | `doudian_inbound.py` |
| mock outbound | ✅ | `doudian_outbound.py` |
| BaseChannel 实现 | ❌ | 无 `DoudianMockChannel` |
| ChannelRegistry 工厂 | ❌ | 无 `register_doudian_channel` |
| AutoReply 接入 | ❌ | `threads.py` 无 platform 路由 |
| 真实 API | ❌ | 明确不做 |

**Readiness：** 足够做 **Registry 契约单测**（11b）；不足做 **生产自动回复** 或真实连接。

---

## 4. 是否应该进入 ChannelRegistry

**应该，但是 flag-gated、test-first，且与 PDD 注册解耦。**

| 理由 | 说明 |
|------|------|
| 对齐 Demo | `register_demo_channel()` 已证明 Registry 多平台模式 |
| 可测性 | `ChannelRegistry.create(DOUDIAN)` 单测，无需改 AutoReply |
| 边界清晰 | 注册 ≠ 生产启用；与 `USE_DEMO_CHANNEL_REGISTRATION` 同模式 |
| 风险可控 | 默认 **不** 进入 `get_default_registration_plan()` |

**不应：** 在 11a/11b 将 Doudian 写入 **默认** `register_default_platforms()` 无条件分支（Route E 禁止）。

---

## 5. flag-gated registration 设计

### 5.1 建议新增 flag（11b 实现，11a 仅文档）

| 环境变量 | 模块（建议） | 默认值 | 作用 |
|----------|--------------|--------|------|
| **`USE_DOUDIAN_CHANNEL_REGISTRATION`** | `Message/bootstrap_flags.py` 或 `Channel/doudian/doudian_flags.py` | **false** | `register_default_platforms` 是否 `register_doudian_channel()` |

**与 Demo 对称：**

| Flag | 默认 | 注册 |
|------|------|------|
| `USE_DEMO_CHANNEL_REGISTRATION` | false | Demo |
| `USE_DOUDIAN_CHANNEL_REGISTRATION` | false | Doudian（规划） |

### 5.2 `register_doudian_channel()`（11b）

建议路径：`Channel/doudian/doudian_factory.py`（仿 `demo_factory.py`）：

```text
def create_doudian_channel(**kwargs) -> DoudianMockChannel: ...
def register_doudian_channel() -> None:
    ChannelRegistry.register(PlatformType.DOUDIAN, create_doudian_channel)
```

**幂等：** 与 `register_pinduoduo_channel` 相同，可重复调用。

### 5.3 不新增 / 不改的 flag（11a 冻结）

| Flag | 11a/11b 要求 |
|------|----------------|
| `USE_CHANNEL_REGISTRY_FOR_AUTOREPLY` | **不改默认值**（unset → True，仍仅 `create(PINDUODUO)`） |
| `USE_PINDUODUO_CHANNEL_WRAPPER` / outbound / dual-track / resolver | 不改默认 |
| 不新增 `USE_DOUDIAN_AUTOREPLY` 直至独立 Phase（Route D 之后） |

### 5.4 flag 默认值是否必须 false

**是。** `USE_DOUDIAN_CHANNEL_REGISTRATION` **必须** 默认 false，以保证：

- `python app.py` 启动后 Registry 仍只有 **pinduoduo**（+ 可选 demo）
- 与「不默认启动 Doudian」一致

---

## 6. AutoReply / factory 边界

### 6.1 `create_auto_reply_runtime_channel` — 继续 PDD-only（11a–11b）

| 问题 | 结论 |
|------|------|
| 是否应按 `account_data["channel_name"]` 路由？ | **否**（11a/11b）；属 Route D，独立 Phase + 新 flag |
| 11b 是否改此函数？ | **否** |
| 9d 语义 | 保持：Registry path = **`PlatformType.PINDUODUO` only** |

### 6.2 `AutoReplyThread` — 禁止默认创建 Doudian（11a–11b）

- 仍 `create_auto_reply_runtime_channel()`，**不传** platform。
- `platform_ui.is_autoreply_supported` 仍仅 `pinduoduo`（10b）；11a 不改 UI。

### 6.3 Doudian mock factory 应返回什么（11b 设计）

| 选项 | 建议 | 说明 |
|------|------|------|
| **仅 outbound** | ❌ 不足 | AutoReply / `BaseChannel` 需要 `start_account` 生命周期 |
| **无 runtime channel** | ❌ 无法 `Registry.create` 契约测 | |
| **`DoudianMockChannel`（推荐）** | ✅ 11b | 内存状态机；可选 `inject_runtime_flow` 调 `enqueue_doudian_raw_message`；`outbound` → `DoudianMockOutbound` |
| **真实 WS Channel** | ❌ | 11+ / 真实 API Phase |

**11b 最小 `DoudianMockChannel`：**

- 实现 `BaseChannel` 契约（仿 `DemoChannel`）
- **不** 连网；**不** 调 `pdd_lifecycle`
- `start_account` 可 no-op 或注入一条 fixture 入队（测试 flag）

### 6.4 是否需要 `DoudianMockChannel`

**11a：** 文档定义 **需要**（11b 交付）。  
**11a：** **不实现**。

---

## 7. 推荐路线

| 路线 | 内容 | 风险 | 阶段 |
|------|------|------|------|
| **A** | 11a 仅文档（本文） | 最低 | **11a ✅ 推荐** |
| **B** | 11a 文档 + flag 设计附录，无 `.py` | 低 | 可合并 A |
| **C** | 11b：`USE_DOUDIAN_CHANNEL_REGISTRATION=false` + `register_doudian_channel` + `DoudianMockChannel` | 中 | **11b** |
| **D** | AutoReply 按 platform 创建 channel | 高 | **12+**，需 `USE_DOUDIAN_AUTOREPLY` |
| **E** | 默认注册 Doudian / 改 factory 默认 | **禁止** | — |

**推荐顺序：** **11a (A)** → **11b (C)** → 11c outbound+channel 联调测试 → 12+ Route D 评估。

---

## 8. Phase 11a 最小安全范围

| 允许 | 禁止 |
|------|------|
| `docs/phase11a_plan.md`、`phase11a_done.md` | 任何 `.py` |
| 更新 architecture / README / phase10m_done | 改 `register_default_platforms` 默认 |
| SSOT：flag 名、边界、11b 清单 | 改 `autoreply_registry_flags` 默认 |
| | 改 `threads.py` / `channel_factory` 默认分支 |
| | 默认注册 Doudian |

---

## 9. 允许修改文件（11a）

```text
docs/phase11a_plan.md
docs/phase11a_done.md
docs/architecture_current.md
docs/README.md
docs/phase10m_done.md          # 可选 next step
docs/runtime_bootstrap 相关文档  # 可选脚注，非必须改 .py
```

---

## 10. 禁止修改文件（11a–11b 冻结，直至显式 Phase）

```text
Channel/pinduoduo/**
Channel/pinduoduo/core/pdd_lifecycle.py
Channel/pinduoduo/core/pdd_message_handler.py
Message/core/consumer.py
Message/handlers/**
Message/autoreply_registry_flags.py    # 9d 默认语义
ui/auto_reply/threads.py               # AutoReply 默认入口
ui/**                                  # 10b 守卫
database/**
app.py                                 # 11b 才可选扩展 register_default_platforms（flag 内）
channel_factory.create_auto_reply_runtime_channel  # 默认分支（11b 仍不改）

# 11a 禁止
Channel/doudian/doudian_factory.py     # 11b 才新增
Channel/doudian/doudian_mock_channel.py

# 始终禁止（直至真实 API Phase）
真实 Doudian SDK / WS / login
```

**11b 允许（Route C）：**

- `Channel/doudian/doudian_factory.py`
- `Channel/doudian/doudian_mock_channel.py`（或 `mock_channel.py`）
- `Channel/doudian/doudian_flags.py` 或扩展 `Message/bootstrap_flags.py`
- `Message/runtime_bootstrap.py` — **仅** 在 `use_doudian_channel_registration()` 为真时注册
- `tests/test_doudian_registry*.py`
- `Message/runtime_capabilities.py` / `diagnose_runtime` — 可选列出 doudian

---

## 11. 测试方案

### 11a（无代码）

- 评审本文与 10j §6.10 registry 设计一致性。

### 11b（规划）

| 测试 | 内容 |
|------|------|
| `test_doudian_registry_factory.py` | flag off → `create(DOUDIAN)` raises；flag on + `register_doudian_channel` → `create` 返回 `DoudianMockChannel` |
| `test_register_default_platforms_doudian.py` | env `USE_DOUDIAN_CHANNEL_REGISTRATION=1` → planned 含 doudian；unset → 不含 |
| parity | PDD `register_default_platforms()` 仍注册 pinduoduo；`create_auto_reply_runtime_channel` 仍 `PINDUODUO` |
| 隔离 | 不启动真实 WS；不改 PDD 单测 |

**不测（11b）：** AutoReplyThread 端到端 Doudian（Route D）。

---

## 12. 文档更新方案

| 文件 | 动作 |
|------|------|
| `docs/phase11a_plan.md` | 本文 |
| `docs/phase11a_done.md` | 签收：纯文档、Route A |
| `docs/architecture_current.md` | Phase 11a/11b 行；Registry 图注 Doudian flag |
| `docs/README.md` | Phase 表 11a |
| `docs/phase10m_done.md` | next → 11a |
| `docs/release_checkpoint_phase9.md` | 可选脚注：9d 仅 PDD，Doudian 另 flag |

---

## 13. Phase 11b prompt

```text
继续 Phase 11b：Doudian flag-gated ChannelRegistry registration（Route C）。

先读：
- docs/phase11a_plan.md
- docs/phase11a_done.md
- Channel/demo/demo_factory.py、demo_channel.py
- Message/runtime_bootstrap.py、Message/bootstrap_flags.py
- Channel/pinduoduo/channel_factory.py
- Message/autoreply_registry_flags.py（只读，不改默认）

目标：
1. 新增 USE_DOUDIAN_CHANNEL_REGISTRATION（默认 false）
2. 新增 register_doudian_channel() + create_doudian_channel()
3. 新增 DoudianMockChannel（BaseChannel，内存，可选 inject_runtime_flow 仿 Demo）
4. register_default_platforms：仅 flag true 时注册 doudian
5. list_available_platforms / get_bootstrap_status / diagnose 可选列出 doudian（test-only）
6. 不改 create_auto_reply_runtime_channel 默认（仍仅 PINDUODUO）
7. 不改 AutoReplyThread、UI、handlers、consumer、PDD 热路径
8. 测试：registry create + bootstrap plan + PDD parity

禁止：
- Route D/E：AutoReply 默认 Doudian、默认注册、真实 API
- 改 USE_CHANNEL_REGISTRY_FOR_AUTOREPLY 默认
- 改 channel_factory 中 create_auto_reply 的 platform 分支

验收：
python -m unittest discover -s tests -v
git diff 无 Channel/pinduoduo/** 行为变更
```

---

## 附录：问题清单速答（§1–12 映射）

| # | 结论 |
|---|------|
| 1 | 见 §2 |
| 2 | 应该，flag-gated（§4） |
| 3 | 11b 需要 `register_doudian_channel()`（§5.2） |
| 4 | 需要 `USE_DOUDIAN_CHANNEL_REGISTRATION`（§5.1） |
| 5 | 必须 false（§5.4） |
| 6 | 11b 返回 `DoudianMockChannel`，非仅 outbound（§6.3） |
| 7 | 11b 需要 `DoudianMockChannel`（§6.4） |
| 8 | AutoReply **不应**默认创建 Doudian（§6.2） |
| 9 | `create_auto_reply_runtime_channel` **继续 PDD-only**（§6.1） |
| 10 | **11a 只做文档**（Route A） |
| 11 | **11b 做 mock 注册更安全**（Route C） |
| 12 | 见 §10 |

---

*规划版本：Phase 11a · 2026-06-03 · docs only · Route A*

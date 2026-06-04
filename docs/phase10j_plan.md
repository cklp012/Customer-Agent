# Phase 10j 规划 — Second-Platform Spike Plan（Doudian 首选）

| 项 | 值 |
|----|-----|
| 类型 | **纯文档**（spike 计划 + 测试/fixture **设计**，本 Phase **不实现**） |
| 状态 | 规划（执行后见 [phase10j_done.md](phase10j_done.md)） |
| 前置 | [phase10i_plan.md](phase10i_plan.md)、[phase10i_done.md](phase10i_done.md) |
| 参考 spike | [phase8a_done.md](phase8a_done.md)（Demo runtime 模式） |
| 下一代码 Phase | **10k** — fixture + mapper contract tests（仍无真实 API） |

**文档导航：** [docs 目录](README.md) · [architecture_current.md](architecture_current.md) · [phase6a_plan.md](phase6a_plan.md) · [phase10c_done.md](phase10c_done.md)

---

## 1. 总体目标

在 **不接真实抖店 API、不改 PDD 默认路径** 的前提下，基于 [phase10i](phase10i_plan.md) capability matrix，为 **`doudian`（抖店）** 输出 **最小 second-platform spike 工作包**：

- 命名与队列隔离（`doudian_{shop_id}`）
- raw fixture、mapper、routing **设计**
- login / inbound transport / outbound **调研清单**
- registry / factory **未来设计**（非本 Phase 实现）
- 拟新增测试 **设计**（文件在 **10k** 才允许创建）
- Phase **11+** 生产门槛 checklist

**10j 不是 production integration。**

---

## 2. 为什么选择 doudian（抖店）

| 因素 | doudian | 说明 |
|------|---------|------|
| 产品形态 | 商家后台 + 飞鸽 IM | 与 PDD「店铺客服 + 实时消息」较接近，利于对照 [phase6a_plan.md §5](phase6a_plan.md) |
| 架构优先级 | 6a 已列 **抖店 > 京东 > 淘宝** | 与 [phase10i_plan.md §6](phase10i_plan.md) spike 矩阵一致 |
| 枚举与队列 | `PlatformType.DOUDIAN`、`build_queue_name("doudian", …)` | 已在 `Channel/base/types.py`、`Message/queue_naming.py` 预留 |
| UI | `platform_ui` 已有「抖店」显示名 | 10b 仅展示；spike 不改 UI 守卫 |
| 风险 | 开放平台需企业资质 | 适合先 **文档 + fixture spike**，再 11b 登录调研 |

**10j 交付物：** 抖店 spike SSOT，供 10k–10l 与 11+ 按同一契约实现。

---

## 3. 不选择 taobao / jingdong 作为本 spike 首选的原因

| 平台 | 相对 doudian | 10j 处理 |
|------|--------------|----------|
| **taobao（淘宝/千牛）** | 客户端形态更重（千牛桌面）；开放平台 ISV 审核周期长；与 PDD WS 差异大 | **推迟** — 11+ 可复用 10k–10l 的 mapper/queue 模式，单独 `taobao_*` fixture |
| **jingdong（京东/京麦）** | 6a 优先级第二；授权与 API 体系独立 | **推迟** — spike 矩阵在 10i 已定义 `jingdong_{shop_id}`，10j 不展开实现 |
| **demo** | 已完成 8a 内存 spike | **不重复** — doudian spike **仿 Demo 模式**，不替代 Demo |

**结论：** 10j 只 **深度规划 doudian**；taobao/jingdong 在本文 §6 gap matrix 保留一行对比，**不** 建 `Channel/taobao` / `Channel/jingdong` 目录。

---

## 4. Spike 与 production 的边界

| 维度 | Spike（10j 计划 → 10k–10l 代码） | Production（11+） |
|------|-----------------------------------|-------------------|
| API / SDK | ❌ 无真实 HTTP/WS | ✅ 开放平台 / 飞鸽协议 |
| 目录 | ❌ 无 `Channel/doudian/**` 生产实现（10j） | ✅ `DoudianChannel`、lifecycle 等 |
| 入站 | fixture + `enqueue_*` 测试（10l） | 真实 transport + lifecycle |
| 出站 | mock `DoudianOutbound` 设计（11c） | 真实发送 API |
| AutoReply | ❌ 不改 `threads.py` / factory 默认 | flag-gated 按 `channel_name`（11a） |
| PDD | 🔒 全程不变 | 🔒 并行路径，不替换 |
| Handler / Consumer | ❌ 不改默认链 | 可选平台化（独立 Phase） |

```text
10j (docs) → 10k (fixtures + mapper tests) → 10l (mock transport + enqueue flow)
          → 11a–11d (flag-gated factory, login, outbound mock, UI/DB)
          → 11+ production gate（真实 API，非默认 flag）
```

---

## 5. Doudian capability gap matrix

相对 [phase10i_plan.md §4 PDD](phase10i_plan.md#4-pdd-capability-matrix) 与 [§5 Demo](phase10i_plan.md#5-demo-capability-matrix)：

| 字段 | PDD | Demo | Doudian（10j 目标状态） |
|------|-----|------|-------------------------|
| platform_id | ✅ `pinduoduo` | 🧪 `demo` | 📋 **`doudian`** |
| inbound_transport | ✅ WS | 🧪 内存 | 📋 调研；10l mock |
| login_session | ✅ Playwright | 🧪 桩 | 📋 11b 调研 |
| raw_message_model | ✅ `PDDChatMessage` | 🧪 dict | 📋 fixture JSON（10k） |
| message_mapper | ✅ handler 内 | 🧪 `demo_raw_to_context` | 📋 `doudian_raw_to_context`（10k） |
| unified_mapper | 🧪 | 🧪 | 📋 `doudian_raw_to_unified`（10k） |
| routing_compute | ✅ `compute_pdd_routing` | ❌ | 📋 `compute_doudian_routing`（10k 草案） |
| queue_naming | ✅ `pdd_{shop_id}` | 🧪 `demo_{shop_id}` | 📋 **`doudian_{shop_id}`** |
| consumer_binding | ✅ lifecycle | 🧪 enqueue | 📋 10l mock enqueue |
| outbound_adapter | ✅/🧪 | 🧪 | 📋 11c mock |
| runtime_registration | ✅ PDD only | 🧪 | 📋 11a 设计 |
| production_autoreply | ✅ | ❌ | ❌ 直至 11+ gate |

---

## 6. 最小 spike 工作包

### 6.1 platform_id 选择与命名

| 项 | 约定 |
|----|------|
| **platform_id** | `doudian`（= DB `channel_name` = `PlatformType.DOUDIAN.value`） |
| **禁止** | 使用 `pdd` 前缀队列、`pinduoduo` 作为抖店 queue 前缀 |
| **文档别名** | 飞鸽 / 抖店商家后台 — 实现仍用 `doudian` |

### 6.2 queue_name 规则

```python
# SSOT（已实现于 Message/queue_naming.py，10k 测 parity）
build_queue_name("doudian", shop_id)  # → "doudian_{shop_id}"
```

| 规则 | 说明 |
|------|------|
| 格式 | `doudian_{shop_id}` |
| shop_id | 非 None、非空白（与 `build_queue_name` 一致） |
| 隔离 | 与 `pdd_{shop_id}` **物理隔离**；禁止混用 Consumer |
| PDD | **不修改** `pdd_{shop_id}` / `_lifecycle_pdd_queue_name` |

### 6.3 raw message fixture 设计（10k 实现）

建议路径（**10k 才创建文件**）：

```text
tests/fixtures/doudian/
  inbound_text.json          # 文本客服消息
  inbound_goods_inquiry.json # 商品咨询（若平台有）
  inbound_system.json        # 系统/通知类（routing=drop 候选）
  README.md                  # 字段说明、来源（合成，非生产抓包）
```

**Fixture 最小字段（草案）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `platform` | str | 固定 `"doudian"` |
| `message_id` | str | 平台消息 ID |
| `shop_id` | str | 测试用 `doudian_shop_spike_01` |
| `conversation_id` | str | 会话 ID |
| `buyer_uid` / `from_uid` | str | 买家标识 |
| `content_type` | str | snake：`text` / `image` / `unknown` |
| `content` | str / object | 正文或结构化体 |
| `timestamp` | int | 可选 |
| `native_type` | str | 原始类型码（mapping 用） |

**原则：** 合成数据；**不** 提交真实商家 cookie、token、抓包含 PII。

### 6.4 raw → Context mapper 设计（10k）

**拟路径：** `Channel/doudian/mappers/doudian_to_context.py`（10k 首建，仅 mapper + 无 transport）

**签名（仿 Demo）：**

```text
doudian_raw_to_context(
    raw: dict,
    shop_id: str,
    account_id: str,
    *,
    from_uid: str | None = None,
) -> Context
```

**契约：**

| 项 | 规则 |
|----|------|
| `Context.type` | 由 `content_type` 映射到 `ContextType`（未知 → `TEXT` 或 `UNKNOWN`，与 10c 一致） |
| `kwargs` | 含 `shop_id`, `user_id`（account）, `from_uid`, **`channel_type="doudian"`** |
| `channel_type` | 必须对齐 `PlatformType.DOUDIAN` / 10c platform SSOT |
| **禁止** | 修改 `bridge/`；不调用 PDD parser |

### 6.5 raw → UnifiedMessage mapper 设计（10k）

**拟路径：** `Channel/doudian/mappers/doudian_to_unified.py`

```text
doudian_raw_to_unified(raw, shop_id, account_id, *, from_uid=None) -> UnifiedMessage
```

| 字段 | 规则 |
|------|------|
| `platform` | `PlatformType.DOUDIAN` |
| `content_type` | 与 Context 侧词汇表一致（10c） |
| `routing` | 由 `compute_doudian_routing` 填入（或 mapper 内调用） |
| dual-track | 测试可 `USE_UNIFIED_MESSAGE_DUAL_TRACK=1`；**生产默认仍 off** |

### 6.6 routing 规则草案（10k 实现 `compute_doudian_routing`）

对齐 [phase10c_done.md §4](phase10c_done.md) 三值语义：

| routing | 条件（草案，10j 可调） | 行为 |
|---------|----------------------|------|
| **immediate** | 心跳、已读回执、无买家动作的 system ping | Channel 内即时处理（10l 可 no-op mock） |
| **queue** | 普通买家文本/商品咨询 | `enqueue` → `doudian_{shop_id}` |
| **drop** | 未知 `native_type`、空 content、店铺级广播 | 日志 + 不入队 |

**规划函数：**

```text
compute_doudian_routing(raw: dict) -> Literal["immediate", "queue", "drop"]
```

**禁止：** 在 `Message/handlers/**` 用 routing 改生产默认分支；handler 仍 `can_handle(Context.type)`。

### 6.7 outbound adapter 能力缺口

相对 `Channel/base/outbound.py`：

| 方法 | doudian spike 状态 | 说明 |
|------|-------------------|------|
| `send_text` | 📋 11c mock | 飞鸽发文本 API TBD |
| `send_image` | 📋 | 媒体上传策略调研 |
| `send_goods_card` | 📋 | 商品卡片格式调研 |
| `transfer_to_human` | 📋 | 转人工规则 |
| `fetch_products` | 📋 | 商品列表 API |
| `fetch_order` | 📋 | 订单查询 API |

**10j：** 仅 **缺口表**；**11c** 实现 `DoudianOutbound` mock（内存记录调用，无 HTTP）。

### 6.8 login / session 调研清单（11b，10j 只列项）

| # | 调研项 | 产出 |
|---|--------|------|
| L1 | 抖店开放平台 vs 飞鸽 IM 文档入口 | 链接归档 `docs/platforms/doudian_research.md`（11b） |
| L2 | 授权模式（OAuth / app_key / 店铺授权） | 序列图 |
| L3 | 会话材料（cookie / token / refresh） | 与 `account_data` 字段对照 |
| L4 | 多店铺 / 多客服账号绑定 | `shop_id` / `user_id` 语义 |
| L5 | Playwright 是否可行 vs 纯 API | 风险与合规 |
| L6 | 与 PDD `pdd_login` 隔离 | **不得** 复用 PDD Playwright 流程 |

### 6.9 inbound transport 调研清单（11+ / 10l mock）

| # | 调研项 | 产出 |
|---|--------|------|
| T1 | 推送方式：WS / 长轮询 / Webhook | 首选技术栈 |
| T2 | 连接参数（URL、鉴权头、心跳） | 对接 lifecycle 设计稿 |
| T3 | 消息 ACK / 重连 | 对标 `pdd_lifecycle` 阶段表 |
| T4 | 限流与幂等 | `message_id` 去重 |
| T5 | **10l mock** | `MockDoudianTransport` 推送 fixture 字典即可 |

### 6.10 registry / factory routing 未来设计（11a，10j 只文档）

```text
# 未来（非默认）伪代码 — 不在 10j/10k 改 channel_factory 默认
def create_auto_reply_runtime_channel(account_data, **kwargs):
    platform = normalize_channel_name(account_data.get("channel_name"))
    if platform == "pinduoduo":
        return _create_auto_reply_legacy(**kwargs)   # 仍默认
    if platform == "doudian" and use_doudian_autoreply():  # 新 flag，默认 false
        return ChannelRegistry.create(PlatformType.DOUDIAN, **kwargs)
    ...
```

| 项 | 说明 |
|----|------|
| 注册 | `ChannelRegistry.register(PlatformType.DOUDIAN, create_doudian_channel)` |
| 默认 | **9d 不变** — unset 仍 PDD legacy |
| UI | `is_autoreply_supported("doudian")` — **独立 Phase**（11d），10j 不放开 |

### 6.11 tests 设计（本 Phase 不创建文件）

见 §10。

### 6.12 不碰 PDD 默认路径的验证方式

| 验证 | 方法 |
|------|------|
| 代码 diff | `git diff` 无 `Channel/pinduoduo/**`、`pdd_lifecycle`、`pdd_message_handler` |
| 测试 | 全量 `unittest` 仍通过；**新增** 测试仅 `test_doudian_*`（10k+） |
| 队列 | 断言无测试注册 `pdd_*` 与 `doudian_*` 同 shop 混用 |
| flag | 不修改 `*_flags.py` 默认值；doudian 测试显式 setUp/tearDown env |
| 黄金路径 | 每 Phase 后跑 `docs/phase0_audit.md` PDD smoke（11+ gate） |

---

## 7. Fixture / mapper / routing 设计（汇总图）

```text
tests/fixtures/doudian/*.json
        │
        ▼
doudian_raw_to_context ──────────► Context (channel_type=doudian)
        │                                    │
doudian_raw_to_unified                     │
        │                                    ▼
        └────► UnifiedMessage ◄── compute_doudian_routing(raw)
                      │
                      ▼ (10l, dual_track optional in test)
              enqueue_inbound_message(queue_name=doudian_{shop_id})
                      │
                      ▼
              MessageConsumer → handlers (unchanged default)
```

---

## 8. Queue naming 设计

| 调用 | 结果 | 测试（10k） |
|------|------|-------------|
| `build_queue_name("doudian", "S1")` | `doudian_S1` | `test_doudian_queue_naming.py` |
| `build_queue_name(PlatformType.DOUDIAN, 123)` | `doudian_123` | 同 |
| `build_queue_name("doudian", "")` | `ValueError` | 同 |
| `build_queue_name("pinduoduo", "S1")` | `pdd_S1` | 回归：与 PDD 无关 |

**Lifecycle（11+）：** 拟 `DoudianLifecycleMixin` 使用 `build_queue_name("doudian", shop_id)` — **禁止** 复制 `_lifecycle_pdd_queue_name` 到 PDD 文件。

---

## 9. Outbound / login / inbound transport 调研清单

- **Outbound：** §6.7 缺口表 → 11c mock 实现顺序：`send_text` → `transfer_to_human` → 其余。
- **Login：** §6.8 L1–L6 → 11b 文档 `docs/platforms/doudian_research.md`。
- **Transport：** §6.9 T1–T5 → 10l `MockDoudianTransport` + 11+ 真实 WS。

---

## 10. Tests 设计（10j 不实现）

| 拟文件 | Phase | 内容 |
|--------|-------|------|
| `tests/test_doudian_queue_naming.py` | **10k** | `build_queue_name("doudian", …)` parity；不与 `pdd_*` 冲突 |
| `tests/test_doudian_mapper_contract.py` | **10k** | fixture → Context / UnifiedMessage；`platform`/`channel_type`/`content_type` SSOT |
| `tests/test_doudian_routing_parity.py` | **10k** | `compute_doudian_routing` 对 fixture 期望 immediate/queue/drop |
| `tests/test_doudian_spike_runtime_flow.py` | **10l** | mock transport → enqueue → Consumer（仿 `test_demo_runtime_flow`）；**不** 起真实 WS |

**10j 禁止：** 创建上述文件或 `tests/fixtures/doudian/`。

**测试环境：**

- 不调用真实登录 / WS / 开放平台 HTTP。
- dual-track / outbound resolver：仅测试方法内临时设置 env，默认 unset。

---

## 11. PDD 保护清单（10j–10l 冻结）

| 路径 / 行为 | 要求 |
|-------------|------|
| `Channel/pinduoduo/core/pdd_lifecycle.py` | 不修改 |
| `Channel/pinduoduo/core/pdd_message_handler.py` | 不修改 |
| `Message/core/consumer.py` | 不修改 |
| `Message/handlers/**` | 不修改 |
| `*_flags.py` 默认值 | 不修改（含 9d registry、dual-track、outbound resolver） |
| `Channel/pinduoduo/channel_factory.py` **默认行为** | 不修改 |
| `ui/auto_reply/threads.py` | AutoReply 默认仍 PDD 入口 |
| **queue** | 生产仍为 **`pdd_{shop_id}`** |
| `app.py` / `database/**` | 不修改 |

---

## 12. Phase 11+ production gate checklist

以下条件 **全部满足** 后，才可规划「真实 doudian 生产试点」（非默认 flag）：

| # | 门槛 |
|---|------|
| G1 | **API 调研完成** — `docs/platforms/doudian_research.md` 评审通过 |
| G2 | **login/session 可测** — 11b 沙箱或 mock 账号可刷新 token |
| G3 | **inbound transport mock 通过** — 10l `test_doudian_spike_runtime_flow` 绿 |
| G4 | **mapper contract 通过** — 10k 全 fixture 覆盖 |
| G5 | **queue isolation 通过** — `doudian_*` 与 `pdd_*` 同进程无串队列 |
| G6 | **outbound adapter mock 通过** — 11c 调用记录与 handler 联调 |
| G7 | **flag-gated runtime registration** — 11a 显式 env 才 `Registry.create(DOUDIAN)` |
| G8 | **UI/DB 独立 Phase** — 11d 放开 `is_autoreply_supported` / seed channel |
| G9 | **PDD golden path smoke** — `phase0_audit` / 真实 PDD 店回归 |
| G10 | **无 PDD 默认漂移** — diagnose 显示 dual-track/resolver 仍 false（unset） |

---

## 13. 后续 Phase 拆分建议

| Phase | 范围 | 真实 API |
|-------|------|----------|
| **10k** | `tests/fixtures/doudian/` + `Channel/doudian/mappers/*` + `test_doudian_queue_naming` + `test_doudian_mapper_contract` + `test_doudian_routing_parity` | ❌ |
| **10l** | `MockDoudianTransport` + `enqueue_doudian_message`（或泛化 enqueue）+ `test_doudian_spike_runtime_flow` | ❌ |
| **11a** | flag-gated `ChannelRegistry` + `create_doudian_channel` 工厂；**默认仍 PDD** | ❌ |
| **11b** | login/session spike（文档 + 可选 Playwright 调研分支） | 沙箱 only |
| **11c** | `DoudianOutbound` mock（内存） | ❌ |
| **11d** | UI 筛选 / DB seed / `is_autoreply_supported("doudian")` | ❌ |
| **11+** | 真实 WS/API lifecycle + 生产试点 | ✅（非默认） |

**依赖链：** 10j (docs) → 10k → 10l → 11a → 11b/11c 可并行 → 11d → 11+ gate。

---

## 14. 禁止修改文件

```text
# 10j 允许
docs/phase10j_plan.md
docs/phase10j_done.md
docs/architecture_current.md
docs/README.md
docs/phase10i_done.md   # 可选 next step

# 10j 禁止（与 10i 一致 + 10j 不加测试）
**/*.py
tests/**
Channel/pinduoduo/**
Channel/doudian/**      # 10j 不建；10k 才允许 mappers/fixtures
Channel/taobao/**
Channel/jingdong/**
Message/core/consumer.py
Message/handlers/**
ui/**
database/**
app.py
```

---

## 附录：与 Demo spike（8a）对照

| 项 | Demo (8a) | Doudian spike |
|----|-----------|---------------|
| platform_id | `demo` | `doudian` |
| queue | `demo_{shop_id}` | `doudian_{shop_id}` |
| mapper 路径 | `Channel/demo/mappers/` | `Channel/doudian/mappers/`（10k） |
| enqueue | `enqueue_demo_message` | 拟 `enqueue_doudian_message`（10l） |
| 生产 | 明确非生产 | 11+ 才讨论生产 |

---

*规划版本：Phase 10j · 2026-06-03 · docs only · doudian spike*

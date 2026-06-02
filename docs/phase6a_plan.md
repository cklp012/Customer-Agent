# Phase 6a：第二平台 Adapter 规划

| 项 | 值 |
|---|---|
| 完成范围 | **仅规划文档**（本文件） |
| 状态 | Phase 6a 交付 |
| 下一里程碑 | Phase 6b — `DemoChannel` / `MockCommerceChannel`（见 §8） |
| 相关基线 | [architecture_current.md](architecture_current.md)、[phase1_done.md](phase1_done.md) |

**文档导航：** [docs 目录](README.md) · [当前架构](architecture_current.md)

---

## 1. 目标与范围

### 1.1 Phase 6a 目标

在**不写业务代码**的前提下，明确：

- 当前 `Channel/base` 能否承载第二平台；
- 拼多多已落地模式哪些可复用、哪些为 PDD 专有；
- 淘宝 / 抖店 / 京东的接入差异与风险；
- **Phase 6b** 应做什么、禁止做什么。

### 1.2 本 Phase 明确不做

- 不新增 `Channel/demo/` 或 `Channel/taobao/` 等代码目录（留给 Phase 6b）；
- 不接淘宝 / 抖店 / 京东真实登录、消息、发送；
- 不修改 `app.py`、`ui/`、`Message/`、`Channel/pinduoduo/`、`bridge/`、`tests/`。

---

## 2. 当前 Channel/base 就绪度与缺口

### 2.1 已具备（Phase 1 + PDD Strangler）

| 组件 | 路径 | 就绪度 | 说明 |
|------|------|--------|------|
| 平台枚举 | `Channel/base/types.py` → `PlatformType` | ✅ | 含 `PINDUODUO`、`TAOBAO`、`DOUYIN`、`JINGDONG` 及预留 `QIANNIU`、`DOUDIAN`、`JINGMAI` 等 |
| 连接状态 | `ChannelStatus` | ✅ | 与 `core.connection_status` 语义对齐 |
| Channel 契约 | `Channel/base/channel.py` → `BaseChannel` | ✅ | `login` / `logout` / `start_account` / `stop_account` / `reconnect` / `outbound` |
| 出站契约 | `Channel/base/outbound.py` → `ChannelOutbound` | ✅ | `send_text` / `send_image` / `send_goods_card` / `transfer_to_human` / `fetch_products` / `fetch_order` |
| 统一模型（数据类） | `Channel/base/models.py` | ✅ | `UnifiedMessage` / `UnifiedConversation` / `UnifiedReply` |
| 工厂注册表 | `Channel/base/registry.py` → `ChannelRegistry` | ✅ | `register` / `create` / `registered_platforms` |
| PDD 参考实现 | `PinduoduoChannel` / `PinduoduoOutbound` | ✅ | Strangler 包装 + 出站适配器（生产路径，默认 flag off） |

### 2.2 缺口（接第二平台「可运行自动回复」前仍需）

| 缺口 | 影响 | 建议阶段 |
|------|------|----------|
| `UnifiedMessage` 未接入 `MessageConsumer` | 入站仍走 `Context` + `PDDChatMessage` | Phase 7 |
| `outbound_resolver` 仅拼多多 | handler 无法平台无关解析 outbound | Phase 7 |
| `ChannelRegistry` 未在 `app.py` 启动时注册 PDD | UI 仍 `import PDDChannel`，非 `Registry.create` | Phase 7+ / 产品化 |
| `bridge.context.ChannelType` 无 `DEMO` | Demo 平台需 6b 扩展枚举或复用测试专用值 | Phase 6b |
| 账号表 / UI 无「平台」维度 | 无法在同一 GUI 选第二平台账号 | Phase 8 或更晚 |
| 各平台登录 / WS / API 未调研落地 | 真实第二平台无法开工 | 独立 spike（6b 之后） |

### 2.3 结论

**足够支持 Phase 6b：** 第二个 `BaseChannel` + `ChannelOutbound` 实现、`ChannelRegistry` 多平台注册、单元测试验证契约。

**不足以支持：** 不改 UI/Handler 的前提下，让淘宝/抖店/京东与 PDD 并列生产运行。

---

## 3. PinduoduoChannel / PinduoduoOutbound 可复用清单

以下**设计模式**可在第二平台（或 Demo）中复用；实现时复制结构，不复制 PDD 代码。

| 模式 | 参考位置 | 复用方式 |
|------|----------|----------|
| **Strangler 包装器** | `PinduoduoChannel` 委托 `PDDChannel` | 新平台若有 legacy 客户端，用 `XxxChannel` 包装；Demo 用内存状态机代替 legacy |
| **出站适配器** | `PinduoduoOutbound` 实现 `ChannelOutbound` | `XxxOutbound` 包装平台 SDK/HTTP；`asyncio.to_thread` 包装同步 API |
| **发送结果归一化** | `PinduoduoOutbound._normalize_send_result` | 各平台 API 返回格式不一，统一为 `bool` |
| **懒加载出站实例** | `outbound` 在 `start_account` 后可用 | 按 `shop_id` + `account_id` 构造 outbound |
| **工厂 + 注册** | `channel_factory.create_*` + `register_pinduoduo_channel()` | `create_demo_channel()` + 测试内 `ChannelRegistry.register` |
| **AutoReply 统一启动签名** | `start_auto_reply_account()` | 6b 不接入 AutoReply；Phase 7 再考虑多平台 factory |
| **账号级 registry** | `AccountOutboundRegistry` + `PinduoduoChannel` start/stop | 仅 PDD 生产使用；第二平台需 **新 resolver 或泛化**（Phase 7），6b 不扩展 |
| **Feature flag 切换** | `USE_PINDUODUO_CHANNEL_WRAPPER` / `USE_PINDUODUO_OUTBOUND` | 新平台应用独立 flag；**禁止**复用 PDD flag 语义 |

---

## 4. PDD 专有逻辑不可复用清单

以下逻辑**不得**在 Phase 6b 中拷贝到 Demo 或第二平台通用层；第二平台需独立实现或 Phase 7 抽象。

| 专有项 | 路径 / 说明 | 原因 |
|--------|-------------|------|
| WebSocket 连接与心跳 | `Channel/pinduoduo/core/pdd_connection.py` 等 | 协议与 PDD 商家后台绑定 |
| 消息解析与入队 | `pdd_message_handler.py`、`PDDChatMessage` | 字段与 PDD 报文结构绑定 |
| Playwright 登录 | `pdd_login.py` | PDD 商家后台 URL / 表单 |
| MMS 发送 | `utils/API/send_message.py` | PDD cookie + 接口 |
| 商品同步 | `product_manager.py` | PDD 商品模型（分、驼峰字段等） |
| 即时消息「[玫瑰]」 | `pdd_message_handler` 撤回/转接 | PDD 业务规则 |
| `outbound_resolver` / `extract_pdd_send_context` | `Message/handlers/outbound_resolver.py` | 硬编码 PDD metadata 键 |
| `PinduoduoKwargs` / `ChannelType.PINDUODUO` | `bridge/context.py` | Context 模型偏 PDD |
| PDD feature flags | `channel_flags.py`、`outbound_flags.py` | 仅控制 PDD Strangler |

**Phase 6b 硬约束：** 不修改上表任何路径；PDD 默认路径（双 flag off）行为保持不变。

---

## 5. 淘宝 / 抖店 / 京东比较表

> 下表为**规划级**对比，用于选型；非已验证 API 清单。实施前须查阅平台最新开放平台文档与商家协议。

| 维度 | 淘宝 / 千牛 (QianNiu) | 抖店 / 飞鸽 (DouDian / Feige) | 京东 / 京麦 (Jingmai) |
|------|------------------------|-------------------------------|------------------------|
| **项目枚举** | `PlatformType.TAOBAO`、`QIANNIU` | `DOUYIN`、`DOUDIAN` | `JINGDONG`、`JINGMAI` |
| **典型客户端** | 千牛桌面 / 卖家中心 | 抖店商家后台、飞鸽客服 | 京麦、商家后台 |
| **官方开放能力** | 淘宝开放平台（偏 ISV 应用、OAuth、需审核） | 抖店开放平台（企业资质、应用授权） | 京东开放平台（ISV、授权体系） |
| **登录** | 难：客户端绑定、验证码、设备指纹 | 中：后台 Web 登录，形态接近电商 SaaS | 难：类似淘宝，京麦封闭 |
| **消息接收** | 难：无面向第三方克隆客服的公开 WS 文档 | 中–难：飞鸽 API/事件需调研 | 难：京麦协议不开放 |
| **文本发送** | 需千牛或开放 API；非 ISV 路径不清晰 | 飞鸽/订单 IM API 待调研 | 开放 API 或京麦内嵌 |
| **图片发送** | 中 | 中 | 中 |
| **商品卡片** | 淘宝卡片模板与 PDD 不同 | 短视频/直播间商品卡片 | SKU / 促销结构不同 |
| **转人工** | 千牛客服组规则复杂 | 飞鸽会话分配规则 | 京麦工单/客服组 |
| **订单查询** | 开放平台订单 API（需授权） | 抖店订单 API | 京东订单 API |
| **风控 / 反自动化** | **很高** | 高 | 高 |
| **无授权 API 时** | 仅 skeleton + 文档；**不宜** 6b 真实接入 | 同上；**优先作为第一个真实平台调研对象** | 同上 |
| **作为 Phase 6b 代码目录** | **不推荐首选** | 不推荐（仅调研） | 不推荐（仅调研） |

### 5.1 第一个真实平台调研优先级（Phase 6b 之后）

1. **抖店 / 飞鸽** — 商家后台 + IM 形态与 PDD 相对接近，开放平台文档可调研。  
2. **京东 / 京麦** — B2C 成熟，ISV 路径清晰，但桌面端封闭。  
3. **淘宝 / 千牛** — 市场最大，但非 ISV 自动化风险最高，放最后。

---

## 6. 合规边界

本项目第二平台集成**只讨论**以下合法路径：

| 允许 | 禁止 |
|------|------|
| 平台**官方开放平台**上已文档化的 API，且商家/ISV **明确授权** | 未授权协议逆向、抓包破解千牛/京麦私有协议 |
| 商家在**自有后台**登录后，由商家自愿提供、本地存储的会话（须符合平台 ToS） | 绕过验证码、滑块、设备指纹、风控策略 |
| 规划文档中的能力对比与架构设计 | 保存或提交真实 **token、密码、cookie 样本** 到仓库 |
| Phase 6b `DemoChannel` 内存假数据 | 编写「规避平台检测」类自动化方案 |

**若无可用官方接口：** Phase 6b **只能**做 `DemoChannel` 类 mock，不得假装已接真实平台。

---

## 7. Phase 6b 路线推荐

### 7.1 推荐：Route A — `DemoChannel` / `MockCommerceChannel`

| 优点 | 说明 |
|------|------|
| 风险最低 | 无网络、无凭证、无 ToS 争议 |
| 验证目标明确 | `ChannelRegistry` 多平台、`BaseChannel` + `ChannelOutbound` 契约 |
| 符合约束 | 不碰 PDD WS/登录、不改 `app.py`/UI |
| 与 architecture §8 一致 | 「skeleton + register，不接 UI」 |

### 7.2 不推荐：Route B — Phase 6b 首选 `TaobaoChannel` 空壳

| 缺点 | 说明 |
|------|------|
| 几乎全是 `NotImplementedError` | 无 API 调研则无实质代码 |
| 误导进度 | 目录存在 ≠ 第二平台可交付 |
| 淘宝真实接入最难 | 空壳对团队学习价值低于 Demo |

**若需「命名占位」：** 可在 `docs/platforms/taobao_research.md`（未来）写调研笔记，**不在 6b 建** `Channel/taobao/` 代码。

### 7.3 PlatformType 扩展（6b 范围）

- **6a：** 不修改枚举。  
- **6b 建议：** 仅新增 `PlatformType.DEMO`（或 `MOCK`），与 `TAOBAO` / `DOUDIAN` 等真实平台区分。  
- **不必**在 6b 为淘宝/抖店/京东新增重复枚举值（已预留）。

---

## 8. Phase 6b 最小实现规格（规划锁定，待实施）

### 8.1 最小文件清单

```text
Channel/demo/
  __init__.py
  demo_channel.py       # BaseChannel：内存状态，fake start/stop
  demo_outbound.py      # ChannelOutbound：no-op / 记录调用 / 固定返回值
  demo_factory.py       # create_demo_channel() + register_demo_channel()
tests/
  test_demo_channel.py
  test_channel_registry_multi.py   # PINDUODUO + DEMO 同册 register（测试 bootstrap）
docs/
  phase6b_done.md       # 6b 完成后撰写
```

### 8.2 行为约定

| 项 | 约定 |
|----|------|
| `DemoChannel.platform` | `PlatformType.DEMO` |
| `start_account` | 内存置 `CONNECTED`；**默认**不注入消息；可选测试 flag 下调用 `on_message` 一次 synthetic 数据 |
| `stop_account` | 状态 `DISCONNECTED`；清理 outbound |
| `DemoOutbound.send_*` | 写入内存 `sent_log`，返回 `True`（或文档约定之 stub） |
| `fetch_products` / `fetch_order` | 返回固定 JSON，不访问网络 |
| Registry | **仅单元测试**内 `register_demo_channel()`；**不**在 `app.py` 注册 |
| AutoReply | **不**修改 `ui/auto_reply/threads.py`；**不**新增 `USE_DEMO_CHANNEL` 生产 flag |

### 8.3 明确不做（6b）

- 不接淘宝 / 抖店 / 京东任何 HTTP / WebSocket / Playwright  
- 不修改 `Message/handlers/outbound_resolver.py` 或 `ai_handler` / `keyword_handler`  
- 不修改 `Channel/pinduoduo/**`（含 WS、login、`pdd_message_handler`）  
- 不修改 `app.py`、`ui/`、`config.py`、`bridge/`（除非 Phase 7 单独立项）  
- 不移除 PDD legacy fallback  
- 不保存敏感 token / 密码  

---

## 9. 允许 / 禁止修改路径

### 9.1 Phase 6a（已完成）

| 允许 | 禁止 |
|------|------|
| `docs/phase6a_plan.md`（本文件） | 一切代码目录 |
| `docs/README.md`（Phase 索引一行） | `README.md`（仓库根） |
| `docs/architecture_current.md`（§7、§8） | `docs/runbook.md`、`docs/runtime_modes.md` |

### 9.2 Phase 6b（未来）

| 允许 | 禁止 |
|------|------|
| `Channel/demo/**`（新建） | `Channel/pinduoduo/**` |
| `Channel/base/types.py`（仅 `DEMO` 枚举） | `app.py`、`ui/**`、`Message/**`、`bridge/**` |
| `tests/test_demo_*.py`、`tests/test_channel_registry_multi.py` | `scripts/diagnose_runtime.py`（可选后续） |

---

## 10. 风险点

| 风险 | 说明 | 缓解 |
|------|------|------|
| Demo 与生产脱节 | Demo 不验证真实 WS/登录 | 文档标明 Demo 非生产；真实平台走独立 spike |
| 过早建 Taobao 空壳 | 目录存在推高错误预期 | 6b 仅 Demo；淘宝只保留规划表 |
| 误改 PDD 路径 | 6b 动 `pinduoduo` 破坏默认行为 | PR 路径审查；全量 unittest |
| Registry 与 UI 双轨 | 注册表有多平台，UI 仍仅 PDD | architecture §7 写明；7+ 再统一 |
| 合规 | 逆向千牛/京麦 | §6 边界；Code review |
| Unified 未接线 | 6b 不进 handler 链 | 单测直调 `DemoOutbound` |

---

## 11. 测试方案

### 11.1 Phase 6a

- 文档评审：本文件 §2–§9 完整；无代码 diff。

### 11.2 Phase 6b（规划）

| 类型 | 内容 |
|------|------|
| 单元 | `ChannelRegistry.create(DEMO)`；`isinstance(outbound, ChannelOutbound)` |
| 多平台注册 | 测试内同时 `register_pinduoduo_channel()` + `register_demo_channel()`，`registered_platforms()` 含两者 |
| 行为 | `send_text` 后 `sent_log` 有记录；`stop_account` 后 `get_status` 为 `DISCONNECTED` |
| 回归 | `python -m unittest discover -s tests -v` 全绿，PDD 用例无行为变化 |
| 不做 | GUI E2E、真实店铺、网络请求 |

---

## 12. 推迟到 Phase 7+ 的事项

| 项 | 建议阶段 | 说明 |
|----|----------|------|
| `UnifiedMessage` mapper + Consumer 接入 | Phase 7 | `PDDChatMessage` → `UnifiedMessage` |
| 泛化 `outbound_resolver` 或每平台 resolver | Phase 7 | handler 平台无关出站 |
| `app.py` / UI 平台选择、`ChannelRegistry` 启动注册 | Phase 7–8 | 产品化 |
| 抖店 / 京东 / 淘宝 **真实** Channel + Outbound | 6b 之后 spike | 需 API 调研 + 商家授权模型 |
| Phase 5b 统一 bool 解析 | 可选 | 与 6b 独立 |
| Phase 4c metadata outbound 镜像 | 暂缓 | 非阻塞 |
| `diagnose_runtime` 打印 `registered_platforms` | 6c 可选 | 只读增强 |
| 设置页运行模式 / 多平台账号 | Phase 8 | 产品 |

---

## 13. 接第二平台前的门禁（不变）

1. PDD **wrapper-and-outbound** 模式在测试店跑通 [phase0_audit.md](phase0_audit.md) 黄金路径（建议）。  
2. 完成 Phase 6b `DemoChannel`，全量单测通过。  
3. 选定真实平台后，先写 **调研文档**（授权方式、API 列表、限制），再开 `Channel/{platform}/` 代码。

---

## 14. 相关文档

| 文档 | 用途 |
|------|------|
| [architecture_current.md](architecture_current.md) | 架构基线、§7 边界、§8 路线图 |
| [phase1_done.md](phase1_done.md) | Channel/base 初版交付 |
| [README.md](README.md) | 文档目录与 Phase 索引 |

---

*Phase 6a 仅规划；Phase 6b 实施时以本节 §8 为范围契约，如有变更须更新 `phase6b_done.md` 与 architecture §8。*

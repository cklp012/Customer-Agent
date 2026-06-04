# Phase 11h 规划 — Doudian Mock Spike Hardening / Production Gate Review

| 项 | 值 |
|----|-----|
| 类型 | **纯文档 SSOT**（mock spike 收口 + production gate；**非 production integration**） |
| 状态 | 执行后见 [phase11h_done.md](phase11h_done.md) |
| 范围 | Phase **10k–11g** Doudian mock spike 全链路 |
| 前置 | [phase11g_done.md](phase11g_done.md) |
| 后续 | **Phase 12a+** — research/design gate（真实 API **默认 off**） |

**文档导航：** [phase10i_plan.md](phase10i_plan.md) · [phase10j_plan.md](phase10j_plan.md) · [architecture_current.md](architecture_current.md)

---

## 1. Phase 11h 总体目标

Phase 11h 是对 **10k–11g Doudian mock spike** 的 **收口评审（hardening review）** 与 **进入真实抖店集成前的 production gate 定义**。

**本 Phase 是：**

- 能力矩阵签收
- 非 production 原因冻结
- PDD 默认路径安全复核
- Phase 12 research/design 拆分

**本 Phase 不是：**

- 真实 Doudian API / login / WS 集成
- handler / AutoReply / Consumer 默认行为变更
- 任何 `.py` 或测试变更

```text
10j (plan) → 10k–10m (mock spike code) → 11a–11g (registry/resolver/handler tests)
         → 11h (gate review, docs only)
         → 12a+ (research/design, still default-off)
         → 13+ (real API prototype, flag-gated, non-default)
```

---

## 2. Doudian mock spike 已完成能力矩阵

| # | 能力 | Phase | 状态 | 交付物 / 测试 |
|---|------|-------|------|----------------|
| 1 | **Fixture** | 10k | ✅ 🧪 | `tests/fixtures/doudian_messages/`（text / product_inquiry / system_notice） |
| 2 | **raw → Context mapper** | 10k | ✅ 🧪 | `doudian_raw_to_context`；drop 返回 None |
| 3 | **raw → UnifiedMessage mapper** | 10k | ✅ 🧪 | `doudian_raw_to_unified`（dual-track 默认 off，未生产接入） |
| 4 | **routing** | 10k | ✅ 🧪 | `compute_doudian_routing`：text/product_inquiry→queue；system_notice→drop |
| 5 | **queue naming** | 10k | ✅ 🧪 | `build_queue_name("doudian", shop)` → `doudian_{shop_id}`；与 `pdd_*` 隔离 |
| 6 | **mock inbound transport** | 10l | ✅ 🧪 | `DoudianMockTransport`（内存，无网络） |
| 7 | **enqueue runtime flow** | 10l | ✅ 🧪 | `enqueue_doudian_raw_message`；测试 patch 入队；**无 Consumer 线程** |
| 8 | **mock outbound** | 10m | ✅ 🧪 | `DoudianMockOutbound` → `sent_messages` |
| 9 | **flag-gated ChannelRegistry** | 11b | ✅ 🧪 | `USE_DOUDIAN_CHANNEL_REGISTRATION`（**默认 false**）；`DoudianMockChannel` |
| 10 | **outbound resolver contract** | 11c | ✅ 🧪 | `resolve_outbound` + `channel_outbound_registry`；R1–R7 |
| 11 | **channel lifecycle outbound auto-registration** | 11e | ✅ 🧪 | `start_account` register / `stop_account` unregister；L1–L6 |
| 12 | **handler unified outbound test path** | 11g | ✅ 🧪 | `test_handler_doudian_unified_outbound.py`；**仅测试内** unified flag |

**符号：** ✅ 🧪 = spike/测试已交付，**非 production**。

### 10k–11g 闭环（mock）

```text
fixtures
  → mappers + routing
  → mock transport → enqueue_doudian_raw_message (patch)
  → DoudianMockOutbound (sent_messages)
  → [optional] DoudianMockChannel.start_account → channel_outbound_registry
  → resolve_outbound (11c)
  → [test-only] AIReplyHandler._send_reply + USE_UNIFIED_OUTBOUND_RESOLVER=true (11g)
```

**仍缺（production）：** 真实 inbound transport、login/session、send API、DB/UI 多平台运营、AutoReply 按 platform 路由、真实店铺 smoke。

---

## 3. 当前仍非 production 的原因

| 类别 | 说明 |
|------|------|
| **无真实 Doudian API** | 无开放平台 HTTP/SDK 调用；无飞鸽 IM 协议 |
| **无真实 login/session** | 无 OAuth/扫码/cookie 刷新；`DoudianMockChannel.login` 恒 true |
| **无真实 WS/webhook/polling** | `DoudianMockTransport` 为内存桩；未接 lifecycle 生产线程 |
| **无真实 send API** | `DoudianMockOutbound` 仅写 `sent_messages` |
| **无真实账号 DB/UI 运营** | UI 仍非 PDD AutoReply 可用；无抖店账号 seed/登录流 |
| **AutoReply 默认 PDD-only** | `create_auto_reply_runtime_channel()` 仍 **仅** `PINDUODUO` |
| **Doudian 默认不注册** | `USE_DOUDIAN_CHANNEL_REGISTRATION` unset → **false** |
| **unified resolver 默认 off** | `USE_UNIFIED_OUTBOUND_RESOLVER` unset → **false**；handler 默认 `resolve_pinduoduo_outbound` |
| **未做真实店铺 smoke** | 无抖店测试店端到端；PDD 黄金路径仍独立维护 |
| **Consumer 未平台化** | 生产 Consumer 仍 PDD metadata 路径；抖店 enqueue 仅测试 patch |
| **无 production release checklist 签收** | 11h 定义 gate；**12+** 才逐项 research/design |

**结论：** 10k–11g 完成的是 **架构验证 spike**，不是 **可运营的第二平台自动回复**。

---

## 4. PDD protection review

| 检查项 | 结论 | 依据 |
|--------|------|------|
| PDD queue 仍为 `pdd_{shop_id}` | ✅ | 10h lifecycle + `pdd_queue_name`；抖店用 `doudian_*` |
| `pdd_lifecycle` 未被 Doudian 修改 | ✅ | 10k–11g 未改 `Channel/pinduoduo/**` |
| `pdd_message_handler` 未改 | ✅ | spike 独立 `Channel/doudian/mappers/` |
| `MessageConsumer` 默认行为未改 | ✅ | 抖店 enqueue 测试 patch，无生产接线 |
| handlers 默认 PDD legacy resolver | ✅ | `USE_UNIFIED_OUTBOUND_RESOLVER` 默认 false |
| AutoReply 默认 PDD-only | ✅ | `channel_factory` 未按 `channel_name` 路由 Doudian |
| `USE_DOUDIAN_CHANNEL_REGISTRATION` 默认 false | ✅ | 11b flag + bootstrap 测试 |
| `USE_UNIFIED_OUTBOUND_RESOLVER` 默认 false | ✅ | 8c + 11g default 测试 |
| 抖店未注册时不回落 PDD outbound | ✅ | 11c R5；`resolve_outbound` 非 PDD → None |
| PDD 平台仍委托 `resolve_pinduoduo_outbound` | ✅ | 11c R6；unified resolver 设计 |

**PDD production：Go — 继续保持默认路径，抖店 spike 与之并行、不替换。**

---

## 5. Production gate checklist

进入 **真实 Doudian 集成**（Phase 13+ prototype）前，须逐项 **research/design 签收**（Phase 12）。默认 **全部 No-Go** 直至显式 flag + smoke。

| ID | Gate | Phase 12 建议 | 说明 |
|----|------|---------------|------|
| **G1** | Doudian API 文档调研 | **12a** | 开放平台、飞鸽 IM、消息/发送/会话 API 清单；权限与资质 |
| **G2** | login/session 方案 | **12b** | OAuth vs cookie vs 扫码；token 刷新；多账号隔离 |
| **G3** | inbound transport 方案 | **12c** | WS vs webhook vs 长轮询；与 `pdd_lifecycle` 对标设计 |
| **G4** | real outbound send 方案 | **12d** | 真实 send_text/transfer；与 `DoudianMockOutbound` 接口对齐 |
| **G5** | token/cookie 存储安全 | **12b/12e** | 加密 at rest、日志脱敏、env/密钥管理 |
| **G6** | account model / DB migration | **12e** | `channel_name`、shop/account 语义；与 10a 对齐 |
| **G7** | UI 支持设计 | **12e** | 10b 骨架 → 抖店登录/启动 AutoReply 守卫与 UX |
| **G8** | flag-gated real `DoudianChannel` | **12f** | 新 flag；默认 off；与 mock 并存或替换策略 |
| **G9** | PDD golden path smoke | **12+ 并行** | `phase0_audit` #3–#8 回归；抖店 work **不得** 破坏 PDD |
| **G10** | rollback plan | **12f** | flag off → 纯 PDD；registry/bootstrap 清理 |
| **G11** | rate limit / retry / error handling | **12c/12d** | 429/5xx、断线重连、消息幂等 |
| **G12** | observability / logs / redaction | **12+** | 结构化日志、7i 脱敏延续、发送/会话 trace |

**Gate 规则：** 每项 **docs + 评审** 先于 **默认-on 代码**；prototype 仅 **flag-gated + 测试店**。

---

## 6. Phase 12 拆分建议

| Phase | 类型 | 内容 |
|-------|------|------|
| **12a** | docs | Doudian real API research（G1） |
| **12b** | docs | login/session design（G2, G5 部分） |
| **12c** | docs | real inbound transport design（G3, G11 部分） |
| **12d** | docs | real outbound send design（G4, G11 部分） |
| **12e** | docs | DB/UI multi-platform production plan（G6, G7） |
| **12f** | docs | flag-gated real Doudian prototype planning（G8, G10） |
| **13+** | code（flag off） | 真实 API prototype；**禁止** 默认注册/默认 unified |

**与历史项关系：**

- **10d+**（AutoReply 按 `channel_name` 路由 factory）→ 并入 **12e/12f** 设计，仍 **默认 PDD**
- **11+ 真实第二平台** → 重命名为 **12–13** 序列，11h 为 mock 收口

---

## 7. Go / No-Go 结论

| 对象 | 结论 | 说明 |
|------|------|------|
| **Doudian mock spike（10k–11g）** | **Go — 已完成** | 契约、registry、resolver、lifecycle、handler 测试链齐全 |
| **Doudian production integration** | **No-Go** | 仅可进入 **Phase 12 research/design**；无真实 API/login/WS/smoke |
| **PDD production 默认路径** | **Go — 保持** | queue、lifecycle、handler、AutoReply 默认未变 |

---

## 8. 禁止修改文件清单

Phase 11h 及 Phase 12 **research 阶段** 默认禁止（除非未来 Phase 显式批准）：

```text
Channel/pinduoduo/**          # PDD 热路径
pdd_lifecycle / pdd_message_handler
MessageConsumer               # 默认行为
Message/handlers/**           # 默认 resolver 分支
*_flags.py                    # 默认值
AutoReplyThread / channel_factory 默认 PDD 路径
ui/** / database/**           # 无 12e 前生产变更
app.py                        # 无新 platform 默认 bootstrap
真实 Doudian API / SDK / WS / webhook
默认 USE_UNIFIED_OUTBOUND_RESOLVER=true
默认 USE_DOUDIAN_CHANNEL_REGISTRATION=true
默认注册 Doudian 到 ChannelRegistry
改变 PDD queue：仍为 pdd_{shop_id}
```

---

## 附录：10k–11g Phase 索引

| Phase | 要点 |
|-------|------|
| 10k | fixture + mappers + routing + queue tests |
| 10l | mock transport + enqueue |
| 10m | mock outbound |
| 11a | registry/factory 边界（docs） |
| 11b | flag-gated ChannelRegistry |
| 11c | resolver contract tests |
| 11d | auto-register 规划 |
| 11e | channel lifecycle register |
| 11f | handler test 边界（docs） |
| 11g | handler unified outbound tests |

---

*规划版本：Phase 11h · 2026-06-03 · docs only · mock spike closed*

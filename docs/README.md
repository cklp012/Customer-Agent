# Customer-Agent 文档目录

本项目正在从拼多多单平台客服改造为**多平台电商 AI 客服工作台**。当前**运行时仅拼多多**；`Channel/base` 为多平台预留，尚未接入淘宝 / 抖店 / 京东。

**文档导航：** [运行手册](runbook.md) · [当前架构](architecture_current.md) · [运行模式](runtime_modes.md) · **[Phase 9 发布检查点](release_checkpoint_phase9.md)** · [Phase 0 审计](phase0_audit.md)

---

## 新开发者 5 分钟路径

按顺序阅读即可回答「是什么、怎么启、架构在哪、模式怎么切、怎么诊断、各 Phase 交付在哪、下一步做什么」：

1. **项目是什么** — 仓库根 [README.md](../README.md) 功能概览 + 本文「核心文档」
2. **怎么启动** — [runbook.md](runbook.md)（安装、`uv sync` / pip、`python app.py`、Playwright、PDD 账号）
3. **当前架构** — [architecture_current.md](architecture_current.md)（模块职责、legacy / 新链路、边界）
3b. **Phase 9 发布快照** — [release_checkpoint_phase9.md](release_checkpoint_phase9.md)（8a–9d 默认路径、flag、回滚）
3c. **多平台账号模型** — [phase10_account_model.md](phase10_account_model.md)（`channel_name` = platform_id；运行时仍仅 PDD）
3d. **消息 routing SSOT** — [phase10c_plan.md](phase10c_plan.md) / [phase10c_done.md](phase10c_done.md)（Context-first；dual-track 默认 off）
4. **运行模式** — [runtime_modes.md](runtime_modes.md)（`USE_PINDUODUO_*` 四组合、Registry 默认 on）
5. **怎么诊断环境** — 见下方「运维与诊断」；细节见 [runtime_modes.md §6](runtime_modes.md#6-诊断脚本) 与 [runbook.md §运行模式](runbook.md#运行模式高级可选)
6. **各 Phase 交付记录** — 见下方「Phase 交付索引」
7. **后续开发从哪开始** — 见下方「后续开发」；路线图以 [architecture_current.md §8](architecture_current.md#8-后续建议路线) 为准

---

## 核心文档

| 文档 | 用途 |
|------|------|
| [runbook.md](runbook.md) | 本机安装、启动、最小配置、PDD 登录、冒烟与故障排查 |
| [architecture_current.md](architecture_current.md) | **架构基线（SSOT）**：目标、Phase 0–5a 完成情况、默认/新链路、模块表、风险与路线图 |
| [runtime_modes.md](runtime_modes.md) | **运行模式（SSOT）**：两个 flag、四种组合、PowerShell 示例、回退 |
| [phase0_audit.md](phase0_audit.md) | Phase 0 审计、GUI 验证、**黄金路径** #3–#8（真实 PDD 测试店） |
| [release_checkpoint_phase9.md](release_checkpoint_phase9.md) | **Phase 9 发布检查点**（8a–9d 默认行为、回滚、验证） |
| [phase10_account_model.md](phase10_account_model.md) | **Phase 10 账号模型 SSOT**（UI 规划、契约、平台能力矩阵） |

---

## 运维与诊断

不启动 GUI、不连接拼多多时，检查 Python、flag 解析、模式名与关键 import：

```powershell
cd D:\agent
python scripts/diagnose_runtime.py
```

说明与输出含义见 [runtime_modes.md §6](runtime_modes.md#6-诊断脚本)。脚本实现见 `scripts/diagnose_runtime.py`（本 Phase 不改脚本）。

---

## Phase 交付索引

各阶段**交付记录**（历史 WHY/WHEN）；架构总览以 [architecture_current.md](architecture_current.md) 为准。

| Phase | 文档 | 要点 |
|-------|------|------|
| **0** | [phase0_audit.md](phase0_audit.md) | 审计、环境、GUI、黄金路径清单 |
| **1** | [phase1_done.md](phase1_done.md) | `Channel/base` 多平台骨架 |
| **2a** | [phase2a_done.md](phase2a_done.md) | `PinduoduoOutbound` 出站适配器 |
| **2b** | [phase2b_done.md](phase2b_done.md) | `ai_handler` / `keyword_handler` outbound-first |
| **2c** | [phase2c_done.md](phase2c_done.md) | `pdd_message_handler` 即时「[玫瑰]」outbound-first |
| **3a** | [phase3_done.md](phase3_done.md) | `PinduoduoChannel` 包装 legacy `PDDChannel` |
| **3b** | [phase3b_done.md](phase3b_done.md) | `AutoReplyThread` + `USE_PINDUODUO_CHANNEL_WRAPPER` |
| **4a** | [phase4a_done.md](phase4a_done.md) | `outbound_resolver` + registry + create fallback |
| **4b** | [phase4b_done.md](phase4b_done.md) | `PinduoduoChannel` start/stop 注册 registry |
| **5a** | [phase5a_done.md](phase5a_done.md) | `runtime_modes.md` + `diagnose_runtime.py` + runbook |
| **5.5** | [architecture_current.md](architecture_current.md) | 当前架构基线文档（非 `phase*_done` 命名） |
| **5.6** | 本文档 | 文档入口索引 |
| **6a** | [phase6a_plan.md](phase6a_plan.md) | 第二平台 Adapter 规划（DemoChannel 推荐、平台比较、6b 范围） |
| **6b** | [phase6b_done.md](phase6b_done.md) | `DemoChannel` + `ChannelRegistry` 双平台单测（非生产） |
| **7a** | [phase7a_plan.md](phase7a_plan.md) | UnifiedMessage mapper 规划（PDD 链路、映射表、7b–8 分期） |
| **7b** | [phase7b_done.md](phase7b_done.md) | `pdd_to_unified` mapper + fixtures + 单测（未接运行时） |
| **7c** | [phase7c_done.md](phase7c_done.md) | `USE_UNIFIED_MESSAGE_SHADOW` 旁路 log（默认 off） |
| **7d** | [phase7d_done.md](phase7d_done.md) | 双轨入队 `MessageWrapper.unified_message`（默认 off，handler 仍 Context） |
| **7e** | [phase7e_done.md](phase7e_done.md) | `metadata_adapter` 统一读取（handler 未改） |
| **7f** | [phase7f_done.md](phase7f_done.md) | `extract_pdd_send_context` 委托 `get_send_context_for_extract`（handler 未改） |
| **7g** | [phase7g_done.md](phase7g_done.md) | `metadata_observability` 安全观测 helper（handler 未改） |
| **7h** | [phase7h_done.md](phase7h_done.md) | handler `handle()` 入口 safe debug；keyword content debug 清理 |
| **7i** | [phase7i_done.md](phase7i_done.md) | INFO 敏感日志清理（BaseHandler / ai reply / CatchAllHandler） |
| **7j** | [phase7j_done.md](phase7j_done.md) | WARNING/DEBUG UID 脱敏（ai / keyword / outbound_resolver） |
| **8a** | [phase8a_done.md](phase8a_done.md) | Demo platform runtime spike（测试级双轨入队 + Consumer） |
| **8b** | [phase8b_done.md](phase8b_done.md) | unified outbound resolver + channel registry |
| **8c** | [phase8c_done.md](phase8c_done.md) | handler 接入 `resolve_outbound`（UNIFIED flag 默认 off） |
| **8d** | [phase8d_done.md](phase8d_done.md) | runtime diagnostics / capability report |
| **8e** | [phase8e_done.md](phase8e_done.md) | ChannelRegistry bootstrap API |
| **8f** | [phase8f_done.md](phase8f_done.md) | app.py 启动一行 registry bootstrap |
| **9a** | [phase9_done.md](phase9_done.md) | AutoReply `USE_CHANNEL_REGISTRY_FOR_AUTOREPLY` 门控 Registry.create |
| **9b** | [phase9b_done.md](phase9b_done.md) | `create_pinduoduo_registry_channel` parity factory |
| **9c** | [phase9c_done.md](phase9c_done.md) | Registry path parity tests |
| **9d** | [phase9d_done.md](phase9d_done.md) | AutoReply Registry 默认 on；`false` 回滚 |
| **9e** | [phase9e_done.md](phase9e_done.md) | Release checkpoint（[主文档](release_checkpoint_phase9.md)） |
| **10a** | [phase10a_done.md](phase10a_done.md) | 多平台 account model 规划（[SSOT](phase10_account_model.md)） |
| **10b** | [phase10b_done.md](phase10b_done.md) | AutoReply UI skeleton（筛选、非 PDD 禁用启动） |
| **10c** | [phase10c_done.md](phase10c_done.md) | routing / content_type / platform SSOT（[规划](phase10c_plan.md)） |
| **10d** | [phase10d_done.md](phase10d_done.md) | 契约测试锁定 10c（routing parity + platform contract） |
| **10e** | [phase10e_done.md](phase10e_done.md) | queue 命名与 Consumer 边界（[规划](phase10e_plan.md)，纯文档） |
| **10f** | [phase10f_done.md](phase10f_done.md) | `build_queue_name` helper（PDD 仍 `pdd_{shop_id}`，lifecycle 未接入） |
| **10g** | [phase10g_done.md](phase10g_done.md) | `pdd_queue_name` + legacy parity（lifecycle 未接入） |
| **10h** | [phase10h_done.md](phase10h_done.md) | lifecycle Route C：`pdd_lifecycle` + lifecycle-safe wrapper，队列名仍为 `pdd_{shop_id}` |
| **10i** | [phase10i_done.md](phase10i_done.md) | capability matrix + 第二平台 spike 边界（[规划](phase10i_plan.md)，纯文档） |
| **10j** | [phase10j_done.md](phase10j_done.md) | doudian second-platform spike 计划（[规划](phase10j_plan.md)，纯文档） |
| **10k** | [phase10k_done.md](phase10k_done.md) | doudian fixture + mapper contract tests（无真实 API） |
| **10l** | [phase10l_done.md](phase10l_done.md) | doudian mock transport + enqueue runtime flow（patch 入队） |
| **10m** | [phase10m_done.md](phase10m_done.md) | doudian mock outbound（`DoudianMockOutbound`） |
| **11a** | [phase11a_done.md](phase11a_done.md) | Doudian registry/factory 边界规划（[规划](phase11a_plan.md)，纯文档） |
| **11b** | [phase11b_done.md](phase11b_done.md) | `USE_DOUDIAN_CHANNEL_REGISTRATION` + `DoudianMockChannel`（默认不注册） |
| **11c** | [phase11c_done.md](phase11c_done.md) | Doudian outbound resolver 契约测试（[规划](phase11c_plan.md)，Route B） |
| **11d** | [phase11d_done.md](phase11d_done.md) | Doudian channel outbound auto-registration 规划（[规划](phase11d_plan.md)，纯文档） |
| **11e** | [phase11e_done.md](phase11e_done.md) | `DoudianMockChannel` outbound auto-registration（[规划](phase11e_plan.md)） |
| **11f** | [phase11f_done.md](phase11f_done.md) | Handler unified outbound 测试边界规划（[规划](phase11f_plan.md)，纯文档） |
| **11g** | [phase11g_done.md](phase11g_done.md) | Doudian handler unified outbound path tests（[规划](phase11g_plan.md)） |
| **11h** | [phase11h_done.md](phase11h_done.md) | Doudian mock spike gate review（[规划](phase11h_plan.md)，纯文档） |
| **12a** | [phase12a_done.md](phase12a_done.md) | 商家 UX / 绑定 / 安全 Preview / MVP 套餐（产品化 SSOT，纯文档） |
| **12b** | [phase12b_done.md](phase12b_done.md) | SaaS 数据模型：Merchant/Workspace/ShopBinding/CredentialRef（纯文档） |
| **12b.1** | [phase12b1_done.md](phase12b1_done.md) | Consultation-only 产品边界：售前咨询副驾驶、intent/send gate SSOT（纯文档） |
| **12c** | [phase12c_done.md](phase12c_done.md) | Intent gate + SendDecision + Preview dry-run 技术设计（纯文档，implementation 未开始） |
| **12d** | [phase12d_done.md](phase12d_done.md) | Dashboard IA + Connection/Reply read model + Alert + API contract（纯文档） |
| **12e** | [phase12e_done.md](phase12e_done.md) | DB migration planning：shadow-first product gate schema（纯文档） |
| **12f** | [phase12f_done.md](phase12f_done.md) | Preview send gate implementation plan：`send_text_guarded`、H0–H6、T1–T12（纯文档） |
| **13a** | [phase13a_done.md](phase13a_done.md) | Product gate 纯函数 + 单元测试（`Message/gates/`） |
| **13b** | [phase13b_done.md](phase13b_done.md) | Shadow SendDecision logging（观察-only，fail-open，不改变发送） |
| **13c** | [phase13c_done.md](phase13c_done.md) | 单测试店 Preview gate **规划**（docs only） |
| **13d** | [phase13d_done.md](phase13d_done.md) | 单测试店 Preview gate **实现**（allowlist · zero-send · in-memory preview log） |
| **13e** | [phase13e_done.md](phase13e_done.md) | Preview ReplyLog **projection** + Dashboard read model bridge（in-memory） |
| **13f** | [phase13f_done.md](phase13f_done.md) | **Assisted mode 规划**（docs only；商家确认后发送 · A1–A12 · auto 未实现） |
| **9–10** | [phase9_plan.md](phase9_plan.md) / [phase8_plan.md](phase8_plan.md) | Registry / 多平台规划 |

---

## 后续开发

| 优先级 | 建议 |
|--------|------|
| **默认开发 / 交付** | 不设置环境变量 → Registry 创建 + `legacy-default`（`PDDChannel` + `SendMessage`）；见 [release_checkpoint_phase9.md](release_checkpoint_phase9.md) |
| **新架构联调** | `USE_PINDUODUO_CHANNEL_WRAPPER=true` 且 `USE_PINDUODUO_OUTBOUND=true` → `wrapper-and-outbound`；先用 `diagnose_runtime.py` 确认模式 |
| **接第二平台前** | 10b UI 已禁用非 PDD 启动；真实 WS / Thread 路由 → 独立 spike + 10c+ |
| **明确不做（当前）** | Phase 5b 统一 bool 解析、接淘宝/抖店/京东运行时、Phase 4c consumer metadata 镜像 — 见 architecture §7 |

---

## 维护约定

完成新 Phase 时：

1. 新增或更新对应的 `docs/phase*_done.md`（或更新 `architecture_current.md` 基线）
2. 在本文 **Phase 交付索引** 表增加或修订一行
3. 若里程碑影响架构总览，同步更新 [architecture_current.md](architecture_current.md) §2 / §8

Phase 明细**只在本表集中维护**；各 `phase*_done.md` 正文无需互链。

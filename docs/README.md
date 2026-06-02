# Customer-Agent 文档目录

本项目正在从拼多多单平台客服改造为**多平台电商 AI 客服工作台**。当前**运行时仅拼多多**；`Channel/base` 为多平台预留，尚未接入淘宝 / 抖店 / 京东。

**文档导航：** [运行手册](runbook.md) · [当前架构](architecture_current.md) · [运行模式](runtime_modes.md) · [Phase 0 审计](phase0_audit.md)

---

## 新开发者 5 分钟路径

按顺序阅读即可回答「是什么、怎么启、架构在哪、模式怎么切、怎么诊断、各 Phase 交付在哪、下一步做什么」：

1. **项目是什么** — 仓库根 [README.md](../README.md) 功能概览 + 本文「核心文档」
2. **怎么启动** — [runbook.md](runbook.md)（安装、`uv sync` / pip、`python app.py`、Playwright、PDD 账号）
3. **当前架构** — [architecture_current.md](architecture_current.md)（模块职责、legacy / 新链路、边界）
4. **运行模式** — [runtime_modes.md](runtime_modes.md)（`USE_PINDUODUO_*` 四组合、回退）
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

---

## 后续开发

| 优先级 | 建议 |
|--------|------|
| **默认开发 / 交付** | 不设置环境变量 → `legacy-default`（`PDDChannel` + `SendMessage`） |
| **新架构联调** | `USE_PINDUODUO_CHANNEL_WRAPPER=true` 且 `USE_PINDUODUO_OUTBOUND=true` → `wrapper-and-outbound`；先用 `diagnose_runtime.py` 确认模式 |
| **接第二平台前** | 在真实 PDD 测试店跑通 [phase0_audit.md](phase0_audit.md) 黄金路径；6b Demo 仅验证契约，下一步见 [architecture_current.md §8](architecture_current.md#8-后续建议路线) Phase 7 |
| **明确不做（当前）** | Phase 5b 统一 bool 解析、接淘宝/抖店/京东运行时、Phase 4c consumer metadata 镜像 — 见 architecture §7 |

---

## 维护约定

完成新 Phase 时：

1. 新增或更新对应的 `docs/phase*_done.md`（或更新 `architecture_current.md` 基线）
2. 在本文 **Phase 交付索引** 表增加或修订一行
3. 若里程碑影响架构总览，同步更新 [architecture_current.md](architecture_current.md) §2 / §8

Phase 明细**只在本表集中维护**；各 `phase*_done.md` 正文无需互链。

# Phase 12e — Migration Sequence M0–M9（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 原则 | **不能一次性替换 legacy DB** · **不能默认 auto** · **不能默认 product gate** |

---

## 总览

| 阶段 | 名称 | 代码 | 发送路径 |
|------|------|------|----------|
| **M0** | docs only | ❌ | legacy |
| **M1** | shadow tables | 新增表，无读写 | legacy |
| **M2** | ShopBinding projection | 投影 job | legacy |
| **M3** | CredentialRef shadow | 加密指针 | legacy |
| **M4** | SendDecision shadow log | gate off 也写 | legacy |
| **M5** | Preview test shop | gate on + preview | gated zero-send |
| **M6** | Assisted internal | approve API | gated |
| **M7** | Auto allowlist test | 高置信 allow only | gated |
| **M8** | Dashboard read shadow | API 读新表 | 混合 |
| **M9** | legacy cleanup optional | 退役计划 | 产品决策 |

---

## M0 — Docs only（当前 Phase 12e）

| 项 | 内容 |
|----|------|
| **scope** | 本交付物；评审 SSOT |
| **flags** | 无变更 |
| **PDD** | 完全不变 |
| **tests** | 无 |
| **rollback** | N/A |
| **go/no-go** | 文档评审通过 → M1 |

---

## M1 — 新增 shadow tables

| 项 | 内容 |
|----|------|
| **scope** | CREATE TABLE merchants, workspaces, shop_bindings, …；**空表** |
| **flags** | 无运行时读 |
| **PDD** | AutoReply 仍只读 legacy |
| **tests** | migration 单测：表存在、默认约束 preview/false |
| **rollback** | DROP new tables |
| **go/no-go** | 表结构符合 12e schema 文档 |

**禁止：** 改 `database/models.py` legacy 类（可新文件 `saas_models.py`）。

---

## M2 — legacy → ShopBinding projection

| 项 | 内容 |
|----|------|
| **scope** | 定时/启动时 `accounts`+`shops`+`channels` → `shop_bindings` |
| **defaults** | `reply_mode=preview`, `product_gate_enabled=false`, `consultation_only=true` |
| **flags** | `SAAS_PROJECTION_ENABLED` default **false** |
| **PDD** | 队列、handler、SendMessage **不变** |
| **tests** | 投影行数 = PDD account 数；字段映射 |
| **rollback** | flag off；TRUNCATE shop_bindings |
| **go/no-go** | 投影不阻塞启动；legacy 登录仍可用 |

---

## M3 — CredentialRef shadow

| 项 | 内容 |
|----|------|
| **scope** | 从 `accounts.cookies` 写 `credential_refs`（加密）；UI **不展示**明文 |
| **flags** | `CREDENTIAL_REF_WRITE` default false |
| **PDD** | 登录仍写 legacy cookies 列（双写可选） |
| **tests** | 加密 round-trip；无 plaintext leak |
| **rollback** | 停双写；读 legacy only |
| **go/no-go** | 安全评审 |

---

## M4 — SendDecision shadow logging

| 项 | 内容 |
|----|------|
| **scope** | handler 旁路写 `send_decisions`；`product_gate_enabled=false` |
| **flags** | `SHADOW_SEND_DECISION_LOG` default false |
| **PDD** | **发送路径不变** |
| **tests** | 每条入站（可选采样）有 decision 行；`allowed_to_send` 与 **实际** send 可不一致（标注 shadow） |
| **rollback** | flag off |
| **go/no-go** | 性能 <5ms 增量 p99 |

---

## M5 — Preview test shop only

| 项 | 内容 |
|----|------|
| **scope** | **选定 1 店** `product_gate_enabled=true`, `reply_mode=preview` |
| **flags** | 店铺级，非全局 |
| **PDD** | 该店 **T10 zero-send**；其他店 legacy |
| **tests** | T1, T10 通过；patch SendMessage |
| **rollback** | `product_gate_enabled=false` |
| **go/no-go** | 7 天无买家误收 AI 消息 |

**Preview logs：** `send_status=not_sent_preview`；`auto_sent_count` 不增加。

---

## M6 — Assisted internal test

| 项 | 内容 |
|----|------|
| **scope** | 内部店 `reply_mode=assisted` + approve API |
| **flags** | gate on |
| **tests** | T4；无 approve 不 send |
| **rollback** | 回 preview |
| **go/no-go** | audit_log 有 approve 记录 |

---

## M7 — Auto allowlist limited test

| 项 | 内容 |
|----|------|
| **scope** | 内部店 `reply_mode=auto` + allowlist intent only |
| **flags** | gate on；**禁止** 全量商家 |
| **tests** | T2, T3, T5 |
| **rollback** | pause + preview |
| **go/no-go** | blocked intent 零 auto send；二次确认 audit 存在 |

**禁止：** 默认开启 auto；不能绕过 intent gate。

---

## M8 — Dashboard read shadow

| 项 | 内容 |
|----|------|
| **scope** | 12d API 读 `shop_bindings` + `usage_meters` + queue |
| **flags** | `DASHBOARD_READ_SAAS` |
| **PDD** | 发送仍按 M5–M7 策略 |
| **tests** | API contract 契约测；effective_status 正确 |
| **rollback** | 读 legacy 占位数据 |
| **go/no-go** | 与 shadow 日志一致 |

---

## M9 — Legacy cleanup（可选 · 远期）

| 项 | 内容 |
|----|------|
| **scope** | 评估退役 `accounts.password` 列；知识库 FK 迁 `shop_binding_id` |
| **flags** | 分模块 |
| **PDD** | **必须** 回归黄金路径 |
| **rollback** | 保留 legacy 表只读备份 |
| **go/no-go** | 董事会 + 商家公告 |

**Doudian：** 仅当 future API Phase 完成前 **不得** M9 标 production connected。

---

## Feature flags 汇总（建议名 · 均默认 false/off）

| Flag | 阶段 |
|------|------|
| `SAAS_PROJECTION_ENABLED` | M2 |
| `CREDENTIAL_REF_WRITE` | M3 |
| `SHADOW_SEND_DECISION_LOG` | M4 |
| `product_gate_enabled` (per shop) | M5+ |
| `DASHBOARD_READ_SAAS` | M8 |

**非 env 替代：** `product_gate_enabled` 存 **ShopBinding 列**（12c SSOT）；env 仅开发 override。

---

## PDD 保护清单（每阶段）

| 检查 | 要求 |
|------|------|
| Queue name | `pdd_{shop_id}` |
| AutoReplyThread | 不删不改行为除非 M5+ 单店 |
| `USE_UNIFIED_OUTBOUND_RESOLVER` | 默认 false |
| Doudian registration | 默认 false |
| Legacy db_manager | M8 前主路径 |

---

## Tests required（按阶段）

| 阶段 | 测试 |
|------|------|
| M1 | schema contract |
| M2 | projection parity |
| M4 | decision row count |
| M5–M7 | phase12c T1–T10 |
| M8 | API + effective_status |
| 全程 | T8 gate off legacy parity |

---

*Phase 12e · Migration Sequence · docs only*

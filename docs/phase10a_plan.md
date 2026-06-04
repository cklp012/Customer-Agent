# Phase 10a 规划 — 多平台 UI / Account Model

| 项 | 值 |
|---|---|
| 状态 | 交付见 [phase10a_done.md](phase10a_done.md) |
| SSOT | [phase10_account_model.md](phase10_account_model.md) |

---

## 1. 目标

为 Phase 10（多平台产品化）建立 **账号模型与 UI 信息架构** 的单一事实来源（SSOT），在 **不接真实第二平台、不改变 PDD 默认行为** 的前提下，说明现状、契约与后续 10b 路线。

---

## 2. 范围

| In | Out |
|----|-----|
| `phase10_account_model.md`（主 SSOT） | 任何 `.py` |
| `phase10a_plan.md` / `phase10a_done.md` | `ui/`、`database/` 改动 |
| 同步 `architecture_current.md`、`docs/README.md` | DB migration |
| 可选更新 `release_checkpoint_phase9.md`、`phase6a_plan.md` | 真实平台 WS / 登录 |

---

## 3. 禁止项

- `app.py`、`ui/**`、`database/**`、`Channel/**`、`Message/**`、`bridge/**`
- `tests/**`、`scripts/**`、各 `*_flags.py`
- 改 `AutoReplyThread`、`channel_factory`、PDD 内核、handlers、consumer
- 注册真实第二平台；默认 Demo；改 Phase 9d 默认

---

## 4. 当前 UI / account model 分析

### 4.1 数据层（已具备多平台 schema）

- `channels.channel_name` = 平台 ID。
- `shops` / `accounts` 通过 FK 挂在渠道下。
- `get_all_accounts_with_details()` 已 JOIN 并输出 `channel_name`。

### 4.2 UI 层（展示有、运行无）

| 页面 | 平台维度 | 自动回复 |
|------|----------|----------|
| 账号管理 `user_ui` | badge + 按渠道加载 | — |
| 自动回复 `auto_reply` | badge + key 含 `channel_name` | **仅 PDD 工厂** |

### 4.3 缺口（相对「多平台自动回复」）

- `AutoReplyThread` 不读 `channel_name` 选择 factory。
- 非 PDD 账号若入库，可能被误点启动（10b 用 UI 守卫解决）。

详见 [phase10_account_model.md §2–6](phase10_account_model.md).

---

## 5. PDD binding points

汇总表见 [phase10_account_model.md §7](phase10_account_model.md#7-current-pdd-binding-points)。

**10a 结论：** 全部标注为「不在本 Phase 修改」。

---

## 6. 推荐 account model

- **canonical 字段：** `channel_name`（DB + `account_data`）。
- **文档别名：** `platform_id` = `channel_name` = `PlatformType.value`。
- **account_key：** 保持 `{channel_name}_{shop_id}_{username}`。
- **能力矩阵：** 见 SSOT §6；生产仅 `pinduoduo` 可 AutoReply。

---

## 7. Phase 10b 入口

下一编码 Phase：**UI skeleton only**

- 平台筛选；非 PDD 禁用「开始回复」；UI 层不调用 `start_auto_reply`。
- **不改** `threads.py` 内 PDD factory 逻辑。

Prompt 摘要见 [phase10a_done.md](phase10a_done.md).

---

## 8. 分期（Phase 10 总览）

| 阶段 | 内容 |
|------|------|
| **10a** ✅ | 本文档 + SSOT（仅规划） |
| **10b** | UI skeleton + 守卫 |
| **10c** | routing / content_type 规划（可选并行） |
| **独立 spike** | 抖店/京东/淘宝 协议 + Channel 实现 |
| **10d+** | `AutoReplyThread` 按 platform 路由（flag 门控，默认 PDD） |

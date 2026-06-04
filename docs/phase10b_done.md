# Phase 10b 完成记录 — 多平台 AutoReply UI Skeleton

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| SSOT 更新 | [phase10_account_model.md](phase10_account_model.md) §9 |

---

## 1. 代码变更

| 文件 | 变更 |
|------|------|
| `ui/auto_reply/platform_ui.py` | **新增** — 展示名、筛选、自动回复支持判断 |
| `ui/auto_reply/ui.py` | 平台筛选 ComboBox；可见列表；UI 层 `start` 守卫 |
| `ui/auto_reply/card.py` | 平台 badge 中文名；非 PDD 禁用自动回复按钮 |
| `tests/test_auto_reply_platform_ui.py` | **新增** — helper 单测 |

**未改：** `threads.py`、`manager.py`（逻辑未变）、`channel_factory.py`、`database/**`。

---

## 2. 行为摘要

| 场景 | 行为 |
|------|------|
| 平台筛选 | 全部 / 拼多多（可选）；抖店/京东/淘宝 为 **disabled** 占位 |
| 非 `pinduoduo` | 「开始回复」disabled；Tooltip「该平台自动回复即将支持」 |
| 启动守卫 | `onAutoReplyToggle` / `_start_auto_reply` / 「开始所有」不调用 `start_auto_reply` |
| `pinduoduo` | 与 Phase 9d 相同：`AutoReplyManager` → `AutoReplyThread` → registry 默认路径 |

---

## 3. 明确未做

- 不接淘宝 / 抖店 / 京东 WS
- 不 seed 第二平台账号
- 不改 `AutoReplyThread` / registry 默认 / legacy fallback

---

## 4. 下一步（10c / spike）

- 真实平台协议 spike（6a 优先级）
- `AutoReplyThread` 按 `channel_name` 路由（flag，默认 PDD）
- routing / `content_type` 规划（10c）

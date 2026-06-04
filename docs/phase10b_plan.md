# Phase 10b 规划 — 多平台 AutoReply UI Skeleton

| 项 | 值 |
|---|---|
| 前置 | [phase10_account_model.md](phase10_account_model.md)（10a SSOT） |
| 交付 | [phase10b_done.md](phase10b_done.md) |

---

## 1. 目标

在自动回复页增加**多平台展示与筛选骨架**，对非拼多多账号**禁止启动**自动回复；**不改变** PDD 运行时（`threads.py` / `channel_factory` / Phase 9d）。

---

## 2. 范围

| In | Out |
|----|-----|
| `ui/auto_reply/platform_ui.py` helper | `ui/auto_reply/threads.py` |
| `ui/auto_reply/ui.py` 筛选 + guard | `Channel/**`、`Message/**` |
| `ui/auto_reply/card.py` badge + 禁用按钮 | DB migration / seed |
| `tests/test_auto_reply_platform_ui.py` | 真实第二平台 WS |

---

## 3. 禁止项

与 [phase10_account_model.md §10](phase10_account_model.md) 一致；10b **仅** UI + 纯逻辑测试 + 文档。

---

## 4. 实现要点

1. **platform_ui**：`platform_display_name`、`is_autoreply_supported`、`PLATFORM_FILTER_OPTIONS`。
2. **AutoReplyUI**：ComboBox 筛选；`_guard_autoreply_start`；「开始所有」仅 PDD + 可见列表。
3. **AutoReplyCard**：中文平台 badge；非 PDD 禁用「开始回复」+ Tooltip。
4. **PDD**：`start_auto_reply` 调用链与 9d 一致（manager/thread 未改）。

---

## 5. 验收

- `python -m unittest discover -s tests -v` 全绿
- `git diff` 不含禁止路径

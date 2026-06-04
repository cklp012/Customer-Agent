# Phase 10m 规划 — Doudian Mock Outbound

| 项 | 值 |
|----|-----|
| 类型 | mock outbound + 单测 |
| 前置 | [phase10l_done.md](phase10l_done.md) |
| 后续 | **11a** flag-gated registry/factory |

---

## 1. 目标

`DoudianMockOutbound` 实现 `ChannelOutbound`：仅 `sent_messages` 记录，无真实发送。

---

## 2. 范围

| 做 | 不做 |
|----|------|
| `doudian_outbound.py` | 真实抖店发消息 API |
| registry 单测（tearDown clear） | 改 handler / resolver 默认 |
| contract tests | 改 PDD / flags |

---

## 3. 与 11a 边界

- **10m：** outbound mock + 测试内 `channel_outbound_registry.register`
- **11a：** `ChannelRegistry` + AutoReply factory 按 platform（flag 默认仍 PDD）

---

## 4. 测试矩阵

| 用例 | 期望 |
|------|------|
| 初始化 | sent_messages 空 |
| send_text | True + 字段含 platform=doudian |
| 隔离 | 无 pinduoduo / SendMessage |
| registry | register/get DOUDIAN |

---

*规划版本：Phase 10m · 2026-06-03*

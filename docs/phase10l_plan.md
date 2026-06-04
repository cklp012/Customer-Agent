# Phase 10l 规划 — Doudian Mock Transport + Enqueue Runtime Flow

| 项 | 值 |
|----|-----|
| 类型 | mock + inbound helper + 单测（patch 入队） |
| 前置 | [phase10k_done.md](phase10k_done.md) |
| 后续 | 11a factory / 10m outbound mock（规划） |

---

## 1. 目标

在 10k mapper 之上增加：

- `DoudianMockTransport` — 内存 poll / poll_all
- `enqueue_doudian_raw_message` — routing 门控 + `enqueue_inbound_message`
- `test_doudian_mock_runtime_flow` — patch 入队，**不** 启 Consumer / 线程

---

## 2. Mock transport

- 无网络、无线程
- `poll()` 逐条；`poll_all()` 一次取完

---

## 3. Enqueue flow

```text
raw → compute_doudian_routing
    → doudian_raw_to_context / doudian_raw_to_unified
    → routing==queue → enqueue_inbound_message(doudian_{shop_id})
    → routing==drop → 不入队
```

---

## 4. 测试矩阵

| 用例 | 期望 |
|------|------|
| text | queue, queued=True, patch 被调用 |
| product_inquiry | queue, queued=True |
| system_notice | drop, patch 未调用 |
| isolation | queue 非 pdd_ 前缀 |

---

*规划版本：Phase 10l · 2026-06-03*

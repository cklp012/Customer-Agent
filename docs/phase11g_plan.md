# Phase 11g 规划 — Doudian Handler Unified Outbound Path Tests

| 项 | 值 |
|----|-----|
| 类型 | **测试 SSOT**（Route C；仅测试 + 文档） |
| 状态 | 执行后见 [phase11g_done.md](phase11g_done.md) |
| 前置 | [phase11f_done.md](phase11f_done.md) |

---

## 目标

验证测试内 `USE_UNIFIED_OUTBOUND_RESOLVER=true` 时：

```text
AIReplyHandler._send_reply
  → resolve_outbound
  → channel_outbound_registry
  → DoudianMockOutbound.send_text
  → sent_messages
```

**生产默认不变：** flag unset → false；handler 仍 `resolve_pinduoduo_outbound`。

---

## 只在测试内开启 unified flag

| 项 | 要求 |
|----|------|
| `setUp` | `USE_UNIFIED_OUTBOUND_RESOLVER=true` |
| `tearDown` | 恢复 env + `channel_outbound_registry.clear()` |
| `unified_outbound_flags.py` | **不改默认值** |

---

## Handler path 测试矩阵

| ID | 用例 |
|----|------|
| — | `use_unified_outbound_resolver()` unset → false |
| H1a | manual register + `_send_reply` → `sent_messages`；无 PDD resolver / legacy |
| H1b | `DoudianMockChannel.start_account` + `_send_reply` |
| H2 | `KeywordDetectionHandler` + registry → `transfer_to_human` |
| H3 | 无 registry → 不调用 PDD resolver；legacy fallback |

---

## PDD 保护清单

- 不改 `ai_handler.py` / `keyword_handler.py` 默认分支
- 不改 `Channel/pinduoduo/**`
- 不启动 Consumer / AutoReply / 真实 API
- H3 仅断言不调用 PDD **resolver**；允许现有 legacy SendMessage fallback

---

*Phase 11g · Route C*

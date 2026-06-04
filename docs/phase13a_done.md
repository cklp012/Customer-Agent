# Phase 13a 完成 — Product Gate Pure Functions + Tests

| 项 | 内容 |
|----|------|
| 状态 | **纯函数 + 单元测试已实现** |
| 日期 | 2026-06-03 |
| 范围 | H1（[phase12f_handler_integration_steps.md](phase12f_handler_integration_steps.md)） |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 新增 | `Message/gates/*` 纯函数 |
| 新增 | `tests/test_product_gate_*.py` |
| handler / SendMessage | **未接** |
| `database/models.py` / migration | **未改** |
| PDD / Doudian 热路径 | **未改** |
| 生产默认 | `product_gate_enabled=false` |
| 13b+ | handler **fail-open shadow** 仅观察（见 [phase13b_done.md](phase13b_done.md)） |

---

## 新增代码

| 模块 | 职责 |
|------|------|
| `intent_types.py` | IntentBucket / SendMode / intent 常量 |
| `consultation_intent_classifier.py` | keyword risk + rule classify |
| `send_decision.py` | `SendDecision` + `build_send_decision` |
| `guarded_send.py` | `evaluate_guarded_send`（无 outbound） |

---

## 测试签收

| 场景 | 状态 |
|------|------|
| Preview zero-send（纯逻辑） | ✅ |
| blocked intent zero auto-send | ✅ |
| `product_gate_enabled=false` legacy passthrough | ✅ |
| 不 import SendMessage（guarded_send 模块） | ✅ |

运行：`python -m unittest discover -s tests -v`

---

## 下一步

| Phase | 状态 | 内容 |
|-------|------|------|
| **13b** | ✅ | shadow SendDecision logging — [phase13b_done.md](phase13b_done.md) |
| **13c** | ✅ | 单测试店 Preview gate 规划 — [phase13c_done.md](phase13c_done.md) |
| **13d** | 待做 | Preview gate 实现（H3 代码） |
| **12g** | 待做 | merchant console wireframe |

---

*签收：Phase 13a · 2026-06-03*

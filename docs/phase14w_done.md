# Phase 14w 完成 — Policy / Template Validation Service Skeleton

| 项 | 内容 |
|----|------|
| 状态 | **validation service skeleton implemented** |
| 日期 | 2026-06-03 |
| 前置 | [phase14v_done.md](phase14v_done.md) · [phase14u_done.md](phase14u_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 实现 | `validate_policy_mode` · `validate_reply_template` · `compute_content_hash` |
| forbidden scan | 复用 `Message.gates.final_guard.scan_forbidden_promise` |
| validation_status | `passed` · `pending_review` · `rejected` |
| DB / SQLite | **未写** |
| handler 集成 | **未接** |
| SendMessage / outbound | **未调用** |
| PDD / Doudian 热路径 | **未改** |
| repositories | **未 import** |
| assisted approve/reject | **未实现** |
| assisted / auto send | **未实现** |

---

## 核心 API

| 组件 | 路径 |
|------|------|
| `PolicyValidationResult` | `policy_template_validation_service.py` |
| `TemplateValidationResult` | `policy_template_validation_service.py` |
| `validate_policy_mode` | `policy_template_validation_service.py` |
| `validate_reply_template` | `policy_template_validation_service.py` |
| `compute_content_hash` | `policy_template_validation_service.py` |

**原则：** 校验 merchant policy 不超过 platform ceiling · 红线 intent 不可放宽 · 模板保存/启用前 forbidden scan · **不发送**。

---

## 规则摘要

| 类别 | 行为 |
|------|------|
| Policy mode | mode ranking · platform ceiling matrix · redline=blocked · effective_mode=min(...) |
| Template | empty/forbidden/unknown variable → rejected · suspicious → pending_review · safe → passed |

---

## 测试

`uv run python -m unittest discover -s tests -v`

- `tests/test_policy_template_validation_service.py` — W1–W15

---

## 下一步

| Phase | 内容 |
|-------|------|
| **14x** | ✅ Assisted service skeleton — [phase14x_done.md](phase14x_done.md) |
| **14y** | Final Guard + Assisted service **integration planning** |
| **14z** | PendingAssisted **dashboard read planning** |
| **15a** | Assisted send **implementation planning only** |

---

*签收：Phase 14w · 2026-06-03*

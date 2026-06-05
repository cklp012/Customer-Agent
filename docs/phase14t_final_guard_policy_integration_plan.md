# Phase 14t — Final Guard + Merchant Policy Integration Plan

| 项 | 内容 |
|----|------|
| 类型 | **planning only · 不写代码** |
| 日期 | 2026-06-03 |
| 前置 | [phase14s_done.md](phase14s_done.md) · [phase14r_done.md](phase14r_done.md) · [phase14q_done.md](phase14q_done.md) |

---

## 1. Phase 14t 定位

| 项 | 结论 |
|----|------|
| 交付 | **仅文档** |
| Python 代码 | **未写** |
| Final Guard 实现 | **未实现**（14v） |
| MerchantSafetyPolicy / Template 代码 | **未实现**（14u/14w） |
| Assisted / auto send | **未实现** |
| handler / SendMessage / PDD / Doudian | **未改** |

Phase 14t 在 14s（Merchant Safety Policy + Template）之上，规划 **Final Guard** 如何与 merchant policy 集成，作为 **outbound 前最后一道安全门**。

---

## 2. 职责分离（核心原则）

**English:**

> **Merchant policy controls participation.**  
> **Final guard controls sendability.**

**中文:**

> **商家策略决定 AI 能不能参与、以什么方式参与；**  
> **Final Guard 决定最终这句话能不能发送。**

| 层 | 决定什么 | 不决定什么 |
|----|----------|------------|
| **MerchantSafetyPolicy** | `effective_mode` · 模板白名单 · 是否需 pending | 文本是否含禁诺 |
| **Final Guard** | `allowed_to_send` · `block_code` | AI 是否可生成草稿（上游） |

---

## 3. Final Guard 行为约束

| # | 约束 |
|---|------|
| 1 | Final Guard 是 **outbound 前**最后一道安全门 |
| 2 | **只返回 decision** · **不执行 outbound** · **不调用 SendMessage** |
| 3 | `allowed_to_send=false` → caller **绝不能** SendMessage |
| 4 | **不能被** merchant policy / merchant approve / template / `auto_allowed` **绕过** |
| 5 | **final guard pass ≠ outbound success** · 仅表示「允许尝试发送」 |
| 6 | **final guard block → no-send** · 无 legacy fallback |
| 7 | 纯函数形态（14v）· 无副作用 · 不写 DB |

---

## 4. 与 14s 四层 scan 关系

| Scan 层 | 时点 | Final Guard 关系 |
|---------|------|------------------|
| 1 template save | 保存 | guard 仍复检渲染文本 |
| 2 AI draft | 生成后 | guard 检 `final_reply` |
| 3 merchant edit | approve 前 | guard 检编辑稿 |
| 4 **final guard** | **发送前** | **权威 sendability 判定** |

Template save scan **不能替代** final guard。

---

## 5. Pipeline 位置

```text
… → send decision → **final guard** → preview | pending | outbound
```

| 路径 | Guard 角色 |
|------|------------|
| preview（14i test shop） | 可 evaluate · **zero-send** · 记录 `allowed_to_send` 供 Dashboard |
| assisted approve（14r future） | **必须** guard pass 才 outbound |
| auto_allowed（future） | **必须** guard pass 才 outbound |
| non-test legacy | **不进入** guard · unchanged |

---

## 6. 文档索引

| 文档 | 内容 |
|------|------|
| [phase14t_guard_input_output_contract.md](phase14t_guard_input_output_contract.md) | I/O contract |
| [phase14t_guard_rule_matrix.md](phase14t_guard_rule_matrix.md) | G1–G27 |
| [phase14t_forbidden_promise_scan_rules.md](phase14t_forbidden_promise_scan_rules.md) | 禁诺 scan |
| [phase14t_template_and_ai_text_guarding.md](phase14t_template_and_ai_text_guarding.md) | 文本来源 |
| [phase14t_audit_snapshot_integration.md](phase14t_audit_snapshot_integration.md) | audit · snapshot |
| [phase14t_failure_policy.md](phase14t_failure_policy.md) | failure |
| [phase14t_test_plan.md](phase14t_test_plan.md) | T1–T25 |

---

## 7. 当前 runtime（unchanged）

- test shop preview：**zero-send**
- non-test legacy：**unchanged**
- flags 默认 off · assisted/auto **未实现**

---

## 8. 下一步

| Phase | 内容 |
|-------|------|
| **14u** | MerchantSafetyPolicy + MerchantReplyTemplate schema skeleton |
| **14v** | Final Guard **pure function** implementation |
| **14w** | Policy/template **validation service** skeleton |

---

*Phase 14t · planning only · 2026-06-03*

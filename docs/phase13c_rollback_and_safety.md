# Phase 13c — Rollback and Safety

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 关联 | [phase13c_single_test_shop_preview_plan.md](phase13c_single_test_shop_preview_plan.md) |

---

## 1. 回滚杠杆（即时生效）

| 动作 | 效果 | 影响范围 |
|------|------|----------|
| 从 `test_shop_allowlist` **移除** shop | 下一消息起 **legacy** | 仅该店 |
| 设置 `product_gate_enabled=false`（allowlist 行或未来 DB） | legacy send | 仅该店 |
| 清空 `TEST_SHOP_ALLOWLIST_PATH` / env | 全店 legacy | 全局（测试） |
| 13d feature flag off（若引入） | 代码路径回 13b | 全局 |
| Revert 13d commit | 回 13b shadow-only | 需 deploy |

**non-test shop：** 任何回滚操作 **不得** 改变其 send 行为（Z2/Z5 回归）。

---

## 2. 故障模式与 fail-safe

| 故障 | test shop | non-test shop |
|------|-------------|---------------|
| preview ReplyLog 写入失败 | **no send**；log error；handler 不 crash | N/A（不写 preview log） |
| `classify_consultation_intent` 异常 | **no send**；uncertain + safe decision | legacy 不变；shadow fail-open（13b） |
| `build_send_decision` 异常 | **no send** | legacy 不变 |
| `evaluate_guarded_send` 异常 | **no send** | legacy 不变 |
| allowlist 解析异常 | **legacy**（解析失败 = 未命中） | legacy |
| ambiguous metadata（缺 shop_id） | **legacy**（不误入 gate） | legacy |

**原则：** test shop **宁可不发**；non-test shop **宁可保持今日发送**。

---

## 3. 审计（DB 阶段 · 13e+）

| 事件 | AuditLog 字段（规划） |
|------|----------------------|
| 添加 test shop 到 allowlist | `action=gate_allowlist_add`, `shop_id`, `actor` |
| 移除 | `gate_allowlist_remove` |
| `product_gate_enabled` true→false | `gate_disable` |
| `reply_mode` 变更 | `reply_mode_change` |

**13d：** 仅结构化 logger + git 管理的 fixture YAML（无 AuditLog 表）。

---

## 4. 人工验证清单（13d 部署前）

- [ ] 确认 allowlist **仅 1 个** test `shop_id`（或明确列出的最少集合）
- [ ] 确认生产 PDD 店 `shop_id` **不在** allowlist
- [ ] 用 test shop 发商品咨询 → 买家端 **无** 新 AI 消息
- [ ] 检查 preview log / 日志有 `not_sent_preview`
- [ ] 用 non-test shop 发消息 → 行为与 13b 一致（仍有 send 若 AI 成功）
- [ ] 退款文案 test shop → 无 send + takeover 状态
- [ ] `workspace_pause` test → 无 send
- [ ] Doudian mock 账号消息 → 无 gate-on 日志
- [ ] `git grep` 无默认 `product_gate_enabled=True` 于生产配置
- [ ] 全量 `uv run python -m unittest discover -s tests -v`

---

## 5. Go / No-Go（进入 13d 实现）

### Go — 仅当全部满足

| # | 条件 |
|---|------|
| G1 | Z1 设计可证明 test shop **zero-send** |
| G2 | Z2 设计可证明 non-test shop **legacy unchanged** |
| G3 | preview 路径 **无** SendMessage / outbound 调用（Z7） |
| G4 | **无** DB migration 依赖即可完成 13d |
| G5 | **无** Doudian production 变更 |
| G6 | allowlist **显式**、无模糊匹配（文档 §3） |
| G7 | `product_gate_enabled` **默认 false** 已写入规划 |
| G8 | 回滚路径 §1 已评审 |

### No-Go — 任一成立则暂停 13d

| # | 条件 |
|---|------|
| N1 | preview 路径可能 **意外** 调用 `_send_reply` / legacy send |
| N2 | allowlist 选型依赖 shop_name 或 env 全局默认 true |
| N3 | handler 重构范围 > 单文件早分支（>~80 行行为变更无测试） |
| N4 | 无法在测试中 patch SendMessage 并断言未调用 |
| N5 | 计划默认全 PDD 开启 gate |

---

## 6. 13d 实现后回滚演练

1. 从 allowlist 移除 test shop → 发消息 → 应恢复 send（Z2）
2. Revert 13d → 仅余 13b shadow → Z5 仍通过
3. 保留 13a 纯函数包 — 不删除

---

*Rollback & safety · Phase 13c · 2026-06-03*

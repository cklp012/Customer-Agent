# Phase 14k — Dashboard Filters & Permissions

| 项 | 内容 |
|----|------|
| 类型 | **planning only** |
| 日期 | 2026-06-03 |
| 对齐 | [phase12d_api_contract.md](phase12d_api_contract.md) · [phase13f_auditlog_and_permissions.md](phase13f_auditlog_and_permissions.md) |

---

## 1. 角色定义

| 角色 | 说明 |
|------|------|
| **owner** | 工作区所有者 · 全部读 + 未来全部设置 |
| **admin** | 管理员 · 读 + 未来 gate/店铺设置 |
| **operator** | 运营 · 读 + **未来** assisted approve |
| **viewer** | 只读 · 读 logs only |

**14k read API：** 四类角色均可 **read ReplyLog**（workspace scoped）。

---

## 2. Read API 权限矩阵（14k 范围）

| 能力 | owner | admin | operator | viewer |
|------|-------|-------|----------|--------|
| GET list reply logs | ✅ | ✅ | ✅ | ✅ |
| GET detail reply log | ✅ | ✅ | ✅ | ✅ |
| POST approve assisted | ❌ 未实现 | ❌ | 未来 | ❌ |
| PATCH gate settings | ❌ 未实现 | 未来 | ❌ | ❌ |
| 查看 credential | ❌ **全员禁止** | ❌ | ❌ | ❌ |

**read API 不能改 `reply_mode` / `product_gate_enabled` / 任何 send flag。**

---

## 3. 多租户隔离

| 规则 | 说明 |
|------|------|
| `workspace_id` 必填 | query 或 session 推导 · 交叉校验 |
| `shop_id` 归属 | 必须属于该 workspace · 否则 403 |
| `account_id` | 必须属于 shop binding |
| 跨 workspace 读 | **禁止** |
| future | PostgreSQL row-level · API gateway tenant header |

**D8 测试：** workspace A 的 token 不能读 workspace B 的 logs。

---

## 4. 数据脱敏

| 字段 | API 策略 |
|------|----------|
| `buyer_id` | 允许返回内部 id · UI 脱敏展示（***5678） |
| `buyer_message` | 完整文本（商家自有会话） |
| cookie / password / token | **永不返回** |
| PDD MMS secret | **永不返回** |

---

## 5. Filters（Dashboard UI + API query 对齐）

| 筛选维度 | Query param | UI 控件 |
|----------|-------------|---------|
| 店铺 | `shop_id` | 店铺下拉 |
| 买家 | `buyer_id` | 搜索框 |
| 发送状态 | `send_status` | 多选 chip |
| 意图桶 | `intent_bucket` | allowed / blocked / uncertain |
| 风险 | `risk_level` | low / medium / high |
| 时间范围 | `created_after` · `created_before` | 日期选择器 |
| 平台 | `platform_id` | 默认 pinduoduo · Doudian 未来 mock only |

### 5.1 常用 preset（UI）

| Preset | filters |
|--------|---------|
| Preview 建议 | `send_status=not_sent_preview` |
| 待人工 | `send_status=not_sent_human_takeover` |
| 高风险 | `risk_level=high` |
| 被拦截 | `intent_bucket=blocked` |

---

## 6. operator 未来 assisted（未实现）

| 能力 | Phase |
|------|-------|
| read logs | 14k ✅ 规划 |
| approve pending reply | 14n+ |
| approve 必须 AuditLog | 13f 规划 |

**14k read API 不包含 approve endpoint。**

---

## 7. Doudian

| 规则 |
|------|
| production read path **不含** Doudian |
| 未来 mock spike logs 可 `platform_id=doudian` · 仅 dev |
| D11：不进入 production send |

---

## 8. non-test shop legacy

| 规则 |
|------|
| read API 独立 HTTP 层 |
| 不调用 handler send path |
| legacy shop 无 preview logs → 空列表 |
| legacy send **不受影响** |

---

*Phase 14k · planning only · 2026-06-03*

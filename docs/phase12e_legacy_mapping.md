# Phase 12e — Legacy → SaaS Mapping（SSOT）

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 来源 | `database/models.py` · `database/db_manager.py` · UI `account_data` · Phase 12b/12d |

---

## 1. Legacy 数据模型（当前生产）

### 1.1 ORM 表（`database/models.py`）

| 表 | 关键字段 | 用途 |
|----|----------|------|
| `channels` | `channel_name` (unique) | 平台 ID，如 `pinduoduo` |
| `shops` | `channel_id`, `shop_id`, `shop_name`, `shop_logo` | 平台侧店铺 |
| `accounts` | `shop_id` (FK), `user_id`, `username`, **`password`**, **`cookies`**, `status` | 客服子账号 + 明文凭证 |
| `keywords` | `keyword` | 转人工词（全局，非 per-shop） |
| `product_knowledge` | `shop_id` (FK→shops.id), `goods_id`, … | 商品知识 |
| `customer_service_knowledge` | `shop_id`, `title`, `content`, `tags` | 客服/售后 FAQ |

**无表：** SendDecision、ReplyLog、AuditLog、message 持久化日志（运行时 loguru 文件）。

### 1.2 运行时概念

| Legacy 概念 | 位置 | 说明 |
|-------------|------|------|
| `account_data` | `ui/user_ui.py` 等 | dict：`channel_name`, `shop_id`, `shop_name`, `username`, `password`, `status`, … |
| Auto reply 配置 | `config.json` + 线程状态 | 非 DB；启停 `AutoReplyThread` |
| Queue name | `Channel/pinduoduo/core/pdd_message_handler.py` | **`pdd_{shop_id}`** 字符串 |
| Handler metadata | `Message/core/consumer.py` | `shop_id`, `user_id`, `from_uid` from kwargs |
| Keywords | `KeywordDetectionHandler` + DB `keywords` | 全局词表 |
| Outbound | `SendMessage` / optional `PinduoduoOutbound` | 发送/转人工 |

### 1.3 `db_manager` 操作模式

- 按 `channel_name` + `shop_id` + `user_id` 解析 `Channel` → `Shop` → `Account`
- `shops.id`（整数 PK）≠ `shops.shop_id`（平台字符串）— 知识库 FK 用 **整数 PK**

---

## 2. 映射表：Legacy → SaaS

| Legacy | SaaS 目标 | 迁移期策略 |
|--------|-----------|------------|
| （无） | `merchants` | 桌面版默认单 merchant；M2 投影 |
| （无） | `workspaces` | 默认 workspace_id=1 本地 |
| `Channel.channel_name` | `shop_bindings.platform_id` | 1:1 枚举映射 |
| `Shop.shop_id` (string) | `shop_bindings.shop_id` | 同值 |
| `Shop.shop_name` | `shop_bindings.shop_name` | 投影 |
| `Account.user_id` | `shop_bindings.account_id` | 同值 |
| `Account.username` | `shop_bindings.account_display_name` | 投影 |
| `Account.password` | `credential_refs` (encrypted) | **不** 复制明文到新表展示；M3 shadow |
| `Account.cookies` | `credential_refs` | JSON → encrypted blob ref |
| `Account.status` | `connection_status` 参考信号 | 派生，非 1:1 |
| `Shop` + `Account` 行 | **一行** `shop_bindings` | 唯一键 `(workspace, platform, shop_id, account_id)` |
| `keywords` (global) | `safety_settings.human_takeover_keywords` | 导入 + 保留 legacy 至 M9 |
| `product_knowledge` | 保留 legacy FK `shops.id` | 后期 `shop_binding_id` 映射表 |
| `customer_service_knowledge` | 同上 | consultation 场景逐步收窄用途 |
| `config.json` LLM | `workspaces.ai_provider_mode` | 平台托管后期覆盖 |
| （无） | `reply_mode` | 新列默认 **`preview`** |
| （无） | `product_gate_enabled` | 新列默认 **`false`** |
| （无） | `send_decisions` / `reply_logs` | M4+ shadow write |
| AutoReply 启停 | `binding_status` + 运行时 | connected ≠ thread running |
| `pdd_{shop_id}` | **不变** | 队列名不迁移 |

---

## 3. ID 对照（关键）

```text
legacy shops.id (int PK)     ──maps──►  shop_bindings.legacy_shop_id (optional column, M2)
legacy shops.shop_id (str)   ──maps──►  shop_bindings.shop_id
legacy accounts.user_id      ──maps──►  shop_bindings.account_id
```

**知识库查询：** 过渡期 `KnowledgeService._resolve_shop_db_id` **继续** 用 `shops.shop_id` → `shops.id`；SaaS API 用 `shop_binding_id`。

---

## 4. 行为映射

| 行为 | Legacy | SaaS（gate on 后） |
|------|--------|-------------------|
| 收消息 | WS → `put_message(pdd_{shop_id})` | 不变 |
| 发消息 | `AIReplyHandler._send_reply` → SendMessage | `send_text_guarded` + SendDecision |
| 转人工 | Keyword → SendMessage.move_conversation | + HumanTakeoverQueue + AuditLog |
| 连接展示 | Account.status + 线程 | `ShopConnectionSummary.effective_status` |

---

## 5. 平台边界

| 平台 | Legacy `Channel` | SaaS `ShopBinding` |
|------|------------------|-------------------|
| PDD | ✅ production | ✅ `binding_status=connected` 允许 |
| Doudian | 可能存在于 channel 表 / mock | **`waitlist`** only；≠ production connected |
| Taobao / JD | UI 灰显 | `waitlist` |

---

## 6. 明确不替换（迁移期）

| 项 | 原因 |
|----|------|
| legacy `shops` / `accounts` 表 | AutoReply、Playwright 登录、db_manager 全依赖 |
| `pdd_{shop_id}` | 文档与代码 SSOT |
| 全局 `keywords` 表 | handler 仍读至 M4+ 并行 |
| 明文 password 列 | 保留至 credential 切换完成；UI **不再展示**（产品） |

---

## 7. Shadow projection 示例（M2，概念）

```sql
-- 文档 only，非执行
INSERT INTO shop_bindings (workspace_id, platform_id, shop_id, account_id, ...)
SELECT :default_workspace, c.channel_name, s.shop_id, a.user_id, ...
FROM accounts a
JOIN shops s ON a.shop_id = s.id
JOIN channels c ON s.channel_id = c.id
WHERE c.channel_name = 'pinduoduo'
ON CONFLICT DO NOTHING;
```

---

*Phase 12e · Legacy Mapping · docs only*

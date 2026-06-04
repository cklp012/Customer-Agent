# Phase 10 — Account Model & Multi-Platform UI（SSOT）

**文档导航：** [docs 目录](README.md) · [phase10a_plan.md](phase10a_plan.md) · [architecture_current.md](architecture_current.md) · [release_checkpoint_phase9.md](release_checkpoint_phase9.md)

| 项 | 值 |
|---|---|
| 类型 | **规划 SSOT**（Phase 10a 文档化；10b+ 再编码） |
| 代码状态 | 运行时 **仅拼多多**；本文描述现状 + 演进契约 |

---

## 1. Executive summary

- 现有数据库 **已有** 三层结构：`channels` → `shops` → `accounts`（见 `database/models.py`）。
- 字段 **`channel_name`** 在库表与 UI 中即 **平台标识**；与 `Channel/base/types.py` 中 `PlatformType.value` 对齐（例如 `pinduoduo`）。
- **Phase 10a 不做** DB migration、不新增 `platform` 列、不把 `channel_name` 改名为 `platform`。
- **Phase 10a 不** 注册真实第二平台、不默认 seed 淘宝/抖店/京东、不默认注册 Demo 到生产。
- **Phase 10a 不改变** PDD 默认行为：自动回复运行时仍只走拼多多 Channel 工厂与 WebSocket 路径。
- 文档中可使用 **`platform_id`** 作为 `channel_name` 的语义别名，避免与 SQLAlchemy `Channel` 模型类名混淆。

---

## 2. Current account data flow

### 2.1 自动回复页（生产路径）

```text
AutoReplyUI (ui/auto_reply/ui.py)
  → loadAccountsFromDB()
  → db_manager.get_all_accounts_with_details()
       → JOIN Account + Shop + Channel
       → 每条 dict 含 channel_name, shop_id, shop_name, shop_logo,
         username, password, status, user_id, cookies

  → refreshAccountList()
  → AutoReplyCard(account_data)
       → 平台 badge = account_data["channel_name"]

  → 用户点击「开始回复」
  → onAutoReplyToggle(account_data)
  → AutoReplyManager.start_auto_reply(account_data)
       → account_key = f"{channel_name}_{shop_id}_{username}"
       → AutoReplyThread(account_data)

  → AutoReplyThread.run() (ui/auto_reply/threads.py)
       → create_auto_reply_runtime_channel()     # 9d：默认 Registry → PDD factory
       → start_auto_reply_account(channel, shop_id, user_id, …)
       → 当前实现：仅 Channel.pinduoduo.channel_factory
```

### 2.2 账号管理页（已有平台展示）

```text
UserManagerWidget (ui/user_ui.py)
  → 按 channel / shop 加载
  → AccountCard 显示 channel_name 为平台 badge
  → 登录验证：LoginThread → 拼多多 Playwright 路径（PDD 专用）
```

### 2.3 与 Phase 9d Registry 的关系

- `app.py` 启动时 `register_default_platforms()` 仅注册 **`pinduoduo`** 工厂（默认）。
- `create_auto_reply_runtime_channel()` **不接收** `platform` 参数；**不**按 `account_data["channel_name"]` 路由到其它 `PlatformType`。
- 因此：UI 可列出多 `channel_name` 的账号，但 **自动回复 WS 仅对 PDD 有效**（直至未来 Phase 显式接入）。

---

## 3. Account data contract

运行时 UI / Manager / Thread 之间传递的 **`account_data: dict`** 契约如下。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `channel_name` | `str` | 是 | **平台 ID**；应等于 `PlatformType.value`；现有生产值：`pinduoduo` |
| `shop_id` | `str` | 是 | 平台侧店铺 ID（PDD：MMS shop id） |
| `shop_name` | `str` | 否 | 展示用店铺名称 |
| `shop_logo` | `str` | 否 | 展示用 logo URL / 路径 |
| `user_id` | `str` | 是 | 平台侧客服账号 UID（PDD：user_id） |
| `username` | `str` | 是 | 登录名；参与 `account_key` |
| `password` | `str` | 否 | 账号密码（账号管理） |
| `status` | `int` | 是 | 账号状态：`0` 休息 / `1` 在线 / `3` 离线等 |
| `cookies` | `str` | 否 | 登录会话材料（PDD Playwright / API） |

**语义别名（仅文档，不新增代码字段）：**

| 别名 | 映射 |
|------|------|
| `platform_id` | `account_data["channel_name"]` |
| `platform` | 同左（口语）；ORM 类名用 `Channel` 表 |

**缺失处理（现有代码惯例）：**

- `SetStatusThread`：`channel_name = account_data.get("channel_name", "pinduoduo")`。
- 10a 建议所有新 UI 守卫沿用：**未设置则视为 `pinduoduo`**，与历史数据一致。

---

## 4. Platform naming convention

| 层级 | 字段 / 枚举 | 约定 |
|------|-------------|------|
| 数据库 | `channels.channel_name` | 平台 ID 字符串，唯一 |
| UI / Manager | `account_data["channel_name"]` | 与 DB 一致 |
| Channel 代码 | `PlatformType.PINDUODUO.value` | `"pinduoduo"` |
| 文档 | `platform_id` | **别名**，等于 `channel_name` |

**示例 `platform_id` 值（`PlatformType`）：**

| platform_id | 说明 |
|-------------|------|
| `pinduoduo` | 拼多多（生产） |
| `demo` | 测试假平台（6b/8a，非生产 AutoReply） |
| `doudian` | 抖店（预留，6a 优先级） |
| `jingdong` | 京东（预留） |
| `taobao` | 淘宝（预留） |
| `douyin` | 抖音（枚举预留） |

**10a 明确不做：**

- 重命名 DB 列 `channel_name` → `platform`。
- 新增冗余 `platform` 列。
- 要求迁移现有 SQLite。

---

## 5. account_key 规则

保持现有实现（`ui/auto_reply/manager.py`）：

```text
account_key = f"{channel_name}_{shop_id}_{username}"
```

| 属性 | 说明 |
|------|------|
| 兼容性 | 10a **不改** key 格式 |
| 隔离性 | `channel_name` 前缀区分平台；避免跨平台 shop_id 碰撞 |
| 使用处 | `running_accounts` 字典键；状态同步 |

---

## 6. Platform capability matrix

| platform_id | 账号管理 UI | AutoReply 运行时 | Registry bootstrap（app） | 生产状态 |
|-------------|-------------|------------------|---------------------------|----------|
| **pinduoduo** | 是 | 是 | 是（默认 `register_pinduoduo_channel`） | **production** |
| **demo** | 否 / 仅测试 | 否 | 仅 `USE_DEMO_CHANNEL_REGISTRATION=true` 时注册 | test spike（8a） |
| **doudian** | 规划中 | 否 | 否 | future spike |
| **jingdong** | 规划中 | 否 | 否 | future spike |
| **taobao** | 规划中 | 否 | 否 | future spike |
| **其它预留** | 否 | 否 | 否 | 未规划 |

**说明：**

- 「账号管理」指 `user_ui` 增删改查与登录验证；Demo 不面向商家账号管理。
- 「Registry bootstrap」指 `apply_app_startup_bootstrap()`；与 9d AutoReply **创建** 路径相关，但不等于该平台可自动回复。

---

## 7. Current PDD binding points

以下绑定点 **均不在 Phase 10a 修改范围**；10b 仅允许 UI 层守卫，不修改这些模块。

| 绑定点 | 位置 | 绑定说明 |
|--------|------|----------|
| AutoReply Channel 工厂 | `ui/auto_reply/threads.py` | `import Channel.pinduoduo.channel_factory`；`create_auto_reply_runtime_channel()` |
| 账号启动签名 | `start_auto_reply_account` | 按 `PinduoduoChannel` vs `PDDChannel` 分支参数个数 |
| 账号登录 | `ui/user_ui.py` → `LoginThread` | 拼多多 Playwright / `pdd_login` 路径 |
| 平台上下线 | `ui/auto_reply/threads.py` → `SetStatusThread` | `AccountMonitor`（PDD API） |
| 消息入站 | `Channel/pinduoduo/.../pdd_message_handler` | PDD WS 解析 → Context / 入队 |
| 消息消费 | `Message/core/consumer.py` | handler 链仍以 **Context** 为主 |
| 出站 | `Message/handlers/*` + `outbound_resolver` | 默认 legacy `SendMessage`；PDD outbound flag 独立 |
| Registry 注册 | `register_default_platforms()` | 默认仅 `pinduoduo`；非按账号 platform 动态注册 |

---

## 8. Compatibility strategy

| 策略 | 内容 |
|------|------|
| 现有 SQLite | **不迁移**；`channels` 表默认种子 `pinduoduo` |
| 现有 PDD 账号行 | **无需修改** `channel_name` |
| `channel_name` 缺失 | 按 **`pinduoduo`** 处理（与现有 default 一致） |
| 第二平台种子 | **不**在 10a/10b 默认写入生产库 |
| 配置文件 | **不**新增并行 JSON account 格式；账号以 DB 为准 |
| 列重命名 | **不**将 `channel_name` 改为 `platform` |
| Phase 9d | **不**改变 Registry 默认、fallback、wrapper 默认 |

---

## 9. Phase 10b UI skeleton（已实现）

| 项 | 实现 |
|----|------|
| 平台筛选 | `AutoReplyUI` ComboBox：全部 / 拼多多；抖店/京东/淘宝 **disabled** 占位 |
| 展示 helper | `ui/auto_reply/platform_ui.py` — `platform_display_name`、`is_autoreply_supported` |
| 卡片 badge | 中文名（如「拼多多」）；unknown 显示原始 `channel_name` |
| 自动回复按钮 | 非 `pinduoduo` → **disabled** + Tooltip |
| 启动守卫 | `_guard_autoreply_start`；不调用 `start_auto_reply` |
| 运行时 | **仍仅 PDD** — `threads.py` / `channel_factory` **未改** |
| 交付记录 | [phase10b_done.md](phase10b_done.md) |

---

## 10. Phase 10 boundary（文档阶段）

### 10a 禁止

- 改 `ui/**`、`database/**`、`AutoReplyThread`、PDD runtime、handlers、consumer、outbound。
- 注册真实第二平台；默认 Demo；改 Phase 9d registry 默认。

### 推迟到独立 spike / 10c+

- `AutoReplyThread` → `ChannelRegistry.create(platform)` 按 `channel_name` 路由。
- 各平台登录、WS、出站协议。
- handler 按 `platform` / `content_type` 路由（10c 规划范畴）。

---

## 11. Related documents

| 文档 | 用途 |
|------|------|
| [phase10a_plan.md](phase10a_plan.md) | Phase 10a 范围与禁止项 |
| [phase10a_done.md](phase10a_done.md) | 10a 交付记录 |
| [phase6a_plan.md](phase6a_plan.md) | 第二平台 Adapter 选型（6a 缺口 → 10a） |
| [release_checkpoint_phase9.md](release_checkpoint_phase9.md) | Phase 9 运行时基线 |

---

*SSOT 版本：Phase 10a · 2026-06-03*

# Phase 0 审计报告 — Agent-Customer (JC0v0/Customer-Agent)

| 项 | 值 |
|---|---|
| 审计日期 | 2026-06-01 |
| GUI 验证日期 | 2026-06-01（Windows 本机） |
| 项目路径 | `D:\agent` |
| 版本 | `pyproject.toml` → 1.1.0 |
| 审计范围 | 环境/依赖、启动、License、核心链路、耦合点、回归清单 |
| 代码变更 | **无业务代码修改**（仅文档更新） |

---

## 一、环境与依赖

### 1.1 Python 版本

| 来源 | 要求 |
|------|------|
| `pyproject.toml` | `requires-python = ">=3.11"` |
| `.python-version` | `3.11` |
| 本机实测 | **Python 3.12.10**（满足要求） |

### 1.2 包管理器 `uv`

| 检查项 | 结果 |
|--------|------|
| `uv` 是否在 PATH | **否**（PowerShell: `uv` 命令未识别） |
| 替代安装 | `pip install -e .` **成功**（见下） |

**建议**：开发机安装 [uv](https://github.com/astral-sh/uv) 后与 README 对齐：`uv sync`。当前可用 `pip install -e .` 等价安装依赖。

### 1.3 依赖安装结果

```
pip install -e .
→ Successfully installed agent-customer-1.1.0 及全部依赖
```

主要依赖（来自 `pyproject.toml`）：

| 类别 | 包 |
|------|-----|
| UI | `pyqt6`, `pyqt6-fluent-widgets` |
| 异步/网络 | `websockets`, `aiohttp`, `requests` |
| AI | `openai`, `tiktoken` |
| 数据 | `sqlalchemy`, `pandas`, `numpy`, `jieba` |
| 浏览器自动化 | **playwright** |
| 文档 | `pypdf`, `python-docx`, `openpyxl`, `xlrd` |
| 其他 | `pydantic`, `loguru`, `volcengine`, `pillow`, `aiofiles` |

### 1.4 Playwright / 浏览器 / Windows

| 项 | 说明 |
|----|------|
| **Playwright** | 登录拼多多依赖 `Channel/pinduoduo/pdd_login.py`（`async_playwright` + Chromium） |
| 浏览器路径 | `app.py` 设置 `PLAYWRIGHT_BROWSERS_PATH` → 项目根 `.browsers`；`pdd_login.py` 优先 `.browsers`，否则 `%LOCALAPPDATA%/ms-playwright` |
| 安装脚本 | `scripts/install_playwright.py`（打包前安装 Chromium） |
| **操作系统** | README 明确要求 **Windows**；PyQt6 桌面端，需图形会话 |
| 打包 | `scripts/build_win_exe.py` → PyInstaller |

**本机已执行**（2026-06-01）：`python scripts/install_playwright.py` 成功，Chromium 安装至 `D:\agent\.browsers`。

### 1.5 环境检查结论

| 状态 | 说明 |
|------|------|
| 依赖安装 | 通过（pip editable） |
| uv sync | 未测（uv 未安装，可用 pip 替代） |
| Playwright 浏览器 | **通过**（`D:\agent\.browsers`） |
| GUI 启动 | **通过**（见 §2.2 本机验证记录） |
| PDD 端到端（WS/消息/AI） | **未测**（尚无真实店铺账号） |

---

## 二、启动验证

### 2.1 启动命令

```powershell
cd D:\agent
python app.py
```

`app.py` 初始化顺序（注释已写明）：

1. `config` → `configure_standard_services()` → `db_manager` / logger  
2. 延迟加载 `MainWindow`（PyQt6）  
3. 设置 `PLAYWRIGHT_BROWSERS_PATH`

### 2.2 本机 GUI 验证记录（Windows，2026-06-01）

执行人：项目维护者本机。前置：`pip install -e .`（或等价环境）、Playwright 已安装。

| # | 检查项 | 结果 | 备注 |
|---|--------|------|------|
| 1 | `python scripts/install_playwright.py` | **通过** | 浏览器目录：`D:\agent\.browsers` |
| 2 | `python app.py` 启动 GUI | **通过** | 主窗口正常显示 |
| 3 | 自动回复页 | **通过** | 页面可打开（未启动 WS，无账号） |
| 4 | 关键词管理页 | **通过** | 可打开，显示默认关键词列表 |
| 5 | 账号管理页 | **通过** | 可打开，当前账号数 **0** |
| 6 | 知识库页 | **通过** | 可打开；提示需先在账号管理添加店铺（符合预期） |
| 7 | 设置页 / LLM 配置 | **未记录** | 建议在添加店铺前完成 API 配置 |
| 8 | PDD 登录 / 添加店铺 | **未测** | 无真实拼多多店铺 |
| 9 | WebSocket 连接 | **未测** | 依赖账号与 cookies |
| 10 | 收消息 / AI 回复 / send_text | **未测** | 依赖 WS + 买家侧发消息 |
| 11 | 商品卡 / 转人工 / 断线重连 | **未测** | 同上 |

**结论**：Phase 0 的 **安装 + 桌面壳层 + 各主页面导航** 已验证；**拼多多业务链路（步骤 3–11）** 待在添加测试店铺后继续。

### 2.2.1 自动化环境备注（首次审计）

| 检查项 | 结果 |
|--------|------|
| CI/沙箱 GUI | 未完成（无图形会话） |
| 导入冒烟（可选） | `python -c "from config import config; from Channel.pinduoduo.pdd_channel import PDDChannel"` |

### 2.3 `config.json`

| 项 | 说明 |
|----|------|
| 仓库内是否存在 | **否**（`config.json` 未提交，符合 `.gitignore` 预期） |
| 首次生成时机 | `config.py` 中 `Config(auto_create=True)`：若 `config.json` 不存在，**首次 import `config` 时**写入默认 `config_base` |
| 默认路径 | 项目根目录 `config.json`（`Config(config_path='config.json')`） |

### 2.4 `config.json` 字段（代码真相源）

**`config.py` 中 `config_base` / `ConfigModel` 正式支持的字段：**

```json
{
  "business_hours": {
    "start": "08:00",
    "end": "23:00"
  },
  "llm": {
    "model_name": "",
    "api_key": "",
    "api_base": ""
  },
  "prompt": {
    "instructions": [ "..." ]
  },
  "db_path": ""
}
```

**README 提到但 `ConfigModel` 未建模的字段**（若手写进 JSON，会保留在原始 dict，但无 Pydantic 校验）：

- `embedder`
- `knowledge_base`（`utils/runtime_path.adjust_config_for_runtime` 会处理 `knowledge_base.vector_db_path` 等，若存在）

**`ui/setting_ui.py` 实际保存的字段**（保存时 `config.update(..., save=True)`）：

- `llm`：`api_base`, `api_key`, `model_name`
- `prompt`：`instructions`
- `business_hours`：`start`, `end`

### 2.5 配置不一致（记录为风险，不修代码）

| 问题 | 位置 | 影响 |
|------|------|------|
| `businessHours` vs `business_hours` | `pdd_channel.py` 使用 `config.get("businessHours")`；默认文件与设置页使用 `business_hours` | `handler_chain(..., businessHours=...)` 传入 **常为 None**；且 `handler_chain` 内 **未使用** 该参数（死参数） |
| README 的 `knowledge_base` / `embedder` | 无设置 UI、无 `ConfigModel` 字段 | 知识库实际走 **SQLite `KnowledgeService`**，不依赖 config 中的 vector 路径 |

### 2.6 启动失败常见原因（预判）

1. 未配置 `llm.api_key` → AI 回复失败（Agent `validate()` 返回 false），但不阻止 UI 启动  
2. Playwright 未安装浏览器 → **登录拼多多失败**  
3. 无图形环境 → PyQt6 无法显示窗口  
4. 首次运行需写 `config.json` / `temp/channel_shop.db` — 需写权限  

---

## 三、License 风险

| 检查项 | 结果 |
|--------|------|
| 根目录 `LICENSE` 文件 | **不存在** |
| `README.md` License 节 | 声明 **MIT** |
| `pyproject.toml` license 字段 | **未声明** |

**商业化授权风险：高**

- README 写 MIT ≠ 法律上已授予权利；缺少 `LICENSE` 文件时，fork/二创/商用前应：
  1. 向作者 **JC0v0** 索取正式 MIT 授权或书面许可，或  
  2. 请作者在仓库根目录添加 `LICENSE`（MIT 全文）后再商用  

---

## 四、核心链路审计（文件级索引）

### 4.1 总览数据流

```
用户发消息 → 拼多多 WS
  → PDDChatMessage 解析
  → Context
  → SimpleMessageQueue (pdd_{shop_id})
  → MessageConsumer → handler_chain
      → KeywordDetectionHandler
      → AIReplyHandler → CustomerAgent
      → CatchAllHandler
  → SendMessage HTTP 出站
```

### 4.2 分模块索引

| 能力 | 路径 | 关键符号 / 行号参考 |
|------|------|---------------------|
| **PDD 登录 / Cookie** | `Channel/pinduoduo/pdd_login.py` | `PDDLogin.login()` L40+；对外 `login_pdd()` L197+；Playwright 登录 `mms.pinduoduo.com/login` |
| UI 触发登录 | `ui/user_ui.py` | `LoginThread` → `login_pdd()` L77-81 |
| **Cookie 缓存** | `Channel/pinduoduo/cookie_cache.py` | 内存/共享 cookie |
| **Cookie 校验/重登** | `Channel/pinduoduo/cookie_utils.py` | `check_cookies_valid`, `perform_relogin`；`pdd_lifecycle._cookie_health_loop` 调用 |
| **HTTP 请求基类（带 cookie）** | `Channel/pinduoduo/utils/base_request.py` | 所有 MMS API 的 cookie、重登守卫 |
| **Token 获取** | `Channel/pinduoduo/utils/API/get_token.py` | `GetToken.get_token()` → `POST .../chats/getToken` |
| **WebSocket 连接** | `Channel/pinduoduo/pdd_channel.py` | `base_url = wss://m-ws.pinduoduo.com/` L66 |
| WS 建连实现 | `Channel/pinduoduo/core/pdd_lifecycle.py` | `init()` L123+：`GetToken` → `websockets.connect(full_url)` L145+ |
| WS 重连 | `Channel/pinduoduo/core/pdd_connection.py` | `_connect_with_retry` |
| 重连/心跳配置 | `Channel/pinduoduo/core/pdd_config.py` | `ReconnectConfig`, `HeartbeatConfig` |
| **消息接收循环** | `pdd_lifecycle.py` | `_message_loop` L434+ |
| **消息解析** | `Channel/pinduoduo/pdd_message.py` | `PDDChatMessage`, `MessageTypeHandler` |
| WS 消息分发 | `Channel/pinduoduo/core/pdd_message_handler.py` | `_process_websocket_message` L50+ |
| **Context 创建** | `pdd_message_handler.py` | `_convert_to_context` L167+ → `Context.create_pinduoduo_context` |
| Context 模型 | `bridge/context.py` | `Context`, `PinduoduoKwargs`, `ChannelType`, `ContextType` |
| **消息队列** | `Message/core/queue.py` | `SimpleMessageQueue.put(Context)` |
| 队列名 | `pdd_lifecycle.init` | `queue_name = f"pdd_{shop_id}"` L131 |
| 入队 API | `Message/__init__.py` | `put_message()` |
| **消费者** | `Message/core/consumer.py` | `MessageConsumer._process_message`；metadata 注入 shop_id/user_id/from_uid |
| **handler_chain** | `Message/__init__.py` | `handler_chain()` L131-146 |
| **关键词转人工** | `Message/handlers/keyword_handler.py` | `KeywordDetectionHandler`；`SendMessage.move_conversation` |
| **AI 回复** | `Message/handlers/ai_handler.py` | `AIReplyHandler.handle` → `CustomerAgent.async_reply` |
| Agent 核心 | `Agent/CustomerAgent/custom/customer_agent.py` | `_run_agent_loop`, 工具调用 |
| **SendMessage 发送** | `Channel/pinduoduo/utils/API/send_message.py` | `send_text` L14+；`send_mallGoodsCard`；`move_conversation` |
| 立即回复（非队列） | `pdd_message_handler.py` | `_handle_immediate_message` L118+ |
| **商品知识库（存储/检索）** | `database/models.py` | 表 `product_knowledge` |
| 知识服务 | `database/knowledge_service.py` | CRUD + `search_knowledge` / jieba |
| Agent 查商品知识 | `Agent/CustomerAgent/tools/get_product_knowledge.py` | `knowledge_service.search_knowledge(goods_id=...)` |
| **客服知识库** | `database/models.py` | 表 `customer_service_knowledge` |
| Agent 查客服知识 | `Agent/CustomerAgent/tools/search_customer_service_knowledge.py` | `search_knowledge(query=...)` |
| UI 管理知识库 | `ui/Knowledge_ui.py` | 产品/客服知识 CRUD、导入 |
| **商品同步** | `database/product_sync.py` | `ProductSyncService.sync_shop` → `ProductManager` + 多模态 LLM 提取 |
| UI 触发同步 | `ui/Knowledge_ui.py` | `ProductSyncService` |
| **商品列表 API** | `Channel/pinduoduo/utils/API/product_manager.py` | `get_product_list` 等 |
| Agent 拉商品 | `Agent/CustomerAgent/tools/get_product_list.py` | `ProductManager` |
| **发商品卡片** | `Agent/CustomerAgent/tools/send_goods_link.py` | `SendMessage.send_mallGoodsCard` |
| **转人工 API** | `send_message.py` + `move_conversation.py` | `getAssignCsList`, `move_conversation` |
| **连接状态** | `core/connection_status.py` | `ConnectionStatusManager` |
| **UI 启动 WS** | `ui/auto_reply/threads.py` | `AutoReplyThread` → `PDDChannel()` L67-88 |
| **店铺/账号 DB** | `database/db_manager.py` | `channel_shop.db` 默认 `./temp/channel_shop.db` |
| DI | `core/di_container.py` | `configure_standard_services` |

### 4.3 PDD 消息类型 → ContextType 映射表

| 条件 | ContextType |
|------|-------------|
| `from.role == mall_cs` | `MALL_CS` |
| `response == push`, `type == 0`, 无特殊 sub_type | `TEXT` |
| `push`, `type == 0`, `sub_type == 1` | `ORDER_INFO` |
| `push`, `type == 0`, `sub_type == 0` | `GOODS_INQUIRY` |
| `push`, `type == 1` | `IMAGE` |
| `push`, `type == 14` | `VIDEO` |
| `push`, `type == 1002` | `WITHDRAW` |
| `push`, `type == 5` | `EMOTION` |
| `push`, `type == 64` | `GOODS_SPEC` |
| `push`, `type == 24` | `TRANSFER` |
| `push`, 未知 type | `SYSTEM_STATUS` |
| `response == auth` | `AUTH` |
| `response == mall_system_msg` | `MALL_SYSTEM_MSG` |
| 其他 response | `SYSTEM_STATUS` |

定义位置：`Channel/pinduoduo/pdd_message.py`（`PDDMsgType` / `PDDSubType` / `PDDChatMessage._process_message`）。

### 4.4 队列 vs 立即处理

| 路径 | 类型 |
|------|------|
| 入队 | `TEXT`, `IMAGE`, `VIDEO`, `EMOTION`, `GOODS_INQUIRY`, `ORDER_INFO`, `GOODS_CARD`, `GOODS_SPEC` |
| 立即 | `SYSTEM_STATUS`, `AUTH`, `WITHDRAW`, `SYSTEM_HINT`, `MALL_CS`, `TRANSFER` |

定义：`pdd_message_handler._should_queue_message` / `_should_process_immediately`。

---

## 五、黄金路径回归清单（每次重构必跑）

> 需：**Windows 桌面**、有效拼多多测试店、LLM API Key、Playwright Chromium、测试买家号或另一客户端发消息。

| # | 步骤 | 操作 | 通过标准 | Phase 0 状态 | 相关日志/模块 |
|---|------|------|----------|--------------|----------------|
| 1 | 启动 UI | `python app.py` | 主窗口显示，无未捕获异常 | **通过** | `App`, `MainWindow` |
| 1b | 主页面导航 | 自动回复/关键词/账号/知识库 | 各页可打开、无崩溃 | **通过**（见 §2.2） | `ui/*` |
| 2 | 配置 | 设置页保存 LLM | `config.json` 含 `llm.*`；重启后仍保留 | **待测** | `ui/setting_ui.py` |
| 3 | 店铺/账号 | 用户页登录并保存账号 | DB `temp/channel_shop.db` 有 shop/account；cookies 非空 | **阻塞**（账号数 0） | `pdd_login`, `db_manager` |
| 4 | WS 连接 | 自动回复页启动账号 | 状态为已连接；日志出现「WebSocket连接已建立」 | **未测** | `AutoReplyThread`, `ConnectionStatusManager` |
| 5 | 收文本消息 | 买家发送「你好」 | 日志 `收到消息: type=0`；队列入队或处理 | **未测** | `pdd_message_handler` |
| 6 | 关键词转人工 | 发送含「转人工」文本 | 会话转接成功或提示无客服；**不再走 AI** | **未测**（UI 已验证关键词列表加载） | `keyword_handler` |
| 7 | AI 回复 | 发送普通咨询 | 日志有 LLM/工具调用；生成中文回复 | **未测** | `customer_agent`, `ai_handler` |
| 8 | send_text | 同上 | 买家端收到文本；API 返回 success | **未测** | `send_message.send_text` |
| 9 | 商品卡片 | 触发 Agent `send_goods_link` 或手动测工具 | 买家收到商品卡 | **未测** | `send_goods_link.py` |
| 10 | transfer_conversation | 触发 `transfer_conversation` 工具或关键词 | 会话转到其他客服 | **未测** | `move_conversation.py` |
| 11 | 断线重连 | 断网 30s 后恢复 | 状态 RECONNECTING → CONNECTED；消息恢复 | **未测** | `pdd_connection`, `ReconnectConfig` |
| 12 | 错误日志 | 故意错误 API Key | Loguru 有 ERROR；应用不崩溃 | **未测** | `utils/logger_loguru` |

**Phase 0 签收范围**：步骤 **1、1b** 已通过；步骤 **3–11** 需在添加真实拼多多测试店后继续，作为 **Phase 0 补测** 或 **Phase 2 前门禁**。

**记录模板**（建议每次重构填写）：

```
日期: 2026-06-01  提交: ______  执行人: ______
[x] 1  [x] 1b  [ ] 2  [ ] 3  [ ] 4  [ ] 5  [ ] 6  [ ] 7  [ ] 8  [ ] 9  [ ] 10  [ ] 11  [ ] 12
失败项: __________  截图/日志路径: __________
```

---

## 六、拼多多耦合点清单（严重程度排序）

| 严重度 | 文件 | 耦合方式 | 多平台影响 | Phase 1/2 处理建议 |
|--------|------|----------|------------|-------------------|
| P0 | `Message/handlers/ai_handler.py` | `SendMessage` 硬编码 | 所有平台 AI 回复无法复用 | Phase 2：`metadata["outbound"]` |
| P0 | `Message/handlers/keyword_handler.py` | 同上 + `move_conversation` | 转人工无法复用 | Phase 2：注入 `ChannelOutbound` |
| P0 | `Agent/CustomerAgent/tools/send_goods_link.py` | `SendMessage.send_mallGoodsCard` | 工具层绑死 PDD | Phase 4：`outbound` 注入 dependencies |
| P0 | `Agent/CustomerAgent/tools/move_conversation.py` | PDD 转接 API | 同上 | Phase 4 |
| P0 | `Agent/CustomerAgent/tools/get_product_list.py` | `ProductManager` | 商品能力无法换平台 | Phase 4：`fetch_products` |
| P1 | `ui/auto_reply/threads.py` | `import PDDChannel` | UI 无法选平台 | Phase 5：`ChannelRegistry` |
| P1 | `ui/user_ui.py` | `login_pdd` | 仅支持 PDD 登录 | Phase 5：按 platform 选 login |
| P1 | `bridge/context.py` | `PinduoduoKwargs`, `create_pinduoduo_context` | 通用 Context 被 PDD 污染 | Phase 3：`UnifiedMessage` + mapper |
| P1 | `pdd_message_handler.py` | 队列名 `pdd_*`、消费者内嵌 PDD | 第二平台需复制整条链 | Phase 2：队列 `{platform}_{shop_id}` |
| P2 | `database/product_sync.py` | `ProductManager` | 同步仅 PDD | 保留在 `pinduoduo` 适配器内 |
| P2 | `database/db_manager.py` `init_db` | 只 seed `pinduoduo` | 新平台需手改 init | Phase 5：配置化 channel 列表 |
| P2 | `pdd_channel.py` | `config.get("businessHours")` | 配置键错误（现未影响行为） | 顺带改为 `business_hours` 或删除死参数 |

**包内耦合（可接受，应保留在 `Channel/pinduoduo/` 内）**：`pdd_login`, `cookie_*`, `utils/API/*`, `pdd_message`, `core/*`。

**外部 import `Channel.pinduoduo` 的文件清单（共 12 处业务耦合）**：

```
ui/user_ui.py
ui/auto_reply/threads.py
database/product_sync.py
Message/handlers/keyword_handler.py
Message/handlers/ai_handler.py
Agent/CustomerAgent/tools/send_goods_link.py
Agent/CustomerAgent/tools/get_product_list.py
Agent/CustomerAgent/tools/move_conversation.py
Channel/pinduoduo/pdd_channel.py          (包内)
Channel/pinduoduo/pdd_login.py            (包内)
Channel/pinduoduo/core/pdd_message_handler.py (包内+SendMessage)
Channel/pinduoduo/core/pdd_lifecycle.py   (包内)
Channel/pinduoduo/utils/base_request.py   (包内)
Channel/pinduoduo/cookie_utils.py         (包内)
```

---

## 七、Phase 0 结论

### 7.1 完成情况

| 任务 | 状态 |
|------|------|
| 依赖安装 | 通过（pip） |
| uv sync | 跳过（uv 未安装，pip 可替代） |
| Playwright + `.browsers` | **通过**（本机 2026-06-01） |
| GUI 启动 + 主页面导航 | **通过**（本机 2026-06-01） |
| PDD 登录 / WS / 消息 / AI | **未测**（无测试店铺） |
| 核心链路文档化 | 完成 |
| 回归清单 | 完成（含 Phase 0 签收状态） |
| License 审计 | 完成（**风险已标记**） |

### 7.2 是否建议进入 Phase 1

| 结论 | 说明 |
|------|------|
| **建议进入 Phase 1 骨架** | GUI 壳层与 Playwright 已就绪；Phase 1 仅新增 `Channel/base/*`，**不改变运行时行为**，与 PDD 端到端是否测通无冲突 |
| **Phase 2 前门禁不变** | 必须在有测试店铺后跑通黄金路径 **步骤 3–8**（建议 3–11 全跑）并记录日志 |

未测 WS/发消息 **不阻塞** Phase 1；**阻塞** Phase 2（改 handler / 封装 Outbound）。

### 7.3 Phase 1 最小安全改动范围

**允许：**

- 新增目录 `Channel/base/`（`types.py`, `models.py`, `outbound.py`, `channel.py`, `registry.py`）
- 新增 `docs/*`、`.env.example`
- **不修改**任何现有 import 路径与运行时行为

**禁止：**

- 修改 `PDDChannel` / `pdd_message_handler` / `ai_handler` / Agent tools
- 修改 UI 逻辑
- 重命名 `Context` / 队列名

---

## 八、附录

### A. 已有抽象（Phase 1 可复用）

- `Channel/channel.py` — 抽象类，仅店铺管理与 `start_account` 声明
- `bridge/context.ChannelType` — 已枚举多平台名
- `core/di_container` — 可注册 `BaseChannel` 工厂（后续）

### B. 推荐本地命令（runbook 详见 `docs/runbook.md`）

```powershell
cd D:\agent
pip install -e .
python scripts/install_playwright.py   # 或: playwright install chromium
python app.py
```

### C. 审计人备注

- `handler_chain(..., businessHours=...)` 参数当前 **未被任何 handler 使用**，营业时间逻辑若要做，属于新功能而非 Phase 0 范围。

# Customer-Agent 运行模式说明

**文档导航：** [docs 目录](README.md) · [运行手册](runbook.md) · [当前架构](architecture_current.md)

本文档说明拼多多相关**环境变量运行模式**。LLM、数据库路径等仍见 `config.json` 与 [runbook.md](./runbook.md)。

---

## 1. 两个 flag 的分工

| 环境变量 | 作用 | 读取位置 |
|----------|------|----------|
| `USE_PINDUODUO_CHANNEL_WRAPPER` | `AutoReplyThread` 是否创建 `PinduoduoChannel`（包装 legacy `PDDChannel`） | `Channel/pinduoduo/channel_flags.py` |
| `USE_PINDUODUO_OUTBOUND` | handler / 即时消息是否优先走 `PinduoduoOutbound` | `Channel/pinduoduo/outbound_flags.py` → `outbound_resolver` |

二者**独立**：可只开其一，也可同时开启。

### ChannelRegistry bootstrap（Phase 8e，独立）

| 环境变量 | 作用 | 读取位置 |
|----------|------|----------|
| `USE_DEMO_CHANNEL_REGISTRATION` | `register_default_platforms()` 是否注册 Demo 工厂 | `Message/bootstrap_flags.py` |

- **默认 false**：默认计划只注册 `pinduoduo`；**不**启动 Demo runtime、**不** `start_account`。
- Demo 为 **test-only** 平台，不应作为生产默认启动项。
- `register_default_platforms()` **不** 替代 `create_auto_reply_runtime_channel()`；`AutoReplyThread` 仍不经 `ChannelRegistry.create()`（见 diagnose **Platform bootstrap** 段）。
- **8e 不接 app.py**；`app.py` 显式 bootstrap 规划为 **Phase 8f**。

```powershell
# 仅测试 / 脚本显式 bootstrap（生产 app 可不调用）
python -c "from Message.runtime_bootstrap import register_default_platforms; register_default_platforms()"
```

### Handler unified outbound（Phase 8c，独立）

| 环境变量 | 作用 | 读取位置 |
|----------|------|----------|
| `USE_UNIFIED_OUTBOUND_RESOLVER` | `ai_handler` / `keyword_handler` 使用 `resolve_outbound` 而非 `resolve_pinduoduo_outbound` | `Message/handlers/unified_outbound_flags.py` |

- **默认 false**（未设置 → 与 8c 前生产行为一致）。
- 真值：`1`、`true`、`yes`、`on`（大小写不敏感）。
- 与上文 **PDD 四模式正交**：不改变 `legacy-default` / `wrapper-and-outbound` 等模式 ID；仅切换 handler 出站**解析函数**。
- `pdd_message_handler` 即时消息路径**仍**只走 `resolve_pinduoduo_outbound`（未接 8c）。
- PDD 分支在 `resolve_outbound` 内**委托**旧 resolver，`USE_PINDUODUO_OUTBOUND` 语义不变。

```powershell
# 仅测试 Demo handler 出站（生产可不设）
$env:USE_UNIFIED_OUTBOUND_RESOLVER = "true"
python -m unittest tests.test_handler_unified_outbound -v
```

### UnifiedMessage shadow（Phase 7c，独立）

| 环境变量 | 作用 | 读取位置 |
|----------|------|----------|
| `USE_UNIFIED_MESSAGE_SHADOW` | WS 收消息后旁路调用 `pdd_to_unified` 并打摘要日志 | `Channel/pinduoduo/mappers/shadow_flags.py` |

- **默认 false**（未设置或空字符串）。
- 真值：`1`、`true`、`yes`、`on`（大小写不敏感）。
- **仅**用于开发/联调观测 mapper；**不**改变 `Context` 主路径、**不**影响 PDD 发送/接收入队、**不**让 `UnifiedMessage` 进入 `MessageConsumer`。
- 与 `USE_PINDUODUO_CHANNEL_WRAPPER` / `USE_PINDUODUO_OUTBOUND` **无依赖**，可任意组合。

```powershell
# 仅开启 shadow（生产默认可不设）
$env:USE_UNIFIED_MESSAGE_SHADOW = "true"
python app.py
```

### UnifiedMessage 双轨入队（Phase 7d，独立）

| 环境变量 | 作用 | 读取位置 |
|----------|------|----------|
| `USE_UNIFIED_MESSAGE_DUAL_TRACK` | 入队时 `MessageWrapper` 附带 `UnifiedMessage` 副本；Consumer metadata 增加观测字段 | `Channel/pinduoduo/mappers/dual_track_flags.py` |

- **默认 false**。
- 真值：`1`、`true`、`yes`、`on`（大小写不敏感）。
- **handler 仍只处理 legacy `Context`**；**不**替代 Context、**不**改变 `outbound_resolver` 与发送路径。
- 仅 **queue** 入队路径；immediate 消息不附带 unified。
- 与 `USE_UNIFIED_MESSAGE_SHADOW` **独立**；双轨 on 时 shadow **不再重复**调用 mapper。

```powershell
$env:USE_UNIFIED_MESSAGE_DUAL_TRACK = "true"
python app.py
```

### 默认值

- 未设置或空字符串 → **false**（与 Phase 0–3 行为一致）

### 视为 true 的值（大小写不敏感）

`1`、`true`、`yes`、`on`

---

## 2. 四种运行模式

| # | Channel wrapper | Outbound | 模式 ID | 行为摘要 |
|---|-----------------|----------|---------|----------|
| 1 | off | off | `legacy-default` | **生产默认**：`PDDChannel` + `SendMessage` |
| 2 | on | off | `wrapper-only` | `PinduoduoChannel` 委托 WS/队列；出站仍 legacy |
| 3 | off | on | `outbound-only` | `PDDChannel`；每条消息 `create` outbound，**不用 registry** |
| 4 | on | on | `wrapper-and-outbound` | wrapper + **registry 复用** `channel.outbound`（Phase 4b） |

### 重要说明

- **outbound on + wrapper off**：resolver 会为每条消息 `create_pinduoduo_outbound`，**不会**使用 `AccountOutboundRegistry`（无注册方）。
- **registry 复用** 需要 **wrapper on + outbound on**，且账号经 `PinduoduoChannel.start_account` 启动。

---

## 3. PowerShell 设置示例

```powershell
cd D:\agent

# 生产默认（可不设任何变量）
Remove-Item Env:USE_PINDUODUO_CHANNEL_WRAPPER -ErrorAction SilentlyContinue
Remove-Item Env:USE_PINDUODUO_OUTBOUND -ErrorAction SilentlyContinue
python app.py

# Phase 4b 目标模式（测试店联调）
$env:USE_PINDUODUO_CHANNEL_WRAPPER = "true"
$env:USE_PINDUODUO_OUTBOUND = "true"
python app.py
```

环境变量对**当前进程**生效；新开终端需重新设置。项目根 `.env` 不会自动加载（除非自行用工具注入）。

---

## 4. 回退

1. 关闭应用。
2. 取消变量或设为 `false`：
   ```powershell
   $env:USE_PINDUODUO_CHANNEL_WRAPPER = "false"
   $env:USE_PINDUODUO_OUTBOUND = "false"
   ```
3. 重新启动 `python app.py`。

无需改代码即可回到 **legacy-default**。

---

## 5. 与 config.json 的关系

| 配置 | 存放位置 | 内容示例 |
|------|----------|----------|
| LLM API、模型名 | `config.json` | `llm.api_key`、`llm.model_name` |
| 运行模式 flag | **环境变量** | 见上文 |
| 账号 cookies | `temp/channel_shop.db` | GUI 登录写入 |

运行模式**不**写入 `config.json`（Phase 5a 未做设置页开关）。

---

## 6. 诊断脚本（Phase 5a + 8d + 8e）

不启动 GUI、不连 PDD、不修改环境变量、**默认不**调用 `register_default_platforms()`：

```powershell
cd D:\agent
python scripts/diagnose_runtime.py
```

输出包括：

- Python 环境与项目根
- **全部 6 个 runtime flag**（含 `USE_DEMO_CHANNEL_REGISTRATION`）的 raw → resolved
- PDD 四模式 ID + 描述
- **Runtime capability report**（见 [phase8d_done.md](./phase8d_done.md)）
- **Platform bootstrap**：Available platforms、Default registration plan、Registered in this process、Bootstrap status
- `ChannelRegistry` 列表（**空列表属正常**，未 bootstrap 时）
- 分组 import 检查
- 提示：`AutoReplyThread` 未用 Registry；Registry 注册 ≠ GUI 切换；Demo test-only

Capability 字段另含：`bootstrap_status`、`default_registration_plan`、`available_platforms`（见 [phase8e_done.md](./phase8e_done.md)）。

---

## 7. Phase 4c 状态

**暂缓 / 跳过**：在 `MessageConsumer` 将 registry 结果镜像到 `metadata["outbound"]` 仅为可观测性优化；resolver 已可直接查 registry，非当前必需。

---

## 8. 相关文档索引

| 文档 | 内容 |
|------|------|
| [README.md](./README.md) | 文档目录与 Phase 全表 |
| [runbook.md](./runbook.md) | 安装、启动、PDD 登录 |
| [architecture_current.md](./architecture_current.md) | 架构基线、模块职责、四模式对照 |
| [phase2b_done.md](./phase2b_done.md) | handler outbound-first |
| [phase3b_done.md](./phase3b_done.md) | AutoReply wrapper 切换 |
| [phase4a_done.md](./phase4a_done.md) | resolver + registry |
| [phase4b_done.md](./phase4b_done.md) | Channel 注册 registry |

---

## 9. 附录：其它环境变量

| 变量 | 用途 |
|------|------|
| `PLAYWRIGHT_BROWSERS_PATH` | Playwright 浏览器目录（见 `app.py`、登录） |
| `LOG_LEVEL` | 日志级别（见 `utils/logger_loguru.py`） |
| `USE_UNIFIED_MESSAGE_SHADOW` | UnifiedMessage mapper 旁路日志（见上文 §1） |
| `USE_UNIFIED_MESSAGE_DUAL_TRACK` | UnifiedMessage 双轨入队（见上文 §1） |
| `USE_UNIFIED_OUTBOUND_RESOLVER` | handler 统一出站解析（见上文 §1） |
| `USE_DEMO_CHANNEL_REGISTRATION` | ChannelRegistry 注册 Demo 工厂（见上文 §1） |

与拼多多 Channel/Outbound 运行模式 flag 无强制组合关系。

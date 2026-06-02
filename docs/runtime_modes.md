# Customer-Agent 运行模式说明

本文档说明拼多多相关**环境变量运行模式**。LLM、数据库路径等仍见 `config.json` 与 [runbook.md](./runbook.md)。

---

## 1. 两个 flag 的分工

| 环境变量 | 作用 | 读取位置 |
|----------|------|----------|
| `USE_PINDUODUO_CHANNEL_WRAPPER` | `AutoReplyThread` 是否创建 `PinduoduoChannel`（包装 legacy `PDDChannel`） | `Channel/pinduoduo/channel_flags.py` |
| `USE_PINDUODUO_OUTBOUND` | handler / 即时消息是否优先走 `PinduoduoOutbound` | `Channel/pinduoduo/outbound_flags.py` → `outbound_resolver` |

二者**独立**：可只开其一，也可同时开启。

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

## 6. 诊断脚本

不启动 GUI、不连 PDD：

```powershell
cd D:\agent
python scripts/diagnose_runtime.py
```

输出：Python 环境、两 flag 解析、当前模式名称、关键模块 import、可选路径存在性。

---

## 7. Phase 4c 状态

**暂缓 / 跳过**：在 `MessageConsumer` 将 registry 结果镜像到 `metadata["outbound"]` 仅为可观测性优化；resolver 已可直接查 registry，非当前必需。

---

## 8. 相关文档索引

| 文档 | 内容 |
|------|------|
| [runbook.md](./runbook.md) | 安装、启动、PDD 登录 |
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

与拼多多运行模式 flag 无直接关系。

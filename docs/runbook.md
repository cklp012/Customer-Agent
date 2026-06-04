# Agent-Customer 本地运行手册（Phase 0）

**文档导航：** [docs 目录](README.md) · [当前架构](architecture_current.md) · [运行模式](runtime_modes.md) · [Phase 0 审计](phase0_audit.md)

> **本机已验证**（2026-06-01，Windows，`D:\agent`）：`install_playwright.py` → `app.py` GUI → 自动回复 / 关键词 / 账号(0) / 知识库 各页可打开。PDD 登录与 WS 待添加测试店铺后补测。详见 [phase0_audit.md](./phase0_audit.md) §2.2。

## 环境要求

- Windows 10/11
- Python **≥ 3.11**（推荐 3.11 或 3.12）
- 图形桌面（PyQt6）
- 可访问拼多多商家后台与 LLM API 的网络

## 安装

### 方式 A：uv（项目推荐）

```powershell
cd D:\agent
uv sync
```

### 方式 B：pip（无 uv 时）

```powershell
cd D:\agent
pip install -e .
```

### Playwright 浏览器（登录拼多多必需）

```powershell
cd D:\agent
python scripts/install_playwright.py
# 或
playwright install chromium
```

浏览器默认目录：项目根目录 **`.browsers`**（见 `app.py`）。

本机实测路径：`D:\agent\.browsers`（`python scripts/install_playwright.py` 成功后）。

## 启动

```powershell
cd D:\agent
python app.py
```

首次启动会在项目根生成 `config.json`（若不存在）。

启动后建议快速巡检（Phase 0 已通过项）：

| 页面 | 预期 |
|------|------|
| 自动回复 | 可打开；无账号时无法启动 WS |
| 关键词管理 | 可打开；显示默认关键词 |
| 账号管理 | 可打开；新环境账号数为 0 |
| 知识库 | 可打开；无店铺时提示先去账号管理添加 |

## 运行模式（高级，可选）

**默认无需设置任何环境变量**，即为 legacy 生产模式（`PDDChannel` + `SendMessage`）。

测试新架构（需真实 PDD 测试店联调）：

```powershell
$env:USE_PINDUODUO_CHANNEL_WRAPPER = "true"
$env:USE_PINDUODUO_OUTBOUND = "true"
python app.py
```

启动前可检查当前模式（不启 GUI、不连 PDD）：

```powershell
python scripts/diagnose_runtime.py
```

**Phase 9d：** AutoReply 默认经 ChannelRegistry 创建（无需再设 env）。故障回滚 legacy path：

```powershell
$env:USE_CHANNEL_REGISTRY_FOR_AUTOREPLY = "false"
python app.py
```

完整说明见 [runtime_modes.md](./runtime_modes.md) 与 [phase9d_done.md](./phase9d_done.md)。

## 最小配置

1. 打开应用 → **设置**
2. 填写 LLM：
   - `api_base`（OpenAI 兼容，如火山引擎）
   - `api_key`
   - `model_name`
3. 保存后重启自动回复

## 拼多多账号（Phase 0 补测 — 尚未在本机执行）

1. **用户/账号** 页 → 添加账号 → 使用 Playwright 登录（需真实拼多多商家账号）
2. 登录成功后 cookies 写入 `temp/channel_shop.db`
3. **自动回复** 页 → 启动对应账号 → 观察连接状态为已连接
4. 用买家号发「你好」→ 验证收消息、AI 回复、`send_text`（见审计文档黄金路径 #4–#8）

完成上述步骤后，在 `phase0_audit.md` 第五节勾选 #3–#11。

## 数据文件位置

| 路径 | 说明 |
|------|------|
| `config.json` | 用户配置 |
| `temp/channel_shop.db` | 渠道/店铺/账号/关键词 |
| `temp/agent.db` | Agent 会话历史（默认，见 `agent_config.DEFAULT_DB_PATH`） |
| `logs/` | Loguru 日志（若配置） |

## 冒烟测试（无 GUI）

```powershell
cd D:\agent
python -c "from config import config; from Channel.pinduoduo.pdd_channel import PDDChannel; print('import ok')"
```

## 打包（可选）

```powershell
python scripts/build_win_exe.py --clean
```

产物：`dist/AgentCustomer/`

## 故障排查

| 现象 | 可能原因 |
|------|----------|
| 登录窗口打不开 | 未安装 Playwright Chromium |
| AI 不回复 | `llm.api_key` 为空或无效 |
| WS 连不上 | cookies 过期 → 重新登录；检查 `get_token` |
| 设置保存后营业时间无效 | 已知：`businessHours` 键名与代码不一致，当前未接入 handler |

详细审计见 [phase0_audit.md](./phase0_audit.md)。

## Phase 0 验证清单（可复制勾选）

```
[x] pip install -e . 或 uv sync
[x] python scripts/install_playwright.py  →  D:\agent\.browsers
[x] python app.py 主窗口启动
[x] 自动回复 / 关键词 / 账号 / 知识库 页面可打开
[ ] 设置页配置 LLM 并保存
[ ] 账号管理：拼多多登录并添加店铺
[ ] 自动回复：启动 WS 连接
[ ] 收消息 + AI 回复 + send_text
[ ] 关键词转人工 / 商品卡 / 断线重连（可选）
```

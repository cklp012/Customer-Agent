# Phase 9c 完成记录 — Registry path parity hardening

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| 路线 | B（默认值不变） |

---

## 1. 交付

| 文件 | 作用 |
|------|------|
| `tests/test_autoreply_registry_parity.py` | registry ≡ legacy；默认 legacy；bootstrap 无 fallback |
| `runtime_capabilities.py` | capability 报告 Notes（9c 仍默认 legacy） |
| `diagnose_runtime.py` | 9c 灰度 / 9d 说明 |
| 文档 | phase9c_plan、phase9_plan、runtime_modes、architecture、README |

---

## 2. 默认值

`USE_CHANNEL_REGISTRY_FOR_AUTOREPLY`：**未改**，未设置环境变量 → **false** → `legacy_factory`。

---

## 3. 手动 app.py 黄金路径验证（待执行）

在真实 PDD 测试店执行并勾选：

- [ ] `python app.py` 能正常启动
- [ ] **默认 env**（不设 registry flag）启动账号 → 仍为 legacy path（`PDDChannel`）
- [ ] 设置 `USE_CHANNEL_REGISTRY_FOR_AUTOREPLY=true` 后重启 app，再启动账号
- [ ] `USE_PINDUODUO_CHANNEL_WRAPPER` 未设置：账号 channel 仍为 `PDDChannel` 行为
- [ ] （可选）`USE_PINDUODUO_CHANNEL_WRAPPER=true`：应为 `PinduoduoChannel` 包装层
- [ ] 日志中无 `ChannelRegistry.create fallback for AutoReply` warning
- [ ] 能连接 / 停止账号
- [ ] 自动回复黄金路径（收消息 → handler → 出站）后续人工验证

```powershell
# 灰度 registry path（需重启 app）
$env:USE_CHANNEL_REGISTRY_FOR_AUTOREPLY = "true"
python app.py
```

---

## 4. 9d 留待

默认开启 registry path（改 flag 默认或 app setdefault）。

# Phase 9d 完成记录 — AutoReply Registry default-on

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| 路线 | C |

---

## 1. 默认值

| env | `use_channel_registry_for_autoreply()` |
|-----|--------------------------------------|
| 未设置 (None) | **true** |
| `false` / `0` / `no` / `off` | false |
| `true` / `1` / `yes` / `on` | true |
| `""` 或未知值 | false |

---

## 2. 保留

- `_create_auto_reply_legacy` fallback
- `create_auto_reply_runtime_channel` / `create_pinduoduo_registry_channel`
- `USE_PINDUODUO_CHANNEL_WRAPPER` 默认仍 false → 生产仍默认 `PDDChannel`

---

## 3. 回滚

```powershell
$env:USE_CHANNEL_REGISTRY_FOR_AUTOREPLY = "false"
python app.py
```

---

## 4. 9d 后建议手动冒烟

- [ ] `python app.py`（**无需**再设 registry flag）
- [ ] 默认 env 启动 / 停止账号
- [ ] 日志无 `ChannelRegistry.create fallback for AutoReply`
- [ ] 自动回复黄金路径（可选）

---

## 5. 测试

`test_autoreply_registry_default.py` + 更新 parity / capabilities / channel_switch。

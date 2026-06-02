# Phase 3b 完成记录 — AutoReplyThread 使用 PinduoduoChannel 包装层

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-02 |
| 范围 | `channel_flags` + `channel_factory` 扩展 + `ui/auto_reply/threads.py` |

---

## 1. 修改文件清单

| 操作 | 文件 |
|------|------|
| 新增 | `Channel/pinduoduo/channel_flags.py` |
| 修改 | `Channel/pinduoduo/channel_factory.py` |
| 修改 | `ui/auto_reply/threads.py` |
| 新增 | `tests/test_auto_reply_channel_switch.py` |
| 新增 | `docs/phase3b_done.md` |
| 可选 | `.env.example`（`USE_PINDUODUO_CHANNEL_WRAPPER` 注释） |

---

## 2. 行为说明

| `USE_PINDUODUO_CHANNEL_WRAPPER` | AutoReplyThread 创建 | `start_account` |
|--------------------------------|----------------------|-----------------|
| 未设置 / false（默认） | `PDDChannel()` | legacy 四参数 |
| true | `PinduoduoChannel()` | `on_message=noop` + 委托 legacy |

`stop()` 仍为 `channel.request_stop()`，未改停止逻辑。

---

## 3. 与 `USE_PINDUODUO_OUTBOUND` 关系

| 变量 | 作用 |
|------|------|
| `USE_PINDUODUO_CHANNEL_WRAPPER` | UI 运行时 Channel 类型 |
| `USE_PINDUODUO_OUTBOUND` | handler 出站是否走 `PinduoduoOutbound` |

二者独立，可分别开关。

---

## 4. 快速回退

```powershell
# 取消或关闭包装层
$env:USE_PINDUODUO_CHANNEL_WRAPPER="false"
# 重启应用
```

---

## 5. 禁止路径

未改：`app.py`、`Message/`、`Agent/`、`Channel/pinduoduo/core/`、`pdd_channel.py`、`handlers`、`pdd_login.py`、`utils/`。

---

## 6. 测试

```powershell
python -m unittest discover -s tests -v
```

---

## 7. 签收

- [x] feature flag 默认 off
- [x] `start_auto_reply_account` 统一签名
- [x] `stop()` 未改
- [ ] 本机 flag on + 真实 PDD 店联调（建议维护者执行）

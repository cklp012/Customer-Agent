# Phase 3a 完成记录 — PinduoduoChannel 包装 PDDChannel

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-02 |
| 项目路径 | `D:\agent` |
| 范围 | 仅新增 `PinduoduoChannel` + factory + 测试；**未接入 UI / 运行时** |

---

## 1. 新增文件清单

| 文件 | 作用 |
|------|------|
| `Channel/pinduoduo/pinduoduo_channel.py` | `PinduoduoChannel(BaseChannel)`，委托 `PDDChannel` |
| `Channel/pinduoduo/channel_factory.py` | `create_pinduoduo_channel` / `register_pinduoduo_channel` |
| `tests/test_pinduoduo_channel.py` | mock legacy 单测 |
| `docs/phase3_done.md` | 本文档 |

---

## 2. Strangler 结构

```text
PinduoduoChannel (BaseChannel)
  ├─ _legacy: PDDChannel          # WebSocket / 队列 / handler_chain
  ├─ outbound (lazy)              # create_pinduoduo_outbound(shop_id, account_id)
  ├─ start_account → legacy.start_account
  ├─ stop_account  → legacy.stop_account
  ├─ reconnect     → stop + start（复用已存回调）
  ├─ get_status    → status_manager + ConnectionState→ChannelStatus
  ├─ login         → await pdd_login.login_pdd（未改 pdd_login.py）
  ├─ logout        → stop_account
  └─ request_stop  → legacy.request_stop
```

**生产运行时仍为：** `ui/auto_reply/threads.py` → `PDDChannel()`（Phase 3b 再切换）。

---

## 3. 设计要点

| 项 | 说明 |
|----|------|
| `on_message` | Phase 3a 仅保存，不调用（推送型 PDD） |
| `outbound` | `start_account` 前访问 → `RuntimeError` |
| `ChannelRegistry` | 仅 `register_pinduoduo_channel()` 显式注册；**不在 app.py 注册** |
| Handler 出站 | 仍用 `resolve_pinduoduo_outbound`（Phase 3b+ 可注入 metadata） |

---

## 4. 禁止路径

**均未修改：** `app.py`、`ui/`、`Message/handlers`、`Message/core`、`pdd_channel.py`、`core/*`、`pdd_login.py`、`pdd_message.py`、`utils/`、`Agent/`。

---

## 5. 测试结果

```powershell
python -m unittest discover -s tests -v
```

```
Ran 40 tests — OK（含 Phase 3a 新增 12 项）
```

```powershell
python -c "from Channel.pinduoduo.pinduoduo_channel import PinduoduoChannel; from Channel.base import BaseChannel; print('ok')"
```

---

## 6. 运行时接入检查

```text
grep PinduoduoChannel
```

预期：仅 `Channel/pinduoduo/pinduoduo_channel.py`、`channel_factory.py`、`tests/`、`docs/phase3_done.md`。**无** `ui/` / `app.py` 引用。

---

## 7. app.py 冒烟

等价启动链：`MainWindow instantiated ok`。建议本机 `python app.py` 目视。

---

## 8. Phase 3b / 4 建议

| 阶段 | 内容 |
|------|------|
| **3b** | `AutoReplyThread` 改用 `PinduoduoChannel` 或 `ChannelRegistry.create` |
| **4** | consumer 注入 `metadata['outbound']`；`Context` → `UnifiedMessage` mapper |

---

## 9. 签收

- [x] PinduoduoChannel 实现 BaseChannel
- [x] 委托 legacy，未改 PDDChannel / core
- [x] 未接入 UI
- [x] registry 工厂（测试注册）
- [x] unittest 全绿
- [ ] 本机 `python app.py` 目视（建议维护者执行）

# Phase 4b 完成记录 — PinduoduoChannel 注册 AccountOutboundRegistry

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-02 |
| 范围 | 仅 `Channel/pinduoduo/pinduoduo_channel.py` + 测试 + 文档 |

---

## 1. 修改文件清单

| 操作 | 文件 |
|------|------|
| 修改 | `Channel/pinduoduo/pinduoduo_channel.py` |
| 新增 | `tests/test_pinduoduo_channel_registry.py` |
| 新增 | `docs/phase4b_done.md` |

---

## 2. 行为说明

| 生命周期 | 动作 |
|----------|------|
| `start_account`（legacy 成功后） | `register(shop_id, account_id, self.outbound)` |
| `stop_account` | `await legacy.stop_account` → `unregister` → 清空 `_outbound` |
| `request_stop` | 仅 `legacy.request_stop()`，**不** `unregister` |

`legacy.start_account` 抛异常时 **不** 注册 registry。

注册本身不依赖 `USE_PINDUODUO_OUTBOUND`；resolver 仅在 outbound flag on 时读取 registry。

---

## 3. 双 flag 组合（运行时）

| `USE_PINDUODUO_CHANNEL_WRAPPER` | `USE_PINDUODUO_OUTBOUND` | 出站行为 |
|--------------------------------|--------------------------|----------|
| off | off | legacy `SendMessage`（现网默认） |
| on | off | 包装 Channel；handler 仍 legacy 出站 |
| off | on | 每消息 `create`（无 registry 条目） |
| on | on | **复用** `channel.outbound`（registry 命中） |

---

## 4. `request_stop` 不清 registry 的原因

UI `AutoReplyThread.stop()` 只调 `request_stop()` + 停 event loop，**不**调 `stop_account`。registry 与完整停账号绑定，避免 WS 仍在跑时 outbound 被摘掉导致后续消息误 `create` 或串号。

---

## 5. 未修改

- `ui/`、`app.py`、`Message/handlers`（除 registry 被 channel import）、`consumer`、`core/`、`pdd_channel.py`

---

## 6. Phase 4c（可选）

`consumer.py` 将 registry 查到的 outbound 写入 `metadata["outbound"]`（可观测性，非必须）。

---

## 7. 测试

```powershell
python -m unittest discover -s tests -v
```

---

## 8. 签收

- [x] start 注册 / stop 注销
- [x] start 失败不注册
- [x] request_stop 不注销
- [x] resolver + flag on 复用同一 outbound
- [ ] wrapper on + outbound on + 真实 PDD 店联调（建议维护者执行）

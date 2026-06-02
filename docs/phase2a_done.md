# Phase 2a 完成记录 — 拼多多出站适配器

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-02 |
| 项目路径 | `D:\agent` |
| 范围 | 仅新增 `Channel/pinduoduo/*_outbound*` + `tests/` + `.env.example` 一行注释，**零 handler / 零运行时接入** |

---

## 1. 新增文件列表

| 文件 | 作用 |
|------|------|
| `Channel/pinduoduo/pinduoduo_outbound.py` | `PinduoduoOutbound` + `_normalize_send_result` |
| `Channel/pinduoduo/outbound_factory.py` | `create_pinduoduo_outbound(shop_id, user_id)` |
| `Channel/pinduoduo/outbound_flags.py` | `use_pinduoduo_outbound()`，读 `USE_PINDUODUO_OUTBOUND` |
| `tests/__init__.py` | 测试包 |
| `tests/test_pinduoduo_outbound_import.py` | import / Protocol / normalize 冒烟 |
| `tests/test_pinduoduo_outbound_mock.py` | mock 异步发送与转接 |
| `.env.example` | 追加 `USE_PINDUODUO_OUTBOUND` 说明（注释行） |

---

## 2. `_normalize_send_result` 规则

| 输入 | 输出 |
|------|------|
| `None` | `False` |
| `str`（如 error_code 10002 时的错误文案） | `False` |
| `dict` 且 `success is True` | `True` |
| `dict` 且 `success` 为 False 或缺失 | `False` |
| 其他类型 | `False`（debug 日志） |

`send_text` / `send_image` / `send_mallGoodsCard` / `move_conversation` 均经此函数归一化，与 Phase 2b 将对齐的 `ai_handler._send_reply` 判断一致。

---

## 3. `transfer_to_human` 行为

对齐 `Agent/CustomerAgent/tools/move_conversation.py`：

1. `getAssignCsList()`
2. 过滤 `cs_{shop_id}_{user_id}`（不转给自己）
3. 取第一个可用客服 `move_conversation(conversation_id, cs_uid)`

**刻意不做：** 转接前后 **不** 调用 `send_text` 发提示语，避免改变现网行为。

`reason` 参数保留签名兼容 Protocol，当前未使用。

---

## 4. `fetch_order` 占位

暂无拼多多订单查询 API 封装，`fetch_order` 恒返回 `None`，不抛异常。

---

## 5. 环境变量

| 变量 | 默认 | 真值 |
|------|------|------|
| `USE_PINDUODUO_OUTBOUND` | 关闭 | `1` / `true` / `yes` / `on`（大小写不敏感） |

Phase 2a **无任何业务代码读取此开关**；供 Phase 2b 在 handler 中切换。

---

## 6. 是否修改业务代码

**否。** 以下均未改动：

- `Message/handlers/ai_handler.py`
- `Message/handlers/keyword_handler.py`
- `Channel/pinduoduo/core/`、`pdd_channel.py`、`utils/`
- `Agent/`、`ui/`、`app.py`、`config.py`、`bridge/context.py`、`Message/core/`

---

## 7. 运行时接入检查

```text
grep "pinduoduo_outbound\|create_pinduoduo_outbound\|use_pinduoduo_outbound" --glob "*.py"
```

预期：仅 `Channel/pinduoduo/` 新增模块与 `tests/`，**无** handler / Agent / ui 引用。

---

## 8. 测试结果

### 8.1 import

```powershell
cd D:\agent
python -c "from Channel.pinduoduo.pinduoduo_outbound import PinduoduoOutbound; from Channel.pinduoduo.outbound_factory import create_pinduoduo_outbound; from Channel.pinduoduo.outbound_flags import use_pinduoduo_outbound; from Channel.base.outbound import ChannelOutbound; print('import ok', use_pinduoduo_outbound())"
```

### 8.2 unittest

```powershell
python -m unittest discover -s tests -p "test_pinduoduo_outbound*.py" -v
```

### 8.3 GUI 冒烟

```powershell
python app.py
```

建议维护者目视确认与 Phase 0 一致。

---

## 9. Phase 2b 预告（不实施）

1. 在 `Message/handlers/ai_handler.py` 的 `_send_reply`：`use_pinduoduo_outbound()` 为真时用 `create_pinduoduo_outbound` + `await outbound.send_text`，否则保留现有 `SendMessage`。
2. 同理改造 `keyword_handler.py` 转人工路径。
3. 合并前需真实拼多多测试店验证黄金路径。

---

## 10. 签收

- [x] 仅新增 outbound 层与 tests
- [x] 无 handler / 运行时接入
- [x] `ChannelOutbound` Protocol 实现
- [x] `transfer_to_human` 不发提示文本
- [x] `fetch_order` 占位返回 `None`
- [ ] 本机 `python app.py` 目视复验（建议维护者执行）
- [ ] 真实 PDD 店 API 联调（Phase 2b 后）

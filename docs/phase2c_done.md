# Phase 2c 完成记录 — pdd_message_handler 即时消息 outbound-first + legacy fallback

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-02 |
| 项目路径 | `D:\agent` |
| 范围 | 仅 `Channel/pinduoduo/core/pdd_message_handler.py` 的即时消息发送点（WITHDRAW / TRANSFER） |

---

## 1. 修改文件清单

| 操作 | 文件 |
|------|------|
| 修改 | `Channel/pinduoduo/core/pdd_message_handler.py`（`_handle_immediate_message` + 新增 2 个私有方法） |
| 新增 | `tests/test_immediate_message_outbound.py` |
| 新增 | `docs/phase2c_done.md` |

**禁止路径：均未修改。** `outbound_resolver.py` / `ai_handler.py` / `keyword_handler.py` / `SendMessage` / WebSocket / 队列 / Context 创建 / handler_chain / Agent / UI 全部未动。

---

## 2. 即时消息出站链路（改造后）

```text
_process_websocket_message
  → _convert_to_context
  → _should_process_immediately?
      → _handle_immediate_message(context, shop_id, user_id)
            ├─ WITHDRAW → await _send_immediate_text(..., "[玫瑰]")
            ├─ TRANSFER → await _send_immediate_text(..., "[玫瑰]")
            └─ AUTH / SYSTEM_STATUS / SYSTEM_HINT / MALL_CS → 仅日志，不发送

_send_immediate_text(context, shop_id, user_id, recipient_uid, text):
  1. outbound = resolve_pinduoduo_outbound({}, context)
  2. outbound 存在 → await outbound.send_text(recipient_uid, text)；成功 return True
  3. 失败 → warning → legacy
  4. _send_immediate_text_legacy(shop_id, user_id, recipient_uid, text)

_send_immediate_text_legacy:
  惰性构造 SendMessage(shop_id, user_id).send_text(recipient_uid, text)
  → dict 且 success 为 True 返回 True，否则 False
```

---

## 3. 关键改动

| 改动 | 说明 |
|------|------|
| 移除顶部无条件 `SendMessage(shop_id, user_id)` | 非发送类型（AUTH 等）不再构造、不再查账户 DB |
| 惰性构造 | 仅 WITHDRAW / TRANSFER 真正发送时，由 legacy 内部构造 SendMessage |
| outbound-first | 复用 `resolve_pinduoduo_outbound({}, context)`，从 `context.kwargs` 取 shop_id/user_id/from_uid |
| 局部 import | `resolve_pinduoduo_outbound` 在方法内 import，避免模块级循环 |

---

## 4. `USE_PINDUODUO_OUTBOUND` 默认关闭

flag 未设置时 `resolve` 恒返回 `None` → 直接 legacy，即时消息行为与 Phase 2c 前一致（撤回/转接回「[玫瑰]」）。

---

## 5. legacy 保留逻辑

| 场景 | 行为 |
|------|------|
| flag off | 仅 legacy 发「[玫瑰]」 |
| resolve None（缺字段） | legacy |
| outbound 发送失败 | warning → legacy |
| 文案 | 固定「[玫瑰]」，未改 |
| 触发类型 | 仅 WITHDRAW / TRANSFER，未改 |
| 非发送分支 | AUTH/SYSTEM_STATUS/SYSTEM_HINT/MALL_CS 仅日志，未改 |

---

## 6. 测试命令与结果

```powershell
cd D:\agent
python -m unittest discover -s tests -v
```

```
Ran 27 tests in ~1.4s — OK
```

Phase 2c 新增 6 项：

- `test_flag_off_withdraw_uses_legacy`
- `test_flag_off_transfer_uses_legacy`
- `test_outbound_success_skips_legacy`
- `test_outbound_fail_falls_back_legacy`
- `test_non_send_types_do_not_send`
- `test_message_text_is_rose`

---

## 7. app.py 冒烟

等价启动链（`configure_standard_services` + `MainWindow()`）：`MainWindow instantiated ok`。建议本机再执行一次 `python app.py` 目视。

---

## 8. 真实 PDD 店铺未测

以 mock / flag off 为主。**未**在真实拼多多测试店验证：买家撤回 / 转接是否经 outbound 收到「[玫瑰]」。建议测试店设 `USE_PINDUODUO_OUTBOUND=true` 后复验。

---

## 9. Phase 3 建议

| 项 | 内容 |
|----|------|
| `PinduoduoChannel` | 实现 `BaseChannel`，集中持有 outbound 实例 |
| outbound 注入 | 由 Channel/consumer 注入 outbound 到 metadata，handler / 即时路径不再每次 `create` |
| Mapper | `PDDChatMessage` / `Context` → `UnifiedMessage` |
| registry | 启动时 `ChannelRegistry.register(PINDUODUO, factory)` |

---

## 10. 签收

- [x] 仅改即时消息发送点 + 新增测试 + 文档
- [x] 移除顶部无条件 SendMessage 构造
- [x] WITHDRAW / TRANSFER outbound-first + legacy fallback
- [x] 非发送分支与「[玫瑰]」文案未变
- [x] 禁止路径未改
- [x] unittest 27 项全绿
- [x] 启动链 + MainWindow 实例化通过
- [ ] 本机 `python app.py` 目视（建议维护者执行）
- [ ] 真实 PDD 店联调（待测试店）

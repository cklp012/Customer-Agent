# Phase 2b 完成记录 — Handler outbound-first + legacy fallback

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-02 |
| 项目路径 | `D:\agent` |
| 范围 | `outbound_resolver` + `ai_handler._send_reply` + `keyword_handler.handle` 转人工段 |

---

## 1. 修改文件清单

| 操作 | 文件 |
|------|------|
| 新增 | `Message/handlers/outbound_resolver.py` |
| 修改 | `Message/handlers/ai_handler.py`（仅 `_send_reply`，新增 `_send_text_legacy`） |
| 修改 | `Message/handlers/keyword_handler.py`（仅 `handle` 转人工，新增 `_transfer_to_human_legacy`） |
| 新增 | `tests/test_outbound_resolver.py` |
| 新增 | `tests/test_handler_outbound_mock.py` |
| 新增 | `docs/phase2b_done.md` |

**禁止路径：均未修改。**

---

## 2. outbound-first + legacy fallback

```text
resolve_pinduoduo_outbound(metadata, context)
  ├─ USE_PINDUODUO_OUTBOUND=false → None → 直接 legacy
  ├─ 缺 shop_id/user_id/from_uid → None → legacy
  ├─ create 异常 → None → legacy
  └─ 有 outbound
        ├─ send_text / transfer_to_human 成功 → True
        └─ 失败 → warning → 整段 legacy（keyword 含离线提示）
```

---

## 3. `USE_PINDUODUO_OUTBOUND`

| 变量 | 默认 | 说明 |
|------|------|------|
| `USE_PINDUODUO_OUTBOUND` | **关闭** | 未设置时与 Phase 2b 前行为一致，仅走 legacy `SendMessage` |

测试环境启用：`USE_PINDUODUO_OUTBOUND=true`

---

## 4. `ai_handler` 改动

- `_send_reply`：`extract_pdd_send_context` → `resolve` → `await outbound.send_text` → 失败则 `_send_text_legacy`
- `_send_text_legacy`：原 `SendMessage` + `success` 判断，逻辑未改
- `handle` / `_handle_fallback` / `_get_ai_reply` 未动；fallback 仍经 `_send_reply`，自动获得 outbound-first

---

## 5. `keyword_handler` 改动

- `handle`：extract → resolve → `await outbound.transfer_to_human(..., reason="keyword")` → 失败则 `_transfer_to_human_legacy`
- `_transfer_to_human_legacy`：原 `getAssignCsList` / 过滤自己 / `move_conversation` / 无客服 `send_text` 离线提示

---

## 6. legacy 保留逻辑

| 场景 | 行为 |
|------|------|
| flag off | 仅 legacy |
| outbound 创建失败 | legacy |
| outbound 发送/转接失败 | legacy |
| 无其他客服 | legacy `send_text` 离线文案 |
| 转接成功 | 不发额外文本；legacy 路径保留 `cs_name` 日志 |

---

## 7. 测试命令与结果

```powershell
cd D:\agent
python -m unittest discover -s tests -v
```

```
Ran 21 tests in ~1.4s — OK
```

---

## 8. 真实 PDD 店铺

本阶段以 mock / 开关关闭为主。**未**在真实拼多多测试店验证 WebSocket 收消息、AI 回复、关键词转人工。建议在测试店设置 `USE_PINDUODUO_OUTBOUND=true` 后复验 `docs/phase0_audit.md` 黄金路径。

---

## 9. Phase 2c / Phase 3 建议

| 阶段 | 内容 |
|------|------|
| **2c（可选）** | `pdd_message_handler` 即时消息（如撤回发「[玫瑰]」）走 outbound |
| **3** | `PinduoduoChannel` 实现 `BaseChannel`；handler 从 metadata 注入 `outbound` 实例；减少每消息 `create` |

---

## 10. 签收

- [x] outbound_resolver 新增
- [x] ai_handler outbound-first + legacy
- [x] keyword_handler outbound-first + 整段 legacy fallback
- [x] 禁止路径未改
- [x] unittest 21 项全绿
- [x] 启动链 + `MainWindow` 实例化通过（等价 `app.py` 冒烟）
- [ ] 本机 `python app.py` 目视（建议维护者执行）
- [ ] 真实 PDD 店联调（待测试店）

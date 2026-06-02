# Phase 4a 完成记录 — outbound_resolver 支持 metadata / registry 复用

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-02 |
| 范围 | 仅 `account_outbound_registry` + `outbound_resolver` 增强 |

---

## 1. 新增 / 修改文件

| 操作 | 文件 |
|------|------|
| 新增 | `Message/handlers/account_outbound_registry.py` |
| 修改 | `Message/handlers/outbound_resolver.py` |
| 新增 | `tests/test_outbound_resolver_injection.py` |
| 新增 | `docs/phase4a_done.md` |

---

## 2. `resolve_pinduoduo_outbound` 解析顺序

| 条件 | 结果 |
|------|------|
| `USE_PINDUODUO_OUTBOUND` 未开启 | **立即 `None`**（不读 metadata / registry） |
| flag on，三元组不全 | `None` |
| flag on，`metadata["outbound"]` 合法且账号匹配 | 返回该实例 |
| flag on，`AccountOutboundRegistry.get` 合法 | 返回该实例 |
| 否则 | `create_pinduoduo_outbound(shop_id, user_id)` |

`_is_usable_pinduoduo_outbound` 校验：`send_text`、`transfer_to_human`、`shop_id`/`user_id` 一致。

---

## 3. Phase 4a 明确未做

- **未**在 `PinduoduoChannel.start/stop` 注册 registry（无生产注入源）
- **未**改 `consumer.py` 写 `metadata["outbound"]`
- **未**改 `ai_handler` / `keyword_handler` / `pdd_message_handler`（仍只调 `resolve`）

因此 **默认双 flag off 行为不变**；flag on 且无 metadata/registry 时仍每消息 `create`（与 Phase 2b 相同）。

---

## 4. Phase 4b 预告

- `PinduoduoChannel.start_account` → `AccountOutboundRegistry.register`
- `stop_account` → `unregister`
- 双 flag on 时复用 `channel.outbound`，减少重复 `create`

---

## 5. 禁止路径

未改：handlers（除 resolver 包内新增 registry）、`PinduoduoChannel`、`consumer`、`core/`、`ui/`、`app.py`、`Agent/`、`bridge/context.py`。

---

## 6. 测试

```powershell
python -m unittest discover -s tests -v
```

---

## 7. 签收

- [x] registry API
- [x] resolver 三阶解析 + flag off 门禁
- [x] 7 项 injection 单测
- [ ] Phase 4b 注册与真实店联调（后续）

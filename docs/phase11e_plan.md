# Phase 11e 规划 — DoudianMockChannel Outbound Auto-Registration

| 项 | 值 |
|----|-----|
| 类型 | **实现 SSOT**（Route C：`doudian_channel.py` + lifecycle tests） |
| 状态 | 执行后见 [phase11e_done.md](phase11e_done.md) |
| 前置 | [phase11d_done.md](phase11d_done.md) |

---

## 目标

`DoudianMockChannel.start_account` / `stop_account` 自动 **register / unregister** `DoudianMockOutbound` 到 **`channel_outbound_registry`**，使 `resolve_outbound` 在 channel 启动后无需手动 register 即可命中。

**不变：**

- PDD 生产路径、handlers 默认、`USE_*` flag 默认值
- 默认 bootstrap 不注册 Doudian（`USE_DOUDIAN_CHANNEL_REGISTRATION` 默认 false）
- `USE_UNIFIED_OUTBOUND_RESOLVER` 默认 false

---

## start_account register

```python
channel_outbound_registry.register(
    PlatformType.DOUDIAN,
    shop_id,
    account_id,
    self._outbound,
)
```

- 创建 `DoudianMockOutbound` 后、 `on_success()` 前
- 无网络、无线程、无真实 API
- **不** 写入 `AccountOutboundRegistry`

---

## stop_account unregister

```python
channel_outbound_registry.unregister(PlatformType.DOUDIAN, shop_id, account_id)
```

- **对传入 shop/account 始终 unregister**（对齐 PDD `PinduoduoChannel.stop_account`）
- 仅当 shop/account 匹配当前 channel 时清理 `_outbound` / `_status`

---

## reconnect

`stop_account` → `start_account`：registry 先空后重新注册新 outbound 实例。

---

## 不改 PDD / 不开 resolver flag

| 项 | 11e |
|----|-----|
| `Channel/pinduoduo/**` | 不改 |
| handlers 默认 | 不改 |
| `USE_UNIFIED_OUTBOUND_RESOLVER` | 默认 false |
| AutoReply | PDD-only |

---

## 测试矩阵

| ID | 文件 | 用例 |
|----|------|------|
| L1 | `test_doudian_channel_outbound_lifecycle.py` | start → registry 同一实例 |
| L2 | stop → registry None |
| L3 | start → stop → start 重注册 |
| L4 | start 后 `resolve_outbound` 命中（无手动 register） |
| L5 | stop 后 `resolve_outbound` None |
| L6 | 无 PDD key；doudian resolve 不调用 PDD resolver |
| + | stop 传入 key 始终 unregister；reconnect 重注册 |

**保留：** `tests/test_doudian_outbound_resolver_contract.py`（11c 手动 register 锚点）

---

## 后续

**11f（可选）：** handler + `USE_UNIFIED_OUTBOUND_RESOLVER=true` 抖店联调测试（仅测试 env）

---

*Phase 11e · Route C*

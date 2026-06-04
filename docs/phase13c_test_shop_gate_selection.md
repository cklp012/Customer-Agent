# Phase 13c — Test Shop Gate Selection

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 实现 Phase | **13d**（in-memory / env test fixture） |
| DB Phase | **13e+**（`ShopBinding.product_gate_enabled` 持久化） |

---

## 1. 设计目标

用**显式、可审计、无歧义**的规则，判定一条 PDD 入站消息是否进入 **preview gate** 路径。

**禁止：**

- 模糊 `shop_name` 子串匹配
- 默认所有 PDD 店铺开启 gate
- 通过全局 env 默认 `product_gate_enabled=true`
- Doudian / 非 PDD 平台误入 gate

---

## 2. Allowlist 结构（概念模型）

### 2.1 `test_shop_allowlist`

每条记录为 **一条绑定**（与 12b `ShopBinding` 对齐，13d 用内存结构模拟）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `workspace_id` | string (UUID) | ✅ | 租户隔离 |
| `shop_binding_id` | string (UUID)? | 推荐 | 13e DB 主键；13d 可省略 |
| `account_id` | string | ✅* | PDD 账号 / 登录维度（与 metadata 一致） |
| `shop_id` | string | ✅ | PDD `shop_id`；队列 `pdd_{shop_id}` |
| `platform_id` | enum | ✅ | **固定 `pinduoduo`** |
| `product_gate_enabled` | bool | ✅ | test 记录必须为 **true** |
| `reply_mode` | enum | ✅ | test 记录必须为 **preview** |
| `consultation_only` | bool | ✅ | test 记录必须为 **true** |
| `workspace_pause` | bool | 可选 snapshot | 默认 false |
| `shop_pause` | bool | 可选 snapshot | 默认 false |
| `label` | string? | 可选 | 如 `pdd-golden-path-test-shop`（仅文档/运维） |

\* `account_id` 与 `shop_id` **至少一个**在运行时 metadata 中可解析；匹配规则见 §3。

### 2.2 示例（13d fixture，非生产配置）

```yaml
# 概念 — phase13d_test_shop_allowlist.yaml（仅测试/本地）
test_shop_allowlist:
  - workspace_id: "ws-test-0001"
    account_id: "acc_pdd_test_01"
    shop_id: "shop_pdd_test_01"
    platform_id: pinduoduo
    product_gate_enabled: true
    reply_mode: preview
    consultation_only: true
```

---

## 3. Gate selection 规则（SSOT）

### 3.1 判定顺序

```text
1) platform_id == pinduoduo ?  ─no→ LEGACY
2) extract (workspace_id, shop_id, account_id) from metadata/context
3) tuple 命中 test_shop_allowlist 且 product_gate_enabled==true ?  ─no→ LEGACY
4) reply_mode == preview ?  ─no→ LEGACY（13d 拒绝 assisted/auto 试点）
5) PREVIEW_GATE_PATH
```

### 3.2 命中条件（必须同时满足）

| # | 条件 |
|---|------|
| G1 | `platform_id == pinduoduo`（来自 Context / metadata，非 shop_name 猜测） |
| G2 | `workspace_id` 与 allowlist 行一致（若 metadata 无 workspace_id，13d **不** 进入 gate — fail-safe legacy） |
| G3 | `shop_id` **或** `account_id` 与 allowlist 行一致（精确相等，非前缀/模糊） |
| G4 | allowlist 行 `product_gate_enabled == true` |
| G5 | allowlist 行 `reply_mode == preview` |
| G6 | allowlist 行 `consultation_only == true` |

### 3.3 未命中 → legacy

- 任意 PDD 生产店（不在 allowlist）
- allowlist 空
- metadata 缺 `shop_id` 且缺 `account_id`
- `product_gate_enabled=false` 的全局默认

### 3.4 其它平台

| platform_id | 路径 |
|-------------|------|
| `pinduoduo` | allowlist 命中 → preview gate；否则 legacy |
| `doudian` | **LEGACY / mock only**；不读 allowlist；gate production **off** |
| `taobao` / `jd` / 其它 | **LEGACY**（未接入） |

---

## 4. 配置来源分期

| Phase | 来源 | 说明 |
|-------|------|------|
| **13c** | 本文档 | 仅规划 |
| **13d** | `TEST_SHOP_ALLOWLIST_PATH` / in-memory dict / pytest fixture | **仅测试与单店试点**；不进 `config.json` 生产默认 |
| **13e** | in-memory **PreviewReplyLog** + 可选 SQLite shadow | 仍可无 Alembic migration |
| **13f+ / 12e M6+** | DB `shop_bindings.product_gate_enabled` | 需 migration；变更写 **AuditLog** |

**13c/13d 禁止：** 直接依赖未迁移的 `database/models.py` 新列作为唯一来源。

---

## 5. 与 metadata 对齐

`AIReplyHandler` / consumer 现有 metadata 键（13b shadow 已用）：

| 键 | gate selection 用途 |
|----|---------------------|
| `shop_id` | 主匹配键 |
| `user_id` / `from_uid` | 非 gate 键 |
| `message_id` | ReplyLog 关联 |
| `platform` | 应规范为 `pinduoduo`（13d 实现时与 `Context.channel_type` 交叉校验） |

**13d 建议：** 新增纯函数 `select_product_gate_config(metadata, context) -> GateConfigSnapshot | None`，handler 仅调用；**不改** SendMessage。

---

## 6. 运维与审计（后续 DB 阶段）

| 动作 | 13d | 13e+ |
|------|-----|------|
| 添加 test shop 到 allowlist | 改 fixture / env | UI + API + AuditLog |
| 移除 test shop | 立即 legacy | 同左 |
| 查看当前 gate 状态 | 读 fixture / 日志 | Dashboard ShopBinding |

---

*Gate selection SSOT · Phase 13c · 2026-06-03*

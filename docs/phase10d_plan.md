# Phase 10d 规划 — routing / platform 契约测试

| 项 | 值 |
|---|---|
| 状态 | **仅规划**（本文档）；实现见 §10 Prompt |
| 前置 | [phase10c_plan.md](phase10c_plan.md)、[phase10c_done.md](phase10c_done.md) |
| 目标 | 用**新增测试**验证 10c SSOT；**不改变**生产默认行为 |

**文档导航：** [phase10_account_model.md](phase10_account_model.md) · [architecture_current.md](architecture_current.md)

---

## 1. Phase 10d 总体分析

### 1.1 目标

为 Phase 10c 冻结的 **routing / content_type / platform** 规则补充**契约级单测**，在不动 `pdd_message_handler`、`MessageConsumer`、handlers、flag 默认值的前提下，证明：

1. `compute_pdd_routing` 与 `pdd_message_handler` 的 immediate/queue/drop 决策**同构**；
2. `pdd_message_to_unified` 的 `content_type` / `extra["routing"]` 与 `ContextType` 一致；
3. `account_data["channel_name"]` ↔ `UnifiedMessage.platform` ↔ `Context.channel_type` ↔ `metadata.platform`（dual-track 路径）字符串对齐；
4. `USE_UNIFIED_MESSAGE_DUAL_TRACK` **默认仍为 false**（现有测试保持 + 不新增「默认 on」断言）。

### 1.2 非目标

- 不改生产代码路径、不默认开 dual-track、不接第二平台 WS、不改 UI/DB/AutoReply。
- 不做 `pdd_message_handler` 集成测试（会牵涉 WS/入队副作用）。
- 不实现 handler Route C、不迁移 queue 前缀。

### 1.3 与现有测试的关系

| 已有套件 | 覆盖 | 10d 缺口 |
|----------|------|----------|
| `test_pdd_to_unified_mapper.py` | 4 个 fixture；抽样 routing | **全量 `ContextType` 表驱动**；与 handler 集合**显式 parity** |
| `test_unified_dual_track.py` | put/enrich；默认 flag false | **fixture→mapper→enrich→metadata_adapter** 一条龙 platform/routing |
| `test_metadata_adapter.py` | get_platform/routing 手工 meta | **与 `enrich_metadata_from_unified` 输出**绑定；account `channel_name` |
| `test_auto_reply_platform_ui.py` | UI guard | 不重复；10d 可引用 `normalize_channel_name` 常量 |

---

## 2. 当前 mapper / handler routing 对照

### 2.1 `compute_pdd_routing` 规则（`pdd_to_unified.py`）

| routing | `ContextType` 集合 |
|---------|-------------------|
| **immediate** | `SYSTEM_STATUS`, `AUTH`, `WITHDRAW`, `SYSTEM_HINT`, `MALL_CS`, `TRANSFER` |
| **queue** | `TEXT`, `IMAGE`, `VIDEO`, `EMOTION`, `GOODS_INQUIRY`, `ORDER_INFO`, `GOODS_CARD`, `GOODS_SPEC` |
| **drop** | 其余（含 `MALL_SYSTEM_MSG`, `SYSTEM_BIZ` 及未识别兜底前的类型） |

`user_msg_type is None` → mapper 视为 `SYSTEM_STATUS` → **immediate**。

### 2.2 `pdd_message_handler` 行为（`pdd_message_handler.py` L136–160）

| 方法 | 集合 | 与 mapper |
|------|------|-----------|
| `_should_process_immediately` | 与 `_IMMEDIATE_TYPES` **字面同构** | ✅ |
| `_should_queue_message` | 与 `_QUEUE_TYPES` **字面同构** | ✅ |
| 否则 | 两方法均 false → **drop**（仅 debug 日志） | ✅ |

**互斥性：** immediate 与 queue 集合无交集；任一 `ContextType` 最多命中一种 routing。

### 2.3 `pdd_message_to_unified` 已覆盖的 content_type（fixture 实测）

| Fixture | content_type | routing |
|---------|--------------|---------|
| `text.json` | `text` | `queue` |
| `goods_inquiry.json` | `goods_inquiry` | `queue` |
| `withdraw.json` | `withdraw` | `immediate` |
| `mall_cs.json` | `mall_cs` | `immediate` |

**未用 fixture 覆盖、但 PDD 可产生的类型：** `image`, `video`, `emotion`, `order_info`, `goods_card`, `goods_spec`, `auth`, `transfer`, `system_status`, `system_hint`, `mall_system_msg`, `system_biz` 等 — 10d 用**合成 `PDDChatMessage` 或最小 JSON** 表驱动补齐，不必改 WS。

### 2.4 `content_type` 生成规则

```text
content_type = pdd.user_msg_type.value   # 缺省 user_msg_type → SYSTEM_STATUS → "system_status"
routing = compute_pdd_routing(user_msg_type)
```

与 `_convert_to_context` 使用的 `context.type` 同源（均来自 `PDDChatMessage.user_msg_type`）。

### 2.5 一致性结论（10c 主张的验证点）

| 检查项 | 预期 |
|--------|------|
| mapper routing vs handler 分支 | **一致**（集合同构，10d 应用测试锁死） |
| mapper `content_type` vs `Context.type.value` | 同一 `ContextType` 时应相等 |
| `get_routing(meta, ctx)` legacy | 无 `has_unified` 时委托 `compute_pdd_routing(context.type)` |
| `get_routing` + dual-track meta | `has_unified` 时优先 `metadata["routing"]` |

---

## 3. 推荐新增测试文件

| 文件 | 职责 | 是否新增 |
|------|------|----------|
| `tests/test_pdd_routing_parity.py` | 全量 `ContextType` ↔ routing；handler 集合 parity；mapper `extra["routing"]` | **推荐新增** |
| `tests/test_platform_message_contract.py` | platform 四层对齐；`channel_name` + enrich + `metadata_adapter` | **推荐新增** |
| `tests/test_pdd_to_unified_mapper.py` | 扩 1–2 个 drop 类型合成用例（可选） | **可选修改** |
| `tests/test_unified_dual_track.py` | 增加「fixture→mapper→enrich」用例（可选） | **可选修改** |

**原则：** 优先 **新文件**，避免扩大已有测试的行为面；若扩展现有文件，仅加用例、不改 setup 默认环境。

---

## 4. 表驱动测试矩阵

### 4.1 Routing parity（`test_pdd_routing_parity.py`）

对 **`list(ContextType)` 每个成员** 参数化：

| 列 | 断言 |
|----|------|
| `context_type` | 枚举成员 |
| `expected_routing` | `compute_pdd_routing(context_type)` |
| `handler_immediate` | `context_type in HANDLER_IMMEDIATE_SET`（测试内常量，注释同步 `pdd_message_handler` L138–145） |
| `handler_queue` | `context_type in HANDLER_QUEUE_SET`（同步 L150–159） |
| `parity` | `handler_immediate` ↔ `expected_routing == "immediate"` |
| | `handler_queue` ↔ `expected_routing == "queue"` |
| | 均 false ↔ `expected_routing == "drop"` |

**附加用例：**

```python
# 合成 PDDChatMessage：仅设置 user_msg_type，最小 raw
unified = pdd_message_to_unified(pdd, shop_id=..., user_id=..., username=...)
assert unified.content_type == context_type.value
assert unified.conversation.extra["routing"] == compute_pdd_routing(context_type)
```

**可选：** 从 `pdd_to_unified` 导入 `_IMMEDIATE_TYPES` / `_QUEUE_TYPES`（或测试内复制一份并注释「须与 mapper 模块同步」）— 若不想测 private，测试内双份集合 + 与 `compute_pdd_routing` 交叉验证即可。

### 4.2 content_type 矩阵（可与 §4.1 合并）

| ContextType | expected content_type | expected routing |
|-------------|----------------------|------------------|
| （全枚举一行） | `member.value` | immediate/queue/drop |

### 4.3 与 handler_chain 可见性（文档级，10d 不测生产 handler）

| routing | handler_chain 是否可见 |
|---------|------------------------|
| `queue` | ✅ Consumer 处理 |
| `immediate` | ❌ 不入队 |
| `drop` | ❌ 不入队 |

10d **不**启动 Consumer 验证该表；仅单测文档注释。

---

## 5. platform 对齐测试方案

### 5.1 契约（10c SSOT）

```text
normalize(account_data["channel_name"])  # 缺省 → pinduoduo
  == UnifiedMessage.platform.value
  == Context.channel_type.value
  == metadata["platform"]             # 当 has_unified
```

### 5.2 测试用例（`test_platform_message_contract.py`）

| # | 场景 | 做法 |
|---|------|------|
| P1 | UI/账号层 | `account_data = {"channel_name": "pinduoduo", ...}` → `normalize_channel_name` / `is_autoreply_supported`（复用 `ui.auto_reply.platform_ui`） |
| P2 | 缺省 channel | `channel_name` None/"" → `"pinduoduo"` |
| P3 | Unified 层 | `text.json` fixture → `pdd_message_to_unified` → `platform == PlatformType.PINDUODUO` |
| P4 | Context 层 | `_make_context()`（同 dual_track 测试）→ `channel_type == ChannelType.PINDUODUO` |
| P5 | metadata 层 | `MessageWrapper` + `_make_unified()` → `enrich_metadata_from_unified` → `platform == "pinduoduo"` |
| P6 | adapter 层 | `get_platform(meta, ctx)` with `has_unified` → `"pinduoduo"`；legacy only → 仍 `"pinduoduo"`（fallback） |
| P7 | 交叉一致 | `meta["platform"] == ctx.channel_type.value == unified.platform.value` |
| P8 | 故意不一致（可选） | meta `platform=taobao` + ctx PDD → 文档化「仅观测/警告」；**不断言 handler 行为变化** |

**不测：** 非 PDD `channel_name` 的 WS 入站（无 spike）。

---

## 6. dual-track metadata 测试方案

### 6.1 必须遵守

- `tearDown` / `tearDownClass` 中 **`os.environ.pop("USE_UNIFIED_MESSAGE_DUAL_TRACK", None)`**；
- **不**在仓库或 conftest 中默认设置该变量；
- **不**调用 `pdd_message_handler._process_websocket_message`。

### 6.2 推荐用例

| # | 内容 |
|---|------|
| D1 | 复用 `test_unified_dual_track.test_default_false`（已有，保持） |
| D2 | **新：** `text.json` → `PDDChatMessage` → `pdd_message_to_unified` → `MessageWrapper(context=合成 Context, unified=...)` → `enrich_metadata_from_unified` |
| D3 | D2 断言：`has_unified`, `routing=="queue"`, `content_type=="text"`, `platform=="pinduoduo"` |
| D4 | D2 + `get_routing` / `get_content_type` / `get_platform` 与 enrich 一致 |
| D5 | D2 + `get_send_context_for_extract` 仍只读 legacy（7e 契约，已有类似，可一条回归） |
| D6 | （可选）测试中 `os.environ["USE_UNIFIED_MESSAGE_DUAL_TRACK"]="true"` 仅断言 **`use_unified_message_dual_track()` 为 true**；**不**要求跑 app |

### 6.3 不做的 dual-track 测试

- 通过真实 WS 触发入队；
- 修改 `dual_track_flags.py` 默认；
- Consumer 并发 / handler 成功发送。

---

## 7. 禁止修改文件

| 类别 | 路径 |
|------|------|
| PDD 入站 | `Channel/pinduoduo/core/pdd_message_handler.py`, `pdd_lifecycle.py` |
| Mapper 实现 | `Channel/pinduoduo/mappers/pdd_to_unified.py`（**除非**发现 parity bug；10d 默认只测不改） |
| Consumer / handler | `Message/core/consumer.py`, `Message/handlers/**` |
| Flag 默认 | `**/dual_track_flags.py`, `**/shadow*.py`, `*_flags.py` |
| AutoReply / UI | `ui/auto_reply/threads.py`, `channel_factory.py`, `ui/**`（读 `platform_ui` 除外） |
| DB | `database/**` |
| 生产配置 | `config.py`, `app.py` |

**允许：** `tests/**` 新增/扩展；`docs/phase10d_done.md` 等文档。

---

## 8. 文档更新方案（10d 编码完成后）

| 文件 | 更新 |
|------|------|
| `docs/phase10d_done.md` | 新增测试列表、无生产变更声明 |
| `docs/architecture_current.md` | Phase 10d 行；SSOT 小节注明「契约测试已覆盖」 |
| `docs/README.md` | Phase 表 10d |
| `docs/phase10c_done.md` | §7 链到 10d done（可选一句） |

**10d 规划阶段：** 仅本文档，不强制改其它 doc。

---

## 9. 风险点

| 风险 | 缓解 |
|------|------|
| 测试集合与 handler 漂移 | parity 测试双份集合 + 注释引用 handler 行号；CI 失败即提醒同步 |
| 环境变量泄漏 | 每个 dual-track 用例 `tearDown` pop |
| 误改 mapper 修测试 | 10d PR 要求 diff 仅 `tests/` + `docs/` |
| 导入 `ui.auto_reply` 拖慢/GUI 依赖 | `platform_ui` 无 PyQt 依赖，可安全导入 |
| 合成 `PDDChatMessage` 不真实 | 仅验证 routing/content_type 契约，不替代黄金路径 |
| 扩大为集成测试 | 明确禁止调用 WS/handler 链 |

---

## 10. 最小安全实现范围

```text
tests/test_pdd_routing_parity.py      # 全 ContextType routing + handler 同构
tests/test_platform_message_contract.py  # platform 四层 + channel_name
（可选）test_unified_dual_track.py  +2 cases  # fixture→mapper→enrich
docs/phase10d_done.md
```

**估计：** ~80–150 行测试代码；0 行生产代码；unittest 全绿。

**推迟到 spike / 10e+：**

- 真实抖店/京东/淘宝 mapper 与 routing 表；
- `pdd_{shop}` → `{platform}_{shop}` queue 名；
- handler 按 `metadata.routing` 分支（Route C + flag）；
- `unified_to_context` 生产接入；
- `pdd_message_handler` dual-track 端到端集成测试。

---

## 11. 第一轮实现 Prompt（复制用）

```text
继续 Phase 10d：routing / platform 契约测试（仅 tests + docs）。

先读：
- docs/phase10d_plan.md
- docs/phase10c_done.md
- Channel/pinduoduo/mappers/pdd_to_unified.py
- Channel/pinduoduo/core/pdd_message_handler.py（L136-160，只读对照）
- Message/metadata_adapter.py
- tests/test_pdd_to_unified_mapper.py
- tests/test_unified_dual_track.py

实现：
1. 新增 tests/test_pdd_routing_parity.py
   - 表驱动：每个 ContextType → compute_pdd_routing
   - 与 pdd_message_handler immediate/queue 集合 parity（测试内常量，注释同步行号）
   - 合成 PDDChatMessage：extra["routing"]、content_type 与枚举一致
2. 新增 tests/test_platform_message_contract.py
   - channel_name（platform_ui normalize）↔ UnifiedMessage.platform ↔ Context.channel_type
   - enrich_metadata_from_unified + get_platform/get_routing（has_unified）
3. 可选：test_unified_dual_track 增加 fixture→pdd_message_to_unified→enrich 一条
4. docs/phase10d_done.md；更新 architecture_current、docs/README

禁止：
- 不改 pdd_message_handler / consumer / handlers / mapper（除非发现真实 bug 需单独说明）
- 不改任何 flag 默认值；不默认开启 USE_UNIFIED_MESSAGE_DUAL_TRACK
- 不改 UI / DB / threads / channel_factory
- 不接第二平台；不 commit/push（除非用户要求）

验收：
python -m unittest discover -s tests -v
git diff --stat  # 预期主要为 tests/ 与 docs/
```

---

*规划版本：Phase 10d · 2026-06-03 · 仅规划，无代码*

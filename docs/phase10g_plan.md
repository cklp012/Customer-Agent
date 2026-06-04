# Phase 10g 规划 — PDD lifecycle 接入 `build_queue_name`

| 项 | 值 |
|---|---|
| 状态 | **仅规划**（本文档） |
| 前置 | [phase10f_done.md](phase10f_done.md)、[phase10e_done.md](phase10e_done.md) |
| 硬约束 | 生产 queue 字符串 **必须** 仍为 `pdd_{shop_id}`（与现网 f-string 一致） |

**文档导航：** [Message/queue_naming.py](../Message/queue_naming.py) · [pdd_lifecycle.py](../Channel/pinduoduo/core/pdd_lifecycle.py)

---

## 1. Phase 10g 总体分析

### 1.1 目标

评估并把规划落地为：**是否**将 `pdd_lifecycle.py` 中硬编码 `f"pdd_{shop_id}"` 改为 `Message.queue_naming.build_queue_name`（或薄封装 `pdd_queue_name`），在 **字符串输出与运行时行为零差异** 前提下统一命名入口。

### 1.2 当前状态（Phase 10f 后）

| 项 | 状态 |
|----|------|
| Helper | `build_queue_name("pinduoduo", shop_id)` → `pdd_{shop_id}`（`shop_id` 经 `str().strip()`） |
| 生产 | `pdd_lifecycle` **未** import helper；5 处字面量 `f"pdd_{shop_id}"` |
| 测试 | `tests/test_queue_naming.py` 覆盖 helper；**无** lifecycle 级 parity |

### 1.3 核心问题

替换是否 **安全**，取决于 `f"pdd_{shop_id}"` 与 `build_queue_name("pinduoduo", shop_id)` 对 **真实入参** 是否 **逐字节相等**。不等时不能直接 Route C。

### 1.4 推荐分期

| Phase | 路线 | 内容 |
|-------|------|------|
| **10g** | **Route B**（推荐） | `pdd_queue_name(shop_id)` 薄封装 + **legacy f-string parity 单测**；**不改** `pdd_lifecycle` |
| **10h** | **Route C** | lifecycle 全部改用 `pdd_queue_name` + 可选集成级测试；须 10g parity 全绿 |
| **禁止** | Route D | `pinduoduo_{shop_id}` |

若团队要求 **10g 零代码**，可采用 **Route A**（仅本文档 + 更新 10f done 脚注）。

---

## 2. 当前 `pdd_lifecycle` queue name 出现点

文件：`Channel/pinduoduo/core/pdd_lifecycle.py`

| # | 行号 | 代码形态 | 所在函数 / 分支 | 用途 |
|---|------|----------|-----------------|------|
| 1 | **131–132** | `queue_name = f"pdd_{shop_id}"` | `init` | **Consumer 创建**：`_setup_message_consumer(queue_name)` |
| 2 | **189** | 使用局部变量 `queue_name` | `init` → `_message_loop(..., queue_name)` | **WS 入队路径**：传入 `pdd_message_handler._process_websocket_message` → `put_message` |
| 3 | **115–116** | `queue_name = f"pdd_{shop_id}"` | `stop_account` | **停止清理**：`_cleanup_resources(queue_name)` |
| 4 | **224** | `f"pdd_{shop_id}"`（内联） | `init` 正常/异常结束 `should_cleanup` | **cleanup**（与 #1 应用同一 shop，但未复用变量） |
| 5 | **247** | `f"pdd_{shop_id}"`（内联） | `init` `CancelledError` | **cleanup** |
| 6 | **257** | `f"pdd_{shop_id}"`（内联） | `init` 顶层 `except Exception` | **cleanup**（连接失败） |

**间接用途（非字面量，但绑定同一字符串）：**

| 模块 | 关系 |
|------|------|
| `pdd_message_handler._setup_message_consumer` | 按 `queue_name` 注册 `MessageConsumer` |
| `message_consumer_manager` | `Dict[queue_name, Consumer]` |
| `put_message(queue_name, context)` | 入队 |
| `_cleanup_resources` | `stop_consumer(queue_name)` + 日志含 `queue_name` |
| 日志 | `shop_id`/`username` 为主；queue 名主要在 consumer 启停 debug/warning |

**Reconnect：** 重连走 `_connect_with_retry` → 再次 `init` → 仍 **#1** 同一命名逻辑；无单独 queue 前缀。

**注意：** #4–#6 与 #1 **重复构造** 同一表达式；若只改 #1 不改 cleanup，会导致 **cleanup 停错队列**（现网靠表达式相同而一致）。Route C **必须 6 处统一** 或抽 `queue_name` 单点赋值。

---

## 3. 替换风险分析

### 3.1 能否安全替换为 `build_queue_name("pinduoduo", shop_id)`？

| 场景 | `f"pdd_{shop_id}"` | `build_queue_name("pinduoduo", shop_id)` | 是否相等 |
|------|-------------------|----------------------------------------|----------|
| 正常 `shop_id="12345"` | `pdd_12345` | `pdd_12345` | ✅ |
| 数字 `shop_id=12345`（若传入 int） | `pdd_12345` | `pdd_12345` | ✅ |
| **首尾空白** `" 12345 "` | `pdd_ 12345 `（含空格） | `pdd_12345`（strip） | ❌ **不等** |
| `shop_id=None` | `pdd_None` | **ValueError** | ❌ **行为变** |
| `shop_id=""` | `pdd_` | **ValueError** | ❌ **行为变** |

**结论：**

- 对 **DB/AutoReply 典型非空、无空白** `shop_id`：可认为 **字符串相等**，Route C **理论上安全**。
- 对 **异常入参**：helper **更严格**（抛 `ValueError` 或 strip），与现网 f-string **不等价** → 盲目 Route C 会改变异常/边缘行为。

### 3.2 `shop_id` 来源与空值风险

| 来源 | 校验 |
|------|------|
| `start_account(shop_id, user_id)` | 先 `db_manager.get_account(...)`；不存在则 **return**，不进入 `init` |
| `stop_account` | 同上 |
| `AutoReplyThread` | `account_data["shop_id"]` 来自 DB |
| 类型注解 | `str`；运行时仍可能 `None` 若调用方传错 |

**规划建议：** Route C 前在 lifecycle **单点** 断言/记录：`shop_id` 非空；或 **10g parity 测试** 用生产样本 shop_id 列表。若存在空白 shop_id 数据，须先 **DB/UI 规范化** 再接入 helper（strip 一致）。

### 3.3 是否会改变异常行为

| 变更 | 影响 |
|------|------|
| 空/None `shop_id` + helper | `init` 可能在 `_setup_message_consumer` **之前** 抛 `ValueError`；现网可能生成 `pdd_` / `pdd_None` 队列名 |
| Consumer 未创建 vs 创建错误队列 | **用户可见差异**（启动失败时机不同） |

**10g 记录：** 若要保持 **完全** 不变，Route C 须 **仅** 在已验证 `shop_id` 有效路径调用 helper，或 `pdd_queue_name` 对无效值 **委托** legacy f-string（不推荐，破坏 helper 契约）。

### 3.4 是否需要先新增 parity 函数但不接入（Route B）

**是，推荐为 10g 默认交付：**

```python
# Message/queue_naming.py（规划）
def pdd_queue_name(shop_id: Any) -> str:
    """PDD 生产队列名；等价于 build_queue_name('pinduoduo', shop_id)。"""
    return build_queue_name("pinduoduo", shop_id)
```

- lifecycle **不 import**（10g）。
- 单测：`assert f"pdd_{sid}" == pdd_queue_name(sid)` 对代表性 `sid`。
- 单独用例文档 **strip / None / ""** 与 f-string **已知差异**（不声称相等）。

### 3.5 是否需要 lifecycle 字符串锁定测试

| 类型 | 10g | 10h (Route C) |
|------|-----|----------------|
| 纯函数 parity | ✅ `test_pdd_queue_name_legacy_parity` | ✅ |
| 静态/单元：patch lifecycle 调用点 | 可选 | ✅ 断言 `pdd_queue_name` 被调用且参数为 `shop_id` |
| 全链路 WS 集成 | 否 | 否（本 Phase 禁止改 WS） |

**不建议** 10g 做重型 integration；**建议** 10h 用 `unittest.mock` 验证 `init`/`stop_account` 使用统一 helper 且返回值等于 `f"pdd_{shop_id}"`。

### 3.6 现网代码异味（Route C 顺带修复）

`init` 内 **#1** 设 `queue_name`，**#4–#6** cleanup 却 **内联** `f"pdd_{shop_id}"`。Route C 应：

```python
queue_name = pdd_queue_name(shop_id)
# ... 全部 cleanup 使用 queue_name，消除 3 处重复
```

行为不变前提下提高 **单点 SSOT**（仍须与 10f helper 输出一致）。

---

## 4. 推荐路线

| Route | 10g 建议 | 说明 |
|-------|----------|------|
| **A** | 可选 | 仅文档；零风险 |
| **B** | **✅ 10g 推荐** | `pdd_queue_name` + parity tests；lifecycle 不动 |
| **C** | **10h** | lifecycle 替换 + mock 测试；依赖 B 的 parity |
| **D** | **禁止** | `pinduoduo_{shop_id}` |

---

## 5. Route C 所需 parity tests（10h）

### 5.1 字符串 parity（必须）

```text
∀ shop_id ∈ REPRESENTATIVE_SHOP_IDS:
  assert pdd_queue_name(shop_id) == f"pdd_{shop_id}"

REPRESENTATIVE_SHOP_IDS:
  - 典型数字字符串（来自 fixtures / 文档样例）
  - 含字母数字混合
  - 勿假设含首尾空格（除非 DB 已清洗并单独测）
```

### 5.2 边界（文档化，不强制与 f-string 相等）

| 用例 | 期望 |
|------|------|
| `shop_id=None` | helper 抛 `ValueError`；记录「现网为 pdd_None」 |
| `shop_id=""` | helper 抛 `ValueError`；记录「现网为 pdd_」 |

### 5.3 lifecycle 接线（mock）

| 测试 | 断言 |
|------|------|
| patch `pdd_queue_name` | `init` 成功后调用 1 次，参数 `shop_id` |
| patch `message_consumer_manager.create_consumer` | 收到 `pdd_{shop_id}` 与 parity 一致 |
| `stop_account` | `_cleanup_resources` 收到相同 queue 名 |

### 5.4 回归

- 全量 `python -m unittest discover -s tests -v`
- 不默认改 golden path；人工 smoke 可选

---

## 6. 最小安全实现路线

```text
10g（规划 + 推荐实现）
  → phase10g_plan.md（本文）
  → Route B: pdd_queue_name + test_pdd_queue_name_legacy_parity.py
  → 文档：strip/None 风险登记表

10h（可选编码）
  → pdd_lifecycle: queue_name = pdd_queue_name(shop_id) 单点
  → 所有 cleanup 复用 queue_name
  → mock tests + 全量 unittest

spike / 11+
  → 第二平台 lifecycle 使用 build_queue_name(platform_id, shop_id)
```

**10g 规划阶段默认：不改 `pdd_lifecycle.py`。**

---

## 7. 允许修改文件（10g Route B 实现时）

| 允许 | 文件 |
|------|------|
| Helper 扩展 | `Message/queue_naming.py`（`pdd_queue_name`） |
| 测试 | `tests/test_pdd_queue_name_parity.py` 或扩 `test_queue_naming.py` |
| 文档 | `phase10g_done.md`、`architecture_current.md`、`README.md` |

## 8. 禁止修改文件（10g 规划 / Route B）

| 禁止 | 文件 |
|------|------|
| 生产入站 | `pdd_lifecycle.py`（Route B） |
| 入站处理 | `pdd_message_handler.py` |
| 消息系统 | `Message/core/consumer.py`、`Message/handlers/**` |
| AutoReply | `ui/auto_reply/threads.py`、`channel_factory.py` |
| Flag / UI / DB | 全部默认与 schema |

**Route C（10h）仅允许改：** `pdd_lifecycle.py` + 上述 tests/docs。

---

## 9. 测试方案

### 9.1 10g（Route B）

- 扩 `test_queue_naming.py` 或新文件 `test_pdd_queue_name_parity.py`
- 表：`shop_id` → `f"pdd_{shop_id}" == pdd_queue_name(shop_id)`
- 负例：`None`/`""` 仅断言 helper raises，**不断言** 等于 f-string

### 9.2 10h（Route C）

- §5 全部 + 全量 unittest

---

## 10. 文档更新方案

| 文件 | 10g 规划 | 10g/10h 实现后 |
|------|----------|----------------|
| `docs/phase10g_plan.md` | 本文 | — |
| `docs/phase10g_done.md` | — | Route 选择 + 风险登记 |
| `docs/phase10f_done.md` | — | 「lifecycle 接入 → 10g/10h」 |
| `architecture_current.md` | 可选索引 | 10g/10h 行 |
| `README.md` | 可选 | Phase 10g/10h |

**纯规划（Route A）：** 仅 `phase10g_plan.md` + README 一行。

---

## 11. 第一轮实现 prompt

### 11a — Phase 10g Route B（推荐）

```text
继续 Phase 10g Route B：pdd_queue_name + legacy parity tests，不改 pdd_lifecycle。

先读：docs/phase10g_plan.md、Message/queue_naming.py、pdd_lifecycle.py（只读）。

实现：
1. Message/queue_naming.py 新增 pdd_queue_name(shop_id) -> build_queue_name("pinduoduo", shop_id)
2. tests/test_pdd_queue_name_parity.py：
   - 多组 shop_id：assert pdd_queue_name(sid) == f"pdd_{sid}"
   - None/"" ：仅 assert raises ValueError，注释 legacy f-string 差异
3. docs/phase10g_done.md；更新 README、architecture_current

禁止：改 pdd_lifecycle、pdd_message_handler、consumer、handlers、flags、UI、DB。
验收：python -m unittest discover -s tests -v
```

### 11b — Phase 10h Route C（后续）

```text
继续 Phase 10h：pdd_lifecycle 接入 pdd_queue_name（输出必须与 f"pdd_{shop_id}" 一致）。

先读：phase10g_done.md、phase10g_plan.md §5。

实现：
1. pdd_lifecycle.py：init/stop 单点 queue_name = pdd_queue_name(shop_id)；cleanup 复用变量（去掉 3 处内联 f-string）
2. 前置：确认 shop_id 在 init 入口非空（若已有 DB 校验则文档化，不新增激进校验除非 parity 要求）
3. tests：mock init/stop 断言 consumer/cleanup 收到 pdd_queue_name(shop_id)
4. parity 测试保持绿

禁止：改 queue 字符串结果、Consumer 逻辑、handlers、WS、flags 默认。
验收：全量 unittest；git diff 聚焦 pdd_lifecycle + tests + docs。
```

---

*规划版本：Phase 10g · 2026-06-03 · 默认不改 lifecycle*

# Phase 10h 规划 — `pdd_lifecycle` 接入 `pdd_queue_name`

| 项 | 值 |
|---|---|
| 状态 | **仅规划**（本文档） |
| 前置 | [phase10g_done.md](phase10g_done.md)、[phase10f_done.md](phase10f_done.md) |
| 硬约束 | 生产 queue 字符串与现网 `f"pdd_{shop_id}"` **逐字节一致**（正常 `shop_id`） |

**代码锚点：** [pdd_lifecycle.py](../Channel/pinduoduo/core/pdd_lifecycle.py) · [queue_naming.py](../Message/queue_naming.py)

---

## 1. Phase 10h 总体分析

### 1.1 目标

将 `pdd_lifecycle.py` 中全部 `f"pdd_{shop_id}"` 收敛为 **`pdd_queue_name(shop_id)`**（或带 legacy 兼容的薄封装），实现 **单点 SSOT**，且：

- `create_consumer` / `_message_loop` / `put_message` / `_cleanup_resources` 使用 **同一** `queue_name` 变量；
- 正常 DB/AutoReply 路径下队列名仍为 `pdd_{shop_id}`；
- **不**改为 `pinduoduo_{shop_id}`；**不**改 Consumer/handler/WS/9d 默认。

### 1.2 10g 已证明

| 项 | 状态 |
|----|------|
| `pdd_queue_name` | 已实现 |
| 正常 `shop_id` parity | `tests/test_pdd_queue_name_parity.py` ✅ |
| lifecycle 生产 | **未接入** |

### 1.3 决策门

| 条件 | 建议 |
|------|------|
| 生产/测试 `shop_id` 无 `None`/`""`/仅空白 | **可执行 Route C** |
| DB 存在空白 `shop_id` 或调用方可能传 `None` | Route C 须 **legacy fallback** 或 **先数据清洗**；否则 **停文档（Route A）** |
| 存在首尾空白 `shop_id` | helper **strip** → 队列名变化 → 须规范化或 fallback |

**本规划默认推荐：Route C（有条件）**，附带 **legacy-compatible 封装** 见 §6。

---

## 2. 当前 `pdd_lifecycle` queue name 出现点

文件：`Channel/pinduoduo/core/pdd_lifecycle.py`（共 **5 处** 表达式，**2 种** 用法）

| ID | 行 | 代码 | 函数 / 分支 |
|----|-----|------|-------------|
| **A** | 131 | `queue_name = f"pdd_{shop_id}"` | `init` 入口 |
| **B** | 189 | 参数 `queue_name` | `_message_loop` → WS → `put_message` |
| **C** | 115 | `queue_name = f"pdd_{shop_id}"` | `stop_account` → `_cleanup_resources` |
| **D** | 224 | `await self._cleanup_resources(f"pdd_{shop_id}")` | `init` 正常/异常结束 |
| **E** | 247 | 同上 | `init` `CancelledError` |
| **F** | 257 | 同上 | `init` 顶层 `except Exception` |

```text
init 路径：
  A → _setup_message_consumer(queue_name)     # Consumer 创建 + start
  B → _message_loop(..., queue_name)          # 入队（经 message_handler）
  D/E/F → cleanup（内联 f-string，未复用 A）   # 风险：若 A 改前缀而 D 未改 → 停错队列

stop 路径：
  C → _cleanup_resources(queue_name)

reconnect：
  start_account → _connect_with_retry → _connect_single_attempt → init(A)
  （无独立 queue 命名；与 A 相同）
```

### 2.1 是否必须统一替换？

**是。** 否则会出现：

- Consumer 在 `pdd_shopA` 上运行；
- cleanup 在 `pdd_shopB` 或拼写不一致名上 `stop_consumer` → **泄漏 Consumer / 队列**。

Route C **必须**：`init` 内 **单变量** `queue_name`，**D/E/F 改为 `_cleanup_resources(queue_name)`**，禁止再内联 f-string。

---

## 3. `shop_id` 有效性分析

### 3.1 来源链路

```text
AutoReplyThread.run
  → start_auto_reply_account(channel, shop_id, user_id, …)
       → PDDChannel / PinduoduoChannel.start_account(shop_id, user_id, …)
            → LifecycleMixin.start_account
                 → db_manager.get_account(channel_name, shop_id, user_id)
                 → 不存在则 on_failure + return（不进入 init）
                 → _connect_with_retry / _connect_single_attempt
                      → init(shop_id, user_id, username, …)
```

| 路径 | `shop_id` 来源 | 进入 `init` 前校验 |
|------|----------------|-------------------|
| **start_account** | `account_data["shop_id"]` / channel API | **DB 账号存在** |
| **stop_account** | 调用方传入 | **DB 账号存在** 才清理；否则 early return |
| **reconnect** | 同 start 的 `shop_id` | 同上 |
| **init 直接调用** | 仅 `_connect_single_attempt` | 无二次 DB 校验 |

### 3.2 是否可能 `None` / `""` / 空白？

| 场景 | 现网 f-string | `pdd_queue_name` |
|------|---------------|------------------|
| `shop_id=None` | `pdd_None` | `ValueError` |
| `shop_id=""` | `pdd_` | `ValueError` |
| `shop_id="  "` | `pdd_  ` | `ValueError` |
| 正常非空字符串 | `pdd_{id}` | `pdd_{id}`（无首尾空白时） |

**生产预期：** UI/DB 路径在账号存在时 `shop_id` 为店铺主键字符串，**通常**非空。  
**不能假设永远成立：** ORM/历史脏数据 / 未来调用方可能传入坏值。

### 3.3 是否需在 lifecycle 内显式校验？

| 策略 | 说明 |
|------|------|
| **S1 — 仅 helper（激进 Route C）** | `queue_name = pdd_queue_name(shop_id)`；坏值 → 启动失败提前抛错（**行为变**） |
| **S2 — legacy-compatible（推荐）** | 坏值仍 `f"pdd_{shop_id}"`；合法值用 `pdd_queue_name` → **字符串与现网一致** |
| **S3 — 入口校验 + return** | 空 `shop_id` 直接 `on_failure` / return；比现网更少创建 `pdd_` 队列（**行为变**） |

**10h 推荐 S2**（见 §6），满足「正常路径不变、边缘路径不恶化」。

### 3.4 是否只在确认有效后使用 helper？

**是（推荐）。** 在 `init` / `stop_account` 中，**DB 校验通过后** 再计算 `queue_name`；`stop_account` 在 `account_info` 缺失时 **不** 计算 queue（与现网一致）。

---

## 4. 替换风险分析

| 风险 | 严重度 | 缓解 |
|------|--------|------|
| D/E/F 未与 A 同步 | 高 | 单变量 `queue_name` |
| `shop_id` 空白/None 行为变化 | 中 | S2 legacy-compatible |
| `shop_id` 首尾空白 → strip | 中 | DB 审计；或 S2 对非 strip 相等时用 f-string |
| `ValueError` 冒泡到 `on_failure` 文案变化 | 低 | S2 |
| import 循环 | 低 | `queue_naming` 无 Channel 依赖 |
| 测试遗漏 | 中 | §7 mock + 全量 unittest |

**若无法接受 S2 额外 5–10 行封装：** 先做 **Route B**（仅 lifecycle mock 测试 + 文档），暂缓 Route C。

---

## 5. 推荐路线

| Route | 内容 | 10h 建议 |
|-------|------|----------|
| **A** | 仅文档 | 风险未消纳时选此 |
| **B** | 新增 `test_pdd_lifecycle_queue_name.py`（mock），**不改** lifecycle | 可与 C 同 sprint 先做 |
| **C** | lifecycle 替换 + S2 封装 + 测试 | **推荐实现**（前提：S2） |
| **D** | `pinduoduo_{shop_id}` | **禁止** |

**推荐顺序：**

```text
10h 规划（本文）→ 可选 Route B 测试先行 → Route C 实现 → phase10h_done.md
```

---

## 6. Route C 最小实现方案

### 6.1 必须替换的位置（全部）

| 原位置 | 替换为 |
|--------|--------|
| L131 | `queue_name = _lifecycle_pdd_queue_name(shop_id)` |
| L115 | 同上（`stop_account`） |
| L224, L247, L257 | `await self._cleanup_resources(queue_name)`（使用 `init` 作用域内变量） |

**`init` 结构建议：**

```python
async def init(self, shop_id: str, user_id: str, username: str, on_success, on_failure):
    queue_name = _lifecycle_pdd_queue_name(shop_id)  # 函数顶部，try 内首行
    try:
        ...
        await self._setup_message_consumer(queue_name)
        ...
        # cleanup 分支一律 queue_name，禁止 f"pdd_{shop_id}"
```

`stop_account` 在 DB 命中后：

```python
queue_name = _lifecycle_pdd_queue_name(shop_id)
await self._cleanup_resources(queue_name)
```

### 6.2 Legacy-compatible 封装（推荐，放 `pdd_lifecycle` 或 `queue_naming`）

```python
def _lifecycle_pdd_queue_name(shop_id: Any) -> str:
    """与历史 f"pdd_{shop_id}" 兼容；正常 shop_id 走 pdd_queue_name。"""
    if shop_id is None:
        return f"pdd_{shop_id}"
    text = str(shop_id)
    if not text.strip():
        return f"pdd_{shop_id}"
    try:
        return pdd_queue_name(shop_id)
    except ValueError:
        return f"pdd_{shop_id}"
```

对 **无空白** 的正常 `shop_id`：`pdd_queue_name(shop_id) == f"pdd_{shop_id}"`（10g 已测）。  
对 **首尾空白**：现网 `f"pdd_{shop_id}"` ≠ strip 后 helper → **仍返回 f-string**（在 `try` 前加 `text != text.strip()` 分支亦可）。

**是否保留 fallback：** **推荐保留** 至确认 DB 无脏数据后，再简化为纯 `pdd_queue_name`（独立 Phase）。

### 6.3 确保 create / put / cleanup 同一 `queue_name`

| 步骤 | 保证方式 |
|------|----------|
| create | `init` 顶部赋值一次 `queue_name` |
| put | `_message_loop` 只接收参数 `queue_name`（已满足） |
| cleanup | D/E/F 改用变量，不用内联 |

### 6.4 避免 None / "" 改变生产行为

采用 **§6.2 S2**；**不要**在 10h 仅裸用 `pdd_queue_name` 除非已审计全部 `shop_id`。

### 6.5 不改动的文件

- `pdd_message_handler.py`（仅接收 `queue_name` 参数，签名不变）
- `MessageConsumer` / handlers / WS / flags

---

## 7. 需要新增 / 修改的测试

### 7.1 保留（须全绿）

- `tests/test_pdd_queue_name_parity.py`
- `tests/test_queue_naming.py`

### 7.2 新增 `tests/test_pdd_lifecycle_queue_name.py`（Route B/C）

| 用例 | 方法 | 断言 |
|------|------|------|
| **init 成功路径** | `AsyncMock` + patch `_setup_message_consumer` | 传入的 `queue_name == pdd_queue_name(shop_id)` |
| | patch `_message_loop` | 第 5 个位置参数为同一 `queue_name` |
| **init cleanup** | 触发 `stop_event` 或 mock `wait` 返回 | `_cleanup_resources` 收到同一 `queue_name` |
| **init 异常 cleanup** | patch `websockets.connect` 抛错 | `_cleanup_resources` 仍为 `pdd_{shop_id}` |
| **stop_account** | 有账号 mock | `_cleanup_resources(pdd_queue_name(shop_id))` |
| **stop 无账号** | `get_account` → None | `_cleanup_resources` **未调用** |
| **parity** | 参数化 `shop_id` | lifecycle 使用的名 == `f"pdd_{shop_id}"` |

实现要点：

- 使用 `unittest.mock.patch` / `AsyncMock`；
- **不**起真实 WS、**不**起 Consumer 线程；
- 可实例化 `PDDChannel` 或 `LifecycleMixin` 合成类（最小 mixin 实例）。

### 7.3 可选 DB 审计（文档/脚本，非 10h 必须）

```sql
-- 规划用：检查空 shop_id（若项目有 SQLite 工具可手动跑）
SELECT shop_id FROM shops WHERE shop_id IS NULL OR trim(shop_id) = '';
```

有结果则 **Route C 必须 S2** 或先清洗。

---

## 8. 允许修改文件（Route C 实现时）

| 允许 | 文件 |
|------|------|
| 接入 | `Channel/pinduoduo/core/pdd_lifecycle.py` |
| 可选封装 | `Message/queue_naming.py`（`_lifecycle_pdd_queue_name` 若放此处） |
| 测试 | `tests/test_pdd_lifecycle_queue_name.py` |
| 文档 | `phase10h_done.md`、`architecture_current.md`、`README.md` |

## 9. 禁止修改文件

| 禁止 |
|------|
| `pdd_message_handler.py`（行为/路由） |
| `Message/core/consumer.py`、`Message/handlers/**` |
| `ui/**`、`database/**`、`app.py`、`*_flags.py` 默认值 |
| `threads.py`、`channel_factory.py`、PDD WS/登录 |
| 真实第二平台 |

---

## 10. 文档更新方案

| 文件 | 内容 |
|------|------|
| `docs/phase10h_plan.md` | 本文 |
| `docs/phase10h_done.md` | Route 选择、替换清单、S2 与否、测试结果 |
| `docs/phase10g_done.md` | 脚注「lifecycle 已接入」 |
| `architecture_current.md` | 10h 行；「生产 queue 仍 `pdd_*`」 |
| `README.md` | Phase 10h |

**纯规划阶段：** 仅 `phase10h_plan.md` + 索引更新。

---

## 11. 第一轮实现 prompt（Route C + 推荐 S2）

```text
继续 Phase 10h Route C：pdd_lifecycle 接入 pdd_queue_name，queue 字符串与现网一致。

先读：docs/phase10h_plan.md、phase10g_done.md、pdd_lifecycle.py、Message/queue_naming.py。

实现：
1. pdd_lifecycle.py：
   - 新增 _lifecycle_pdd_queue_name(shop_id)（legacy-compatible，见 phase10h_plan §6.2）
   - init：首行 queue_name；_setup_message_consumer / _message_loop / 所有 _cleanup_resources(queue_name)
   - stop_account：DB 命中后 queue_name = _lifecycle_pdd_queue_name(shop_id)
   - 删除全部内联 f"pdd_{shop_id}"（5 处）
2. tests/test_pdd_lifecycle_queue_name.py：mock init/stop/cleanup/异常路径；断言 queue 名 == f"pdd_{sid}" 对正常 shop_id
3. docs/phase10h_done.md；更新 architecture_current、README、phase10g_done

禁止：改 pdd_message_handler 逻辑、consumer、handlers、WS、flags、UI、DB、channel_factory。
禁止：pinduoduo_{shop_id}。

验收：
python -m unittest discover -s tests -v
test_pdd_queue_name_parity 仍绿
git diff 聚焦 pdd_lifecycle + tests + docs
```

### 11b — 若审计发现脏数据（停 Route C）

```text
仅完成 phase10h_done.md 记录：保持 lifecycle 不变，原因 shop_id 边缘情况；
执行 Route B 测试文件作为回归基线供下一 Phase。
```

---

## 12. 风险 → 是否应停文档不改代码

| 信号 | 行动 |
|------|------|
| 仅正常 shop_id、无空白/空 | ** proceed Route C + S2** |
| 存在空白 shop_id 且必须保持 `pdd_ ` 队列名 | **停 C**；文档 + 数据清洗 Phase |
| 团队不愿接受 fallback 封装 | **Route B only**（测试锁定现网字符串） |

---

*规划版本：Phase 10h · 2026-06-03 · 无代码变更*

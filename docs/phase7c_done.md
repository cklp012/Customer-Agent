# Phase 7c 完成记录 — UnifiedMessage shadow

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-02 |
| 范围 | shadow helper + `pdd_message_handler` 一处 hook |

---

## 1. 新增 / 修改文件

| 操作 | 文件 |
|------|------|
| 新增 | `Channel/pinduoduo/mappers/shadow_flags.py` |
| 新增 | `Channel/pinduoduo/mappers/shadow.py` |
| 修改 | `Channel/pinduoduo/mappers/__init__.py` |
| 修改 | `Channel/pinduoduo/core/pdd_message_handler.py`（一处 hook） |
| 新增 | `tests/test_unified_shadow.py` |
| 修改 | `docs/runtime_modes.md`、`docs/README.md`、`docs/architecture_current.md` |

---

## 2. 行为摘要

- **`USE_UNIFIED_MESSAGE_SHADOW`**：默认 **false**；为 true 时在 `_convert_to_context` 成功后旁路调用 `pdd_message_to_unified`。
- 打 **debug** 摘要日志（不含完整 raw/content）；mapper 失败或 context/unified 不一致打 **warning**。
- **不改变** `Context`、不入队、不影响 immediate / `put_message` / drop。

---

## 3. 联调示例

```powershell
$env:USE_UNIFIED_MESSAGE_SHADOW = "true"
python app.py
# 日志中搜索 unified_shadow ok / mismatch / failed
Remove-Item Env:USE_UNIFIED_MESSAGE_SHADOW -ErrorAction SilentlyContinue
```

---

## 4. 验收

```powershell
python -m unittest discover -s tests -v
```

---

## 5. 相关文档

- [runtime_modes.md](runtime_modes.md) — flag 说明
- [phase7b_done.md](phase7b_done.md) — mapper

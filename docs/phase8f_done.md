# Phase 8f 完成记录 — app startup bootstrap

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| 路线 | Route A |

---

## 1. 变更

| 文件 | 说明 |
|------|------|
| `Message/runtime_bootstrap.py` | `apply_app_startup_bootstrap()` |
| `app.py` | `main()` 在 QApplication 后、MainWindow 前调用 |

---

## 2. 行为

- 成功：`logger.info("ChannelRegistry bootstrap ok: ['pinduoduo']")`（Demo 仅 flag on）
- 失败：`logger.warning(..., exc_info=True)`，GUI 继续
- **不** 改变 AutoReply / WS / handler 路径

---

## 3. diagnose vs app

- `python scripts/diagnose_runtime.py`：**独立进程**，通常仍 `not_applied`
- `python app.py`：**同进程** 会 register `pinduoduo`（bootstrap 成功时）

---

## 4. 验收

```powershell
python -m unittest discover -s tests -v
```

# Phase 8d 完成记录 — runtime diagnostics

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-03 |
| 路线 | Route B |

---

## 1. 新增 / 修改

| 文件 | 说明 |
|------|------|
| `Message/runtime_capabilities.py` | flag / import / capability report |
| `scripts/diagnose_runtime.py` | Phase 8d 扩展输出 |
| `tests/test_runtime_capabilities.py` | 单测 |
| `tests/test_diagnose_runtime.py` | subprocess 冒烟 |

---

## 2. 使用

```powershell
cd D:\agent
python scripts/diagnose_runtime.py
```

---

## 3. 验收

```powershell
python scripts/diagnose_runtime.py
python -m unittest discover -s tests -v
```

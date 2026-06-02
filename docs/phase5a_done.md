# Phase 5a 完成记录 — 运行模式文档 + diagnose_runtime

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-02 |
| 范围 | 仅文档、诊断脚本、`.env.example` / `runbook` 轻量更新 |

---

## 1. 新增 / 修改文件

| 操作 | 文件 |
|------|------|
| 新增 | `docs/runtime_modes.md` |
| 新增 | `scripts/diagnose_runtime.py` |
| 新增 | `docs/phase5a_done.md` |
| 修改 | `.env.example` |
| 修改 | `docs/runbook.md` |
| 修改 | `scripts/README.md`（diagnose 简短说明） |

---

## 2. 未做事项

- 未改业务逻辑（handler / core / channel 实现）
- 未改 UI、`app.py`、`config.py`
- 未统一 `channel_flags` / `outbound_flags`（Phase 5b 可选）
- 未做 Phase 4c（consumer metadata 镜像）

---

## 3. 验收命令

```powershell
cd D:\agent
python scripts/diagnose_runtime.py
python -m unittest discover -s tests -v
python app.py
```

---

## 4. Phase 5b 可选方向

- `runtime_env.py` 统一 bool 解析
- `config.json` 或设置页暴露运行模式（需 UI）
- Phase 4c consumer metadata 镜像

---

## 5. 签收

- [x] `runtime_modes.md` 四模式矩阵
- [x] `diagnose_runtime.py` 复用 flags 模块
- [x] runbook / `.env.example` 更新
- [ ] 维护者目视 `python app.py`（建议）

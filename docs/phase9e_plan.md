# Phase 9e 规划 — Release Checkpoint

| 项 | 值 |
|---|---|
| 状态 | 交付见 [phase9e_done.md](phase9e_done.md) |
| 主文档 | [release_checkpoint_phase9.md](release_checkpoint_phase9.md) |

---

## 1. 目标

在 **不改业务代码、不改测试、不改 flag 默认值** 的前提下，为 Phase **8a–9d** 整理正式 **release checkpoint**，作为进入 Phase 10 前的 SSOT 快照。

---

## 2. 范围

| In | Out |
|----|-----|
| 新增 `release_checkpoint_phase9.md` | 任何 `.py` |
| 更新 architecture / runtime_modes / runbook / README / phase9_plan | `tests/` |
| flag 矩阵、默认路径、回滚、验证清单 | 改 flag 默认 |
| Phase 10 边界与建议方向 | 接真实第二平台 |

---

## 3. 禁止项

- `app.py`、`channel_factory`、handlers、consumer、`autoreply_registry_flags.py`
- `diagnose_runtime.py`、`runtime_capabilities.py`（9e 不碰脚本）
- 根目录 `README.md`

---

## 4. 输出文档

1. `docs/phase9e_plan.md`（本文）
2. `docs/phase9e_done.md`
3. `docs/release_checkpoint_phase9.md`
4. 同步 `architecture_current.md`、`runtime_modes.md`、`runbook.md`、`docs/README.md`、`phase9_plan.md`

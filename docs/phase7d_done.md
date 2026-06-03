# Phase 7d 完成记录 — UnifiedMessage / Context 双轨入队

| 项 | 值 |
|---|---|
| 完成日期 | 2026-06-02 |
| 范围 | MessageWrapper 双轨 + 入队 + Consumer metadata |

---

## 1. 新增 / 修改文件

| 操作 | 文件 |
|------|------|
| 新增 | `Channel/pinduoduo/mappers/dual_track_flags.py` |
| 修改 | `Message/models/queue_models.py` |
| 修改 | `Message/core/queue.py`、`Message/__init__.py` |
| 修改 | `Message/core/consumer.py`（`enrich_metadata_from_unified`） |
| 修改 | `Channel/pinduoduo/core/pdd_message_handler.py`（入队分支） |
| 修改 | `Channel/pinduoduo/mappers/shadow.py`（双轨 on 时跳过重复 mapper） |
| 新增 | `tests/test_unified_dual_track.py` |

---

## 2. 行为摘要

- **`USE_UNIFIED_MESSAGE_DUAL_TRACK`**（默认 **false**）：入队时 `MessageWrapper` 可附带 `unified_message`。
- **handler 仍只处理 `Context`**；发送仍以 `metadata` 中 legacy `shop_id` / `user_id` / `from_uid`（来自 kwargs）为准。
- **immediate 路径**未纳入双轨。
- mapper 失败：`unified_message=None`，仍 `put_message(context)`。

---

## 3. 与 shadow 关系

| SHADOW | DUAL_TRACK | 行为 |
|--------|------------|------|
| off | off | 仅 Context（生产默认） |
| on | off | 旁路 log（7c） |
| off | on | 入队带 Unified + metadata |
| on | on | 入队带 Unified；**shadow 跳过**重复 mapper |

---

## 4. 联调

```powershell
$env:USE_UNIFIED_MESSAGE_DUAL_TRACK = "true"
python app.py
# Consumer metadata 含 has_unified、routing 等（debug/日志观测）
```

---

## 5. 验收

```powershell
python -m unittest discover -s tests -v
```

---

## 6. 下一步

- **7e**：handler adapter（可选读 metadata / UnifiedMessage）
- **8**：产品化、第二平台、`unified_outbound_resolver`

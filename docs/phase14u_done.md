# Phase 14u 完成 — MerchantSafetyPolicy + MerchantReplyTemplate Schema Behind Flags

| 项 | 内容 |
|----|------|
| 状态 | **schema + repository skeleton implemented** |
| 日期 | 2026-06-03 |
| 前置 | [phase14t_done.md](phase14t_done.md) · [phase14s_done.md](phase14s_done.md) |

---

## 交付说明

| 项 | 结论 |
|----|------|
| 实现 | `MerchantSafetyPolicyRow` · `MerchantReplyTemplateRow` ORM + SQLite repositories |
| flags | `WRITE_MERCHANT_POLICY` · `WRITE_REPLY_TEMPLATE` · `READ_MERCHANT_POLICY` 默认 **off** |
| final guard | **未实现** |
| assisted approve/reject | **未实现** |
| assisted send | **未实现** |
| auto send | **未实现** |
| handler / SendMessage / PDD / Doudian | **未改** |
| Dashboard API（14o） | **未改** |
| legacy database | **未改** |

---

## ORM / Repository

| 组件 | 文件 |
|------|------|
| `MerchantSafetyPolicyRow` | `product_persistence/models.py` |
| `MerchantReplyTemplateRow` | `product_persistence/models.py` |
| `MerchantPolicyRepositorySQLite` | `sqlite_merchant_policy_repository.py` |
| `MerchantReplyTemplateRepositorySQLite` | `sqlite_reply_template_repository.py` |

**Policy 方法：** `create_policy` · `get_policy` · `find_policy` · `list_policies` · `update_policy` · `disable_policy`（仅存取 · 无 effective_mode · 无 send）

**Template 方法：** `create_template` · `get_template` · `list_templates` · `update_template` · `disable_template`（`content_hash` = sha256 · 无 forbidden scan · 无 send）

---

## Flags

| Flag | 默认 | 激活条件 |
|------|------|----------|
| `PRODUCT_PERSISTENCE_ENABLED` | off | 总开关 |
| `PRODUCT_PERSISTENCE_WRITE_MERCHANT_POLICY` | off | ENABLED + flag |
| `PRODUCT_PERSISTENCE_WRITE_REPLY_TEMPLATE` | off | ENABLED + flag |
| `PRODUCT_PERSISTENCE_READ_MERCHANT_POLICY` | off | ENABLED + flag |

import module **不创建 DB**；flags off **不创建 product_gate.db**。

---

## 测试

`uv run python -m unittest discover -s tests -v`

- `tests/test_merchant_policy_template_schema.py`
- `tests/test_merchant_policy_template_repositories.py`

---

## 下一步

| Phase | 内容 |
|-------|------|
| **14v** | Final Guard **pure function** implementation |
| **14w** | Policy/template **validation service** skeleton |
| **14x** | Assisted service **skeleton behind flags** |

---

*签收：Phase 14u · 2026-06-03*

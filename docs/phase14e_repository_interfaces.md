# Phase 14e — Repository Interfaces

| 项 | 值 |
|----|-----|
| 类型 | docs only |
| 实现 | 14f Protocol stub · 14g SQLite · tests InMemory fake |
| 对齐 | [phase14a_replylog_schema.md](phase14a_replylog_schema.md) 等 |

---

## 1. 设计原则

| # | 原则 |
|---|------|
| R1 | Repository **不** 调用 SendMessage / outbound |
| R2 | Repository **不** classify intent / evaluate guard |
| R3 | Service 层组合 gates + repository |
| R4 | 每个 repository 可有 **InMemory** 实现供单元测试 |
| R5 | 方法 **幂等**  where applicable（create 用 UUID） |

---

## 2. ReplyLogRepository

```python
# 概念 Protocol — 14f

class ReplyLogRepository(Protocol):
    def create_preview_reply_log(
        self,
        *,
        workspace_id: str,
        shop_id: str,
        account_id: str,
        platform_id: str,
        buyer_id: str,
        inbound_message_id: str,
        buyer_message: str,
        ai_suggested_reply: str,
        send_status: str,          # not_sent_preview, ...
        send_mode: str,
        intent: str,
        intent_bucket: str,
        intent_confidence: float,
        risk_level: str,
        blocked_reason: str | None,
        human_takeover_reason: str | None,
        not_sent_explanation: str,
        product_gate_enabled: bool,
        reply_mode: str = "preview",
        conversation_id: str | None = None,
    ) -> str:  # reply_log_id
        ...

    def list_reply_logs(
        self,
        *,
        workspace_id: str | None = None,
        shop_id: str | None = None,
        buyer_id: str | None = None,
        send_status: str | None = None,
        limit: int = 100,
    ) -> list[ReplyLogRecordDTO]: ...

    def get_reply_log(self, reply_log_id: str) -> ReplyLogRecordDTO | None: ...

    def update_sent(
        self,
        reply_log_id: str,
        *,
        final_reply: str,
        send_status: str,  # sent | failed
        sent_at: datetime | None = None,
    ) -> None: ...  # assisted 未来
```

**映射：** 13e `PreviewReplyLogListItem` ↔ DTO。

---

## 3. SendDecisionRepository

```python
class SendDecisionRepository(Protocol):
    def create_snapshot(
        self,
        *,
        reply_log_id: str | None,
        workspace_id: str,
        shop_id: str,
        account_id: str,
        platform_id: str,
        inbound_message_id: str,
        decision_phase: str,       # ai_generate | merchant_confirm | shadow_only
        intent: str,
        intent_bucket: str,
        intent_confidence: float,
        risk_level: str,
        reply_mode: str,
        workspace_pause: bool,
        shop_pause: bool,
        product_gate_enabled: bool,
        allowed_to_generate: bool,
        allowed_to_send: bool,
        send_mode: str,
        blocked_reason: str | None,
        human_takeover_reason: str | None,
        decision_source: str,
        merchant_approved: bool = False,
    ) -> str:  # send_decision_id
        ...

    def list_snapshots_by_reply_log(
        self,
        reply_log_id: str,
    ) -> list[SendDecisionSnapshotDTO]: ...
```

**语义：** append-only；assisted confirm 写 **第二条** `merchant_confirm` snapshot。

---

## 4. PendingAssistedReplyRepository

```python
class PendingAssistedReplyRepository(Protocol):
    def create_pending(
        self,
        *,
        reply_log_id: str,
        workspace_id: str,
        shop_id: str,
        account_id: str,
        platform_id: str,
        buyer_id: str,
        inbound_message_id: str,
        suggested_reply: str,
        intent: str,
        risk_level: str,
        expires_at: datetime,
    ) -> str:  # pending_reply_id
        ...

    def mark_approved(
        self,
        pending_reply_id: str,
        *,
        approved_by: str,
        edited_reply: str | None = None,
    ) -> None: ...

    def mark_rejected(
        self,
        pending_reply_id: str,
        *,
        rejected_by: str,
        reason: str | None = None,
    ) -> None: ...

    def mark_expired(self, pending_reply_id: str) -> None: ...

    def mark_superseded(
        self,
        pending_reply_id: str,
        *,
        superseded_by_message_id: str,
    ) -> None: ...

    def get_pending(self, pending_reply_id: str) -> PendingAssistedReplyDTO | None: ...
```

**注意：** `mark_approved` **不** 发送；发送在 `AssistedReplyService` + SendMessage。

---

## 5. AuditLogRepository

```python
class AuditLogRepository(Protocol):
    def append_audit_log(
        self,
        *,
        workspace_id: str,
        shop_id: str | None,
        account_id: str | None,
        actor_member_id: str,
        actor_role: str,
        action: str,
        target_type: str,
        target_id: str,
        before_state: dict | None = None,
        after_state: dict | None = None,
        reason: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> str:  # audit_log_id
        ...

    def list_audit_logs(
        self,
        *,
        workspace_id: str,
        shop_id: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list[AuditLogDTO]: ...
```

**append-only：** 无 update/delete 方法。

---

## 6. 实现矩阵（规划）

| 实现 | Phase | 用途 |
|------|-------|------|
| `InMemoryReplyLogRepository` | 14f | 单元测试 |
| `SqliteReplyLogRepository` | 14g | test shop shadow |
| `Postgres*Repository` | 未来 C | SaaS 规模化 |

---

## 7. DTO 与 ORM 分离

- Repository 对外返回 **DTO**（dataclass），不泄漏 SQLAlchemy model
- `product_persistence/models.py` 仅 repository 内部使用

---

*Repository interfaces · Phase 14e · 2026-06-03*

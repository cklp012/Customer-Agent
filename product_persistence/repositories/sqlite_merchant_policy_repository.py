"""SQLite MerchantSafetyPolicy repository (Phase 14u) — schema skeleton only, no send."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, List, Optional, Sequence
from uuid import uuid4

from product_persistence.db_manager import ProductDbManager, get_product_db_manager
from product_persistence.models import MerchantSafetyPolicyDTO, MerchantSafetyPolicyRow

_DEFAULT_AI_MODE = "assisted_only"
_DEFAULT_PLATFORM_CEILING = "assisted_only"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json_list(values: Optional[Sequence[str]]) -> Optional[str]:
    if values is None:
        return None
    return json.dumps(list(values), ensure_ascii=False)


def _parse_string_list(raw: Optional[str]) -> tuple[str, ...]:
    if not raw:
        return ()
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        return ()
    return tuple(str(item) for item in parsed)


def _dto_from_row(row: MerchantSafetyPolicyRow) -> MerchantSafetyPolicyDTO:
    return MerchantSafetyPolicyDTO(
        policy_id=row.policy_id,
        workspace_id=row.workspace_id or "",
        shop_id=row.shop_id or "",
        intent_category=row.intent_category,
        ai_intervention_mode=row.ai_intervention_mode,
        platform_mode_ceiling=row.platform_mode_ceiling,
        allowed_template_ids=_parse_string_list(row.allowed_template_ids),
        require_human_confirmation=bool(row.require_human_confirmation),
        allow_auto_reply=bool(row.allow_auto_reply),
        forbidden_keywords_extra=_parse_string_list(row.forbidden_keywords_extra),
        policy_version=row.policy_version,
        enabled=bool(row.enabled),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class MerchantPolicyRepositorySQLite:
    """Merchant safety policy persistence skeleton — no effective_mode or send paths."""

    def __init__(self, db_manager: Optional[ProductDbManager] = None) -> None:
        self._db_manager = db_manager or get_product_db_manager()

    def create_policy(
        self,
        *,
        workspace_id: str,
        shop_id: str,
        intent_category: str,
        ai_intervention_mode: str = _DEFAULT_AI_MODE,
        platform_mode_ceiling: str = _DEFAULT_PLATFORM_CEILING,
        allowed_template_ids: Optional[Sequence[str]] = None,
        require_human_confirmation: bool = True,
        allow_auto_reply: bool = False,
        forbidden_keywords_extra: Optional[Sequence[str]] = None,
        enabled: bool = True,
        policy_id: Optional[str] = None,
        created_at: Optional[str] = None,
        **_kwargs: Any,
    ) -> str:
        pid = policy_id or str(uuid4())
        now = created_at or _utc_now_iso()
        row = MerchantSafetyPolicyRow(
            policy_id=pid,
            workspace_id=workspace_id,
            shop_id=shop_id,
            intent_category=intent_category,
            ai_intervention_mode=ai_intervention_mode,
            platform_mode_ceiling=platform_mode_ceiling,
            allowed_template_ids=_json_list(allowed_template_ids),
            require_human_confirmation=1 if require_human_confirmation else 0,
            allow_auto_reply=1 if allow_auto_reply else 0,
            forbidden_keywords_extra=_json_list(forbidden_keywords_extra),
            policy_version=1,
            enabled=1 if enabled else 0,
            created_at=now,
            updated_at=now,
        )
        session = self._db_manager.get_product_session()
        try:
            existing = session.get(MerchantSafetyPolicyRow, pid)
            if existing is not None:
                raise ValueError(f"policy_id already exists: {pid}")
            session.add(row)
            session.commit()
            return pid
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_policy(self, policy_id: str) -> Optional[MerchantSafetyPolicyDTO]:
        session = self._db_manager.get_product_session()
        try:
            row = session.get(MerchantSafetyPolicyRow, policy_id)
            if row is None:
                return None
            return _dto_from_row(row)
        finally:
            session.close()

    def find_policy(
        self,
        workspace_id: str,
        shop_id: str,
        intent_category: str,
    ) -> Optional[MerchantSafetyPolicyDTO]:
        session = self._db_manager.get_product_session()
        try:
            from sqlalchemy import select

            stmt = (
                select(MerchantSafetyPolicyRow)
                .where(MerchantSafetyPolicyRow.workspace_id == workspace_id)
                .where(MerchantSafetyPolicyRow.shop_id == shop_id)
                .where(MerchantSafetyPolicyRow.intent_category == intent_category)
                .where(MerchantSafetyPolicyRow.enabled == 1)
                .order_by(MerchantSafetyPolicyRow.updated_at.desc())
                .limit(1)
            )
            row = session.scalars(stmt).first()
            if row is None:
                return None
            return _dto_from_row(row)
        finally:
            session.close()

    def list_policies(
        self,
        *,
        workspace_id: Optional[str] = None,
        shop_id: Optional[str] = None,
        enabled: Optional[bool] = None,
        limit: int = 100,
    ) -> List[MerchantSafetyPolicyDTO]:
        session = self._db_manager.get_product_session()
        try:
            from sqlalchemy import select

            stmt = select(MerchantSafetyPolicyRow)
            if workspace_id is not None:
                stmt = stmt.where(MerchantSafetyPolicyRow.workspace_id == workspace_id)
            if shop_id is not None:
                stmt = stmt.where(MerchantSafetyPolicyRow.shop_id == shop_id)
            if enabled is not None:
                stmt = stmt.where(
                    MerchantSafetyPolicyRow.enabled == (1 if enabled else 0)
                )
            stmt = stmt.order_by(MerchantSafetyPolicyRow.updated_at.desc()).limit(limit)
            rows = session.scalars(stmt).all()
            return [_dto_from_row(row) for row in rows]
        finally:
            session.close()

    def update_policy(
        self,
        policy_id: str,
        **fields: Any,
    ) -> bool:
        session = self._db_manager.get_product_session()
        try:
            row = session.get(MerchantSafetyPolicyRow, policy_id)
            if row is None:
                return False
            if "ai_intervention_mode" in fields:
                row.ai_intervention_mode = fields["ai_intervention_mode"]
            if "platform_mode_ceiling" in fields:
                row.platform_mode_ceiling = fields["platform_mode_ceiling"]
            if "allowed_template_ids" in fields:
                row.allowed_template_ids = _json_list(fields["allowed_template_ids"])
            if "require_human_confirmation" in fields:
                row.require_human_confirmation = (
                    1 if fields["require_human_confirmation"] else 0
                )
            if "allow_auto_reply" in fields:
                row.allow_auto_reply = 1 if fields["allow_auto_reply"] else 0
            if "forbidden_keywords_extra" in fields:
                row.forbidden_keywords_extra = _json_list(
                    fields["forbidden_keywords_extra"]
                )
            if "enabled" in fields:
                row.enabled = 1 if fields["enabled"] else 0
            row.policy_version = row.policy_version + 1
            row.updated_at = _utc_now_iso()
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def disable_policy(self, policy_id: str) -> bool:
        return self.update_policy(policy_id, enabled=False)

"""SQLite MerchantReplyTemplate repository (Phase 14u) — schema skeleton only, no send."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence
from uuid import uuid4

from product_persistence.db_manager import ProductDbManager, get_product_db_manager
from product_persistence.models import MerchantReplyTemplateDTO, MerchantReplyTemplateRow

_DEFAULT_VALIDATION_STATUS = "pending_review"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _json_dict(value: Optional[Mapping[str, Any]]) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(dict(value), ensure_ascii=False, sort_keys=True)


def _parse_dict(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        return None
    return parsed


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


def _dto_from_row(row: MerchantReplyTemplateRow) -> MerchantReplyTemplateDTO:
    return MerchantReplyTemplateDTO(
        template_id=row.template_id,
        workspace_id=row.workspace_id or "",
        shop_id=row.shop_id or "",
        intent_category=row.intent_category,
        title=row.title,
        content=row.content,
        variables=_parse_dict(row.variables),
        content_hash=row.content_hash,
        validation_status=row.validation_status,
        validation_warnings=_parse_string_list(row.validation_warnings),
        template_version=row.template_version,
        enabled=bool(row.enabled),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class MerchantReplyTemplateRepositorySQLite:
    """Merchant reply template persistence skeleton — no validation scan or send paths."""

    def __init__(self, db_manager: Optional[ProductDbManager] = None) -> None:
        self._db_manager = db_manager or get_product_db_manager()

    def create_template(
        self,
        *,
        workspace_id: str,
        shop_id: str,
        intent_category: str,
        title: str,
        content: str,
        variables: Optional[Mapping[str, Any]] = None,
        validation_status: str = _DEFAULT_VALIDATION_STATUS,
        validation_warnings: Optional[Sequence[str]] = None,
        enabled: bool = True,
        template_id: Optional[str] = None,
        created_at: Optional[str] = None,
        **_kwargs: Any,
    ) -> str:
        tid = template_id or str(uuid4())
        now = created_at or _utc_now_iso()
        row = MerchantReplyTemplateRow(
            template_id=tid,
            workspace_id=workspace_id,
            shop_id=shop_id,
            intent_category=intent_category,
            title=title,
            content=content,
            variables=_json_dict(variables),
            content_hash=_content_hash(content),
            validation_status=validation_status,
            validation_warnings=_json_list(validation_warnings),
            template_version=1,
            enabled=1 if enabled else 0,
            created_at=now,
            updated_at=now,
        )
        session = self._db_manager.get_product_session()
        try:
            existing = session.get(MerchantReplyTemplateRow, tid)
            if existing is not None:
                raise ValueError(f"template_id already exists: {tid}")
            session.add(row)
            session.commit()
            return tid
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_template(self, template_id: str) -> Optional[MerchantReplyTemplateDTO]:
        session = self._db_manager.get_product_session()
        try:
            row = session.get(MerchantReplyTemplateRow, template_id)
            if row is None:
                return None
            return _dto_from_row(row)
        finally:
            session.close()

    def list_templates(
        self,
        *,
        workspace_id: Optional[str] = None,
        shop_id: Optional[str] = None,
        intent_category: Optional[str] = None,
        enabled: Optional[bool] = None,
        validation_status: Optional[str] = None,
        limit: int = 100,
    ) -> List[MerchantReplyTemplateDTO]:
        session = self._db_manager.get_product_session()
        try:
            from sqlalchemy import select

            stmt = select(MerchantReplyTemplateRow)
            if workspace_id is not None:
                stmt = stmt.where(MerchantReplyTemplateRow.workspace_id == workspace_id)
            if shop_id is not None:
                stmt = stmt.where(MerchantReplyTemplateRow.shop_id == shop_id)
            if intent_category is not None:
                stmt = stmt.where(
                    MerchantReplyTemplateRow.intent_category == intent_category
                )
            if enabled is not None:
                stmt = stmt.where(
                    MerchantReplyTemplateRow.enabled == (1 if enabled else 0)
                )
            if validation_status is not None:
                stmt = stmt.where(
                    MerchantReplyTemplateRow.validation_status == validation_status
                )
            stmt = stmt.order_by(MerchantReplyTemplateRow.updated_at.desc()).limit(limit)
            rows = session.scalars(stmt).all()
            return [_dto_from_row(row) for row in rows]
        finally:
            session.close()

    def update_template(
        self,
        template_id: str,
        **fields: Any,
    ) -> bool:
        session = self._db_manager.get_product_session()
        try:
            row = session.get(MerchantReplyTemplateRow, template_id)
            if row is None:
                return False
            if "title" in fields:
                row.title = fields["title"]
            if "content" in fields:
                row.content = fields["content"]
                row.content_hash = _content_hash(fields["content"])
            if "variables" in fields:
                row.variables = _json_dict(fields["variables"])
            if "validation_status" in fields:
                row.validation_status = fields["validation_status"]
            if "validation_warnings" in fields:
                row.validation_warnings = _json_list(fields["validation_warnings"])
            if "enabled" in fields:
                row.enabled = 1 if fields["enabled"] else 0
            row.template_version = row.template_version + 1
            row.updated_at = _utc_now_iso()
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def disable_template(self, template_id: str) -> bool:
        return self.update_template(template_id, enabled=False)

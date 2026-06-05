"""Product DB manager skeleton (Phase 14f). No engine, no create_all, no DB file."""

from __future__ import annotations

import os
from typing import Any, Optional

_DEFAULT_DB_URL = "sqlite:///./temp/product_gate.db"


class ProductDbManager:
    """Lazy product_gate.db access — implementation deferred to Phase 14g+."""

    def __init__(self, db_url: Optional[str] = None) -> None:
        self._db_url = db_url or os.environ.get("PRODUCT_DB_URL", _DEFAULT_DB_URL)

    def get_db_url(self) -> str:
        return self._db_url

    def init_product_db(self) -> None:
        """No-op skeleton — does not create engine or tables."""

    def get_product_session(self) -> Any:
        raise NotImplementedError(
            "Product DB sessions are not available until Phase 14g+"
        )

    def close_product_db(self) -> None:
        """No-op skeleton."""


_default_manager: Optional[ProductDbManager] = None


def get_product_db_manager() -> ProductDbManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = ProductDbManager()
    return _default_manager


def init_product_db() -> None:
    get_product_db_manager().init_product_db()


def get_product_session() -> Any:
    return get_product_db_manager().get_product_session()


def close_product_db() -> None:
    get_product_db_manager().close_product_db()

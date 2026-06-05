"""Product DB manager (Phase 14l). product_gate.db only — no legacy database."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from product_persistence import flags

_DEFAULT_DB_URL = "sqlite:///./temp/product_gate.db"


def _sqlite_path_from_url(db_url: str) -> Optional[Path]:
    if db_url.startswith("sqlite:///"):
        return Path(db_url[len("sqlite:///") :])
    if db_url.startswith("sqlite://"):
        return Path(db_url[len("sqlite://") :])
    return None


class ProductDbManager:
    """Lazy product_gate.db access — init only when flags enabled or explicit init."""

    def __init__(self, db_url: Optional[str] = None) -> None:
        self._db_url = db_url or os.environ.get("PRODUCT_DB_URL", _DEFAULT_DB_URL)
        self._engine: Any = None
        self._session_factory: Any = None
        self._initialized = False

    def get_db_url(self) -> str:
        return self._db_url

    def _persistence_active(self) -> bool:
        return (
            flags.should_write_reply_log()
            or flags.should_write_send_decision()
            or flags.should_read_dashboard_from_product_db()
        )

    def _ensure_sqlite_directory(self) -> None:
        path = _sqlite_path_from_url(self._db_url)
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)

    def init_product_db(self) -> None:
        """Create engine and product tables when persistence flags are on."""
        if not self._persistence_active():
            return
        if self._initialized:
            return
        from product_persistence.models import ProductBase

        self._ensure_sqlite_directory()
        self._engine = create_engine(
            self._db_url,
            connect_args={"check_same_thread": False},
        )
        ProductBase.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)
        self._initialized = True

    def get_product_session(self) -> Session:
        if not self._initialized:
            if not self._persistence_active():
                raise NotImplementedError(
                    "Product DB sessions are not available until persistence flags enabled"
                )
            self.init_product_db()
        if not self._initialized or self._session_factory is None:
            raise RuntimeError("Product DB failed to initialize")
        return self._session_factory()

    def close_product_db(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
        self._engine = None
        self._session_factory = None
        self._initialized = False


_default_manager: Optional[ProductDbManager] = None


def get_product_db_manager() -> ProductDbManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = ProductDbManager()
    return _default_manager


def reset_product_db_manager() -> None:
    """Test helper — close engine and discard singleton."""
    global _default_manager
    if _default_manager is not None:
        _default_manager.close_product_db()
    _default_manager = None


def init_product_db() -> None:
    get_product_db_manager().init_product_db()


def get_product_session() -> Session:
    return get_product_db_manager().get_product_session()


def close_product_db() -> None:
    get_product_db_manager().close_product_db()

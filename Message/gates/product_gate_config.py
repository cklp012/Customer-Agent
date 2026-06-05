"""
Test-shop product gate configuration (Phase 13d).

In-memory allowlist only — default empty/disabled; no DB or network.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_PDD_PLATFORM_ALIASES = frozenset({"pinduoduo", "pdd"})
_NON_PDD_PLATFORMS = frozenset(
    {"doudian", "taobao", "jd", "jingdong", "tmall", "douyin"}
)


@dataclass(frozen=True)
class ProductGateConfig:
    product_gate_enabled: bool = False
    reply_mode: str = "preview"
    consultation_only: bool = False
    workspace_id: Optional[str] = None
    platform_id: Optional[str] = None
    shop_id: Optional[str] = None
    account_id: Optional[str] = None
    workspace_pause: bool = False
    shop_pause: bool = False


@dataclass(frozen=True)
class TestShopAllowlistEntry:
    workspace_id: str
    shop_id: str
    account_id: str
    platform_id: str = "pinduoduo"
    product_gate_enabled: bool = True
    reply_mode: str = "preview"
    consultation_only: bool = True
    workspace_pause: bool = False
    shop_pause: bool = False


_DISABLED = ProductGateConfig()

_test_shop_allowlist: List[TestShopAllowlistEntry] = []


def set_test_shop_allowlist(entries: List[TestShopAllowlistEntry]) -> None:
    """Replace in-memory allowlist (tests / local pilot only)."""
    global _test_shop_allowlist
    _test_shop_allowlist = list(entries)


def clear_test_shop_allowlist() -> None:
    """Remove all allowlist entries — production default."""
    set_test_shop_allowlist([])


def get_test_shop_allowlist() -> List[TestShopAllowlistEntry]:
    return list(_test_shop_allowlist)


def _normalize_platform(metadata: Dict[str, Any]) -> Optional[str]:
    raw = (
        metadata.get("platform_id")
        or metadata.get("platform")
        or metadata.get("channel_name")
    )
    if raw is None:
        return None
    return str(raw).strip().lower()


def _is_pinduoduo_platform(platform: Optional[str]) -> bool:
    if not platform:
        return False
    if platform in _NON_PDD_PLATFORMS:
        return False
    return platform in _PDD_PLATFORM_ALIASES


def _metadata_str(metadata: Dict[str, Any], key: str) -> Optional[str]:
    value = metadata.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def select_product_gate_config(metadata: Optional[Dict[str, Any]]) -> ProductGateConfig:
    """
    Resolve per-message gate config from metadata + in-memory allowlist.

    Default: product_gate_enabled=False (legacy). Never reads DB.
    """
    if not metadata:
        return _DISABLED

    platform = _normalize_platform(metadata)
    if not _is_pinduoduo_platform(platform):
        return _DISABLED

    shop_id = _metadata_str(metadata, "shop_id")
    account_id = _metadata_str(metadata, "account_id")
    workspace_id = _metadata_str(metadata, "workspace_id")

    if not shop_id or not account_id:
        return _DISABLED

    if not _test_shop_allowlist:
        return _DISABLED

    for entry in _test_shop_allowlist:
        if not entry.product_gate_enabled:
            continue
        if entry.platform_id.lower() not in _PDD_PLATFORM_ALIASES:
            continue
        if entry.shop_id != shop_id:
            continue
        if entry.account_id != account_id:
            continue
        if entry.workspace_id != workspace_id:
            continue
        if entry.reply_mode != "preview":
            continue
        if not entry.consultation_only:
            continue
        return ProductGateConfig(
            product_gate_enabled=True,
            reply_mode=entry.reply_mode,
            consultation_only=entry.consultation_only,
            workspace_id=workspace_id,
            platform_id=platform,
            shop_id=shop_id,
            account_id=account_id,
            workspace_pause=entry.workspace_pause,
            shop_pause=entry.shop_pause,
        )

    return _DISABLED

# Phase 10b：多平台 AutoReply UI 展示与守卫（纯 UI，不改运行时）
from __future__ import annotations

from typing import Any, List, Optional, Tuple

AUTOREPLY_UNSUPPORTED_TOOLTIP = "该平台自动回复即将支持"

PLATFORM_DISPLAY_NAMES = {
    "pinduoduo": "拼多多",
    "demo": "Demo",
    "doudian": "抖店",
    "jingdong": "京东",
    "taobao": "淘宝",
    "douyin": "抖音",
}

# (label, filter channel_name or None for all, selectable)
PLATFORM_FILTER_OPTIONS: List[Tuple[str, Optional[str], bool]] = [
    ("全部", None, True),
    ("拼多多", "pinduoduo", True),
    ("抖店（即将支持）", "doudian", False),
    ("京东（即将支持）", "jingdong", False),
    ("淘宝（即将支持）", "taobao", False),
]

PRODUCTION_AUTOREPLY_PLATFORM = "pinduoduo"


def normalize_channel_name(channel_name: Any) -> str:
    """缺失或空白 channel_name 视为 pinduoduo（与 SetStatusThread / 10a 约定一致）。"""
    if channel_name is None:
        return PRODUCTION_AUTOREPLY_PLATFORM
    text = str(channel_name).strip()
    if not text:
        return PRODUCTION_AUTOREPLY_PLATFORM
    return text.lower()


def platform_display_name(channel_name: Any) -> str:
    """已知平台显示中文名；unknown 显示原始 channel_name。"""
    if channel_name is None or (isinstance(channel_name, str) and not str(channel_name).strip()):
        return PLATFORM_DISPLAY_NAMES[PRODUCTION_AUTOREPLY_PLATFORM]
    raw = str(channel_name).strip()
    return PLATFORM_DISPLAY_NAMES.get(raw.lower(), raw)


def is_autoreply_supported(channel_name: Any) -> bool:
    """仅拼多多账号可启动自动回复（10b UI skeleton）。"""
    return normalize_channel_name(channel_name) == PRODUCTION_AUTOREPLY_PLATFORM


def account_matches_platform_filter(account_data: dict, filter_channel: Optional[str]) -> bool:
    """filter_channel 为 None 表示「全部」。"""
    if filter_channel is None:
        return True
    return normalize_channel_name(account_data.get("channel_name")) == filter_channel


__all__ = [
    "AUTOREPLY_UNSUPPORTED_TOOLTIP",
    "PLATFORM_DISPLAY_NAMES",
    "PLATFORM_FILTER_OPTIONS",
    "PRODUCTION_AUTOREPLY_PLATFORM",
    "account_matches_platform_filter",
    "is_autoreply_supported",
    "normalize_channel_name",
    "platform_display_name",
]

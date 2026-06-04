"""
多平台消息队列命名 helper（Phase 10f）。

仅提供命名契约；生产 PDD 路径仍使用 pdd_lifecycle 内 f"pdd_{shop_id}"，本模块未强制接入。
"""

from __future__ import annotations

from typing import Any, Mapping

# platform_id（归一化后）→ queue 前缀
_PLATFORM_QUEUE_PREFIX: Mapping[str, str] = {
    "pinduoduo": "pdd",
    "pdd": "pdd",
    "demo": "demo",
    "doudian": "doudian",
    "jingdong": "jingdong",
    "taobao": "taobao",
}

_DEFAULT_PLATFORM_ID = "pinduoduo"
_PDD_PREFIX = "pdd"


def _platform_id_to_str(platform_id: Any) -> str:
    if platform_id is None:
        return ""
    value = getattr(platform_id, "value", platform_id)
    return str(value).strip()


def normalize_platform_id(platform_id: Any) -> str:
    """
    归一化平台 ID（小写字符串）。

    None / 空白 → pinduoduo（与 account model 缺省一致）。
    """
    text = _platform_id_to_str(platform_id)
    if not text:
        return _DEFAULT_PLATFORM_ID
    return text.lower()


def queue_prefix_for_platform(platform_id: Any) -> str:
    """返回队列名前缀（不含 shop_id）。"""
    normalized = normalize_platform_id(platform_id)
    return _PLATFORM_QUEUE_PREFIX.get(normalized, normalized)


def build_queue_name(platform_id: Any, shop_id: Any) -> str:
    """
    构造消息队列名：{prefix}_{shop_id}。

    pinduoduo / pdd → pdd_{shop_id}；其它已知平台见 _PLATFORM_QUEUE_PREFIX；
    unknown 平台使用归一化后的 platform_id 作为 prefix。

    Raises:
        ValueError: shop_id 为 None 或空白。
    """
    if shop_id is None:
        raise ValueError("shop_id is required for queue name")
    shop = str(shop_id).strip()
    if not shop:
        raise ValueError("shop_id is required for queue name")

    prefix = queue_prefix_for_platform(platform_id)
    return f"{prefix}_{shop}"


__all__ = [
    "build_queue_name",
    "normalize_platform_id",
    "queue_prefix_for_platform",
]

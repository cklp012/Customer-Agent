"""
Demo 入站 raw dict → legacy Context（Phase 8a）。

不修改 bridge；kwargs 使用 dict，含 shop_id / user_id / from_uid / channel_type。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from bridge.context import Context, ContextType


class _DemoKwargs:
    """Demo 入站 kwargs（非 bridge 类型，供 getattr 与 Consumer metadata 兼容）。"""

    def __init__(
        self,
        shop_id: str,
        user_id: str,
        from_uid: str,
        *,
        channel_type: str = "demo",
        message_id: Any = None,
    ) -> None:
        self.shop_id = shop_id
        self.user_id = user_id
        self.from_uid = from_uid
        self.channel_type = channel_type
        self.message_id = message_id


def demo_raw_to_context(
    raw: Dict[str, Any],
    shop_id: str,
    account_id: str,
    *,
    from_uid: Optional[str] = None,
) -> Context:
    """将 Demo 合成入站 dict 转为 handler 可消费的 Context（TEXT）。"""
    buyer = from_uid or raw.get("from_uid") or raw.get("buyer_uid") or "demo-buyer-1"
    content = raw.get("content", "")
    if not isinstance(content, str):
        content = str(content)

    kwargs = _DemoKwargs(
        str(shop_id),
        str(account_id),
        str(buyer),
        channel_type="demo",
        message_id=raw.get("message_id"),
    )

    return Context(
        type=ContextType.TEXT,
        content=content,
        kwargs=kwargs,
    )

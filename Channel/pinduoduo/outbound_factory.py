"""拼多多出站适配器工厂（Phase 2a）。"""

from __future__ import annotations

from Channel.pinduoduo.pinduoduo_outbound import PinduoduoOutbound


def create_pinduoduo_outbound(shop_id: str, user_id: str) -> PinduoduoOutbound:
    """按店铺与账号创建出站适配器实例。"""
    return PinduoduoOutbound(str(shop_id), str(user_id))

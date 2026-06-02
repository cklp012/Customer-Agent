"""拼多多出站适配器功能开关（Phase 2a，供 Phase 2b 接入 handler 使用）。"""

from __future__ import annotations

import os

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def use_pinduoduo_outbound() -> bool:
    """是否启用 PinduoduoOutbound。默认 False，读取环境变量 USE_PINDUODUO_OUTBOUND。"""
    raw = os.environ.get("USE_PINDUODUO_OUTBOUND", "")
    return raw.strip().lower() in _TRUE_VALUES

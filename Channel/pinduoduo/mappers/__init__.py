"""拼多多 UnifiedMessage 映射（Phase 7b，未接入运行时）。"""

from Channel.pinduoduo.mappers.pdd_to_unified import (
    compute_pdd_routing,
    pdd_message_to_unified,
)

__all__ = [
    "compute_pdd_routing",
    "pdd_message_to_unified",
]

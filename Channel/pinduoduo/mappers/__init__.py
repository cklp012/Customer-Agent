"""拼多多 UnifiedMessage 映射（Phase 7b/7c）。"""

from Channel.pinduoduo.mappers.pdd_to_unified import (
    compute_pdd_routing,
    pdd_message_to_unified,
)
from Channel.pinduoduo.mappers.shadow import maybe_shadow_unified_message
from Channel.pinduoduo.mappers.shadow_flags import use_unified_message_shadow

__all__ = [
    "compute_pdd_routing",
    "maybe_shadow_unified_message",
    "pdd_message_to_unified",
    "use_unified_message_shadow",
]

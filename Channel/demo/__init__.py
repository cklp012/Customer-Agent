"""Demo 平台 Channel（Phase 6b，非生产）。"""

from Channel.demo.demo_channel import DemoChannel
from Channel.demo.demo_factory import (
    create_demo_channel,
    register_demo_channel,
    unregister_demo_channel,
)
from Channel.demo.demo_outbound import DemoOutbound

__all__ = [
    "DemoChannel",
    "DemoOutbound",
    "create_demo_channel",
    "register_demo_channel",
    "unregister_demo_channel",
]

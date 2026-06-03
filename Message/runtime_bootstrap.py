"""
ChannelRegistry 运行时 bootstrap（Phase 8e）。

仅注册工厂，不 start_account、不连网、不启动 Demo runtime。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from Channel.base.registry import ChannelRegistry
from Channel.base.types import PlatformType
from Message.bootstrap_flags import use_demo_channel_registration


@dataclass(frozen=True)
class PlatformBootstrapInfo:
    """可 bootstrap 的平台元数据。"""

    platform_id: str
    production_safe: bool
    test_only: bool


@dataclass(frozen=True)
class BootstrapStatus:
    """当前进程 ChannelRegistry bootstrap 状态。"""

    available: List[str]
    planned: List[str]
    registered: List[str]
    missing: List[str]
    extra: List[str]
    status: str


def list_available_platforms() -> List[PlatformBootstrapInfo]:
    """代码库内具备工厂、可被 bootstrap 的平台目录。"""
    return [
        PlatformBootstrapInfo(
            platform_id=PlatformType.PINDUODUO.value,
            production_safe=True,
            test_only=False,
        ),
        PlatformBootstrapInfo(
            platform_id=PlatformType.DEMO.value,
            production_safe=False,
            test_only=True,
        ),
    ]


def get_default_registration_plan() -> List[str]:
    """默认应注册的平台（不含 start）。"""
    plan = [PlatformType.PINDUODUO.value]
    if use_demo_channel_registration():
        plan.append(PlatformType.DEMO.value)
    return plan


def register_default_platforms(*, force: bool = False) -> List[str]:
    """
    向 ChannelRegistry 注册默认平台工厂。

    幂等；不 start_account。force 保留供未来扩展，8e 未使用。
    """
    del force
    registered_now: List[str] = []

    from Channel.pinduoduo.channel_factory import register_pinduoduo_channel

    register_pinduoduo_channel()
    registered_now.append(PlatformType.PINDUODUO.value)

    if use_demo_channel_registration():
        from Channel.demo.demo_factory import register_demo_channel

        register_demo_channel()
        registered_now.append(PlatformType.DEMO.value)

    return registered_now


def get_bootstrap_status() -> BootstrapStatus:
    """对比 available / planned / 当前已注册。"""
    available = [p.platform_id for p in list_available_platforms()]
    planned = get_default_registration_plan()
    registered = [p.value for p in ChannelRegistry.registered_platforms()]

    planned_set = set(planned)
    registered_set = set(registered)
    missing = sorted(planned_set - registered_set)
    extra = sorted(registered_set - planned_set)

    if not registered_set:
        status = "not_applied"
    elif planned_set <= registered_set and not extra:
        status = "default_applied"
    elif missing:
        status = "partial"
    else:
        status = "extra_registered"

    return BootstrapStatus(
        available=available,
        planned=planned,
        registered=registered,
        missing=missing,
        extra=extra,
        status=status,
    )


def clear_channel_registry_for_tests() -> None:
    """清空 ChannelRegistry（仅测试 tearDown 使用）。"""
    ChannelRegistry.clear()


def format_bootstrap_for_console(status: BootstrapStatus) -> str:
    """人类可读 Platform bootstrap 报告。"""
    avail_lines = []
    for info in list_available_platforms():
        tags = []
        if info.production_safe:
            tags.append("production")
        if info.test_only:
            tags.append("test-only")
        tag_str = ", ".join(tags) if tags else "n/a"
        avail_lines.append(f"    - {info.platform_id} ({tag_str})")

    reg = (
        ", ".join(status.registered)
        if status.registered
        else "(none)"
    )
    lines = [
        "  Available platforms:",
        *avail_lines,
        "  Default registration plan:  " + ", ".join(status.planned),
        "  Registered in this process: " + reg,
        "  Bootstrap status:           " + status.status,
    ]
    if status.missing:
        lines.append("  Missing from registry:      " + ", ".join(status.missing))
    if status.extra:
        lines.append("  Extra (not in default plan): " + ", ".join(status.extra))
    lines.extend(
        [
            "",
            "  Notes:",
            "    - Empty ChannelRegistry is normal until register_default_platforms() "
            "or app bootstrap (Phase 8f).",
            "    - AutoReplyThread still uses create_auto_reply_runtime_channel(), "
            "not ChannelRegistry.create().",
            "    - Registry registration does not mean GUI switched to Registry.",
            "    - Demo is test-only; default plan excludes demo unless "
            "USE_DEMO_CHANNEL_REGISTRATION=true.",
        ]
    )
    return "\n".join(lines)

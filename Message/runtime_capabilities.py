"""
Runtime capability 探测（Phase 8d）。

只读 import / flag / ChannelRegistry；不启动 GUI、不连 PDD、不修改环境变量。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple

# Flag env 名 → 现有 helper（不重复解析语义）
_FLAG_READERS: Dict[str, Callable[[], bool]] = {}


def _ensure_flag_readers() -> Dict[str, Callable[[], bool]]:
    if _FLAG_READERS:
        return _FLAG_READERS
    from Channel.pinduoduo.channel_flags import use_pinduoduo_channel_wrapper
    from Channel.pinduoduo.mappers.dual_track_flags import use_unified_message_dual_track
    from Channel.pinduoduo.mappers.shadow_flags import use_unified_message_shadow
    from Channel.pinduoduo.outbound_flags import use_pinduoduo_outbound
    from Message.autoreply_registry_flags import use_channel_registry_for_autoreply
    from Message.handlers.unified_outbound_flags import use_unified_outbound_resolver

    _FLAG_READERS.update(
        {
            "USE_PINDUODUO_CHANNEL_WRAPPER": use_pinduoduo_channel_wrapper,
            "USE_PINDUODUO_OUTBOUND": use_pinduoduo_outbound,
            "USE_UNIFIED_MESSAGE_SHADOW": use_unified_message_shadow,
            "USE_UNIFIED_MESSAGE_DUAL_TRACK": use_unified_message_dual_track,
            "USE_UNIFIED_OUTBOUND_RESOLVER": use_unified_outbound_resolver,
            "USE_CHANNEL_REGISTRY_FOR_AUTOREPLY": use_channel_registry_for_autoreply,
        }
    )
    return _FLAG_READERS


def read_all_runtime_flags() -> Dict[str, bool]:
    """读取全部运行模式 flag 的 resolved 布尔值。"""
    readers = _ensure_flag_readers()
    return {name: reader() for name, reader in readers.items()}


def _try_import(label: str, import_fn: Callable[[], Any]) -> Tuple[str, bool, str | None]:
    try:
        import_fn()
        return label, True, None
    except Exception as exc:
        return label, False, str(exc)


def check_module_imports() -> Dict[str, Dict[str, bool]]:
    """分组模块 import 检查（仅 import，不启动 runtime）。"""
    groups: Dict[str, List[Tuple[str, Callable[[], Any]]]] = {
        "pdd_core": [
            (
                "PinduoduoChannel",
                lambda: __import__(
                    "Channel.pinduoduo.pinduoduo_channel",
                    fromlist=["PinduoduoChannel"],
                ).PinduoduoChannel,
            ),
            (
                "PinduoduoOutbound",
                lambda: __import__(
                    "Channel.pinduoduo.pinduoduo_outbound",
                    fromlist=["PinduoduoOutbound"],
                ).PinduoduoOutbound,
            ),
            (
                "AccountOutboundRegistry",
                lambda: __import__(
                    "Message.handlers.account_outbound_registry",
                    fromlist=["register", "get", "unregister", "clear"],
                ),
            ),
        ],
        "demo_8a": [
            (
                "demo_raw_to_context",
                lambda: __import__(
                    "Channel.demo.mappers.demo_to_context",
                    fromlist=["demo_raw_to_context"],
                ).demo_raw_to_context,
            ),
            (
                "demo_raw_to_unified",
                lambda: __import__(
                    "Channel.demo.mappers.demo_to_unified",
                    fromlist=["demo_raw_to_unified"],
                ).demo_raw_to_unified,
            ),
        ],
        "inbound_enqueue": [
            (
                "enqueue_inbound_message",
                lambda: __import__(
                    "Message.inbound_enqueue",
                    fromlist=["enqueue_inbound_message"],
                ).enqueue_inbound_message,
            ),
        ],
        "outbound_8b_8c": [
            (
                "channel_outbound_registry",
                lambda: __import__(
                    "Message.handlers.channel_outbound_registry",
                    fromlist=["register", "get"],
                ),
            ),
            (
                "resolve_outbound",
                lambda: __import__(
                    "Message.handlers.unified_outbound_resolver",
                    fromlist=["resolve_outbound"],
                ).resolve_outbound,
            ),
            (
                "unified_outbound_flags",
                lambda: __import__(
                    "Message.handlers.unified_outbound_flags",
                    fromlist=["use_unified_outbound_resolver"],
                ).use_unified_outbound_resolver,
            ),
        ],
        "channel_registry": [
            (
                "ChannelRegistry",
                lambda: __import__(
                    "Channel.base.registry", fromlist=["ChannelRegistry"]
                ).ChannelRegistry,
            ),
            (
                "PlatformType",
                lambda: __import__(
                    "Channel.base.types", fromlist=["PlatformType"]
                ).PlatformType,
            ),
        ],
    }

    result: Dict[str, Dict[str, bool]] = {}
    for group_name, checks in groups.items():
        result[group_name] = {}
        for label, fn in checks:
            _, ok, _ = _try_import(label, fn)
            result[group_name][label] = ok
    return result


def get_channel_registry_status() -> List[str]:
    """当前 ChannelRegistry 已注册平台（空列表合法）。"""
    from Channel.base.registry import ChannelRegistry

    return [p.value for p in ChannelRegistry.registered_platforms()]


def _resolve_pdd_mode(flags: Dict[str, bool]) -> Tuple[str, str]:
    wrapper_on = flags["USE_PINDUODUO_CHANNEL_WRAPPER"]
    outbound_on = flags["USE_PINDUODUO_OUTBOUND"]
    if not wrapper_on and not outbound_on:
        return (
            "legacy-default",
            "legacy PDDChannel + legacy SendMessage（生产默认）",
        )
    if wrapper_on and not outbound_on:
        return (
            "wrapper-only",
            "PinduoduoChannel 包装层；出站仍 legacy SendMessage",
        )
    if not wrapper_on and outbound_on:
        return (
            "outbound-only",
            "legacy PDDChannel；handler 每消息 create PinduoduoOutbound（不用 registry）",
        )
    return (
        "wrapper-and-outbound",
        "PinduoduoChannel + registry 复用 channel.outbound（Phase 4b 目标模式）",
    )


def _active_pdd_send_path(flags: Dict[str, bool]) -> str:
    if flags["USE_PINDUODUO_OUTBOUND"]:
        return "PinduoduoOutbound (USE_PINDUODUO_OUTBOUND=true), fallback legacy SendMessage"
    return "legacy SendMessage (USE_PINDUODUO_OUTBOUND=false, production default)"


def infer_autoreply_channel_source(
    *,
    flags: Dict[str, bool] | None = None,
    registry_platforms: List[str] | None = None,
) -> str:
    """
    推断 AutoReply create_auto_reply_runtime_channel 将使用的创建路径（只读，不创建实例）。
    """
    flags = flags if flags is not None else read_all_runtime_flags()
    registry_platforms = (
        registry_platforms
        if registry_platforms is not None
        else get_channel_registry_status()
    )

    if not flags.get("USE_CHANNEL_REGISTRY_FOR_AUTOREPLY", False):
        return "legacy_factory"

    from Channel.base.types import PlatformType

    if PlatformType.PINDUODUO.value in registry_platforms:
        return "registry"

    return "registry_fallback"


@dataclass(frozen=True)
class RuntimeCapabilityReport:
    """Runtime capability 报告（Phase 8d）。"""

    active_pdd_send_path: str
    handler_outbound_resolver: str
    immediate_message_resolver: str
    demo_inbound_pipeline: bool
    demo_test_runtime: bool
    unified_outbound_available: bool
    handler_unified_outbound_enabled: bool
    unified_inbound_dual_track_enabled: bool
    unified_shadow_mapper_enabled: bool
    channel_registry_platforms: List[str]
    pdd_mode_id: str
    pdd_mode_description: str
    bootstrap_status: str
    default_registration_plan: List[str]
    available_platforms: List[str]
    autoreply_channel_source: str


def build_runtime_capability_report(
    *,
    flags: Dict[str, bool] | None = None,
    imports: Dict[str, Dict[str, bool]] | None = None,
    registry_platforms: List[str] | None = None,
) -> RuntimeCapabilityReport:
    """构建 capability 报告。"""
    flags = flags if flags is not None else read_all_runtime_flags()
    imports = imports if imports is not None else check_module_imports()
    registry_platforms = (
        registry_platforms
        if registry_platforms is not None
        else get_channel_registry_status()
    )

    demo_8a = imports.get("demo_8a", {})
    inbound = imports.get("inbound_enqueue", {})
    outbound_grp = imports.get("outbound_8b_8c", {})
    channel_reg = imports.get("channel_registry", {})

    demo_inbound_pipeline = all(demo_8a.values()) and all(inbound.values())
    consumer_ok = _try_import(
        "MessageConsumer",
        lambda: __import__(
            "Message.core.consumer", fromlist=["message_consumer_manager"]
        ).message_consumer_manager,
    )[1]
    demo_test_runtime = demo_inbound_pipeline and consumer_ok

    unified_outbound_available = all(outbound_grp.values()) and all(
        channel_reg.values()
    )

    handler_resolver = (
        "resolve_outbound (USE_UNIFIED_OUTBOUND_RESOLVER=true)"
        if flags["USE_UNIFIED_OUTBOUND_RESOLVER"]
        else "resolve_pinduoduo_outbound (production default)"
    )

    mode_id, mode_desc = _resolve_pdd_mode(flags)

    from Message.runtime_bootstrap import get_bootstrap_status

    bootstrap = get_bootstrap_status()
    autoreply_source = infer_autoreply_channel_source(
        flags=flags,
        registry_platforms=registry_platforms,
    )

    return RuntimeCapabilityReport(
        active_pdd_send_path=_active_pdd_send_path(flags),
        handler_outbound_resolver=handler_resolver,
        immediate_message_resolver="resolve_pinduoduo_outbound (pdd_message_handler, unchanged)",
        demo_inbound_pipeline=demo_inbound_pipeline,
        demo_test_runtime=demo_test_runtime,
        unified_outbound_available=unified_outbound_available,
        handler_unified_outbound_enabled=flags["USE_UNIFIED_OUTBOUND_RESOLVER"],
        unified_inbound_dual_track_enabled=flags["USE_UNIFIED_MESSAGE_DUAL_TRACK"],
        unified_shadow_mapper_enabled=flags["USE_UNIFIED_MESSAGE_SHADOW"],
        channel_registry_platforms=list(registry_platforms),
        pdd_mode_id=mode_id,
        pdd_mode_description=mode_desc,
        bootstrap_status=bootstrap.status,
        default_registration_plan=list(bootstrap.planned),
        available_platforms=list(bootstrap.available),
        autoreply_channel_source=autoreply_source,
    )


def format_capability_report_for_console(report: RuntimeCapabilityReport) -> str:
    """人类可读 capability 报告。"""
    reg = (
        ", ".join(report.channel_registry_platforms)
        if report.channel_registry_platforms
        else "(none — expected before app bootstrap)"
    )
    lines = [
        "  Active PDD send path (handler):     "
        + report.active_pdd_send_path,
        "  PDD mode ID:                       " + report.pdd_mode_id,
        "  PDD mode description:              " + report.pdd_mode_description,
        "  Handler outbound resolver:         " + report.handler_outbound_resolver,
        "  Immediate message resolver:        " + report.immediate_message_resolver,
        "  Demo inbound pipeline (imports):   "
        + ("available" if report.demo_inbound_pipeline else "unavailable"),
        "  Demo test runtime (imports):       "
        + (
            "available (test-only, not production platform)"
            if report.demo_test_runtime
            else "unavailable"
        ),
        "  Unified outbound resolver:         "
        + (
            "available"
            if report.unified_outbound_available
            else "unavailable"
        ),
        "  Handler unified outbound enabled:  "
        + str(report.handler_unified_outbound_enabled),
        "  Unified dual-track inbound:        "
        + str(report.unified_inbound_dual_track_enabled),
        "  Unified shadow mapper:             "
        + str(report.unified_shadow_mapper_enabled),
        "  ChannelRegistry platforms:         " + reg,
        "  Bootstrap status:                  " + report.bootstrap_status,
        "  Default registration plan:         "
        + ", ".join(report.default_registration_plan),
        "  Available platforms (bootstrap):   "
        + ", ".join(report.available_platforms),
        "  AutoReply channel source:          " + report.autoreply_channel_source,
        "",
        "  Notes:",
        "    - Phase 9d: USE_CHANNEL_REGISTRY_FOR_AUTOREPLY defaults true (registry path);",
        "      set false to roll back to legacy_factory. diagnose subprocess may show",
        "      registry_fallback before bootstrap; app.py after bootstrap usually registry.",
        "    - pdd_message_handler still uses resolve_pinduoduo_outbound only.",
        "    - Demo runtime is for unittest/integration tests, not production.",
        "    - See diagnose ## Platform bootstrap for Registry vs AutoReplyThread.",
    ]
    return "\n".join(lines)


def format_import_checks_for_console(imports: Dict[str, Dict[str, bool]]) -> str:
    """分组 import 检查结果文本。"""
    group_titles = {
        "pdd_core": "PDD core",
        "demo_8a": "Demo (Phase 8a)",
        "inbound_enqueue": "Inbound enqueue (Phase 8a)",
        "outbound_8b_8c": "Unified outbound (Phase 8b–8c)",
        "channel_registry": "Channel registry",
    }
    lines: List[str] = []
    for group_key, title in group_titles.items():
        lines.append(f"  ### {title}")
        for label, ok in imports.get(group_key, {}).items():
            status = "ok" if ok else "fail"
            lines.append(f"    [{status}] {label}")
        lines.append("")
    return "\n".join(lines).rstrip()

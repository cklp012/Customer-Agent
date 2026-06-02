#!/usr/bin/env python3
"""
运行模式诊断（Phase 5a）。

不启动 GUI、不连接 PDD、不读取账号密码、不修改环境变量。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _find_project_root() -> Path:
    """从脚本位置向上查找含 app.py 的目录。"""
    here = Path(__file__).resolve().parent
    for candidate in (here.parent, here.parent.parent):
        if (candidate / "app.py").is_file():
            return candidate
    return here.parent


def _env_display(name: str) -> str:
    raw = os.environ.get(name)
    if raw is None:
        return "<unset>"
    stripped = raw.strip()
    return stripped if stripped else "<empty>"


def _resolve_mode(wrapper_on: bool, outbound_on: bool) -> tuple[str, str]:
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


def _try_import(label: str, import_fn) -> bool:
    try:
        import_fn()
        print(f"  [ok] {label}")
        return True
    except Exception as exc:
        print(f"  [fail] {label}: {exc}")
        return False


def main() -> int:
    project_root = _find_project_root()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    print("=" * 60)
    print("Customer-Agent Runtime Diagnostics (Phase 5a)")
    print("=" * 60)
    print()

    print("## Environment")
    print(f"  Python version: {sys.version.split()[0]} ({sys.version})")
    print(f"  sys.executable: {sys.executable}")
    print(f"  cwd:            {Path.cwd()}")
    print(f"  project root:   {project_root}")
    print()

    from Channel.pinduoduo.channel_flags import use_pinduoduo_channel_wrapper
    from Channel.pinduoduo.outbound_flags import use_pinduoduo_outbound

    wrapper_raw = _env_display("USE_PINDUODUO_CHANNEL_WRAPPER")
    outbound_raw = _env_display("USE_PINDUODUO_OUTBOUND")
    wrapper_on = use_pinduoduo_channel_wrapper()
    outbound_on = use_pinduoduo_outbound()
    mode_id, mode_desc = _resolve_mode(wrapper_on, outbound_on)

    print("## Runtime mode flags")
    print(f"  USE_PINDUODUO_CHANNEL_WRAPPER: {wrapper_raw} -> {wrapper_on}")
    print(f"  USE_PINDUODUO_OUTBOUND:        {outbound_raw} -> {outbound_on}")
    print(f"  Mode: {mode_id}")
    print(f"  Description: {mode_desc}")
    print()
    print("  True values (case-insensitive): 1, true, yes, on")
    print("  Default when unset: false")
    print()

    print("## Import checks")
    import_results: list[bool] = []

    import_results.append(
        _try_import(
            "PinduoduoChannel",
            lambda: __import__(
                "Channel.pinduoduo.pinduoduo_channel", fromlist=["PinduoduoChannel"]
            ).PinduoduoChannel,
        )
    )
    import_results.append(
        _try_import(
            "PinduoduoOutbound",
            lambda: __import__(
                "Channel.pinduoduo.pinduoduo_outbound", fromlist=["PinduoduoOutbound"]
            ).PinduoduoOutbound,
        )
    )
    import_results.append(
        _try_import(
            "AccountOutboundRegistry",
            lambda: __import__(
                "Message.handlers.account_outbound_registry",
                fromlist=["register", "get", "unregister", "clear"],
            ),
        )
    )
    import_results.append(
        _try_import(
            "use_pinduoduo_channel_wrapper",
            lambda: use_pinduoduo_channel_wrapper(),
        )
    )
    import_results.append(
        _try_import(
            "use_pinduoduo_outbound",
            lambda: use_pinduoduo_outbound(),
        )
    )
    print()

    print("## Optional path checks (existence only)")
    for rel in ("config.json", "temp/channel_shop.db", ".browsers"):
        path = project_root / rel
        status = "yes" if path.exists() else "no"
        print(f"  {rel}: {status} ({path})")
    print()

    print("## Docs")
    print(f"  Runtime modes: {project_root / 'docs' / 'runtime_modes.md'}")
    print()

    if not any(import_results):
        print("ERROR: all import checks failed.")
        return 1

    print("Diagnostics complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

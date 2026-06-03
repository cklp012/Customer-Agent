#!/usr/bin/env python3
"""
运行模式诊断（Phase 5a + 8d + 8e）。

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


def main() -> int:
    project_root = _find_project_root()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from Message.runtime_bootstrap import format_bootstrap_for_console, get_bootstrap_status
    from Message.runtime_capabilities import (
        build_runtime_capability_report,
        check_module_imports,
        format_capability_report_for_console,
        format_import_checks_for_console,
        get_channel_registry_status,
        read_all_runtime_flags,
    )

    print("=" * 60)
    print("Customer-Agent Runtime Diagnostics (Phase 5a + 8d + 8e)")
    print("=" * 60)
    print()

    print("## Environment")
    print(f"  Python version: {sys.version.split()[0]} ({sys.version})")
    print(f"  sys.executable: {sys.executable}")
    print(f"  cwd:            {Path.cwd()}")
    print(f"  project root:   {project_root}")
    print()

    flags = read_all_runtime_flags()
    imports = check_module_imports()
    registry_platforms = get_channel_registry_status()
    report = build_runtime_capability_report(
        flags=flags,
        imports=imports,
        registry_platforms=registry_platforms,
    )

    print("## Runtime mode flags")
    print("  ### PDD channel / outbound")
    print(
        "  USE_PINDUODUO_CHANNEL_WRAPPER: "
        f"{_env_display('USE_PINDUODUO_CHANNEL_WRAPPER')} -> "
        f"{flags['USE_PINDUODUO_CHANNEL_WRAPPER']}"
    )
    print(
        "  USE_PINDUODUO_OUTBOUND:        "
        f"{_env_display('USE_PINDUODUO_OUTBOUND')} -> "
        f"{flags['USE_PINDUODUO_OUTBOUND']}"
    )
    print(f"  Mode: {report.pdd_mode_id}")
    print(f"  Description: {report.pdd_mode_description}")
    print()
    print("  ### Unified / multi-platform")
    from Message.bootstrap_flags import use_demo_channel_registration

    for env_name in (
        "USE_UNIFIED_MESSAGE_SHADOW",
        "USE_UNIFIED_MESSAGE_DUAL_TRACK",
        "USE_UNIFIED_OUTBOUND_RESOLVER",
        "USE_DEMO_CHANNEL_REGISTRATION",
    ):
        if env_name == "USE_DEMO_CHANNEL_REGISTRATION":
            resolved = use_demo_channel_registration()
        else:
            resolved = flags[env_name]
        print(f"  {env_name}: {_env_display(env_name)} -> {resolved}")
    print()
    print("  True values (case-insensitive): 1, true, yes, on")
    print("  Default when unset: false")
    print()

    print("## Runtime capability report")
    print(format_capability_report_for_console(report))
    print()

    bootstrap_status = get_bootstrap_status()
    print("## Platform bootstrap")
    print(format_bootstrap_for_console(bootstrap_status))
    print()

    print("## ChannelRegistry")
    if registry_platforms:
        for platform in registry_platforms:
            print(f"  - {platform}")
    else:
        print("  (none registered — normal before app bootstrap)")
    print()

    print("## Import checks")
    print(format_import_checks_for_console(imports))
    print()

    print("## Optional path checks (existence only)")
    for rel in ("config.json", "temp/channel_shop.db", ".browsers"):
        path = project_root / rel
        status = "yes" if path.exists() else "no"
        print(f"  {rel}: {status} ({path})")
    print()

    print("## Docs")
    print(f"  Runtime modes: {project_root / 'docs' / 'runtime_modes.md'}")
    print(f"  Phase 8d:      {project_root / 'docs' / 'phase8d_done.md'}")
    print(f"  Phase 8e:      {project_root / 'docs' / 'phase8e_done.md'}")
    print()

    pdd_core = imports.get("pdd_core", {})
    if pdd_core and not any(pdd_core.values()):
        print("ERROR: all PDD core import checks failed.")
        return 1

    print("Diagnostics complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""配置读写，默认值。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from paths import CONFIG_PATH, DEFAULT_ADB, DEFAULT_MUMU_MANAGER, DEFAULT_MUMU_ROOT, ensure_under_root

DEFAULT_CONFIG: dict[str, Any] = {
    "mumu_root": str(DEFAULT_MUMU_ROOT),
    "mumu_manager": str(DEFAULT_MUMU_MANAGER),
    "adb_path": str(DEFAULT_ADB),
    "workers": 3,
    # Worker/模拟器/登录流程全部按 workers 运行；只限制同时在飞的 adb.exe。
    "max_active_vms": 8,
    "adb_workflow_limit": 8,
    "adb_command_limit": 2,
    # 只做8秒错峰派发；代理检查、启动、登录各自继续，不相互堵塞。
    "startup_wave_size": 1,
    "startup_wave_settle_seconds": 8,
    # 代理少于 Worker 时按池顺序均衡复用；ADB由命令级 broker 背压。
    "allow_proxy_reuse": True,
    "create_count": 1,
    "create_launch_workers": 2,
    "use_nekobox": True,
    "prefer_aurora_venmo": False,
    "venmo_local_install": True,
    "auto_sort_windows": True,
    "window_width": 360,
    "window_height": 640,
    "window_margin": 0,
    "window_auto_fit": True,
    "restart_interval_minutes": 0,
    "login_timeout_seconds": 90,
    "boot_timeout_seconds": 240,
    "venmo_package": "com.venmo",
    "nekobox_package": "moe.nb4a",
    "kitsune_package": "io.github.huskydg.magisk",
    "create_defaults": {
        "resolution_width": 1440,
        "resolution_height": 2560,
        "resolution_dpi": 640,
        # custom 2C/2G = 可启动省电档；不要用默认 low(1C/1G)
        "performance_mode": "custom",
        "performance_cpu": 2,
        "performance_mem": 2.0,
        "root_permission": True,
        "system_disk_readonly": False,
        "mini_disk": True,
    },
    "adb_base_port": 16384,
    "adb_port_step": 32,
    # SOCKS5 change-ip: 同链接最短间隔；启动前刷新后等10秒并多次复测
    "proxy_refresh_min_interval_seconds": 180,
    "proxy_refresh_wait_seconds": 10,
    "proxy_startup_check_rounds": 5,
    "proxy_startup_check_gap_seconds": 10,
    # 无网络刷IP成功后，对当前账号最多再试几次
    "no_network_retry_after_refresh": 1,
    # step4 停止/选择
    "last_selected_vms": [],
    "stop_shutdown_vms": True,
    "stop_join_timeout_seconds": 1800,
    "reuse_existing_vms_on_start": True,
    # 内置安装包勾选（assets 内打包）
    "install_packages": {
        "nekobox": True,
        "kitsune": True,
        "ih8": True,
        "aurora": False,
        "venmo": True,
    },
    # 三类导出目录（可自由选择，默认项目 export/classified）
    "export_dir": "",
}



def load_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = ensure_under_root(path or CONFIG_PATH)
    data = dict(DEFAULT_CONFIG)
    data["create_defaults"] = dict(DEFAULT_CONFIG["create_defaults"])
    if cfg_path.exists():
        with cfg_path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            data.update(raw)
            if isinstance(raw.get("create_defaults"), dict):
                data["create_defaults"] = {
                    **DEFAULT_CONFIG["create_defaults"],
                    **raw["create_defaults"],
                }
            if isinstance(raw.get("install_packages"), dict):
                data["install_packages"] = {
                    **DEFAULT_CONFIG["install_packages"],
                    **raw["install_packages"],
                }
    return data


def save_config(cfg: dict[str, Any], path: Path | None = None) -> None:
    cfg_path = ensure_under_root(path or CONFIG_PATH)
    with cfg_path.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

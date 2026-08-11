# -*- coding: utf-8 -*-
"""项目路径与目录约束：所有读写仅限 mumuvenmo 根目录内，并按类型分文件夹。"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

ROOT = Path(__file__).resolve().parent

CORE_DIR = ROOT / "core"
TOOLS_DIR = ROOT / "tools"

ASSETS_DIR = ROOT / "assets"
APK_DIR = ASSETS_DIR / "apk"
MODULES_DIR = ASSETS_DIR / "modules"
NEKOBOX_APK = APK_DIR / "NekoBox-1.4.2-x86_64.apk"
KITSUNE_APK = APK_DIR / "狐狸面具_v27.2.apk"
AURORA_APK = APK_DIR / "AuroraStore-4.8.3.apk"
VENMO_BUNDLE_DIR = APK_DIR / "venmo_bundle"
VENMO_BASE_ONLY_BROKEN = APK_DIR / "venmo_base_only_BROKEN.apk"
IH8_MODULE_ZIP = MODULES_DIR / "ih8SecureLock-v8.zip"

ACCOUNTS_DIR = ROOT / "accounts"
ACCOUNTS_INPUT_DIR = ACCOUNTS_DIR / "input"
ACCOUNTS_SAMPLES_DIR = ACCOUNTS_DIR / "samples"
PROXIES_DIR = ROOT / "proxies"
PROXY_FILE = PROXIES_DIR / "cocks5.txt"
DOCS_DIR = ROOT / "docs"

EXPORT_DIR = ROOT / "export"
EXPORT_LIVE_DIR = EXPORT_DIR / "live"
EXPORT_RESULTS_DIR = EXPORT_DIR / "results"
EXPORT_ALL_DIR = EXPORT_DIR / "all"
EXPORT_CLASSIFIED_DIR = EXPORT_DIR / "classified"

# 四类实时导出固定文件名（叠加写入，不按时间戳拆分）
EXPORT_CORRECT_NAME = "correct.txt"
EXPORT_RISK_NAME = "risk_control.txt"
EXPORT_WRONG_NAME = "wrong_password.txt"
EXPORT_NONET_NAME = "no_network.txt"

LOG_DIR = ROOT / "logs"
LOG_RUN_DIR = LOG_DIR / "run"
LOG_TEST_DIR = LOG_DIR / "test"

DATA_DIR = ROOT / "data"
DATA_SETUP_DIR = DATA_DIR / "setup_flags"
DATA_NEKO_DIR = DATA_DIR / "nekobox_profiles"
DATA_STATE_DIR = DATA_DIR / "state"

CONFIG_PATH = ROOT / "config.json"

VENMO_PACKAGE = "com.venmo"
NEKOBOX_PACKAGE = "moe.nb4a"
KITSUNE_PACKAGE = "io.github.huskydg.magisk"

DEFAULT_MUMU_ROOT = Path(r"C:\Program Files\Netease\MuMuPlayer")
DEFAULT_MUMU_MANAGER = DEFAULT_MUMU_ROOT / "nx_main" / "MuMuManager.exe"
DEFAULT_ADB = DEFAULT_MUMU_ROOT / "nx_main" / "adb.exe"


def ensure_project_dirs() -> None:
    for d in (
        CORE_DIR, TOOLS_DIR, APK_DIR, VENMO_BUNDLE_DIR, MODULES_DIR,
        ACCOUNTS_INPUT_DIR, ACCOUNTS_SAMPLES_DIR, PROXIES_DIR, DOCS_DIR,
        EXPORT_LIVE_DIR, EXPORT_RESULTS_DIR, EXPORT_ALL_DIR, EXPORT_CLASSIFIED_DIR,
        LOG_RUN_DIR, LOG_TEST_DIR, DATA_SETUP_DIR, DATA_NEKO_DIR, DATA_STATE_DIR,
    ):
        d.mkdir(parents=True, exist_ok=True)


ensure_project_dirs()


def ensure_under_root(path: Path | str) -> Path:
    p = Path(path).resolve()
    root = ROOT.resolve()
    try:
        p.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"禁止在项目目录外读写文件: {p}") from exc
    return p


def project_path(*parts: str) -> Path:
    return ensure_under_root(ROOT.joinpath(*parts))


def resolve_export_dir(path: Path | str | None = None) -> Path:
    """导出目录可自由选择（允许项目外）。源码/日志仍限制在 ROOT 内。"""
    if path is None or str(path).strip() == "":
        d = EXPORT_CLASSIFIED_DIR
    else:
        d = Path(path).expanduser()
    d = d.resolve()
    d.mkdir(parents=True, exist_ok=True)
    return d

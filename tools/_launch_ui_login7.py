# -*- coding: utf-8 -*-
from __future__ import annotations
import os, sys, subprocess, time
from pathlib import Path

ROOT = Path(r"C:\Users\zhang\Desktop\mumuvenmo")
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.dont_write_bytecode = True

from core.config_store import load_config, save_config
from core.mumu_manager import MuMuManager
from core.win_process import is_elevated

cfg = load_config()
cfg["workers"] = 7
cfg["create_count"] = 0
cfg["use_nekobox"] = True
cfg["auto_sort_windows"] = True
cfg["window_auto_fit"] = True
cfg["window_margin"] = 0
cfg["reuse_existing_vms_on_start"] = True
cfg["last_selected_vms"] = [1, 2, 3, 4, 5, 6, 7]
cfg["export_dir"] = str(ROOT / "export" / "classified")
save_config(cfg)

m = MuMuManager(cfg.get("mumu_manager"), adb_path=cfg.get("adb_path"))
for idx in [1, 2, 3, 4, 5, 6, 7]:
    before = m.read_player_name(idx)
    ok = m.ensure_index_player_name(idx, str(idx), retries=5, delay=0.25)
    after = m.read_player_name(idx)
    print(f"name idx={idx} {before!r}->{after!r} ok={ok}", flush=True)

acc = ROOT / "accounts" / "samples" / "测试登录的账号 大部分是密码错误.txt"
# Use short 8.3-safe path via accounts/input copy with ascii name for bat env
inp = ROOT / "accounts" / "input"
inp.mkdir(parents=True, exist_ok=True)
acc_ascii = inp / "sample_wrongpw.txt"
acc_ascii.write_bytes(acc.read_bytes())
print("acc_ascii", acc_ascii, "bytes", acc_ascii.stat().st_size, flush=True)

log_dir = ROOT / "logs" / "run"
log_dir.mkdir(parents=True, exist_ok=True)
bat = log_dir / "start_ui_login7.cmd"
py = sys.executable
# Write bat as UTF-8 with chcp 65001 so Chinese path works if needed; use ascii import path
lines = [
    "@echo off",
    "chcp 65001 >nul",
    f'cd /d "{ROOT}"',
    "set PYTHONDONTWRITEBYTECODE=1",
    "set PYTHONIOENCODING=utf-8",
    "set MUMUVENMO_AUTO_START=1",
    "set MUMUVENMO_WORKERS=7",
    "set MUMUVENMO_NEKOBOX=1",
    "set MUMUVENMO_VMS=1,2,3,4,5,6,7",
    "set MUMUVENMO_CREATE=0",
    "set MUMUVENMO_CREATE_LAUNCH=0",
    f'set MUMUVENMO_IMPORT={acc_ascii}',
    f'"{py}" -B "{ROOT / "main.py"}"',
]
bat.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
print("bat", bat, flush=True)
print("elevated", is_elevated(), flush=True)

# Launch unelevated via explorer association is flaky for .cmd.
# Prefer: cmd start from non-elevated? When elevated, use scheduled task or explorer.
# Simple reliable approach used before: cmd /c start "" bat
# Even if elevated, MuMuManager path force_unelevated=True.
subprocess.Popen(["cmd.exe", "/c", "start", "MuMuVenmoUI", str(bat)], cwd=str(ROOT))
print("UI launch requested", flush=True)
print("wait for main.py...", flush=True)
for i in range(20):
    time.sleep(1)
    out = subprocess.check_output(
        ["wmic", "process", "where", "name='python.exe'", "get", "ProcessId,CommandLine", "/FORMAT:LIST"],
        text=True,
        errors="ignore",
    )
    if "mumuvenmo" in out.lower() and "main.py" in out.lower():
        print("UI main.py detected", flush=True)
        break
else:
    print("UI main.py NOT detected yet", flush=True)

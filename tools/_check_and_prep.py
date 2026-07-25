from pathlib import Path
import os, sys, subprocess, time, json
from core.config_store import load_config, save_config
from core.mumu_manager import MuMuManager
from core.win_process import is_elevated

ROOT = Path(r"C:\Users\zhang\Desktop\mumuvenmo")
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

cfg = load_config()
cfg["workers"] = 7
cfg["use_nekobox"] = True
cfg["auto_sort_windows"] = True
cfg["window_auto_fit"] = True
cfg["window_margin"] = 0
cfg["reuse_existing_vms_on_start"] = True
cfg["last_selected_vms"] = [1, 2, 3, 4, 5, 6, 7]
cfg["export_dir"] = str(ROOT / "export" / "classified")
save_config(cfg)

m = MuMuManager(cfg.get("mumu_manager"), adb_path=cfg.get("adb_path"))
print("elevated", is_elevated())
print("indices", m.list_indices())
info = m.info("all") or {}
for k, v in sorted(info.items(), key=lambda x: int(x[0]) if str(x[0]).isdigit() else 999):
    if not str(k).isdigit():
        continue
    idx = int(k)
    print(
        "idx", idx,
        "name", m.read_player_name(idx),
        "api", (v or {}).get("name"),
        "proc", (v or {}).get("is_process_started"),
        "android", (v or {}).get("is_android_started"),
    )
acc = ROOT / "accounts" / "samples" / "测试登录的账号 大部分是密码错误.txt"
print("acc", acc.exists(), acc.stat().st_size if acc.exists() else 0)
print("proxy", (ROOT / "proxies" / "cocks5.txt").exists())

# kill existing mumuvenmo main.py only
out = subprocess.check_output(
    [
        "powershell", "-NoProfile", "-Command",
        "Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress",
    ],
    text=True,
    errors="ignore",
)
killed = []
try:
    data = json.loads(out) if out.strip() else []
    if isinstance(data, dict):
        data = [data]
    for item in data or []:
        cmd = item.get("CommandLine") or ""
        pid = item.get("ProcessId")
        if pid and "mumuvenmo" in cmd.replace("/", "\\").lower() and "main.py" in cmd:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            killed.append(pid)
except Exception as e:
    print("kill scan err", e)
print("killed_ui", killed)

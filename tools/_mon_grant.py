import re
import time
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(r"C:\Users\zhang\Desktop\mumuvenmo")
LOG = ROOT / "logs" / "run" / "run_20260725.log"
SHOT = ROOT / "screenshots" / "monitor"
SHOT.mkdir(parents=True, exist_ok=True)
ADB = r"C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe"

PORTS = {
    1: 16416,
    2: 16448,
    3: 16480,
    4: 16512,
    5: 16544,
    6: 16576,
    7: 16608,
}

keys = re.compile(
    r"GRANT|Superuser|popup_grant|Shell授权|SharedUID|RIGHT Switch|"
    r"NekoBox|VPN|proxy|STEP1|STEP2|登录|Incorrect|trouble|Something went wrong|"
    r"掩码|wrong_password|risk|no_network|correct|provision|Direct Install|"
    r"Uninstall Magisk|LET'S GO|排列|layout|worker",
    re.I,
)

text = LOG.read_text(encoding="utf-8", errors="replace")
lines = text.splitlines()
# only after GUI restart
after = [ln for ln in lines if ln.startswith("2026-07-25 05:34") or ln.startswith("2026-07-25 05:3")]
# better: from 05:34:00
picked = []
for ln in lines:
    if "2026-07-25 05:34" in ln[:30] or "2026-07-25 05:35" in ln[:30] or "2026-07-25 05:36" in ln[:30] or "2026-07-25 05:37" in ln[:30] or "2026-07-25 05:38" in ln[:30]:
        if keys.search(ln) and "[DEBUG]" not in ln:
            picked.append(ln)
print("=== KEY INFO after restart ===")
for ln in picked[-80:]:
    print(ln)

print("\n=== latest 15 INFO overall ===")
info = [ln for ln in lines if "[INFO]" in ln]
for ln in info[-15:]:
    print(ln)

# screenshots via adb
ts = datetime.now().strftime("%H%M%S")
for idx, port in PORTS.items():
    serial = f"127.0.0.1:{port}"
    remote = f"/sdcard/mumuvenmo_mon_{idx}.png"
    local = SHOT / f"vm{idx}_{ts}.png"
    try:
        subprocess.run([ADB, "-s", serial, "shell", "screencap", "-p", remote], capture_output=True, timeout=15)
        subprocess.run([ADB, "-s", serial, "pull", remote, str(local)], capture_output=True, timeout=15)
        print(f"shot VM{idx}: {local} exists={local.exists()} size={local.stat().st_size if local.exists() else 0}")
    except Exception as exc:
        print(f"shot VM{idx} err: {exc}")

import subprocess, time, re
from pathlib import Path
adb = r"C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe"
s = "127.0.0.1:16672"
mon = Path(r"C:\Users\zhang\Desktop\mumuvenmo\screenshots\monitor")
log = Path(r"C:\Users\zhang\Desktop\mumuvenmo\logs\run\run_20260725.log")
ts = time.strftime("%H%M%S")
p = mon / f"vm9_{ts}.png"
cp = subprocess.run([adb, "-s", s, "exec-out", "screencap", "-p"], capture_output=True, timeout=15)
p.write_bytes(cp.stdout or b"")
print("shot", p.name, len(cp.stdout or b""))
subprocess.run([adb, "-s", s, "shell", "uiautomator", "dump", "/sdcard/mumuvenmo_ui.xml"], capture_output=True, timeout=12)
x = subprocess.run([adb, "-s", s, "shell", "cat", "/sdcard/mumuvenmo_ui.xml"], capture_output=True, text=True, timeout=12).stdout or ""
(mon / f"vm9_{ts}.xml").write_text(x, encoding="utf-8")
texts = re.findall(r'text="([^"]+)"', x)
print("UI:", " | ".join([t for t in texts if t][:50]))
for ln in log.read_text(encoding="utf-8", errors="ignore").splitlines()[-100:]:
    if "[INFO]" in ln and "VM=9" in ln:
        print(ln[-250:])

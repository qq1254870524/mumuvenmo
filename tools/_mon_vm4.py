import re, subprocess
from pathlib import Path
adb=r"C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe"
s="127.0.0.1:16512"
subprocess.run([adb,"-s",s,"shell","uiautomator","dump","/sdcard/mumuvenmo_ui.xml"], capture_output=True, timeout=25)
r=subprocess.run([adb,"-s",s,"shell","cat","/sdcard/mumuvenmo_ui.xml"], capture_output=True, timeout=15)
xml=(r.stdout or b"").decode("utf-8","ignore")
texts=[t for t in re.findall(r'text="([^"]*)"', xml) if t]
print("texts", texts[:50])
print("desc", re.findall(r'content-desc="([^"]+)"', xml)[:20])
r2=subprocess.run([adb,"-s",s,"shell","dumpsys","window"], capture_output=True, timeout=15)
out=(r2.stdout or b"").decode("utf-8","ignore")
for line in out.splitlines():
    if "mCurrentFocus" in line or "mFocusedApp" in line:
        print(line.strip()[:220])
local=Path(r"C:\Users\zhang\Desktop\mumuvenmo\screenshots\monitor\vm4_c.png")
subprocess.run([adb,"-s",s,"shell","screencap","-p","/sdcard/mumuvenmo_mon.png"], capture_output=True, timeout=15)
subprocess.run([adb,"-s",s,"pull","/sdcard/mumuvenmo_mon.png", str(local)], capture_output=True, timeout=15)
print("shot", local.exists(), local.stat().st_size if local.exists() else 0)
r3=subprocess.run([adb,"-s",s,"shell","cat","/proc/net/dev"], capture_output=True, timeout=10)
print("tun", b"tun0" in (r3.stdout or b""))
lines=Path(r"C:\Users\zhang\Desktop\mumuvenmo\logs\run\run_20260725.log").read_text(encoding="utf-8",errors="ignore").splitlines()[-120:]
print("=== log tail info ===")
for l in lines:
    if " [INFO] " in l:
        print(l[11:210])

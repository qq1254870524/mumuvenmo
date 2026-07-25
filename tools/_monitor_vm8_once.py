import subprocess, time, re
from pathlib import Path
adb = r"C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe"
s = "127.0.0.1:16640"
mon = Path(r"C:\Users\zhang\Desktop\mumuvenmo\screenshots\monitor")
mon.mkdir(parents=True, exist_ok=True)

def run(*args, timeout=30):
    cp = subprocess.run([adb, "-s", s, *args], capture_output=True, timeout=timeout)
    return cp.stdout

ts = time.strftime("%H%M%S")
shot = mon / f"vm8_{ts}.png"
shot.write_bytes(run("exec-out", "screencap", "-p"))
print("desktop", shot, shot.stat().st_size)
subprocess.run([adb, "-s", s, "shell", "monkey", "-p", "io.github.huskydg.magisk", "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True, timeout=20)
time.sleep(3)
ts2 = time.strftime("%H%M%S")
shot2 = mon / f"vm8_kitsune_{ts2}.png"
shot2.write_bytes(run("exec-out", "screencap", "-p"))
print("kitsune", shot2, shot2.stat().st_size)
subprocess.run([adb, "-s", s, "shell", "uiautomator", "dump", "/sdcard/mumuvenmo_ui.xml"], capture_output=True, timeout=20)
xml = run("shell", "cat", "/sdcard/mumuvenmo_ui.xml").decode("utf-8", "ignore")
(mon / f"vm8_kitsune_{ts2}.xml").write_text(xml, encoding="utf-8")
texts = re.findall(r'text="([^"]+)"', xml)
print("TEXTS:", " | ".join([x for x in texts if x][:70]))
mods = subprocess.run([adb, "-s", s, "shell", "su", "-c", "ls /data/adb/modules"], capture_output=True, text=True, timeout=15)
print("modules:", (mods.stdout or mods.stderr or "").strip())

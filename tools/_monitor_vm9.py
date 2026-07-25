import subprocess, time, re
from pathlib import Path
adb = r"C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe"
s = "127.0.0.1:16672"
mon = Path(r"C:\Users\zhang\Desktop\mumuvenmo\screenshots\monitor")
log = Path(r"C:\Users\zhang\Desktop\mumuvenmo\logs\run\run_20260725.log")
mon.mkdir(parents=True, exist_ok=True)

def shot(tag=""):
    ts = time.strftime("%H%M%S")
    p = mon / f"vm9_{tag}{ts}.png"
    try:
        cp = subprocess.run([adb, "-s", s, "exec-out", "screencap", "-p"], capture_output=True, timeout=20)
        if cp.stdout:
            p.write_bytes(cp.stdout)
            print("SHOT", p.name, len(cp.stdout))
            return p
    except Exception as e:
        print("SHOT_ERR", e)
    return None

def dump_texts():
    try:
        subprocess.run([adb, "-s", s, "shell", "uiautomator", "dump", "/sdcard/mumuvenmo_ui.xml"], capture_output=True, timeout=15)
        cp = subprocess.run([adb, "-s", s, "shell", "cat", "/sdcard/mumuvenmo_ui.xml"], capture_output=True, text=True, timeout=15)
        t = cp.stdout or ""
        texts = re.findall(r'text="([^"]+)"', t)
        print("UI:", " | ".join([x for x in texts if x][:50]))
        return t, texts
    except Exception as e:
        print("DUMP_ERR", e)
        return "", []

def info_tail():
    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    for ln in lines[-30:]:
        if "[INFO]" in ln and ("VM=9" in ln or "STEP" in ln or "GRANT" in ln or "settings" in ln or "ih8" in ln or "provision" in ln or "Direct" in ln or "Install" in ln or "Hide" in ln):
            print(ln[-220:])

print("=== T0 ===")
shot("t0_")
dump_texts()
info_tail()
time.sleep(8)
print("=== T1 ===")
shot("t1_")
dump_texts()
info_tail()
time.sleep(8)
print("=== T2 ===")
shot("t2_")
dump_texts()
info_tail()

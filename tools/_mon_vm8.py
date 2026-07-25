import re, subprocess
from pathlib import Path
adb = r"C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe"
serial = "127.0.0.1:16640"
r = subprocess.run([adb, "-s", serial, "shell", "cat", "/sdcard/mumuvenmo_ui.xml"], capture_output=True, text=True, encoding="utf-8", errors="ignore")
xml = r.stdout or ""
print("ui_len", len(xml))
texts = re.findall(r'text="([^"]+)"', xml)
descs = re.findall(r'content-desc="([^"]+)"', xml)
print("TEXTS:", " | ".join(texts[:50]))
print("DESCS:", " | ".join(descs[:30]))
for k in ["Install", "Hide", "Uninstall", "Direct", "GRANT", "Allow", "Remember", "Zygisk", "Modules", "Settings", "LET"]:
    print(k, k.lower() in xml.lower())
p = Path(r"C:\Users\zhang\Desktop\mumuvenmo\logs\run\run_20260725.log")
lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
print("log_size", p.stat().st_size, "lines", len(lines))
want = [ln for ln in lines[-250:] if any(x in ln for x in ["[INFO]", "[ERROR]", "[WARNING]"]) and "MuMu cmd" not in ln and "stdout:" not in ln]
for ln in want[-60:]:
    print(ln)

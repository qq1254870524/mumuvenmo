from pathlib import Path
import time
p = Path(r"C:\Users\zhang\Desktop\mumuvenmo\logs\run\run_20260725.log")
last_size = 0
for i in range(4):
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    size = p.stat().st_size
    print(f"\n=== poll {i} size={size} lines={len(lines)} ===")
    want = []
    for ln in lines[-400:]:
        if any(x in ln for x in ["[INFO]", "[ERROR]", "[WARNING]"]) and "MuMu cmd" not in ln and "stdout:" not in ln:
            want.append(ln)
    for ln in want[-60:]:
        print(ln)
    time.sleep(8)

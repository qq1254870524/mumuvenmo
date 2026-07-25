from pathlib import Path
p = Path(r"C:\Users\zhang\Desktop\mumuvenmo\logs\run\run_20260725.log")
lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
print("lines", len(lines), "size", p.stat().st_size)
want = []
for ln in lines[-800:]:
    if "[INFO]" in ln or "[ERROR]" in ln or "[WARNING]" in ln:
        if "MuMu cmd" in ln or "stdout:" in ln:
            continue
        want.append(ln)
for ln in want[-120:]:
    print(ln)

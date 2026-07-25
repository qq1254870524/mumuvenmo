from pathlib import Path
import time
p = Path(r"C:\Users\zhang\Desktop\mumuvenmo\logs\run\run_20260725.log")
time.sleep(10)
lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
print("size", p.stat().st_size, "lines", len(lines))
keys = (
    "INFO", "ERROR", "WARNING", "Kitsune", "GRANT", "Install", "Direct",
    "NekoBox", "VPN", "VM=", "login", "Uninstall", "Hide", "ih8", "Zygisk",
    "fail", "Incorrect", "trouble", "Something", "worker", "线程", "启动",
    "代理", "SOCKS", "排列", "stop", "restart", "Magisk", "Shell", "Remember",
    "Allow", "Modules", "LET", "provision", "创建", "新建",
)
for ln in lines[-300:]:
    s = ln.strip()
    if not s or s.startswith("{") or s.startswith('"') or "stdout:" in ln or "MuMu cmd" in ln:
        continue
    if any(k in ln for k in keys):
        print(ln)

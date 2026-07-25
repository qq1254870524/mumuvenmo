from pathlib import Path
import time
p = Path(r"C:\Users\zhang\Desktop\mumuvenmo\logs\run\run_20260725.log")
prev = p.stat().st_size
time.sleep(15)
text = p.read_text(encoding="utf-8", errors="ignore")
lines = text.splitlines()
print("size", p.stat().st_size, "delta", p.stat().st_size - prev, "lines", len(lines))
keys = (
    "INFO", "ERROR", "WARNING", "Kitsune", "GRANT", "Install", "Direct",
    "NekoBox", "VPN", "VM=", "login", "Uninstall", "Hide", "ih8", "Zygisk",
    "fail", "Incorrect", "trouble", "Something", "worker", "启动",
    "代理", "SOCKS", "Magisk", "Shell", "Modules", "LET", "provision",
    "新建", "账号", "导出", "tun", "Connect", "profile", "排列", "step",
    "STEP", "venmo", "Venmo", "clear", "refresh", "刷新",
)
# print last 80 matching from last 500 lines
hit = []
for ln in lines[-500:]:
    s = ln.strip()
    if not s or s.startswith("{") or s.startswith('"') or "stdout:" in ln or "MuMu cmd" in ln or "DEBUG" in ln and "MuMu" in ln:
        continue
    if any(k in ln for k in keys):
        hit.append(ln)
for ln in hit[-100:]:
    print(ln)

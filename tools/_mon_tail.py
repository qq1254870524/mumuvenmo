from pathlib import Path
import re
LOG = Path(r"C:\Users\zhang\Desktop\mumuvenmo\logs\run\run_20260725.log")
lines = LOG.read_text(encoding="utf-8", errors="replace").splitlines()
pat = re.compile(r"^2026-07-25 05:(3[4-9]|[4-5]\d)")
info = []
for ln in lines:
    if not pat.match(ln):
        continue
    if "[INFO]" in ln or "[WARNING]" in ln or "[ERROR]" in ln:
        info.append(ln)
print(f"info_count_after_restart={len(info)} total_lines={len(lines)}")
for ln in info[-70:]:
    print(ln)
grant = [ln for ln in info if re.search(r"GRANT|Superuser|popup_grant|RIGHT Switch|SharedUID|Shell", ln, re.I)]
print("\n=== GRANT related ===")
for ln in grant[-40:]:
    print(ln)
res = [ln for ln in info if re.search(r"Incorrect|trouble|Something went wrong|导出|wrong_password|risk|no_network|登录|Venmo|proxy|VPN|tun0|profile", ln, re.I)]
print("\n=== login/proxy related ===")
for ln in res[-50:]:
    print(ln)

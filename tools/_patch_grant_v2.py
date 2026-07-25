from pathlib import Path
ROOT = Path(r"C:\Users\zhang\Desktop\mumuvenmo")
p = ROOT / "core" / "root_setup.py"
src = p.read_text(encoding="utf-8")
old_header = (
    "# 2026-07-25 shell-grant-popup-first-v1: "
    "Shell授权优先点GRANT弹窗(Remember forever+Allow)，Superuser开关仅兜底"
)
new_header = (
    "# 2026-07-25 shell-grant-popup-first-v2: "
    "全路径GRANT弹窗优先(Remember forever+Allow/Grant)；"
    "Superuser右侧开关仅失败兜底；configure_flags/provision不再直进Superuser"
)
if old_header in src:
    src = src.replace(old_header, new_header, 1)
    print("header: v1->v2")
elif "shell-grant-popup-first-v2" not in src:
    src = new_header + "\n" + src
    print("header: prepended")
else:
    print("header: already v2")
p.write_text(src, encoding="utf-8")
print("size", len(src))

from pathlib import Path
p = Path(r"C:\Users\zhang\Desktop\mumuvenmo\core\root_setup.py")
t = p.read_text(encoding="utf-8")
o = "            desktop_streak = 0\n            soft_pull_count = 0"
n = "            desktop_streak = 0\n            no_magisk_streak = 0\n            soft_pull_count = 0"
if o not in t:
    raise SystemExit("a missing")
t = t.replace(o, n, 1)
o2 = (
    "                if on_desktop:\n"
    "                    saw_desktop = True\n"
    "                    desktop_streak += 1\n"
    "                else:\n"
    "                    desktop_streak = 0\n"
    "\n"
    "                # \u6389\u684c\u9762/\u7a7a dump\uff1a\u6570\u79d2\u5185\u8f6f\u62c9\u56de\u518d\u70b9 Install\uff0c\u907f\u514d\u7a7a\u7b49\u6ee1 attempts\n"
    "                need_soft_pull = (\n"
    "                    (on_desktop and desktop_streak >= 1)\n"
    "                    or empty_streak >= 2\n"
    "                )"
)
n2 = (
    "                if on_desktop:\n"
    "                    saw_desktop = True\n"
    "                    desktop_streak += 1\n"
    "                else:\n"
    "                    desktop_streak = 0\n"
    "\n"
    "                if has_magisk_markers:\n"
    "                    no_magisk_streak = 0\n"
    "                else:\n"
    "                    no_magisk_streak += 1\n"
    "\n"
    "                # desktop/empty/no-magisk UI soft pull\n"
    "                need_soft_pull = (\n"
    "                    (on_desktop and desktop_streak >= 1)\n"
    "                    or empty_streak >= 2\n"
    "                    or no_magisk_streak >= 2\n"
    "                )"
)
if o2 not in t:
    raise SystemExit("c missing")
t = t.replace(o2, n2, 1)
o3 = 'f"empty_streak={empty_streak} soft_pull={soft_pull_count}",'
n3 = 'f"empty_streak={empty_streak} no_magisk_streak={no_magisk_streak} soft_pull={soft_pull_count}",'
if o3 not in t:
    raise SystemExit("e missing")
t = t.replace(o3, n3, 1)
p.write_text(t, encoding="utf-8", newline="\n")
print("OK2")

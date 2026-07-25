from pathlib import Path
import py_compile
p = Path("core/root_setup.py")
t = p.read_text(encoding="utf-8")
marker = "desktop-no-blind-tap-v1: desktop/not-foreground"
i = t.find(marker)
assert i > 0, marker
old = (
"except Exception:\n"
"                    top_kitsune = False\n"
"                if on_desktop or not top_kitsune:"
)
new = (
"except Exception:\n"
"                    top_kitsune = False\n"
"                has_magisk_ui = (\n"
'                    "io.github.huskydg.magisk:id/" in low\n'
'                    or "ramdisk" in low\n'
'                    or "home_magisk_button" in low\n'
'                    or "uninstall magisk" in low\n'
'                    or bool(__import__("re").search(r\'text="Install"\', xml or ""))\n'
'                    or "modify /system directly" in low\n'
'                    or "method_direct" in low\n'
"                )\n"
"                if on_desktop or (not top_kitsune and not has_magisk_ui):"
)
head, tail = t[:i], t[i:]
assert old in tail, "old missing"
tail = tail.replace(old, new, 1)
oldlog = "(desktop={on_desktop} top={top_kitsune})"
newlog = "(desktop={on_desktop} top={top_kitsune} magisk_ui={has_magisk_ui})"
assert oldlog in tail
tail = tail.replace(oldlog, newlog, 1)
t2 = head + tail
t2 = t2.replace(
    "desktop-no-blind-tap-v1: drop-to-desktop",
    "desktop-no-blind-tap-v1b: drop-to-desktop",
    1,
)
p.write_text(t2, encoding="utf-8")
py_compile.compile(str(p), doraise=True)
print("PATCHED_OK", t2.count("has_magisk_ui"))
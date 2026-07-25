# -*- coding: utf-8 -*-
from __future__ import annotations
import re
import subprocess
import time
from pathlib import Path

ADB = r"C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe"
LOG = Path(r"C:\Users\zhang\Desktop\mumuvenmo\logs\run\run_20260725.log")
OUT = Path(r"C:\Users\zhang\Desktop\mumuvenmo\screenshots\monitor")
EXP = Path(r"C:\Users\zhang\Desktop\mumuvenmo\export\classified")
PORTS = {i: 16384 + i * 32 for i in range(1, 8)}
OUT.mkdir(parents=True, exist_ok=True)

lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
info = [l for l in lines[-4000:] if " [INFO] " in l]
print("=== key events recent ===")
keys = (
    "wrong_password",
    "risk_control",
    "no_network",
    "Incorrect",
    "trouble",
    "Something went",
    "masked",
    "换绑",
    "刷IP",
    "fallback",
    "first_submit",
    "Modules",
    "Uninstall",
    "不通",
    "proxy",
    "tun",
    "结果",
)
seen = set()
for l in info:
    if any(k in l for k in keys):
        s = l[11:230]
        if s not in seen:
            seen.add(s)
            print(s)

print("=== per VM latest info ===")
for vm in range(1, 8):
    vl = [l for l in info if f"VM-{vm} " in l]
    print(f"-- VM{vm} n={len(vl)}")
    for l in vl[-4:]:
        print(l.split(" [INFO] ", 1)[-1][:170])

print("=== device state ===")
for i, port in PORTS.items():
    serial = f"127.0.0.1:{port}"
    subprocess.run([ADB, "connect", serial], capture_output=True, text=True)
    r3 = subprocess.run(
        [ADB, "-s", serial, "shell", "cat", "/proc/net/dev"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    tun = "tun0" in (r3.stdout or "")
    subprocess.run(
        [ADB, "-s", serial, "shell", "uiautomator", "dump", "/sdcard/mumuvenmo_ui.xml"],
        capture_output=True,
        timeout=25,
    )
    r = subprocess.run(
        [ADB, "-s", serial, "shell", "cat", "/sdcard/mumuvenmo_ui.xml"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    xml = r.stdout or ""
    texts = re.findall(r'text="([^"]{2,90})"', xml)
    keep = []
    for t in texts:
        tl = t.lower()
        if any(
            k in tl
            for k in [
                "venmo",
                "log in",
                "password",
                "incorrect",
                "trouble",
                "something went",
                "email",
                "forgot",
                "nekobox",
                "socks",
                "error",
                "verify",
                "phone",
                "code",
                "allow",
                "grant",
                "install",
                "create account",
            ]
        ):
            if t not in keep:
                keep.append(t)
    local = OUT / f"vm{i}_now.png"
    subprocess.run(
        [ADB, "-s", serial, "shell", "screencap", "-p", "/sdcard/mumuvenmo_mon.png"],
        capture_output=True,
        timeout=15,
    )
    subprocess.run(
        [ADB, "-s", serial, "pull", "/sdcard/mumuvenmo_mon.png", str(local)],
        capture_output=True,
        timeout=15,
    )
    print(f"VM{i} tun={tun} texts={keep[:10]} shot={local.exists()}")

print("=== export ===")
if EXP.exists():
    for f in sorted(EXP.glob("*.txt")):
        n = sum(1 for _ in f.open(encoding="utf-8", errors="ignore"))
        print(f.name, n)

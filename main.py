# -*- coding: utf-8 -*-
"""入口：MuMu Venmo 登录器。所有产物仅限本目录。"""
from __future__ import annotations

# 2026-07-31 single-instance-v1: 禁止双开 main.py 抢 ADB/MuMu（旧僵尸会打挂装包）

import atexit
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.dont_write_bytecode = True


def _acquire_single_instance() -> None:
    """同目录只允许一个 main.py。已有实例则提示并退出。"""
    import ctypes
    from ctypes import wintypes

    lock_path = ROOT / "data" / "state" / "mumuvenmo_single_instance.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    # 用 Windows 互斥量，进程崩溃也会自动释放
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.GetLastError.restype = wintypes.DWORD
    name = r"Local\MuMuVenmoSingleInstance_v1"
    handle = kernel32.CreateMutexW(None, False, name)
    ERROR_ALREADY_EXISTS = 183
    if not handle:
        return
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        try:
            # 再写 lock 方便排查
            lock_path.write_text(
                f"blocked_at={time.strftime('%Y-%m-%d %H:%M:%S')} pid={os.getpid()}\n",
                encoding="utf-8",
            )
        except Exception:
            pass
        try:
            ctypes.windll.user32.MessageBoxW(
                0,
                "MuMu Venmo 登录器已经在运行。\n\n请不要双开，否则会抢 ADB 导致装包/门禁卡死。\n请先关掉旧窗口再启动。",
                "已有实例在运行",
                0x00000030,
            )
        except Exception:
            print("MuMu Venmo 登录器已经在运行，禁止双开。", flush=True)
        sys.exit(2)
    try:
        lock_path.write_text(
            f"pid={os.getpid()}\nstarted={time.strftime('%Y-%m-%d %H:%M:%S')}\n",
            encoding="utf-8",
        )
    except Exception:
        pass

    def _cleanup() -> None:
        try:
            if handle:
                kernel32.CloseHandle(handle)
        except Exception:
            pass
        try:
            if lock_path.exists():
                txt = lock_path.read_text(encoding="utf-8")
                if f"pid={os.getpid()}" in txt:
                    lock_path.unlink(missing_ok=True)
        except Exception:
            pass

    atexit.register(_cleanup)


_acquire_single_instance()

from app_ui import main

if __name__ == "__main__":
    main()

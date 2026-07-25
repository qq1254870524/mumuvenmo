# 2026-07-25 tree-kill-v1: MuMuManager 超时杀进程树，避免主界面卡死
# -*- coding: utf-8 -*-
"""Windows 进程启动辅助：管理员环境下以降权(Medium IL)运行子进程。

MuMu/Hyper-V 在管理员权限下 launch 会报:
VERR_NEED_NO_ADMIN_ERROR / unable to start with administrator privileges.
本模块在父进程 elevated 时，用 explorer shell token + CreateProcessWithTokenW 降权执行。
"""
from __future__ import annotations

import ctypes
import logging
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path
from typing import Sequence

logger = logging.getLogger("mumuvenmo")

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)
shell32 = ctypes.WinDLL("shell32", use_last_error=True)


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(wintypes.BYTE)),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]


def is_elevated() -> bool:
    try:
        return bool(shell32.IsUserAnAdmin())
    except Exception:
        return False


def _state_dir() -> Path:
    try:
        from paths import DATA_STATE_DIR

        p = Path(DATA_STATE_DIR)
    except Exception:
        p = Path(__file__).resolve().parents[1] / "data" / "state"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _get_shell_token() -> wintypes.HANDLE:
    hwnd = user32.GetShellWindow()
    if not hwnd:
        # fallback: find explorer.exe
        raise OSError("GetShellWindow 失败：explorer 可能未运行")
    pid = wintypes.DWORD(0)
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        raise OSError("无法取得 explorer PID")

    PROCESS_QUERY_INFORMATION = 0x0400
    h_proc = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid.value)
    if not h_proc:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        TOKEN_DUPLICATE = 0x0002
        h_token = wintypes.HANDLE()
        if not advapi32.OpenProcessToken(h_proc, TOKEN_DUPLICATE, ctypes.byref(h_token)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            TOKEN_ASSIGN_PRIMARY = 0x0001
            TOKEN_QUERY = 0x0008
            TOKEN_ADJUST_DEFAULT = 0x0080
            TOKEN_ADJUST_SESSIONID = 0x0100
            access = (
                TOKEN_ASSIGN_PRIMARY
                | TOKEN_DUPLICATE
                | TOKEN_QUERY
                | TOKEN_ADJUST_DEFAULT
                | TOKEN_ADJUST_SESSIONID
            )
            SecurityImpersonation = 2
            TokenPrimary = 1
            h_new = wintypes.HANDLE()
            if not advapi32.DuplicateTokenEx(
                h_token,
                access,
                None,
                SecurityImpersonation,
                TokenPrimary,
                ctypes.byref(h_new),
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            return h_new
        finally:
            kernel32.CloseHandle(h_token)
    finally:
        kernel32.CloseHandle(h_proc)


def _run_with_token(
    args: Sequence[str],
    timeout: int,
    cwd: str | None,
) -> subprocess.CompletedProcess:
    state = _state_dir()
    stamp = f"{os.getpid()}_{time.time_ns()}"
    out_path = state / f"proc_{stamp}.out"
    err_path = state / f"proc_{stamp}.err"
    bat_path = state / f"proc_{stamp}.cmd"
    cmdline = subprocess.list2cmdline(list(args))
    # 用 cmd 批处理收集 stdout/stderr 与 exit code
    bat_path.write_text(
        f'@echo off\r\n{cmdline} >"{out_path}" 2>"{err_path}"\r\nexit /b %ERRORLEVEL%\r\n',
        encoding="utf-8",
    )
    h_token = _get_shell_token()
    try:
        si = STARTUPINFOW()
        si.cb = ctypes.sizeof(STARTUPINFOW)
        si.dwFlags = 0x00000001  # STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        pi = PROCESS_INFORMATION()
        CREATE_NO_WINDOW = 0x08000000
        CREATE_UNICODE_ENVIRONMENT = 0x00000400
        # LOGON_WITH_PROFILE often helps GUI subsystems; MuMu may need env
        LOGON_WITH_PROFILE = 0x00000001
        cmd_buf = ctypes.create_unicode_buffer(f'cmd.exe /c "{bat_path}"')
        cwd_buf = ctypes.create_unicode_buffer(cwd) if cwd else None
        ok = advapi32.CreateProcessWithTokenW(
            h_token,
            LOGON_WITH_PROFILE,
            None,
            cmd_buf,
            CREATE_NO_WINDOW | CREATE_UNICODE_ENVIRONMENT,
            None,
            cwd_buf,
            ctypes.byref(si),
            ctypes.byref(pi),
        )
        if not ok:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            WAIT_TIMEOUT = 0x00000102
            wait_ms = int(max(1, timeout) * 1000)
            wr = kernel32.WaitForSingleObject(pi.hProcess, wait_ms)
            if wr == WAIT_TIMEOUT:
                try:
                    kill_process_tree(int(pi.dwProcessId))
                except Exception:
                    pass
                try:
                    kernel32.TerminateProcess(pi.hProcess, 1)
                except Exception:
                    pass
                raise TimeoutError(f"降权进程超时 {timeout}s: {cmdline}")
            code = wintypes.DWORD(0)
            kernel32.GetExitCodeProcess(pi.hProcess, ctypes.byref(code))
            stdout = ""
            stderr = ""
            try:
                if out_path.exists():
                    stdout = out_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
            try:
                if err_path.exists():
                    stderr = err_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
            return subprocess.CompletedProcess(list(args), int(code.value), stdout, stderr)
        finally:
            kernel32.CloseHandle(pi.hThread)
            kernel32.CloseHandle(pi.hProcess)
    finally:
        kernel32.CloseHandle(h_token)
        for p in (out_path, err_path, bat_path):
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass



def kill_process_tree(pid: int) -> None:
    """超时后尽量杀掉整棵进程树，避免 MuMuManager 残留把主界面卡死。"""
    if not pid:
        return
    try:
        subprocess.run(
            ["taskkill", "/PID", str(int(pid)), "/T", "/F"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        try:
            kernel32.TerminateProcess(int(pid), 1)
        except Exception:
            pass


def run_process(
    args: Sequence[str],
    timeout: int = 120,
    cwd: str | None = None,
    *,
    force_unelevated: bool = True,
) -> subprocess.CompletedProcess:
    """运行子进程；默认在 elevated 时自动降权。"""
    arg_list = [str(a) for a in args]
    cf = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if sys.platform != "win32" or not force_unelevated or not is_elevated():
        try:
            proc = subprocess.Popen(
                arg_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=cwd,
                creationflags=cf,
            )
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                kill_process_tree(proc.pid)
                try:
                    stdout, stderr = proc.communicate(timeout=5)
                except Exception:
                    stdout, stderr = "", ""
                raise TimeoutError(f"进程超时 {timeout}s: {subprocess.list2cmdline(arg_list)}")
            return subprocess.CompletedProcess(arg_list, int(proc.returncode or 0), stdout, stderr)
        except TimeoutError:
            raise
        except Exception:
            # 兜底
            return subprocess.run(
                arg_list,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                cwd=cwd,
                creationflags=cf,
            )
    try:
        logger.debug("elevated -> unelevated run: %s", subprocess.list2cmdline(arg_list))
        return _run_with_token(arg_list, timeout=timeout, cwd=cwd)
    except Exception as exc:
        logger.warning("降权启动失败，回退同权限执行: %s", exc)
        return subprocess.run(
            arg_list,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            cwd=cwd,
            creationflags=cf,
        )

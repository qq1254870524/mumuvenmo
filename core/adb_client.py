# 2026-07-31 install-heal-fast-v3: pure TIMEOUT/package-dead 不再空重试，立刻返回促 MuMu heal
# 2026-07-31 instant-stop-v2: cancel 轮询保持可重入
# 2026-07-31 package-installed-hangfix-v4: pm 连续超时快速失败+service check；install 首超 120s 促 heal
# 2026-07-31 package-service-heal-v1: install/pm 遇 package 服务挂掉则重连再试
# 2026-07-31 taskkill-tree-v1: 超时/取消用 taskkill /T 杀 adb 进程树，防僵尸堵串口
# 2026-07-31 pipe-deadlock-fix-v1: communicate线程读PIPE，避免cat ui.xml互锁超时
# 2026-07-31 zombie-cancel-v2: stacked cancel checks + wait_device cancel
# -*- coding: utf-8 -*-
# 2026-07-25 grant-no-deny-v1: Magisk GRANT 只点 id/grant 或精确 GRANT 文本，禁用 deny_right，空树区分 Magisk/MuMu
# 2026-07-25 shell-su-quote-v1: su -c 整段命令单参数，修复 magisk --install-module 被 su 拆参
# 2026-07-25 shareduid-grant-fastpath-v2: Magisk SharedUID GRANT immediate click
# 2026-07-25 shareduid-grant-click-v1: Magisk [SharedUID] Shell 弹窗直接点 GRANT（不再被 forever_missing 卡住）
# 2026-07-24 no-uninstall-tap-v1: tap_text/find_node 支持 exact；禁止点 Uninstall Magisk
"""ADB 客户端：通过 adb.exe -s host:port 操作模拟器。\n\n更新 2026-07-24 step3: 修复 shell_script/shell_su_script 引号，保证管道与 su 脚本可用。\n更新 2026-07-24 fix-white: release_ui_control 释放 uiautomator，防人工点白屏。
更新 2026-07-24 su-grant: Magisk [SharedUID] Shell 授权弹窗自动点同意；su 并行 dismiss。 GRANT-first v2: 空SuRequest坐标点Grant；Forever不当成功。
更新 2026-07-24 portrait-lock: 关闭自动旋转并锁定竖屏，防止 NekoBox/传感器导致横竖屏狂切。
更新 2026-07-25 shareduid-grant-click-v1: Magisk SuRequest 见 GRANT/[SharedUID] Shell 时直接点 GRANT。"""
from __future__ import annotations

# 2026-07-31 concurrent-adb-v2: 单实例后 global=10 heavy=6，10台可同步装包
# 2026-07-31 package-installed-v3: 缩短 pm path 超时+连续软失败重连；配合 taskkill-tree
# 2026-07-31 package-installed-v2: pm path 软失败多试 + pm list packages 兜底，防 Success 后假缺失
# 2026-07-31 concurrent-adb-v1: 10路并行 force-stop/pm 超时软失败; 全局限流; su-grant 降频
# 2026-07-31 install-timeout-retry-v1: install TIMEOUT/offline 重连再试；package_installed 严格匹配
# 2026-07-31 heavy-install-v1: install/push 全局限3; 可中断Popen; package_installed加固
# 2026-07-31 zombie-cancel-v1+adb-pressure: global=6 heavy=4; interruptible acquire; offline retry
# 2026-07-31 immediate-stop-v1: request_cancel_all/interrupt_all 杀活动adb

import logging
import os
import threading
import re
import subprocess
import time
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

logger = logging.getLogger("mumuvenmo")


class AdbClient:
    def __init__(self, adb_path: str | Path, serial: str):
        self.adb = Path(adb_path)
        self.serial = serial
        if not self.adb.exists():
            raise FileNotFoundError(f"adb 不存在: {self.adb}")
        self._last_dump_xml = ""
        self._last_dump_ts = 0.0
        self._dump_min_interval = 2.0


    # 同类串口互斥，避免同 VM 主线程 + su-grant 双路 uiautomator 互抢
    _serial_locks: dict[str, "threading.RLock"] = {}
    _serial_locks_guard = threading.Lock()
    # 全局 ADB 并发：单实例下 10 台可并行；12 易 thrash
    _global_adb_sema = threading.Semaphore(10)
    # 重操作(install/push) 全局限流：6 路同步装包
    _heavy_adb_sema = threading.Semaphore(6)
    _cancel_all = threading.Event()
    _active_procs_guard = threading.Lock()
    _active_procs = {}
    _instance_cancel_checks_guard = threading.Lock()
    _instance_cancel_checks = {}

    @classmethod
    def request_cancel_all(cls):
        cls._cancel_all.set()
        cls.interrupt_all()

    @classmethod
    def clear_cancel_all(cls):
        cls._cancel_all.clear()

    @classmethod
    def interrupt_all(cls):
        killed = 0
        with cls._active_procs_guard:
            items = list(cls._active_procs.items())
        for pid, proc in items:
            try:
                if cls._kill_proc_tree(proc):
                    killed += 1
            except Exception:
                pass
        if killed:
            logger.warning("ADB interrupt_all killed=%s", killed)
        return killed


    @staticmethod
    def _kill_proc_tree(proc) -> bool:
        """Windows 上 adb 常有子进程；只 kill 父进程会留僵尸占串口。"""
        if proc is None:
            return False
        pid = getattr(proc, "pid", None)
        if not pid:
            return False
        killed = False
        try:
            if proc.poll() is None:
                # 先 taskkill 整树（含子进程）
                if os.name == "nt":
                    try:
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(pid)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=5,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                        )
                        killed = True
                    except Exception:
                        pass
                try:
                    if proc.poll() is None:
                        proc.kill()
                        killed = True
                except Exception:
                    pass
                try:
                    proc.wait(timeout=1.5)
                except Exception:
                    pass
        except Exception:
            pass
        return killed


    @classmethod
    def _register_proc(cls, proc):
        try:
            with cls._active_procs_guard:
                cls._active_procs[int(proc.pid)] = proc
        except Exception:
            pass

    @classmethod
    def _unregister_proc(cls, proc):
        if proc is None:
            return
        try:
            with cls._active_procs_guard:
                cls._active_procs.pop(int(proc.pid), None)
        except Exception:
            pass

    def set_cancel_check(self, fn):
        # stacked cancel: 多线程可叠加；任一 True 即取消（避免新任务覆盖旧检查导致僵尸复活）
        try:
            with self._instance_cancel_checks_guard:
                if fn is None:
                    self._instance_cancel_checks.pop(self.serial, None)
                else:
                    cur = self._instance_cancel_checks.get(self.serial)
                    if cur is None:
                        self._instance_cancel_checks[self.serial] = [fn]
                    elif isinstance(cur, list):
                        if fn not in cur:
                            cur.append(fn)
                    else:
                        self._instance_cancel_checks[self.serial] = [cur, fn] if cur is not fn else [cur]
        except Exception:
            pass

    def _cancel_requested(self):
        if self._cancel_all.is_set():
            return True
        try:
            with self._instance_cancel_checks_guard:
                cur = self._instance_cancel_checks.get(self.serial)
            if cur is None:
                return False
            fns = cur if isinstance(cur, list) else [cur]
            for fn in list(fns):
                try:
                    if callable(fn) and bool(fn()):
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def _is_heavy_args(self, args):
        if not args:
            return False
        head = str(args[0]).lower()
        return head in ("install", "install-multiple", "push")

    def _acquire_interruptible(self, sema, timeout: float) -> bool:
        """停止任务时可打断的信号量等待。"""
        deadline = time.time() + max(0.2, float(timeout))
        while True:
            if self._cancel_requested():
                return False
            if sema.acquire(timeout=0.2):
                return True
            if time.time() >= deadline:
                return False

    @classmethod
    def _lock_for(cls, serial: str):
        with cls._serial_locks_guard:
            lk = cls._serial_locks.get(serial)
            if lk is None:
                lk = threading.RLock()
                cls._serial_locks[serial] = lk
            return lk

    def _run(self, args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
        cmd = [str(self.adb), "-s", self.serial, *args]
        logger.debug("ADB: %s", " ".join(cmd))
        if self._cancel_requested():
            return subprocess.CompletedProcess(cmd, 130, "", "adb_cancelled")
        flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        heavy = self._is_heavy_args(args)
        heavy_got = False
        heavy_waited = 0.0
        if heavy:
            t0 = time.time()
            heavy_got = self._acquire_interruptible(self._heavy_adb_sema, max(30, int(timeout) + 30))
            heavy_waited = time.time() - t0
            if not heavy_got:
                if self._cancel_requested():
                    return subprocess.CompletedProcess(cmd, 130, "", "adb_cancelled")
                logger.warning("ADB heavy sema wait timeout waited=%.1fs: %s", heavy_waited, " ".join(cmd)[:180])
                return subprocess.CompletedProcess(cmd, 124, "", "adb_heavy_sema_timeout")
            logger.info(
                "ADB heavy begin serial=%s waited=%.1fs cmd=%s",
                self.serial, heavy_waited, " ".join(cmd)[:160],
            )
        got = self._acquire_interruptible(self._global_adb_sema, max(5, int(timeout) + 5))
        if not got:
            if heavy and heavy_got:
                try:
                    self._heavy_adb_sema.release()
                except Exception:
                    pass
            if self._cancel_requested():
                return subprocess.CompletedProcess(cmd, 130, "", "adb_cancelled")
            logger.warning("ADB sema wait timeout: %s", " ".join(cmd)[:180])
            return subprocess.CompletedProcess(cmd, 124, "", "adb_sema_timeout")
        proc = None
        t_run = time.time()
        try:
            if self._cancel_requested():
                return subprocess.CompletedProcess(cmd, 130, "", "adb_cancelled")
            # pipe-deadlock-fix-v1:
            # 大输出(cat ui.xml / dumpsys)若只用 poll 不读 PIPE，子进程写满缓冲区会互锁到超时。
            # 用线程 communicate + 可取消等待。
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=flags,
            )
            self._register_proc(proc)
            deadline = time.time() + max(1, int(timeout))
            result_box: dict = {}

            def _comm() -> None:
                try:
                    out, err = proc.communicate()
                    result_box["out"] = out or ""
                    result_box["err"] = err or ""
                    result_box["rc"] = proc.returncode if proc.returncode is not None else 0
                except Exception as exc:
                    result_box["out"] = ""
                    result_box["err"] = str(exc)
                    result_box["rc"] = 125

            th = threading.Thread(target=_comm, name=f"adb-comm-{self.serial}", daemon=True)
            th.start()
            while th.is_alive():
                if self._cancel_requested():
                    self._kill_proc_tree(proc)
                    th.join(timeout=1.5)
                    out = str(result_box.get("out") or "")
                    err = str(result_box.get("err") or "")
                    return subprocess.CompletedProcess(
                        cmd, 130, out, (err + "\nadb_cancelled").strip()
                    )
                if time.time() >= deadline:
                    self._kill_proc_tree(proc)
                    th.join(timeout=1.5)
                    out = str(result_box.get("out") or "")
                    err = str(result_box.get("err") or "")
                    logger.warning("ADB timeout %ss: %s", timeout, " ".join(cmd)[:180])
                    return subprocess.CompletedProcess(
                        cmd, 124, out, (err + f"\nTIMEOUT:{timeout}").strip()
                    )
                time.sleep(0.05)
            out = str(result_box.get("out") or "")
            err = str(result_box.get("err") or "")
            rc = int(result_box.get("rc", proc.returncode if proc.returncode is not None else 0) or 0)
            return subprocess.CompletedProcess(cmd, rc, out, err)
        except Exception as exc:
            logger.warning("ADB err: %s | %s", exc, " ".join(cmd)[:160])
            try:
                if proc is not None and proc.poll() is None:
                    self._kill_proc_tree(proc)
            except Exception:
                pass
            return subprocess.CompletedProcess(cmd, 125, "", str(exc))
        finally:
            self._unregister_proc(proc)
            try:
                self._global_adb_sema.release()
            except Exception:
                pass
            if heavy and heavy_got:
                try:
                    self._heavy_adb_sema.release()
                except Exception:
                    pass
                logger.info(
                    "ADB heavy end serial=%s elapsed=%.1fs waited=%.1fs cmd=%s",
                    self.serial, time.time() - t_run, heavy_waited, " ".join(cmd)[:120],
                )

    def connect(self) -> bool:
        host, _, port = self.serial.partition(":")
        if not port:
            return False
        cmd = [str(self.adb), "connect", self.serial]
        cp = subprocess.run(
            cmd,
            capture_output=True,
            text=True, encoding="utf-8", errors="replace",
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        out = (cp.stdout or "") + (cp.stderr or "")
        logger.info("adb connect %s -> %s", self.serial, out.strip()[:200])
        return "connected" in out.lower() or "already" in out.lower()

    def device_state(self) -> str:
        """返回 adb devices 中本 serial 的状态: device/offline/空。"""
        try:
            cp = self._run(["devices"], timeout=8)
            text = (cp.stdout or "") + (cp.stderr or "")
        except Exception:
            return ""
        for line in text.splitlines():
            if self.serial in line:
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1].strip()
        return ""

    def is_online(self) -> bool:
        return self.device_state() == "device"

    def shell(self, *shell_args: str, timeout: int = 45) -> str:
        cp = self._run(["shell", *shell_args], timeout=timeout)
        return (cp.stdout or "") + (cp.stderr or "")

    def shell_su(self, command: str, timeout: int = 45) -> str:
        """以 root 执行单条命令；并行自动点 Magisk [SharedUID] Shell 授权。

        Magisk su -c 只接受紧跟的一个参数。多词命令必须整段作为单参数。
        """
        safe = (command or "").replace("'", '\'"\'"\'')

        def _body() -> str:
            cp = self._run(["shell", f"su -c '{safe}'"], timeout=timeout)
            return (cp.stdout or "") + (cp.stderr or "")

        return self._run_su_with_auto_grant(_body, timeout=timeout)

    def shell_script(self, script: str, timeout: int = 45) -> str:
        """在设备 sh 中执行完整脚本（base64 传输，避免 #/括号/引号被 adb shell 吃掉）。

        注意：adb shell 多参数时不会给 -c 的脚本加引号，管道会断裂。
        必须把整个 `sh -c '...'` 作为单一 remote 参数传入。
        """
        import base64
        b64 = base64.b64encode(script.encode("utf-8")).decode("ascii")
        # base64 仅 [A-Za-z0-9+/=]，可安全放进单引号
        remote = f"echo {b64}|base64 -d|sh"
        cp = self._run(["shell", f"sh -c '{remote}'"], timeout=timeout)
        return (cp.stdout or "") + (cp.stderr or "")

    def shell_su_script(self, script: str, timeout: int = 45) -> str:
        """root 下执行完整脚本（base64 落临时文件再 su，避免管道/引号问题）。

        Magisk `su -c` 只吃紧跟的一个参数。若写成:
          adb shell su -c sh /path
        则 `/path` 会被当成 uid，报 Unknown id。
        必须: adb shell "su -c 'sh /path'" 或 "su 0 sh /path"。
        执行期间并行自动点 Magisk [SharedUID] Shell 授权弹窗。
        """
        import base64
        import time as _time

        def _body() -> str:
            b64 = base64.b64encode(script.encode("utf-8")).decode("ascii")
            remote = f"/data/local/tmp/mumuvenmo_su_{int(_time.time()*1000)}.sh"
            # 1) 非 root 写入脚本文件并校验存在
            write_cmd = (
                f"echo {b64}|base64 -d > {remote} && chmod 755 {remote} "
                f"&& test -s {remote} && echo WRITE_OK || echo WRITE_FAIL"
            )
            wr = self._run(["shell", f"sh -c '{write_cmd}'"], timeout=min(30, max(10, timeout)))
            wr_out = ((wr.stdout or "") + (wr.stderr or "")).strip()
            if "WRITE_OK" not in wr_out:
                # 回退：整段脚本用 su -c 单参数直接跑（无临时文件）
                esc = script.replace("'", "'\"'\"'")
                cp = self._run(["shell", f"su -c '{esc}'"], timeout=timeout)
                return (cp.stdout or "") + (cp.stderr or "") + "\n#write_fail:" + wr_out[:120]
            # 2) 优先 su 0 sh path（多参数安全）；失败再 su -c 单参数
            cp = self._run(["shell", f"su 0 sh {remote}"], timeout=timeout)
            out = (cp.stdout or "") + (cp.stderr or "")
            if "Unknown id" in out or (cp.returncode not in (0, None) and not out.strip()):
                cp2 = self._run(["shell", f"su -c 'sh {remote}'"], timeout=timeout)
                out2 = (cp2.stdout or "") + (cp2.stderr or "")
                out = out2 if out2.strip() else out
            # 3) 清理
            try:
                self._run(["shell", f"rm -f {remote}"], timeout=10)
            except Exception:
                pass
            return out

        return self._run_su_with_auto_grant(_body, timeout=timeout)

    def _run_su_with_auto_grant(self, fn, timeout: int = 45) -> str:
        """在 su 可能弹出 Magisk 授权框时，后台轮询自动点同意。"""
        import threading

        stop = threading.Event()
        hits: list[str] = []

        def _is_real_grant(hit: str) -> bool:
            h = (hit or "").strip().lower()
            if not h:
                return False
            # 无实际点击 / 明确失败
            if h in ("forever_missing_no_temp_allow", "") or h.startswith("forever_missing"):
                return False
            if "via_deny" in h or "deny_right" in h or "拒绝" in h:
                return False
            if re.search(r"(^|[_=|])deny($|[_=|])", h) and "grant" not in h:
                return False
            # 只认明确 GRANT / Allow 点击结果
            if any(k in h for k in (
                "magisk_grant", "grant_fast", "exact=grant", "exact=allow",
                "allow_nemu", "allow_rid", "|allow", "=grant", "grant_rid",
            )):
                return True
            if "allow" in h and "grant" in h:
                return True
            if h.startswith("forever=") and "allow" in h and "missing" not in h:
                return True
            return False

        def _loop() -> None:
            while not stop.is_set():
                try:
                    hit = self.dismiss_magisk_su_dialog()
                    if hit and _is_real_grant(hit):
                        hits.append(hit)
                        logger.info("auto-grant Magisk SU: %s @ %s", hit, self.serial)
                    elif hit:
                        logger.debug("auto-grant intermediate (not final): %s @ %s", hit, self.serial)
                except Exception as exc:
                    logger.debug("auto-grant dismiss err: %s", exc)
                if stop.wait(0.55):
                    break

        th = threading.Thread(target=_loop, name=f"su-grant-{self.serial}", daemon=True)
        th.start()
        try:
            try:
                self.dismiss_magisk_su_dialog()
            except Exception:
                pass
            out = fn()
            if hits:
                out = (out or "") + f"\n#auto_grant={','.join(hits[:5])}"
            return out
        finally:
            stop.set()
            try:
                th.join(timeout=1.5)
            except Exception:
                pass


    def dismiss_magisk_su_dialog(self) -> str:
        """Magisk/Superuser 授权：必须先 Remember choice forever，再 Allow。

        用户明确：临时授权不会出现第3项 Direct Install (modify /system directly)。
        必须：弹出框点 Remember choice forever，再点 Allow。绝不点 Deny / This time only。

        MuMu 实测弹窗（com.android.settings / com.nemu.superuser.RequestActivity）：
          - text: Kitsune Mask is requesting Superuser access.
          - rid: remember_forever / this_time_only / allow / deny
        """
        try:
            xml = self.uiautomator_dump(force=True) or ""
        except Exception:
            xml = ""
        low = (xml or "").lower()
        empty = (not xml.strip()) or ('bounds="[0,0][0,0]"' in xml) or (xml.count("<node") <= 2)

        def _is_nemu_su_dialog(cur_xml: str = "", cur_low: str = "") -> bool:
            x = cur_xml if cur_xml is not None else xml
            l = cur_low if cur_low else (x or "").lower()
            if any(
                k in l
                for k in (
                    "com.android.settings:id/remember_forever",
                    "com.android.settings:id/this_time_only",
                    "com.android.settings:id/request",
                    "requesting superuser access",
                    "com.nemu.superuser",
                    "remember choice forever",
                )
            ) and any(
                k in l
                for k in (
                    'text="allow"',
                    'text="Allow"',
                    "com.android.settings:id/allow",
                    "deny",
                )
            ):
                return True
            # dumpsys 焦点兜底
            for cmd in (
                ("dumpsys", "activity", "activities"),
                ("dumpsys", "window", "windows"),
            ):
                try:
                    out = (self.shell(*cmd, timeout=8) or "").lower()
                except Exception:
                    out = ""
                if not out:
                    continue
                if "com.nemu.superuser" in out or "requestactivity" in out:
                    for ln in out.splitlines():
                        ll = ln.lower()
                        if any(
                            k in ll
                            for k in (
                                "mcurrentfocus",
                                "mfocusedapp",
                                "topresumedactivity",
                                "mholdsscreen",
                            )
                        ) and (
                            "com.nemu.superuser" in ll
                            or "requestactivity" in ll
                            or "superuser" in ll
                        ):
                            return True
            return False

        def _is_surequest() -> bool:
            needles = (
                "surequestactivity",
                "su_request",
                "su request",
                ".surequest",
                "com.topjohnwu.magisk.ui.surequest",
                "io.github.huskydg.magisk/com.topjohnwu.magisk.ui.surequest",
                "com.nemu.superuser",
                "com.nemu.superuser.requestactivity",
                "requesting superuser access",
            )
            for cmd in (
                ("dumpsys", "activity", "activities"),
                ("dumpsys", "window", "windows"),
            ):
                try:
                    out = (self.shell(*cmd, timeout=8) or "").lower()
                except Exception:
                    out = ""
                if not out:
                    continue
                if any(n in out for n in needles):
                    for ln in out.splitlines():
                        ll = ln.lower()
                        if any(
                            k in ll
                            for k in (
                                "mcurrentfocus",
                                "mfocusedapp",
                                "topresumedactivity",
                                "mholdsscreen",
                            )
                        ):
                            if any(n in ll for n in needles) or (
                                "surequest" in ll and "magisk" in ll
                            ) or ("superuser" in ll and "request" in ll):
                                return True
                    if "surequestactivity" in out or "com.nemu.superuser" in out:
                        return True
            return False

        # -------- Magisk SharedUID Shell GRANT fast path --------
        def _find_grant_bounds(cur_xml: str):
            """只找 GRANT/Allow 按钮，绝不返回 Deny。"""
            if not (cur_xml or "").strip():
                return None, ""
            try:
                root = ET.fromstring(cur_xml)
            except ET.ParseError:
                # 正则兜底：resource-id .../grant
                m = re.search(
                    r'resource-id="[^"]*?/(?:grant|allow)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                    cur_xml,
                    re.I,
                )
                if not m:
                    m = re.search(
                        r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*resource-id="[^"]*?/(?:grant|allow)"',
                        cur_xml,
                        re.I,
                    )
                if m:
                    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))), "regex_rid"
                m = re.search(
                    r'text="(GRANT|Grant|Allow|ALLOW|允许|同意)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                    cur_xml,
                )
                if not m:
                    m = re.search(
                        r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*text="(GRANT|Grant|Allow|ALLOW|允许|同意)"',
                        cur_xml,
                    )
                    if m:
                        return (int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))), f"regex_text={m.group(5)}"
                elif m:
                    return (int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))), f"regex_text={m.group(1)}"
                return None, ""

            candidates = []
            for node in root.iter("node"):
                rid = (node.attrib.get("resource-id") or "")
                text_v = (node.attrib.get("text") or "").strip()
                desc = (node.attrib.get("content-desc") or "").strip()
                rid_l = rid.lower()
                tv_l = text_v.lower()
                desc_l = desc.lower()
                # 硬排除 Deny / This time only
                if rid_l.endswith("/deny") or tv_l in ("deny", "拒绝", "this time only") or desc_l in ("deny", "拒绝"):
                    continue
                if "this_time_only" in rid_l:
                    continue
                score = 0
                why = ""
                if rid_l.endswith("/grant"):
                    score = 100
                    why = "rid_grant"
                elif rid_l.endswith("/allow") and "remember" not in rid_l:
                    score = 90
                    why = "rid_allow"
                elif tv_l in ("grant",) or text_v == "GRANT":
                    score = 95
                    why = "text_GRANT"
                elif tv_l == "allow" or text_v == "ALLOW":
                    score = 85
                    why = "text_Allow"
                elif tv_l in ("允许", "同意"):
                    score = 80
                    why = f"text_{text_v}"
                else:
                    continue
                b = self._parse_bounds(node.attrib.get("bounds") or "")
                if not b:
                    continue
                x1, y1, x2, y2 = b
                w, h = max(1, x2 - x1), max(1, y2 - y1)
                # 按钮应是中等尺寸，排除整屏容器
                if w > 1200 or h > 400:
                    continue
                if w < 40 or h < 30:
                    continue
                clickable = node.attrib.get("clickable") == "true"
                if clickable:
                    score += 5
                # 右侧按钮优先（GRANT 通常在 DENY 右边）
                cx = (x1 + x2) // 2
                score += min(20, cx // 100)
                candidates.append((score, b, why, text_v or rid))
            if not candidates:
                return None, ""
            candidates.sort(key=lambda x: x[0], reverse=True)
            best = candidates[0]
            return best[1], best[2]

        def _magisk_grant_fast(cur_xml: str, cur_low: str) -> str:
            if not cur_xml or not cur_low:
                return ""
            # MuMu SuperUser 走 Forever→Allow，不走 Magisk GRANT 快路径
            if any(k in cur_low for k in (
                "com.android.settings:id/remember_forever",
                "com.android.settings:id/this_time_only",
                "com.nemu.superuser",
                "remember choice forever",
                "requesting superuser access",
            )):
                return ""
            has_grant_btn = any(k in cur_low for k in (
                "io.github.huskydg.magisk:id/grant",
                "com.topjohnwu.magisk:id/grant",
                'text="grant"', 'text="Grant"', 'text="GRANT"',
                'content-desc="grant"', 'content-desc="Grant"',
                'resource-id="io.github.huskydg.magisk:id/grant"',
            ))
            has_shell_ctx = any(k in cur_low for k in (
                "shareduid", "shell", "surequest", "superuser request",
                "wants to access", "root access", "magisk",
            ))
            has_deny = any(k in cur_low for k in ('text="deny"', 'text="Deny"', "拒绝", "id/deny"))
            if not has_grant_btn:
                # 仅有 Deny 绝不可猜点
                if has_deny and not has_grant_btn:
                    return ""
                if not (has_shell_ctx and has_deny):
                    # 仍尝试精确解析 grant bounds
                    pass
            # 可选：先把超时点到 Forever（不强制）
            for lab in ("Forever", "永久", "Always", "始终"):
                try:
                    b = self.find_node_bounds(text_substr=lab, xml=cur_xml, exact=True)
                except Exception:
                    b = None
                if b:
                    try:
                        self.tap_bounds(b)
                        time.sleep(0.12)
                    except Exception:
                        pass
                    break
            # 优先 resource-id / 精确文本 GRANT
            b, why = _find_grant_bounds(cur_xml)
            if b:
                self.tap_bounds(b)
                time.sleep(0.25)
                return f"magisk_grant_fast_{why}"
            # 精确 exact 文本，绝不用子串误匹配
            for lab in ("GRANT", "Grant", "Allow", "ALLOW", "允许", "同意"):
                try:
                    bb = self.find_node_bounds(text_substr=lab, xml=cur_xml, exact=True)
                except Exception:
                    bb = None
                if bb:
                    self.tap_bounds(bb)
                    time.sleep(0.25)
                    return f"magisk_grant_fast_exact={lab}"
            for rid in (
                "io.github.huskydg.magisk:id/grant",
                "com.topjohnwu.magisk:id/grant",
            ):
                bb = self.find_node_bounds(resource_id=rid, xml=cur_xml)
                if bb:
                    self.tap_bounds(bb)
                    time.sleep(0.25)
                    return f"magisk_grant_fast_rid={rid.split('/')[-1]}"
            # 禁止 via_deny_right：找不到 GRANT 就返回空，留给后续重试
            return ""

        try:
            mg = _magisk_grant_fast(xml, low)
            if mg:
                return mg
        except Exception:
            pass

        # -------- Magisk SuRequest 空树/dump 失败：只点右侧 GRANT 坐标，绝不点左侧 DENY --------
        def _is_magisk_surequest_focus() -> bool:
            """True only when Magisk SuRequest activity is focused."""
            try:
                act = (self.shell("dumpsys", "activity", "activities", timeout=8) or "").lower()
            except Exception:
                act = ""
            if not act or "com.nemu.superuser" in act:
                return False
            needles = (
                "surequestactivity",
                "magisk.ui.surequest",
                "com.topjohnwu.magisk.ui.surequest",
                "io.github.huskydg.magisk/com.topjohnwu.magisk.ui.surequest",
                "com.topjohnwu.magisk/com.topjohnwu.magisk.ui.surequest",
            )
            for ln in act.splitlines():
                ll = ln.lower()
                if any(k in ll for k in ("mcurrentfocus", "mfocusedapp", "topresumedactivity")):
                    if "mainactivity" in ll and "surequest" not in ll:
                        return False
                    if any(n in ll for n in needles):
                        return True
            return False

        def _has_visible_grant_ui(cur_low: str) -> bool:
            l = cur_low or ""
            return any(
                k in l
                for k in (
                    "id/grant",
                    'text="grant"',
                    'text="Grant"',
                    'text="GRANT"',
                    'content-desc="grant"',
                    'content-desc="Grant"',
                    'content-desc="GRANT"',
                    'resource-id="io.github.huskydg.magisk:id/grant"',
                    'resource-id="com.topjohnwu.magisk:id/grant"',
                )
            )

        # HARD RULE grant-only-when-popup-v1:
        # GRANT only when popup is visible. No popup => no click, no coord guess.
        # Magisk home / PP donate / empty MainActivity must never be tapped as GRANT.
        if not _has_visible_grant_ui(low):
            # Keep going only for MuMu Forever/Allow path below; do NOT coord-tap Magisk GRANT.
            pass
        else:
            # Visible GRANT: use fast path only (already tried above). No blind coords.
            pass


        # grant-only-when-popup-v2: 没有弹窗证据就直接返回，绝不点任何坐标
        popup_evidence = any(
            k in (low or "")
            for k in (
                "id/grant",
                'text="grant"',
                'text="Grant"',
                'text="GRANT"',
                "remember choice forever",
                "remember_forever",
                "this_time_only",
                "requesting superuser",
                "com.nemu.superuser",
                "shareduid",
                "wants to access",
            )
        )
        if not popup_evidence:
            # dumpsys 再确认一次是否真有 SuRequest / MuMu SuperUser
            try:
                act_e = (self.shell("dumpsys", "activity", "activities", timeout=6) or "").lower()
            except Exception:
                act_e = ""
            focus_popup = False
            for ln in (act_e or "").splitlines():
                ll = ln.lower()
                if any(k in ll for k in ("mcurrentfocus", "mfocusedapp", "topresumedactivity")):
                    if any(
                        k in ll
                        for k in (
                            "surequest",
                            "com.nemu.superuser",
                            "requestactivity",
                        )
                    ):
                        focus_popup = True
                        break
            if not focus_popup:
                return ""

        # -------- MuMu SuperUser 专用快路径：resource-id 点 Forever → Allow --------

        nemu = False

        try:
            # 空树 + surequest 可能是 Magisk SuRequest，不能当成 MuMu 弹窗乱点坐标
            nemu = _is_nemu_su_dialog(xml, low)
            if empty and not nemu:
                try:
                    act_chk = (self.shell("dumpsys", "activity", "activities", timeout=8) or "").lower()
                except Exception:
                    act_chk = ""
                if "com.nemu.superuser" in act_chk or "requesting superuser access" in act_chk:
                    nemu = True
        except Exception:
            nemu = False
        if nemu or (
            "remember_forever" in low
            or "this_time_only" in low
            or "requesting superuser access" in low
        ):
            # 重新 dump 一次，避免空树
            if empty:
                try:
                    xml = self.uiautomator_dump(force=True) or xml
                    low = (xml or "").lower()
                except Exception:
                    pass
            forever_b = self.find_node_bounds(
                resource_id="com.android.settings:id/remember_forever", xml=xml
            ) or self.find_node_bounds(
                text_substr="Remember choice forever", xml=xml
            ) or self.find_node_bounds(
                text_substr="remember choice forever", xml=xml
            )
            if forever_b:
                self.tap_bounds(forever_b)
                time.sleep(0.35)
            else:
                # 坐标兜底：实测 forever 在 [277,1777][1163,1969] 中心约 (720,1873)
                for x, y in ((720, 1873), (720, 1850), (900, 1870), (720, 1900)):
                    try:
                        self.tap(x, y)
                    except Exception:
                        pass
                    time.sleep(0.05)
                time.sleep(0.25)
            # 绝不再点 this_time_only
            try:
                xml2 = self.uiautomator_dump(force=True) or xml
            except Exception:
                xml2 = xml
            allow_b = self.find_node_bounds(
                resource_id="com.android.settings:id/allow", xml=xml2
            ) or self.find_node_bounds(text_substr="Allow", xml=xml2, exact=True)
            if not allow_b:
                # 避免误点 Deny：Allow 在右半 [722,1989][1312,2181]
                for x, y in ((1017, 2085), (1100, 2085), (980, 2085), (1017, 2050)):
                    try:
                        self.tap(x, y)
                    except Exception:
                        pass
                    time.sleep(0.06)
                time.sleep(0.35)
                # 成功判据：弹窗消失
                try:
                    xml3 = self.uiautomator_dump(force=True) or ""
                except Exception:
                    xml3 = ""
                low3 = (xml3 or "").lower()
                if (
                    "requesting superuser access" not in low3
                    and "remember_forever" not in low3
                    and "this_time_only" not in low3
                ):
                    return "forever=Remember choice forever|Allow_nemu_coord"
                return "forever=Remember choice forever|Allow_nemu_coord_try"
            self.tap_bounds(allow_b)
            time.sleep(0.35)
            return "forever=Remember choice forever|Allow_nemu_rid"

        surequest = False
        try:
            surequest = _is_surequest()
        except Exception:
            pass

        has_forever_phrase = any(
            k in low
            for k in (
                "remember choice forever",
                "remember forever",
                "remember choice",
                "永久记住",
                "始终允许",
                "记住选择",
            )
        )
        has_timeout_ui = any(
            k in low
            for k in (
                "timeout",
                "for 10 minutes",
                "for 20 minutes",
                "for 30 minutes",
                "10 minutes",
                "20 minutes",
                "30 minutes",
                "once",
                "this time",
                "仅此一次",
                "10 分钟",
                "20 分钟",
                "30 分钟",
            )
        )
        has_grant = any(
            k in low
            for k in (
                "grant",
                "允许",
                "同意",
                'text="allow"',
                'text="ALLOW"',
                'text="Allow"',
                'content-desc="allow"',
                'content-desc="Allow"',
            )
        )
        has_deny = any(
            k in low
            for k in ('text="deny"', 'text="Deny"', "拒绝", 'content-desc="deny"')
        )
        has_su_words = any(
            m in low
            for m in (
                "shareduid",
                "superuser request",
                "superuser",
                "surequest",
                "wants to access",
                "requesting root",
                "requesting superuser",
                "请求超级用户",
                "超级用户",
                "root access",
                "wants root",
            )
        )
        looks = bool(
            surequest
            or has_forever_phrase
            or (has_timeout_ui and (has_grant or has_deny))
            or (has_su_words and (has_grant or has_deny))
            or (
                has_grant
                and has_deny
                and ("shell" in low or "uid" in low or "magisk" in low or "root" in low)
            )
        )
        if not looks:
            return ""

        forever_labels = [
            "Remember choice forever",
            "Remember forever",
            "Always allow",
            "永久记住",
            "始终允许",
            "记住选择",
            "Forever",
        ]
        timeout_spinner_ids = (
            "io.github.huskydg.magisk:id/timeout",
            "io.github.huskydg.magisk:id/spinner",
            "com.topjohnwu.magisk:id/timeout",
            "com.topjohnwu.magisk:id/spinner",
            "android:id/text1",
            "com.android.settings:id/remember_forever",
        )
        temp_labels = (
            "Once",
            "10 minutes",
            "20 minutes",
            "30 minutes",
            "For 10 minutes",
            "For 20 minutes",
            "For 30 minutes",
            "仅此一次",
            "10 分钟",
            "20 分钟",
            "30 分钟",
            # 注意：This time only 是 MuMu 临时项，绝不能当 spinner 点开后选它
        )
        allow_labels = ["Allow", "ALLOW", "Grant", "GRANT", "允许", "同意"]

        def _select_forever(cur_xml: str):
            hit = ""
            xml_local = cur_xml or ""
            # 优先 MuMu rid
            b = self.find_node_bounds(
                resource_id="com.android.settings:id/remember_forever", xml=xml_local
            )
            if b:
                self.tap_bounds(b)
                hit = "Remember choice forever"
                time.sleep(0.45)
                try:
                    xml_local = self.uiautomator_dump(force=True) or xml_local
                except Exception:
                    pass
                return hit, xml_local
            for lab in forever_labels:
                b = self.find_node_bounds(text_substr=lab, xml=xml_local)
                if b:
                    # 禁止点到 This time only
                    if "this time" in lab.lower():
                        continue
                    self.tap_bounds(b)
                    hit = lab
                    time.sleep(0.45)
                    try:
                        xml_local = self.uiautomator_dump(force=True) or xml_local
                    except Exception:
                        pass
                    return hit, xml_local
            opened = False
            for rid in timeout_spinner_ids:
                b = self.find_node_bounds(resource_id=rid, xml=xml_local)
                if b:
                    self.tap_bounds(b)
                    opened = True
                    time.sleep(0.45)
                    break
            if not opened:
                for temp in temp_labels:
                    b = self.find_node_bounds(text_substr=temp, xml=xml_local)
                    if b and b[1] < 1900:
                        # 不要点 This time only 本身当“打开菜单”
                        if "this time" in temp.lower():
                            continue
                        self.tap_bounds(b)
                        opened = True
                        time.sleep(0.45)
                        break
            if opened:
                try:
                    xml_local = self.uiautomator_dump(force=True) or xml_local
                except Exception:
                    pass
                b = self.find_node_bounds(
                    resource_id="com.android.settings:id/remember_forever", xml=xml_local
                )
                if b:
                    self.tap_bounds(b)
                    hit = "Remember choice forever"
                    time.sleep(0.45)
                    try:
                        xml_local = self.uiautomator_dump(force=True) or xml_local
                    except Exception:
                        pass
                    return hit, xml_local
                for lab in forever_labels:
                    b = self.find_node_bounds(text_substr=lab, xml=xml_local)
                    if b:
                        self.tap_bounds(b)
                        hit = lab
                        time.sleep(0.45)
                        try:
                            xml_local = self.uiautomator_dump(force=True) or xml_local
                        except Exception:
                            pass
                        return hit, xml_local
                try:
                    import xml.etree.ElementTree as ET

                    root = ET.fromstring(xml_local)
                    bottoms = []
                    for node in root.iter("node"):
                        t = (node.attrib.get("text") or "").strip().lower()
                        if not t:
                            continue
                        if "this time" in t:
                            continue
                        if any(
                            k in t
                            for k in (
                                "forever",
                                "always",
                                "永久",
                                "始终",
                                "minute",
                                "once",
                                "次",
                                "分钟",
                            )
                        ):
                            bb = self._parse_bounds(node.attrib.get("bounds") or "")
                            if bb:
                                bottoms.append((bb[1], bb, t))
                    if bottoms:
                        bottoms.sort(key=lambda x: x[0])
                        _, bb, t = bottoms[-1]
                        self.tap_bounds(bb)
                        hit = f"list_bottom:{t}"
                        time.sleep(0.45)
                        try:
                            xml_local = self.uiautomator_dump(force=True) or xml_local
                        except Exception:
                            pass
                        return hit, xml_local
                except Exception:
                    pass
            return hit, xml_local

        forever_hit = ""
        if xml and not empty:
            forever_hit, xml = _select_forever(xml)
        if not forever_hit and (surequest or looks):
            try:
                xml = self.uiautomator_dump(force=True) or xml
            except Exception:
                pass
            forever_hit, xml = _select_forever(xml)

        try:
            xml = self.uiautomator_dump(force=True) or xml
        except Exception:
            pass
        low = (xml or "").lower()
        forever_selected = bool(forever_hit) or (
            "remember choice forever" in low
        ) or ("永久记住" in low) or ("always allow" in low) or (
            "remember_forever" in low
        )

        if xml and not empty:
            if not forever_selected:
                forever_hit2, xml = _select_forever(xml)
                forever_hit = forever_hit or forever_hit2
                low2 = (xml or "").lower()
                forever_selected = bool(forever_hit) or (
                    "remember choice forever" in low2
                ) or ("永久记住" in low2) or ("remember_forever" in low2)
            if forever_selected:
                # 优先 MuMu allow rid
                b_allow = self.find_node_bounds(
                    resource_id="com.android.settings:id/allow", xml=xml
                )
                if b_allow:
                    self.tap_bounds(b_allow)
                    time.sleep(0.3)
                    return f"forever={forever_hit or 'shown'}|Allow_nemu_rid"
                hit = self.tap_any(allow_labels, xml=xml, match_desc=True, match_text=True)
                if hit:
                    time.sleep(0.3)
                    return f"forever={forever_hit or 'shown'}|{hit}"
                for rid in (
                    "io.github.huskydg.magisk:id/grant",
                    "com.topjohnwu.magisk:id/grant",
                    "com.android.settings:id/allow",
                ):
                    b = self.find_node_bounds(resource_id=rid, xml=xml)
                    if b:
                        self.tap_bounds(b)
                        return f"forever={forever_hit or 'shown'}|Allow_rid"
                # grant-no-deny-v1: 已删除 Allow_via_Deny_right，避免误点 Deny
            else:
                # Magisk SuRequest 主路径：可见 GRANT 时直接点 GRANT（[SharedUID] Shell）
                # MuMu SuperUser 弹窗仍要求 Forever，不在这里放行临时 Allow。
                is_magisk_grant_ui = any(
                    k in low
                    for k in (
                        "io.github.huskydg.magisk:id/grant",
                        "com.topjohnwu.magisk:id/grant",
                        'text="grant"',
                        'text="Grant"',
                        'text="GRANT"',
                        'content-desc="grant"',
                        'content-desc="Grant"',
                    )
                ) and any(
                    k in low
                    for k in (
                        "shareduid",
                        "shell",
                        "superuser",
                        "surequest",
                        "magisk",
                        "root",
                    )
                )
                if is_magisk_grant_ui:
                    # 尽量先把超时策略点到 Forever，再点 GRANT
                    for lab in ("Forever", "永久", "Always", "始终"):
                        try:
                            b = self.find_node_bounds(text_substr=lab, xml=xml, exact=True)
                        except Exception:
                            b = None
                        if b:
                            try:
                                self.tap_bounds(b)
                                time.sleep(0.15)
                            except Exception:
                                pass
                            break
                    # 优先精确 grant bounds，绝不 tap_any 子串误匹配
                    b_g, why_g = _find_grant_bounds(xml)
                    if b_g:
                        self.tap_bounds(b_g)
                        time.sleep(0.25)
                        return f"magisk_grant_{why_g}"
                    for rid in (
                        "io.github.huskydg.magisk:id/grant",
                        "com.topjohnwu.magisk:id/grant",
                    ):
                        b = self.find_node_bounds(resource_id=rid, xml=xml)
                        if b:
                            self.tap_bounds(b)
                            time.sleep(0.25)
                            return f"magisk_grant_rid={rid.split('/')[-1]}"
                    for lab in ("GRANT", "Grant", "Allow", "ALLOW", "允许", "同意"):
                        b = self.find_node_bounds(text_substr=lab, xml=xml, exact=True)
                        if b:
                            self.tap_bounds(b)
                            time.sleep(0.25)
                            return f"magisk_grant_exact={lab}"
                # MuMu SuperUser：未选 Forever 绝不点临时 Allow（否则没有 Direct Install 第3项）
                try:
                    mg2 = _magisk_grant_fast(xml, low)
                    if mg2:
                        return mg2
                except Exception:
                    pass
                return ""

        # grant-only-when-popup-v1: no coord guess for Magisk GRANT.
        # If SuRequest is up but GRANT text not in dump yet, return empty and let caller retry.
        if surequest and not _is_nemu_su_dialog():
            if not _has_visible_grant_ui(low):
                return ""

        if _is_nemu_su_dialog() or (
            surequest and "com.nemu.superuser" in ((xml or "") + " " + low).lower()
        ):
            # MuMu 坐标：Forever 中部，Allow 右下（仅 MuMu SuperUser）
            for x, y in ((720, 1873), (720, 1850), (900, 1870)):
                try:
                    self.tap(x, y)
                except Exception:
                    pass
                time.sleep(0.08)
            time.sleep(0.35)
            try:
                xml2 = self.uiautomator_dump(force=True) or ""
            except Exception:
                xml2 = ""
            forever_hit3, xml2 = _select_forever(xml2)
            forever_hit = forever_hit or forever_hit3
            if forever_hit or "remember choice forever" in (xml2 or "").lower() or "remember_forever" in (xml2 or "").lower():
                b_allow = self.find_node_bounds(
                    resource_id="com.android.settings:id/allow", xml=xml2
                )
                if b_allow:
                    self.tap_bounds(b_allow)
                    return f"forever={forever_hit or 'coord'}|Allow_nemu_rid"
                for x, y in (
                    (1017, 2085),
                    (1100, 2085),
                    (980, 2085),
                    (1050, 2080),
                    (1150, 2100),
                ):
                    try:
                        self.tap(x, y)
                    except Exception:
                        pass
                    time.sleep(0.06)
                if not _is_surequest() and not _is_nemu_su_dialog():
                    return f"forever={forever_hit or 'coord'}|Allow_coord"
                try:
                    xml2 = self.uiautomator_dump(force=True) or ""
                    hit2 = self.tap_any(allow_labels, xml=xml2, match_desc=True, match_text=True)
                    if hit2:
                        return f"forever={forever_hit or 'coord'}|{hit2}"
                except Exception:
                    pass
            return ""
        return ""


    def wait_and_forever_allow_su(
        self,
        *,
        timeout: float = 12.0,
        poll: float = 0.55,
        dump_dir: str | None = None,
        tag: str = "su",
    ) -> str:
        """Install/su 弹窗专用：在 timeout 内反复 Forever→Allow，空返回也不提前放弃。

        临时授权不会出现 Direct Install 第3项，必须 Remember choice forever 再 Allow。
        返回最后一次命中串；全程无弹窗返回空串。
        MuMu 弹窗额外用 dumpsys 检测 com.nemu.superuser / RequestActivity。
        """
        import time as _t
        from pathlib import Path as _P

        t0 = _t.time()
        last = ""
        n = 0
        while _t.time() - t0 < float(timeout):
            n += 1
            # dumpsys 先探弹窗，避免 uiautomator 空树漏掉
            try:
                act = (self.shell("dumpsys", "activity", "activities", timeout=8) or "").lower()
            except Exception:
                act = ""
            has_dialog = any(
                k in act
                for k in (
                    "com.nemu.superuser",
                    "requestactivity",
                    "surequestactivity",
                    "requesting superuser",
                )
            )
            try:
                hit = self.dismiss_magisk_su_dialog()
            except Exception as exc:
                hit = f"err={exc}"
            if hit:
                last = str(hit)
                low = last.lower()
                if "forever_missing" not in low and any(
                    k in low for k in ("allow", "grant", "允许", "同意")
                ):
                    return last
            elif has_dialog:
                # dump 失败但焦点在 su 弹窗：坐标 Forever→Allow
                try:
                    for x, y in ((720, 1873), (900, 1870)):
                        self.tap(x, y)
                        _t.sleep(0.05)
                    _t.sleep(0.25)
                    for x, y in ((1017, 2085), (1100, 2085), (980, 2085)):
                        self.tap(x, y)
                        _t.sleep(0.05)
                    last = "forever=coord_dumpsys|Allow_coord"
                    # 再确认是否消失
                    try:
                        act2 = (self.shell("dumpsys", "activity", "activities", timeout=8) or "").lower()
                    except Exception:
                        act2 = act
                    if not any(
                        k in act2
                        for k in (
                            "com.nemu.superuser",
                            "requestactivity",
                            "surequestactivity",
                        )
                    ):
                        return last
                except Exception as exc:
                    last = f"coord_err={exc}"
            if dump_dir and n in (1, 3, 6, 10, 15, 20):
                try:
                    d = _P(dump_dir)
                    d.mkdir(parents=True, exist_ok=True)
                    xml = self.uiautomator_dump(force=True) or ""
                    (d / f"{tag}_{n}.xml").write_text(xml, encoding="utf-8")
                    if act:
                        (d / f"{tag}_{n}_act.txt").write_text(act[:4000], encoding="utf-8")
                except Exception:
                    pass
            _t.sleep(float(poll))
        return last

    def grant_shell_superuser_db(self) -> str:
        """把 adb shell(uid=2000) 永久写入 Magisk policies，避免反复弹 [SharedUID] Shell。"""
        script = r"""
# Magisk policy: ALLOW=2
for SQL in \
  "INSERT OR REPLACE INTO policies (uid,package_name,policy,until,logging,notification) VALUES(2000,'com.android.shell',2,0,1,0);" \
  "INSERT OR REPLACE INTO policies (uid,package_name,policy,until,logging,notification) VALUES(2000,'shell',2,0,1,0);" \
  "INSERT OR REPLACE INTO policies (uid,package_name,policy,until,logging,notification) VALUES(2000,'[SharedUID] Shell',2,0,1,0);"
do
  magisk --sqlite "$SQL" 2>/dev/null || true
  /data/adb/magisk/magisk64 --sqlite "$SQL" 2>/dev/null || true
done
# 直接改 magisk.db（若可写）
if [ -f /data/adb/magisk.db ]; then
  for BIN in sqlite3 /data/adb/magisk/busybox; do
    if command -v $BIN >/dev/null 2>&1 || [ -x $BIN ]; then
      $BIN /data/adb/magisk.db "INSERT OR REPLACE INTO policies (uid,package_name,policy,until,logging,notification) VALUES(2000,'com.android.shell',2,0,1,0);" 2>/dev/null || true
      break
    fi
  done
fi
echo GRANT_SHELL_DONE
"""
        try:
            out = self.shell_su_script(script, timeout=20)
        except Exception as exc:
            out = f"err={exc}"
        return (out or "").strip()[:200]

    def tap_any(
        self,
        labels: list[str],
        *,
        xml: str | None = None,
        match_desc: bool = True,
        match_text: bool = True,
    ) -> str:
        """单次 dump UI，按顺序点中第一个匹配的 text/content-desc 子串。返回命中标签或空串。"""
        xml = xml if xml is not None else self.uiautomator_dump()
        if not (xml or "").strip():
            return ""
        for lab in labels:
            if not lab:
                continue
            if match_text:
                b = self.find_node_bounds(text_substr=lab, xml=xml)
                if b:
                    self.tap_bounds(b)
                    return lab
            if match_desc:
                b = self.find_node_bounds(content_desc=lab, xml=xml)
                if b:
                    self.tap_bounds(b)
                    return lab
        return ""

    def wait_device(self, timeout: int = 120) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._cancel_requested():
                return False
            try:
                out = self.shell("getprop", "sys.boot_completed", timeout=15).strip()
                if out.splitlines()[-1:] == ["1"] or out.endswith("1"):
                    return True
            except Exception:
                pass
            end = time.time() + 2
            while time.time() < end:
                if self._cancel_requested():
                    return False
                time.sleep(0.2)
        return False


    def lock_portrait(self) -> str:
        """关闭自动旋转并锁定竖屏（user_rotation=0）。

        根因：accelerometer_rotation=1 时，NekoBox(常横屏)/Venmo(竖屏)/键盘/传感器
        会交替触发 ROTATION_0 <-> ROTATION_90，表现为横竖屏不停切换。
        登录坐标按 1440x2560 竖屏布局，必须在 ADB 就绪与每次登录前锁定。
        """
        script = """
settings put system accelerometer_rotation 0
settings put system user_rotation 0
settings put secure show_rotation_suggestions 0
cmd window set-user-rotation lock 0 >/dev/null 2>&1 || true
wm set-user-rotation lock 0 >/dev/null 2>&1 || true
echo ACC=$(settings get system accelerometer_rotation)
echo ROT=$(settings get system user_rotation)
wm size 2>/dev/null || true
"""
        try:
            out = self.shell_script(script, timeout=20)
        except Exception as exc:
            out = f"lock_portrait_err:{exc}"
            try:
                out += " | " + self.shell(
                    "settings", "put", "system", "accelerometer_rotation", "0", timeout=10
                )
                out += " | " + self.shell(
                    "settings", "put", "system", "user_rotation", "0", timeout=10
                )
            except Exception as exc2:
                out += f" | fallback_err:{exc2}"
        logger.info(
            "lock_portrait %s -> %s",
            self.serial,
            (out or "").replace("\n", " ")[:200],
        )
        return out or ""

    def display_rotation(self) -> str:
        """返回当前旋转摘要，便于日志确认是否仍横屏。"""
        try:
            acc = (
                self.shell("settings", "get", "system", "accelerometer_rotation", timeout=8) or ""
            ).strip()
            rot = (
                self.shell("settings", "get", "system", "user_rotation", timeout=8) or ""
            ).strip()
            dump = self.shell("dumpsys", "window", timeout=15) or ""
            cur = ""
            for line in dump.splitlines():
                if "mCurrentRotation" in line or "mRotation=" in line:
                    cur = line.strip()
                    break
            return f"acc={acc} user_rot={rot} {cur}"
        except Exception as exc:
            return f"display_rotation_err:{exc}"

    def pm_clear(self, package: str) -> str:
        return self.shell("pm", "clear", package, timeout=60)

    def force_stop(self, package: str) -> str:
        return self.shell("am", "force-stop", package, timeout=3)

    def start_app(self, package: str) -> str:
        # Venmo 等包 am start 常无法 resolve，优先 monkey
        out = self.shell(
            "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1",
            timeout=30,
        )
        if "Events injected" in out or "injected" in out.lower():
            return out
        out2 = self.shell(
            "am", "start", "-a", "android.intent.action.MAIN",
            "-c", "android.intent.category.LAUNCHER", package, timeout=30
        )
        return (out or "") + "\n" + (out2 or "")

    def _run_install_with_offline_retry(self, args: list[str], timeout: int) -> str:
        """install-heal-fast-v3: offline reconnect-retry; pure TIMEOUT/package-dead return for MuMu heal."""
        def _once(tmo: int) -> str:
            cp = self._run(args, timeout=tmo)
            return ((cp.stdout or "") + (cp.stderr or "")).strip()

        def _is_timeout(low: str) -> bool:
            return (
                f"timeout:{timeout}" in low
                or low.strip().endswith(f"timeout:{timeout}")
                or ("timeout:" in low)
                or low.startswith("timeout:")
                or "adb_sema_timeout" in low
                or "adb_heavy_sema_timeout" in low
            )

        def _is_offline(low: str) -> bool:
            return (
                "device offline" in low
                or "device not found" in low
                or "no devices" in low
                or "connection reset" in low
            )

        def _is_pkg_dead(low: str) -> bool:
            return (
                "can't find service: package" in low
                or "cannot find service: package" in low
                or "find service: package" in low
                or "broken pipe" in low
                or "error: closed" in low
            )

        text = _once(timeout)
        if self._cancel_requested():
            return text or "adb_cancelled"
        low = text.lower()
        half = ("performing streamed install" in low) and ("success" not in low)
        timed = _is_timeout(low)
        offline = _is_offline(low)
        pkg_dead = _is_pkg_dead(low)
        if not (timed or offline or pkg_dead or half):
            return text

        # install-heal-fast-v3: dead package service or pure TIMEOUT -> no blind second install
        service_dead = False
        try:
            if timed or pkg_dead or half:
                if not self.package_service_alive():
                    service_dead = True
        except Exception:
            service_dead = True
        if service_dead or (timed and not offline) or pkg_dead:
            logger.info(
                "ADB install skip-blind-retry serial=%s timed=%s pkg_dead=%s service_dead=%s half=%s -> heal-upper",
                self.serial, timed, pkg_dead, service_dead, half,
            )
            marker = "NEED_PACKAGE_SERVICE_HEAL"
            if marker.lower() not in low:
                text = (text + chr(10) + marker).strip()
            return text

        # offline/transient only: reconnect once
        try:
            self.connect()
        except Exception:
            pass
        time.sleep(1.2)
        if self._cancel_requested():
            return "adb_cancelled"
        t2 = max(int(timeout), int(timeout * 1.25))
        text2 = _once(t2)
        logger.info(
            "ADB install retry serial=%s reason=offline_or_transient -> %s",
            self.serial,
            text2[:120],
        )
        return text2

    def install(self, apk: str | Path) -> str:
        # kitsune/large apk under multi-VM pressure often >180s
        return self._run_install_with_offline_retry(["install", "-r", str(apk)], 120)

    def install_multiple(self, apks: list[str | Path], replace: bool = True) -> str:
        """完整 split 包安装。禁止把 Venmo 只装 base.apk。"""
        args = ["install-multiple"]
        if replace:
            args.append("-r")
        args.extend(str(p) for p in apks)
        return self._run_install_with_offline_retry(args, 420)

    def uninstall(self, package: str) -> str:
        cp = self._run(["uninstall", package], timeout=60)
        return (cp.stdout or "") + (cp.stderr or "")

    def push(self, local: str | Path, remote: str) -> str:
        cp = self._run(["push", str(local), remote], timeout=180)
        return (cp.stdout or "") + (cp.stderr or "")

    def pull(self, remote: str, local: str | Path) -> str:
        cp = self._run(["pull", remote, str(local)], timeout=180)
        return (cp.stdout or "") + (cp.stderr or "")

    def input_text(self, text: str) -> str:
        """尽量可靠输入；对特殊字符用逐字符 keyevent/text 混合。"""
        # adb input text 不能带空格，特殊字符易失败
        # 先尝试整串（转义后），失败则逐字符
        escaped = self._escape_input_text(text)
        out = self.shell("input", "text", escaped, timeout=30)
        return out

    @staticmethod
    def _escape_input_text(text: str) -> str:
        # Android input text 约定：空格 %s，部分 shell 特殊字符加反斜杠
        s = text
        s = s.replace("\\", "\\\\")
        s = s.replace(" ", "%s")
        s = s.replace("'", "\\'")
        s = s.replace('"', '\\"')
        s = s.replace("&", "\\&")
        s = s.replace("<", "\\<")
        s = s.replace(">", "\\>")
        s = s.replace("|", "\\|")
        s = s.replace(";", "\\;")
        s = s.replace("(", "\\(")
        s = s.replace(")", "\\)")
        s = s.replace("$", "\\$")
        s = s.replace("`", "\\`")
        s = s.replace("@", "\\@")
        s = s.replace("!", "\\!")
        s = s.replace("#", "\\#")
        s = s.replace("%", "\\%")
        return s

    def input_text_safe(self, text: str) -> None:
        """逐字符输入，兼容 @ ! # 等。字母数字直接 text，其它走 keyevent 或 text 单字符转义。"""
        buf = []
        for ch in text:
            if ch.isalnum():
                buf.append(ch)
                continue
            if buf:
                self.shell("input", "text", "".join(buf), timeout=20)
                buf = []
            if ch == " ":
                self.shell("input", "text", "%s", timeout=20)
            elif ch == "@":
                # KEYCODE 不通用，用转义 text
                self.shell("input", "text", "\\@", timeout=20)
            elif ch == "!":
                self.shell("input", "text", "\\!", timeout=20)
            elif ch == "#":
                self.shell("input", "text", "\\#", timeout=20)
            elif ch == ".":
                self.shell("input", "text", ".", timeout=20)
            elif ch == "_":
                self.shell("input", "text", "_", timeout=20)
            elif ch == "-":
                self.shell("input", "text", "-", timeout=20)
            else:
                self.shell("input", "text", self._escape_input_text(ch), timeout=20)
        if buf:
            self.shell("input", "text", "".join(buf), timeout=20)

    def input_keyevent(self, code: int) -> str:
        return self.shell("input", "keyevent", str(code), timeout=15)

    def clear_field(self, times: int = 40) -> None:
        # 快速清空：多次 DEL + 可选全选
        self.shell("input", "keyevent", "KEYCODE_MOVE_END", timeout=10)
        # 批量 DEL 减少进程开销
        batch = min(times, 20)
        self.shell("input", "keyevent", *(["67"] * batch), timeout=20)
        if times > 20:
            self.shell("input", "keyevent", *(["67"] * min(times - 20, 20)), timeout=20)

    def tap(self, x: int, y: int) -> str:
        return self.shell("input", "tap", str(x), str(y), timeout=15)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, ms: int = 300) -> str:
        return self.shell("input", "swipe", str(x1), str(y1), str(x2), str(y2), str(ms), timeout=20)

    def screencap(self, local_path: str | Path) -> bool:
        remote = "/sdcard/mumuvenmo_cap.png"
        self.shell("screencap", "-p", remote, timeout=30)
        self.pull(remote, local_path)
        return Path(local_path).exists()

    def ui_dump_xml(self) -> str:
        return self.uiautomator_dump()

    def uiautomator_dump(self, force: bool = False) -> str:
        """Dump UI hierarchy；null root 时仅 WAKEUP 重试，绝不 HOME。

        force=False 时若距上次 dump < dump_min_interval 秒则复用缓存，降低卡白风险。
        """
        import time as _t
        now = _t.time()
        if (
            not force
            and getattr(self, "_last_dump_xml", "")
            and (now - float(getattr(self, "_last_dump_ts", 0.0))) < float(getattr(self, "_dump_min_interval", 1.2))
        ):
            return self._last_dump_xml
        remote = "/sdcard/mumuvenmo_ui.xml"
        last = ""
        if not self.is_online():
            return getattr(self, "_last_dump_xml", "") or ""
        for attempt in range(2):
            out = self.shell("uiautomator", "dump", remote, timeout=15)
            last = out or ""
            low = last.lower()
            if (
                "device offline" in low
                or "not found" in low
                or "no devices" in low
                or "error: closed" in low
            ):
                return getattr(self, "_last_dump_xml", "") or last
            if "null root" in low or "ERROR" in last:
                # 更新 2026-07-24: null root 时不要 HOME，否则会把 Venmo 打到后台
                try:
                    self.shell("input", "keyevent", "224", timeout=5)  # WAKEUP
                except Exception:
                    pass
                import time as _t
                _t.sleep(0.8)
                continue
            cp = self._run(["shell", "cat", remote], timeout=12)
            xml = cp.stdout or ""
            if xml.strip().startswith("<?xml") or "<hierarchy" in xml or "<node" in xml:
                self._last_dump_xml = xml
                self._last_dump_ts = _t.time()
                return xml
            # empty file: brief wait and retry
            import time as _t
            _t.sleep(0.5)
        cp = self._run(["shell", "cat", remote], timeout=12)
        xml = cp.stdout or ""
        if xml:
            self._last_dump_xml = xml
            self._last_dump_ts = _t.time()
        return xml

    def ui_texts(self) -> list[str]:
        xml = self.uiautomator_dump()
        texts: list[str] = []
        if not xml.strip():
            return texts
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            texts = re.findall(r'text="([^"]*)"', xml)
            return [t for t in texts if t]
        for node in root.iter("node"):
            t = node.attrib.get("text") or ""
            desc = node.attrib.get("content-desc") or ""
            if t:
                texts.append(t)
            if desc and desc != t:
                texts.append(desc)
        return texts

    def ui_full_text(self) -> str:
        return "\n".join(self.ui_texts())

    def _parse_bounds(self, bounds: str) -> Optional[tuple[int, int, int, int]]:
        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds or "")
        if not m:
            return None
        return tuple(int(x) for x in m.groups())  # type: ignore

    def _is_forbidden_uninstall_target(self, text: str = "", desc: str = "", rid: str = "") -> bool:
        """绝对禁止点击 Uninstall Magisk / 卸载 Magisk。"""
        blob = f"{text} {desc} {rid}".lower()
        if "uninstall magisk" in blob:
            return True
        if "卸载 magisk" in blob or "卸载magisk" in blob:
            return True
        # 单独 Uninstall 且与 magisk 相关
        if "uninstall" in blob and "magisk" in blob:
            return True
        if "卸载" in f"{text}{desc}" and "magisk" in blob:
            return True
        return False

    def find_node_bounds(
        self,
        text_substr: str = "",
        resource_id: str = "",
        content_desc: str = "",
        clickable_only: bool = False,
        password: Optional[bool] = None,
        class_endswith: str = "",
        xml: Optional[str] = None,
        exact: bool = False,
        exclude_uninstall_magisk: bool = True,
    ) -> Optional[tuple[int, int, int, int]]:
        xml = xml if xml is not None else self.uiautomator_dump()
        if not (xml or "").strip():
            return None
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return None
        needle = (text_substr or "").lower().strip()
        rid_n = (resource_id or "").lower()
        desc_n = (content_desc or "").lower()
        for node in root.iter("node"):
            rid = (node.attrib.get("resource-id") or "")
            text = node.attrib.get("text") or ""
            desc = node.attrib.get("content-desc") or ""
            cls = node.attrib.get("class") or ""
            if exclude_uninstall_magisk and self._is_forbidden_uninstall_target(text, desc, rid):
                # 除非调用方明确要找 Uninstall 文本（仅状态检测），否则跳过
                if not (needle and ("uninstall" in needle or "卸载" in needle)):
                    continue
            if rid_n and rid_n not in rid.lower():
                continue
            if needle:
                tlow = text.lower().strip()
                dlow = desc.lower().strip()
                blob = f"{text} {desc} {rid}".lower()
                if exact:
                    if tlow != needle and dlow != needle:
                        continue
                else:
                    if needle not in blob:
                        continue
            if desc_n and desc_n not in desc.lower():
                continue
            if class_endswith and not cls.endswith(class_endswith):
                continue
            if clickable_only and node.attrib.get("clickable") != "true":
                continue
            if password is True and node.attrib.get("password") != "true":
                continue
            if password is False and node.attrib.get("password") == "true":
                continue
            b = self._parse_bounds(node.attrib.get("bounds") or "")
            if b:
                return b
        return None

    def tap_bounds(self, b: tuple[int, int, int, int]) -> None:
        x1, y1, x2, y2 = b
        self.tap((x1 + x2) // 2, (y1 + y2) // 2)

    def tap_text(self, text_substr: str, exact: bool = False) -> bool:
        """点击文本。exact=True 时精确匹配，避免 Install 误点 Uninstall Magisk。"""
        needle = (text_substr or "").strip()
        # 硬禁止：任何想点 Uninstall Magisk 的调用直接拒绝
        low = needle.lower()
        if "uninstall magisk" in low or ("uninstall" in low and "magisk" in low) or "卸载 magisk" in low:
            return False
        b = self.find_node_bounds(text_substr=text_substr, exact=exact, exclude_uninstall_magisk=True)
        if not b:
            return False
        # 二次校验：再 dump 一次太慢，直接用已解析 bounds 前的文本过滤已在 find 中完成
        self.tap_bounds(b)
        return True

    def tap_exact_text(self, text: str) -> bool:
        """精确点击 text/content-desc，绝不子串误匹配。"""
        return self.tap_text(text, exact=True)

    def tap_id(self, resource_id: str) -> bool:
        b = self.find_node_bounds(resource_id=resource_id)
        if not b:
            return False
        self.tap_bounds(b)
        return True


    def release_ui_control(self, home: bool = False) -> None:
        """释放 UIAutomator/输入占用，避免脚本控机后人工一点就白屏。

        不 force-stop 任何业务 App（尤其 NekoBox）。只清理 dump 缓存与 uiautomator 进程。
        脚本每段 UI 操作结束后应调用；账号之间/线程退出时也要调用。
        """
        self._last_dump_xml = ""
        self._last_dump_ts = 0.0
        # 结束残留 uiautomator / instrumentation 测试进程（勿杀 NekoBox）
        for cmd in (
            ["shell", "pkill", "-f", "uiautomator"],
            ["shell", "pkill", "-f", "com.android.commands.uiautomator"],
            ["shell", "pkill", "-f", "app_process.*uiautomator"],
            ["shell", "killall", "uiautomator"],
            ["shell", "am", "force-stop", "com.github.uiautomator"],
            ["shell", "am", "force-stop", "com.github.uiautomator.test"],
            ["shell", "am", "force-stop", "com.android.commands.monkey"],
        ):
            try:
                self._run(cmd, timeout=8)
            except Exception:
                pass
        # 轻量清掉可能卡住的 input 焦点占用
        try:
            self.shell("input", "keyevent", "123", timeout=5)  # KEYCODE_MOVE_END noop-ish
        except Exception:
            pass
        if home:
            try:
                self.shell("input", "keyevent", "3", timeout=8)
            except Exception:
                pass

    def package_service_alive(self) -> bool:
        """快速判断 package 服务是否还活着（高并发 hang 检测）。"""
        try:
            out = self.shell("service", "check", "package", timeout=5) or ""
        except Exception as exc:
            out = str(exc)
        low = (out or "").lower()
        if "timeout" in low or "device offline" in low or "not found" in low or "no devices" in low:
            return False
        # Service package: found
        if "found" in low and "not found" not in low:
            return True
        if "cannot find" in low or "can't find" in low or "find service: package" in low:
            return False
        # 空/未知偏保守：不直接判死，交给上层超时逻辑
        return True

    def package_installed(self, package: str) -> bool:
        """高并发下 pm path 易超时：短超时 + 少次重试 + list packages 兜底。

        package-installed-hangfix-v4:
        - 只认 package:<path> 且含包名
        - soft-fail（timeout/empty/offline/sema）少次快退，避免 6 台互堵数分钟
        - 连续超时后 service check；服务挂则立刻 False 让上层 install/heal
        - 仍不确定时用 `pm list packages <pkg>` 精确兜底，避免 Success 后假阴性
        """
        out = ""
        pkg = str(package or "").strip()
        if not pkg:
            return False

        def _path_hit(text: str) -> bool:
            for line in (text or "").splitlines():
                ls = line.strip()
                if ls.lower().startswith("package:") and pkg in ls:
                    return True
            return False

        def _soft_fail(text: str) -> bool:
            low = (text or "").lower()
            return (
                "timeout" in low
                or (text or "").strip() == ""
                or "adb_sema_timeout" in low
                or "adb_heavy_sema_timeout" in low
                or "device offline" in low
                or "not found" in low
                or "error:" in low
                or "no devices" in low
                or "can't find service: package" in low
                or "cannot find service: package" in low
                or "find service: package" in low
                or "broken pipe" in low
                or "error: closed" in low
            )

        soft_timeouts = 0
        for attempt in range(3):
            if self._cancel_requested():
                return False
            try:
                out = self.shell("pm", "path", pkg, timeout=8) or ""
            except Exception as exc:
                out = str(exc)
            if _path_hit(out):
                return True
            if _soft_fail(out):
                soft_timeouts += 1
                try:
                    low = out.lower()
                    if (
                        "device offline" in low
                        or "not found" in low
                        or "no devices" in low
                        or "find service: package" in low
                        or "broken pipe" in low
                        or soft_timeouts >= 2
                    ):
                        self.connect()
                except Exception:
                    pass
                # 连续 2 次软失败：若 package 服务挂了，立刻返回 False 促 heal/重装
                if soft_timeouts >= 2:
                    try:
                        if not self.package_service_alive():
                            return False
                    except Exception:
                        return False
                time.sleep(0.25 + 0.2 * attempt)
                continue
            break

        # list packages 兜底（高并发 pm path 空/超时假阴性）
        list_soft = 0
        for attempt in range(2):
            if self._cancel_requested():
                return False
            try:
                listed = self.shell("pm", "list", "packages", pkg, timeout=8) or ""
            except Exception as exc:
                listed = str(exc)
            for line in (listed or "").splitlines():
                ls = line.strip()
                # package:com.xxx 精确匹配，避免前缀误伤
                if ls.lower() == f"package:{pkg}".lower() or ls.lower().startswith(f"package:{pkg.lower()}="):
                    return True
                if ls.lower() == f"package:{pkg}".lower():
                    return True
            low = (listed or "").lower()
            needle = f"package:{pkg.lower()}"
            # 整词行匹配
            for line in (listed or "").splitlines():
                if line.strip().lower() == needle:
                    return True
            if _soft_fail(listed):
                list_soft += 1
                try:
                    if "device offline" in low or "not found" in low or list_soft >= 1:
                        self.connect()
                except Exception:
                    pass
                if list_soft >= 1:
                    try:
                        if not self.package_service_alive():
                            return False
                    except Exception:
                        return False
                time.sleep(0.3 + 0.2 * attempt)
                continue
            break
        return False

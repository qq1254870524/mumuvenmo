# -*- coding: utf-8 -*-
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"C:\Users\zhang\Desktop\mumuvenmo")

# ===================== root_setup.py: prefer GRANT popup =====================
rs_path = ROOT / "core" / "root_setup.py"
rs = rs_path.read_text(encoding="utf-8")
if "shell-grant-popup-first-v1" not in rs:
    rs = (
        "# 2026-07-25 shell-grant-popup-first-v1: Shell授权优先点GRANT弹窗(Remember forever+Allow)，Superuser开关仅兜底\n"
        + rs
    )

# Improve grant_shell_superuser: if popup grant succeeds with uid=0, skip Superuser page
old_gss = '''    def grant_shell_superuser(self, log: LogFn = None) -> str:
        """永久放行 adb shell 的 Magisk su。

        优先：
        1) UI 识别文字点 Grant（[SharedUID] Shell 弹窗）
        2) 打开 Kitsune Mask -> Superuser 给 Shell 永久 Allow
        3) magisk.db / sqlite 写入 policies
        """
        outs: list[str] = []
        # 1) 弹窗文字 Grant
        try:
            for _ in range(4):
                hit = self.adb.dismiss_magisk_su_dialog()
                if hit:
                    outs.append(f"tap={hit}")
                    self._log(log, f"SharedUID Shell auto-tap: {hit}")
                    if "grant" in hit.lower() or "允许" in hit or "同意" in hit:
                        break
                time.sleep(0.25)
        except Exception as exc:
            outs.append(f"tap_err={exc}")

        # 2) Kitsune Superuser 页授权（用户指定路径，可靠）
        try:
            ui_ok = self.grant_shell_via_kitsune_superuser(log=log)
            outs.append(f"superuser_ui={ui_ok}")
            self._log(log, f"Kitsune Superuser 授权: {ui_ok}")
        except Exception as exc:
            outs.append(f"superuser_ui_err={exc}")
            self._log(log, f"Kitsune Superuser 授权失败: {exc}")
'''

new_gss = '''    def grant_shell_prefer_popup(self, log: LogFn = None) -> str:
        """优先用 [SharedUID] Shell GRANT 弹窗授权（Remember forever → Allow/Grant）。

        不打开 Superuser 页。成功判据：su probe 含 uid=0，或明确 forever+allow/grant。
        """
        outs: list[str] = []
        # 清掉已有弹窗
        try:
            for _ in range(3):
                hit = self.adb.dismiss_magisk_su_dialog()
                if hit:
                    outs.append(f"pre={hit}")
                    self._log(log, f"SharedUID Shell GRANT弹窗: {hit}")
                else:
                    break
                time.sleep(0.15)
        except Exception as exc:
            outs.append(f"pre_err={exc}")

        # 触发 su，内部会并发点 Remember forever + Allow/Grant
        probe = ""
        try:
            probe = self.adb.shell_su("id", timeout=16) or ""
            outs.append(f"probe={(probe or '').strip()[:100]}")
            self._log(log, f"Shell GRANT 触发su probe: {(probe or '')[:120]}")
        except Exception as exc:
            outs.append(f"probe_err={exc}")
            self._log(log, f"Shell GRANT 触发su失败: {exc}")

        # 再扫一次残留弹窗
        try:
            hit2 = self.adb.dismiss_magisk_su_dialog()
            if hit2:
                outs.append(f"post={hit2}")
                self._log(log, f"SharedUID Shell GRANT弹窗(post): {hit2}")
                # 再 probe 一次
                try:
                    probe = self.adb.shell_su("id", timeout=12) or probe
                    outs.append(f"probe2={(probe or '').strip()[:80]}")
                except Exception:
                    pass
        except Exception:
            pass

        low = " | ".join(outs).lower()
        ok = ("uid=0" in (probe or "")) or (
            ("forever" in low or "remember" in low)
            and any(k in low for k in ("grant", "allow", "允许", "同意"))
        )
        tag = "popup_grant_ok" if ok else "popup_grant_incomplete"
        return f"{tag}|{'|'.join(outs)}"[:420]

    def grant_shell_superuser(self, log: LogFn = None) -> str:
        """永久放行 adb shell 的 Magisk su。

        优先：
        1) UI 识别文字点 Grant（[SharedUID] Shell 弹窗）——主路径
        2) 仅弹窗失败时：打开 Kitsune Mask -> Superuser 右侧开关
        3) magisk.db / sqlite 写入 policies
        """
        outs: list[str] = []
        # 1) 弹窗 Grant（主路径）
        popup_ok = False
        try:
            popup = self.grant_shell_prefer_popup(log=log)
            outs.append(f"popup={popup}")
            popup_ok = str(popup).startswith("popup_grant_ok") or "uid=0" in str(popup)
            self._log(log, f"Shell授权优先GRANT弹窗: {popup[:160]}")
        except Exception as exc:
            outs.append(f"popup_err={exc}")
            self._log(log, f"Shell GRANT弹窗失败: {exc}")

        # 2) 仅弹窗未确认时才进 Superuser 页（兜底）
        if not popup_ok:
            try:
                ui_ok = self.grant_shell_via_kitsune_superuser(log=log)
                outs.append(f"superuser_ui={ui_ok}")
                self._log(log, f"Kitsune Superuser 兜底授权: {ui_ok}")
            except Exception as exc:
                outs.append(f"superuser_ui_err={exc}")
                self._log(log, f"Kitsune Superuser 授权失败: {exc}")
        else:
            outs.append("superuser_ui=skipped_popup_ok")
            self._log(log, "Shell GRANT弹窗已成功，跳过 Superuser 页")
'''

if old_gss not in rs:
    print("WARN: grant_shell_superuser block not exact match")
else:
    rs = rs.replace(old_gss, new_gss, 1)
    print("patched grant_shell_superuser")

# complete_kitsune_post_install_session: popup first
old_sess = '''        try:
            g = self.grant_shell_via_kitsune_superuser(log=log, reuse_session=True)
            out["grant"] = g
            notes.append("grant_ok")
            self._log(log, f"VM={vmindex} 一次会话 Shell 授权: {str(g)[:160]}")
        except Exception as exc:
            out["grant"] = f"err={exc}"
            notes.append(f"grant_err={exc}")
            self._log(log, f"VM={vmindex} 一次会话 Shell 授权失败: {exc}")
'''

new_sess = '''        try:
            # 主路径：触发 su + 点 [SharedUID] Shell 的 GRANT/Allow（Remember forever）
            popup = self.grant_shell_prefer_popup(log=log)
            out["grant"] = popup
            popup_ok = str(popup).startswith("popup_grant_ok") or "uid=0" in str(popup)
            if popup_ok:
                notes.append("grant_popup_ok")
                self._log(log, f"VM={vmindex} 一次会话 Shell GRANT弹窗成功: {str(popup)[:160]}")
            else:
                notes.append("grant_popup_incomplete")
                self._log(log, f"VM={vmindex} 一次会话 Shell GRANT弹窗未确认，改 Superuser 兜底: {str(popup)[:160]}")
                # 兜底：Superuser 页右侧开关（不强制，仅弹窗失败时）
                g = self.grant_shell_via_kitsune_superuser(log=log, reuse_session=True)
                out["grant"] = f"{popup}||superuser={g}"
                notes.append("grant_superuser_fallback")
                self._log(log, f"VM={vmindex} 一次会话 Shell Superuser兜底: {str(g)[:160]}")
        except Exception as exc:
            out["grant"] = f"err={exc}"
            notes.append(f"grant_err={exc}")
            self._log(log, f"VM={vmindex} 一次会话 Shell 授权失败: {exc}")
'''

if old_sess not in rs:
    print("WARN: complete_kitsune session grant block not found")
else:
    rs = rs.replace(old_sess, new_sess, 1)
    print("patched complete_kitsune_post_install_session grant")

rs_path.write_text(rs, encoding="utf-8")

# ===================== mumu_manager.py layout boot win32 =====================
mm_path = ROOT / "core" / "mumu_manager.py"
mm = mm_path.read_text(encoding="utf-8")
if "layout-boot-win32-v1" not in mm:
    mm = (
        "# 2026-07-25 layout-boot-win32-v1: 启动后立即一字排列；纯Win32定位(不占MuMuManager锁)；窗口标题强制序号\n"
        + mm
    )

HELPER = '''
    def _parse_hwnd_value(self, v) -> int:
        s = str(v or "").strip()
        if not s:
            return 0
        try:
            if s.lower().startswith("0x") or any(c in s.lower() for c in "abcdef"):
                return int(s, 16)
            return int(s, 0)
        except Exception:
            try:
                return int(s, 16)
            except Exception:
                return 0

    def _enum_windows_by_titles(self, titles: set[str]) -> dict[str, int]:
        """返回 title->hwnd（可见大窗口）。不调用 MuMuManager。"""
        out: dict[str, int] = {}
        want = {str(t).strip() for t in titles if str(t).strip()}
        if not want:
            return out
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            EnumWindows = user32.EnumWindows
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            GetWindowTextW = user32.GetWindowTextW
            GetWindowTextLengthW = user32.GetWindowTextLengthW
            IsWindowVisible = user32.IsWindowVisible
            GetWindowRect = user32.GetWindowRect

            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long),
                ]

            found: dict[str, int] = {}

            @EnumWindowsProc
            def _cb(hwnd, lParam):
                try:
                    if not IsWindowVisible(hwnd):
                        return True
                    n = GetWindowTextLengthW(hwnd)
                    if n <= 0:
                        return True
                    buf = ctypes.create_unicode_buffer(n + 1)
                    GetWindowTextW(hwnd, buf, n + 1)
                    title = (buf.value or "").strip()
                    if title not in want:
                        return True
                    r = RECT()
                    if not GetWindowRect(hwnd, ctypes.byref(r)):
                        return True
                    w = int(r.right - r.left)
                    h = int(r.bottom - r.top)
                    if w < 80 or h < 80:
                        return True
                    old = found.get(title)
                    if old:
                        r2 = RECT()
                        GetWindowRect(old, ctypes.byref(r2))
                        area_old = max(0, r2.right - r2.left) * max(0, r2.bottom - r2.top)
                        if w * h < area_old:
                            return True
                    found[title] = int(hwnd)
                except Exception:
                    return True
                return True

            EnumWindows(_cb, 0)
            out = found
        except Exception:
            return {}
        return out

    def resolve_main_hwnd(self, vmindex: int | str, *, lock_timeout: float = 0.25) -> int:
        """解析模拟器主窗口 hwnd。优先标题匹配，其次短等 manager info。"""
        idx = int(vmindex)
        titles = {
            str(idx),
            f"Android Device-{idx}",
            f"Android Device - {idx}",
            f"AndroidDevice-{idx}",
        }
        by_title = self._enum_windows_by_titles(titles)
        for t in (str(idx), f"Android Device-{idx}", f"Android Device - {idx}", f"AndroidDevice-{idx}"):
            if t in by_title:
                return int(by_title[t])

        info = None
        got_lock = False
        try:
            got_lock = self._manager_lock.acquire(timeout=max(0.0, float(lock_timeout)))
            if got_lock:
                try:
                    info = self.info(idx) or {}
                except Exception:
                    info = None
        except Exception:
            info = None
        finally:
            if got_lock:
                try:
                    self._manager_lock.release()
                except Exception:
                    pass
        if isinstance(info, dict):
            hwnd = self._parse_hwnd_value(info.get("main_wnd"))
            if hwnd:
                return hwnd
        return 0

    def set_player_window_title(self, vmindex: int | str, title: str | None = None) -> bool:
        """强制主窗口标题为序号数字，避免残留 Android Device-N。"""
        idx = int(vmindex)
        name = str(title if title is not None else idx)
        hwnd = self.resolve_main_hwnd(idx, lock_timeout=0.2)
        if not hwnd:
            return False
        try:
            import ctypes
            return bool(ctypes.windll.user32.SetWindowTextW(hwnd, name))
        except Exception:
            return False

    def measure_player_window_win32(self, vmindex: int, *, hwnd: int | None = None) -> dict[str, int]:
        """纯 Win32 测 main 窗口；不调用 MuMuManager。"""
        out: dict[str, int] = {}
        try:
            import ctypes

            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long),
                ]

            user32 = ctypes.windll.user32
            hwin = int(hwnd or 0) or self.resolve_main_hwnd(int(vmindex), lock_timeout=0.05)
            if not hwin:
                return out
            r = RECT()
            if not user32.GetWindowRect(hwin, ctypes.byref(r)):
                return out
            left, top, right, bottom = int(r.left), int(r.top), int(r.right), int(r.bottom)
            out["main_left"], out["main_top"], out["main_right"], out["main_bottom"] = left, top, right, bottom
            out["outer_w"] = max(0, right - left)
            out["outer_h"] = max(0, bottom - top)
            est_il, est_it, est_ir, est_ib = 0, 32, 0, 0
            out["inset_left"] = est_il
            out["inset_top"] = est_it
            out["inset_right"] = est_ir
            out["inset_bottom"] = est_ib
            out["render_left"] = left + est_il
            out["render_top"] = top + est_it
            out["render_right"] = right - est_ir
            out["render_bottom"] = bottom - est_ib
            out["render_w"] = max(0, out["render_right"] - out["render_left"])
            out["render_h"] = max(0, out["render_bottom"] - out["render_top"])
            out["chrome_w"] = max(0, out["outer_w"] - out["render_w"])
            out["chrome_h"] = max(0, out["outer_h"] - out["render_h"])
        except Exception:
            return out
        return out

'''

if "def resolve_main_hwnd" not in mm:
    anchor = "    def measure_player_window(self, vmindex: int) -> dict[str, int]:"
    if anchor not in mm:
        raise SystemExit("measure_player_window missing")
    mm = mm.replace(anchor, HELPER + anchor, 1)
    print("added hwnd helpers")
else:
    print("hwnd helpers already present")

# replace _set_main_window_rect
old_set = '''    def _set_main_window_rect(self, vmindex: int, x: int, y: int, w: int, h: int) -> bool:
        """用 Win32 精确定位 main 窗口（layout_window 后再校准，去缝隙）。"""
        try:
            info = self.info(int(vmindex)) or {}
        except Exception:
            info = {}
        if not isinstance(info, dict):
            return False
        raw = str(info.get("main_wnd") or "").strip()
        if not raw:
            return False
        try:
            hwnd = (
                int(raw, 16)
                if raw.lower().startswith("0x") or any(c in raw.lower() for c in "abcdef")
                else int(raw, 0)
            )
        except Exception:
            try:
                hwnd = int(raw, 16)
            except Exception:
                return False
        if not hwnd:
            return False
        try:
            import ctypes

            user32 = ctypes.windll.user32
            # SWP_NOZORDER | SWP_NOACTIVATE
            flags = 0x0004 | 0x0010
            ok = user32.SetWindowPos(hwnd, 0, int(x), int(y), int(w), int(h), flags)
            return bool(ok)
        except Exception as exc:
            logger.warning("SetWindowPos VM=%s failed: %s", vmindex, exc)
            return False
'''

new_set = '''    def _set_main_window_rect(
        self,
        vmindex: int,
        x: int,
        y: int,
        w: int,
        h: int,
        *,
        hwnd: int | None = None,
        title: str | None = None,
    ) -> bool:
        """用 Win32 精确定位 main 窗口（不依赖 MuMu layout_window，避免 manager 锁阻塞）。"""
        hwin = int(hwnd or 0)
        if not hwin:
            hwin = self.resolve_main_hwnd(int(vmindex), lock_timeout=0.2)
        if not hwin:
            return False
        try:
            import ctypes

            user32 = ctypes.windll.user32
            flags = 0x0004 | 0x0010  # SWP_NOZORDER | SWP_NOACTIVATE
            ok = user32.SetWindowPos(hwin, 0, int(x), int(y), int(w), int(h), flags)
            t = str(title if title is not None else int(vmindex))
            try:
                user32.SetWindowTextW(hwin, t)
            except Exception:
                pass
            return bool(ok)
        except Exception as exc:
            logger.warning("SetWindowPos VM=%s failed: %s", vmindex, exc)
            return False
'''

if old_set in mm:
    mm = mm.replace(old_set, new_set, 1)
    print("patched _set_main_window_rect")
elif "hwnd: int | None = None" in mm and "def _set_main_window_rect" in mm:
    print("_set_main_window_rect already patched")
else:
    print("WARN: _set_main_window_rect not patched")

# Replace layout_row_from_top_left function entirely
lines = mm.splitlines(keepends=True)
start = end = None
for i, line in enumerate(lines):
    if line.startswith("    def layout_row_from_top_left("):
        start = i
        continue
    if start is not None and i > start and line.startswith("    def "):
        end = i
        break
if start is None or end is None:
    raise SystemExit(f"layout_row bounds missing {start} {end}")

new_layout = '''    def layout_row_from_top_left(
        self,
        indices: list[int],
        width: int | None = None,
        height: int | None = None,
        margin: int = 0,
        start_x: int = 0,
        start_y: int = 0,
        *,
        auto_fit: bool = True,
        aspect_w: float = 9.0,
        aspect_h: float = 16.0,
        screen_w: int | None = None,
        screen_h: int | None = None,
    ) -> dict[str, Any]:
        """从电脑左上角一字排列：纯 Win32 贴紧，不占用 MuMuManager 锁。

        启动后即可排列（装包期间也能排）。窗口标题同步为序号数字。
        """
        import time

        ids = [int(i) for i in (indices or [])]
        if not ids:
            return {"count": 0, "width": 0, "height": 0, "margin": int(margin)}

        if screen_w is None or screen_h is None:
            sw, sh = self.get_primary_screen_size()
            screen_w = screen_w or sw
            screen_h = screen_h or sh

        use_auto = bool(auto_fit) or width is None or height is None
        est_chrome_w = 8
        est_chrome_h = 40
        chrome_w = est_chrome_w
        chrome_h = est_chrome_h
        inset_left = 0
        inset_top = 0

        if use_auto:
            width, height = self.calc_tight_row_cell(
                len(ids),
                aspect_w=aspect_w,
                aspect_h=aspect_h,
                screen_w=screen_w,
                screen_h=screen_h,
                start_x=start_x,
                start_y=start_y,
                chrome_w=chrome_w,
                chrome_h=chrome_h,
            )
        else:
            width = int(width or 480)
            height = int(height or 860)

        hwnds: dict[int, int] = {}
        for idx in ids:
            h = self.resolve_main_hwnd(idx, lock_timeout=0.15)
            if h:
                hwnds[idx] = h
                try:
                    import ctypes
                    ctypes.windll.user32.SetWindowTextW(h, str(idx))
                except Exception:
                    pass

        render_w = max(100, int(width) - int(chrome_w))
        step_x = render_w if use_auto else (int(width) + int(margin))
        placed = 0
        for i, idx in enumerate(ids):
            mx = int(start_x) + i * int(step_x) - int(inset_left)
            my = int(start_y)
            ok = self._set_main_window_rect(
                idx, mx, my, int(width), int(height), hwnd=hwnds.get(idx), title=str(idx)
            )
            if ok:
                placed += 1
        time.sleep(0.12)

        for idx in ids:
            m = self.measure_player_window_win32(idx, hwnd=hwnds.get(idx))
            if m.get("chrome_w") is not None:
                chrome_w = max(int(chrome_w), int(m.get("chrome_w") or 0))
            if m.get("chrome_h") is not None:
                chrome_h = max(int(chrome_h), int(m.get("chrome_h") or 0))
            if m.get("inset_left") is not None:
                inset_left = int(m.get("inset_left") or 0)
            if m.get("inset_top") is not None:
                inset_top = int(m.get("inset_top") or 0)
            if m.get("outer_w"):
                width = int(m.get("outer_w") or width)
            if m.get("outer_h"):
                height = int(m.get("outer_h") or height)

        if use_auto:
            width, height = self.calc_tight_row_cell(
                len(ids),
                aspect_w=aspect_w,
                aspect_h=aspect_h,
                screen_w=screen_w,
                screen_h=screen_h,
                start_x=start_x,
                start_y=start_y,
                chrome_w=chrome_w,
                chrome_h=chrome_h,
            )
            render_w = max(100, int(width) - int(chrome_w))
            step_x = render_w
            for i, idx in enumerate(ids):
                target_rl = int(start_x) + i * int(step_x)
                mx = target_rl - int(inset_left)
                my = int(start_y)
                self._set_main_window_rect(
                    idx, mx, my, int(width), int(height), hwnd=hwnds.get(idx), title=str(idx)
                )
            time.sleep(0.1)

            measures2 = [self.measure_player_window_win32(idx, hwnd=hwnds.get(idx)) for idx in ids]
            gaps = []
            for i in range(len(measures2) - 1):
                a = measures2[i]
                b = measures2[i + 1]
                if a.get("render_right") is not None and b.get("render_left") is not None:
                    gaps.append(int(b["render_left"]) - int(a["render_right"]))
            if gaps:
                gap = sorted(gaps)[len(gaps) // 2]
                if abs(gap) >= 1:
                    step_x = max(100, int(step_x) + int(gap))
                    for i, idx in enumerate(ids):
                        target_rl = int(start_x) + i * int(step_x)
                        m = measures2[i] if i < len(measures2) else {}
                        il = int(m.get("inset_left") or inset_left or 0)
                        ow = int(m.get("outer_w") or width)
                        oh = int(m.get("outer_h") or height)
                        self._set_main_window_rect(
                            idx,
                            target_rl - il,
                            int(start_y),
                            ow,
                            oh,
                            hwnd=hwnds.get(idx),
                            title=str(idx),
                        )

        return {
            "count": len(ids),
            "placed": int(placed),
            "indices": ids,
            "width": int(width),
            "height": int(height),
            "margin": 0 if use_auto else int(margin),
            "step_x": int(step_x),
            "chrome_w": int(chrome_w),
            "chrome_h": int(chrome_h),
            "inset_left": int(inset_left),
            "inset_top": int(inset_top),
            "start_x": int(start_x),
            "start_y": int(start_y),
            "auto_fit": bool(use_auto),
            "tile": "win32_no_manager_lock",
        }

'''
lines = lines[:start] + [new_layout if new_layout.endswith("\n") else new_layout + "\n"] + lines[end:]
mm = "".join(lines)
print("replaced layout_row_from_top_left")

# create_and_launch title after boot
old_one = '''        def _one(idx: int) -> tuple[int, bool]:
            ok = self.launch_and_wait(
                idx,
                timeout=boot_timeout,
                defaults=defaults,
                log=log,
                ensure_settings=True,
            )
            return idx, ok
'''
new_one = '''        def _one(idx: int) -> tuple[int, bool]:
            ok = self.launch_and_wait(
                idx,
                timeout=boot_timeout,
                defaults=defaults,
                log=log,
                ensure_settings=True,
            )
            try:
                self.ensure_index_player_name(idx, str(int(idx)), retries=2, delay=0.2, log=log)
            except Exception as exc:
                self._log(log, f"VM={idx} 启动后写序号名失败: {exc}")
            try:
                self.set_player_window_title(idx, str(int(idx)))
            except Exception:
                pass
            return idx, ok
'''
if old_one in mm:
    mm = mm.replace(old_one, new_one, 1)
    print("patched create_and_launch _one")
else:
    print("create_and_launch _one already patched or missing")

mm_path.write_text(mm, encoding="utf-8")

# ===================== app_ui immediate layout =====================
ui_path = ROOT / "app_ui.py"
ui = ui_path.read_text(encoding="utf-8")
if "layout-boot-immediate-v1" not in ui:
    ui = "# 2026-07-25 layout-boot-immediate-v1: 新建启动成功后立刻一字排列，不等待装包结束\n" + ui

old_ui = '''            result = self.mumu.create_and_launch(
                number=n,
                defaults=defaults,
                name_prefix="venmo",
                launch_workers=workers,
                boot_timeout=boot_timeout,
                log=self._log,
            )
            self._log(f"新建并启动结果: {result}")
            new_ids = result.get("new_ids") or []
            boot = result.get("boot") or {}
            # 新建后按勾选并行装包：Kitsune/Zygisk/ih8/NekoBox/Aurora/Venmo
'''
new_ui = '''            result = self.mumu.create_and_launch(
                number=n,
                defaults=defaults,
                name_prefix="venmo",
                launch_workers=workers,
                boot_timeout=boot_timeout,
                log=self._log,
            )
            self._log(f"新建并启动结果: {result}")
            new_ids = result.get("new_ids") or []
            boot = result.get("boot") or {}
            # 启动完成后立刻一字排列 + 强制序号名（不等待装包）
            if new_ids:
                for idx in new_ids:
                    try:
                        self.mumu.ensure_index_player_name(
                            int(idx), str(int(idx)), retries=2, delay=0.15, log=self._log
                        )
                        self.mumu.set_player_window_title(int(idx), str(int(idx)))
                    except Exception as exc:
                        self._log(f"VM={idx} 序号名/标题加固失败: {exc}")
                if self.var_sort.get():
                    try:
                        booted = [int(i) for i in new_ids if boot.get(i, True)]
                        layout = self.mumu.layout_row_from_top_left(
                            booted or [int(i) for i in new_ids],
                            auto_fit=bool(self.cfg.get("window_auto_fit", True)),
                            margin=0 if bool(self.cfg.get("window_auto_fit", True)) else int(self.cfg.get("window_margin", 0) or 0),
                        )
                        self._log(
                            "启动后立即一字排列: "
                            f"count={layout.get('count')} placed={layout.get('placed')} "
                            f"step={layout.get('step_x')} size={layout.get('width')}x{layout.get('height')} "
                            f"tile={layout.get('tile')}"
                        )
                    except Exception as exc:
                        self._log(f"启动后排列警告: {exc}")
            # 新建后按勾选并行装包：Kitsune/Zygisk/ih8/NekoBox/Aurora/Venmo
'''
if old_ui in ui:
    ui = ui.replace(old_ui, new_ui, 1)
    print("patched app_ui immediate layout")
else:
    print("WARN: app_ui create block not found / already patched")

old_after = '''            if new_ids:
                cur = self.var_vms.get().strip()
                add = ",".join(str(i) for i in new_ids)

                def _set() -> None:
                    self.var_vms.set(f"{cur},{add}".strip(",") if cur else add)
                    if self.var_sort.get():
                        try:
                            self.mumu.layout_row_from_top_left(
                                list(new_ids),
                                auto_fit=bool(self.cfg.get("window_auto_fit", True)),
                                margin=0 if bool(self.cfg.get("window_auto_fit", True)) else int(self.cfg.get("window_margin", 0) or 0),
                            )
                        except Exception as exc:
                            self._log(f"排列警告: {exc}")
                    try:
                        self.refresh_vms()
                    except Exception:
                        pass

                self.after(0, _set)
'''
new_after = '''            if new_ids:
                if self.var_sort.get():
                    try:
                        layout2 = self.mumu.layout_row_from_top_left(
                            [int(i) for i in new_ids],
                            auto_fit=bool(self.cfg.get("window_auto_fit", True)),
                            margin=0 if bool(self.cfg.get("window_auto_fit", True)) else int(self.cfg.get("window_margin", 0) or 0),
                        )
                        self._log(
                            "装包后再次一字排列: "
                            f"count={layout2.get('count')} placed={layout2.get('placed')} "
                            f"step={layout2.get('step_x')} tile={layout2.get('tile')}"
                        )
                    except Exception as exc:
                        self._log(f"装包后排列警告: {exc}")
                cur = self.var_vms.get().strip()
                add = ",".join(str(i) for i in new_ids)

                def _set() -> None:
                    self.var_vms.set(f"{cur},{add}".strip(",") if cur else add)
                    try:
                        self.refresh_vms()
                    except Exception:
                        pass

                self.after(0, _set)
'''
if old_after in ui:
    ui = ui.replace(old_after, new_after, 1)
    print("patched app_ui post-provision layout")
else:
    print("WARN: app_ui after provision block not found / already patched")

ui_path.write_text(ui, encoding="utf-8")

import py_compile
for p in (rs_path, mm_path, ui_path):
    py_compile.compile(str(p), doraise=True)
    print("compile OK", p.name)
print("ALL DONE")

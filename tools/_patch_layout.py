from pathlib import Path

p = Path("core/mumu_manager.py")
text = p.read_text(encoding="utf-8")

old_h = "# 2026-07-25 layout-render-tile-v1: 按 render 区贴紧排列，消除窗口装饰造成的缝隙/黑边"
new_h = "# 2026-07-25 layout-render-tile-v2: render 实测贴紧+Win32精确定位，消除黑边与缝隙\n" + old_h
if "layout-render-tile-v2" not in text:
    text = text.replace(old_h, new_h, 1)

start = text.find("    def layout_row_from_top_left(")
end = text.find("\n    def ", start + 10)
assert start > 0 and end > start, (start, end)

new_fn = r'''
    def _set_main_window_rect(self, vmindex: int, x: int, y: int, w: int, h: int) -> bool:
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

    def layout_row_from_top_left(
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
        """从电脑左上角一字排列：render 区贴紧、无缝隙、竖屏 9:16 减黑边。

        流程：
        1) 按屏幕/数量算 outer 尺寸（9:16 render）
        2) MuMu layout_window 粗排
        3) 实测 main/render 装饰
        4) 按 render 宽度步进 + Win32 SetWindowPos 精确定位（允许 chrome 重叠）
        5) 再测相邻 render 间隙并修正到 0
        """
        ids = [int(i) for i in (indices or [])]
        if not ids:
            return {"count": 0, "width": 0, "height": 0, "margin": int(margin)}

        if screen_w is None or screen_h is None:
            sw, sh = self.get_primary_screen_size()
            screen_w = screen_w or sw
            screen_h = screen_h or sh

        use_auto = bool(auto_fit) or width is None or height is None
        chrome_w = 0
        chrome_h = 0
        inset_left = 0
        inset_top = 0
        # MuMu 经验装饰：侧边约 0~16，标题栏约 32~48
        est_chrome_w = 16
        est_chrome_h = 40
        if use_auto:
            width, height = self.calc_tight_row_cell(
                len(ids),
                aspect_w=aspect_w,
                aspect_h=aspect_h,
                screen_w=screen_w,
                screen_h=screen_h,
                start_x=start_x,
                start_y=start_y,
                chrome_w=est_chrome_w,
                chrome_h=est_chrome_h,
            )
            margin = 0
        else:
            width = max(120, int(width or 360))
            height = max(200, int(height or 640))
            margin = max(0, int(margin))

        def _apply_mumu(step_x: int, w: int, h: int) -> None:
            x = int(start_x)
            y = int(start_y)
            for idx in ids:
                try:
                    self.layout_window(idx, x, y, int(w), int(h))
                except Exception as exc:
                    logger.warning("layout_window VM=%s failed: %s", idx, exc)
                x += int(step_x) + int(margin)

        def _apply_precise(step_x: int, w: int, h: int, base_main_x: int, base_main_y: int) -> None:
            x = int(base_main_x)
            y = int(base_main_y)
            for idx in ids:
                try:
                    self.layout_window(idx, x, y, int(w), int(h))
                except Exception as exc:
                    logger.warning("layout_window VM=%s failed: %s", idx, exc)
                self._set_main_window_rect(idx, x, y, int(w), int(h))
                x += int(step_x) + int(margin)

        # 第一遍：render 步进粗排
        step_x = int(width) + int(margin)
        if use_auto:
            step_x = max(120, int(width) - est_chrome_w)
        _apply_mumu(step_x if use_auto else int(width) + int(margin), int(width), int(height))
        time.sleep(0.30)

        measures = [self.measure_player_window(idx) for idx in ids]
        good = [m for m in measures if m.get("render_w") and m.get("outer_w")]
        if use_auto and good:
            def _med(key: str, default: int) -> int:
                vals = sorted(int(m[key]) for m in good if m.get(key) is not None)
                if not vals:
                    return default
                return vals[len(vals) // 2]

            chrome_w = _med("chrome_w", est_chrome_w)
            chrome_h = _med("chrome_h", est_chrome_h)
            inset_left = max(0, _med("inset_left", 0))
            inset_top = max(0, _med("inset_top", 0))
            if chrome_w < 0 or chrome_w > 160:
                chrome_w = est_chrome_w
            if chrome_h < 0 or chrome_h > 200:
                chrome_h = est_chrome_h

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
            render_w = max(120, int(width) - int(chrome_w))
            render_h = max(200, int(height) - int(chrome_h))
            # 强制 render 9:16，减少内容区黑边
            want_h = int(round(render_w * float(aspect_h) / float(aspect_w)))
            if abs(want_h - render_h) > 2:
                render_h = want_h
                height = render_h + int(chrome_h)
            step_x = render_w
            base_main_x = int(start_x) - int(inset_left)
            base_main_y = int(start_y)
            _apply_precise(step_x, int(width), int(height), base_main_x, base_main_y)
            time.sleep(0.18)

            # 第三遍：按实测相邻 render 间隙修正
            measures2 = [self.measure_player_window(idx) for idx in ids]
            gaps = []
            for i in range(len(measures2) - 1):
                a = measures2[i]
                b = measures2[i + 1]
                if a.get("render_right") is not None and b.get("render_left") is not None:
                    gaps.append(int(b["render_left"]) - int(a["render_right"]))
            gap = 0
            if gaps:
                gaps_sorted = sorted(gaps)
                gap = gaps_sorted[len(gaps_sorted) // 2]
            if abs(gap) >= 1:
                step_x = max(100, int(step_x) + int(gap))
                m0 = measures2[0] if measures2 else {}
                if m0.get("outer_w"):
                    width = int(m0["outer_w"])
                if m0.get("outer_h"):
                    height = int(m0["outer_h"])
                if m0.get("inset_left") is not None:
                    inset_left = max(0, int(m0["inset_left"]))
                base_main_x = int(start_x) - int(inset_left)
                _apply_precise(step_x, int(width), int(height), base_main_x, int(start_y))
                time.sleep(0.12)

            # 最终：逐窗按目标 render 左缘钉死
            for i, idx in enumerate(ids):
                target_rl = int(start_x) + i * int(step_x)
                m = self.measure_player_window(idx)
                il = int(m.get("inset_left") or inset_left or 0)
                ow = int(m.get("outer_w") or width)
                oh = int(m.get("outer_h") or height)
                mx = target_rl - il
                my = int(start_y)
                try:
                    self.layout_window(idx, mx, my, ow, oh)
                except Exception:
                    pass
                self._set_main_window_rect(idx, mx, my, ow, oh)
        elif not use_auto:
            _apply_mumu(int(width) + int(margin), int(width), int(height))

        return {
            "count": len(ids),
            "indices": ids,
            "width": int(width),
            "height": int(height),
            "margin": 0 if use_auto else int(margin),
            "step_x": int(step_x),
            "chrome_w": int(chrome_w or (est_chrome_w if use_auto else 0)),
            "chrome_h": int(chrome_h or (est_chrome_h if use_auto else 0)),
            "inset_left": int(inset_left),
            "inset_top": int(inset_top),
            "start_x": int(start_x),
            "start_y": int(start_y),
            "auto_fit": bool(use_auto),
            "tile": "render_win32",
        }

'''.lstrip("\n")

# keep leading 4-space indent of class method: new_fn already has 4 spaces
text = text[:start] + new_fn + text[end:]
p.write_text(text, encoding="utf-8")
print("layout ok", len(text.splitlines()))

from pathlib import Path
p = Path(r"C:\Users\zhang\Desktop\mumuvenmo\app_ui.py")
t = p.read_text(encoding="utf-8")
old = '''        self.title("MuMu Venmo 登录器")
        # 默认更大窗口，避免右侧按钮/文字被挡；可再手动拉大
        try:
            sw = int(self.winfo_screenwidth() or 1920)
            sh = int(self.winfo_screenheight() or 1080)
        except Exception:
            sw, sh = 1920, 1080
        win_w = min(max(1480, int(sw * 0.82)), max(1200, sw - 40))
        win_h = min(max(860, int(sh * 0.82)), max(720, sh - 60))
        self.geometry(f"{win_w}x{win_h}+20+20")
        self.minsize(1280, 720)
'''
new = '''        self.title("MuMu Venmo 登录器")
        # 窗口恢复上一次大小；排版仍用两行，避免右侧按钮被挡
        self.geometry("1080x700")
        self.minsize(880, 560)
'''
if old not in t:
    raise SystemExit("geometry block not found")
t = t.replace(old, new, 1)
t = t.replace(
    "# 2026-07-25 gui-window-larger-v1: 默认窗口加大；参数/操作按钮拆两行，右侧四字按钮不再被挡住\n",
    "# 2026-07-25 gui-layout-two-row-v2: 窗口恢复1080x700；参数/操作按钮仍两行完整显示\n",
    1,
)
p.write_text(t, encoding="utf-8")
print("ok")
print("geo1080", 'self.geometry("1080x700")' in t)
print("row3b", "row3b" in t)
print("minsize880", "minsize(880, 560)" in t)

# 2026-08-12 adb-flow-control-v1: 允许8台全部多开；启动逐台、ADB命令2路、登录工作流3路，避免请求风暴
# 2026-08-12 proxy-reuse-autoassign-v1: 代理可自动均衡复用；4套代理可供8个Worker使用
# 2026-08-12 staged-start-4plus4-v1: GUI 增加启动批次；8 台默认 4+4 有序放行，限制ADB启动拥堵
# 2026-08-12 graceful-stop-v1: 第一次停止等待当前账号完成后关机；第二次才强制取消；停止回调前不提前恢复空闲
# 2026-08-12 gui-live-vm-status-v1: 登录运行中每秒按实际可见 MuMu 窗口/当前账号/启动任务刷新 VM 状态，禁止长期显示启动前的 OFF 快照
# 2026-08-11 force-stop-no-tail-v1: Worker 真正退出前保持“停止收尾中”，禁止提前显示停止完成；收尾线程归零后再恢复空闲
# 2026-08-11 socks5-gui-pool-v3: 代理在线检查改为各 Worker 并发门禁；可用 IP 线程先启动，不通则刷新后每 10 秒多次复测
# 2026-07-31 zombie-cancel-v2: Event代际 + provision捕获cancel，旧线程不因clear复活
# 2026-07-31 instant-stop-v2: 停止任务秒级生效(wait轮询+脉冲杀adb+跳过收尾)
# 2026-07-25 stop-task-force-v1: 顶栏【■ 停止任务】强制中断新建/装包/后台任务；_run_bg 可取消
# 2026-07-25 gui-layout-two-row-v2: 窗口恢复1080x700；参数/操作按钮仍两行完整显示
# 2026-07-25 layout-boot-immediate-v1: 新建启动成功后立刻一字排列，不等待装包结束
# 2026-07-25 pkg-parallel-create-v1: 新建后并行 provision 勾选软件；排列用 render 贴紧
# 2026-07-25 layout-tight-v1: 排列按钮按屏幕/数量一字紧贴无缝隙无黑边
# -*- coding: utf-8 -*-
"""
MuMu Venmo 多开登录器 UI（紧凑顶栏：开始/停止始终可见）
- 2026-07-24 step5: 新建数量+默认竖屏/省电/小磁盘/ROOT/可写系统盘；新建后按勾选装包(Kitsune/Zygisk/ih8/NekoBox/Aurora/Venmo)
- 2026-07-24 full-btn-text: 按钮按字数加宽，完整中文不截断；悬停仍有说明
- 2026-07-24 compact: 小窗口也能看到停止；控件紧凑多行
- 2026-07-24 delete: 勾选模拟器 → 删除=shutdown结束进程后 MuMu delete
- step4: 停止=等当前登录完成→关模拟器; 启动复用已有模拟器; 勾选要启动的模拟器
- 导入/导出账号，实时导出
- 多线程分配账号（禁止同账号并发）
- 窗口左上角一行排列
- NekoBox SOCKS5 + profile 自动分配
- 定时 restart 模拟器
- 新建模拟器 portrait/省电(custom 2C2G)/小磁盘/1440x2560@640/ROOT/可写系统盘
- GUI 自定义：登录并发、新建数量、新建启动线程
"""
from __future__ import annotations

# 2026-07-31 concurrent-create-v1
# 2026-07-31 heavy-install-v1+immediate-stop-v1: 错峰0.45; 停止杀adb; pool shutdown cancel: 新建装包 10 路真正并行；提交即打 START；轻微错峰减 ADB 惊群
# 2026-07-31 zombie-cancel-v1: 新任务用新 cancel Event，避免旧装包线程复活

import os
import time
import re
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.dont_write_bytecode = True

from core.account_store import (
    AccountStore,
    atomic_write_text,
    load_accounts_from_file,
    load_accounts_from_text,
)
from core.config_store import load_config, save_config
from core.logger_util import UiLogBridge, setup_logger
from core.mumu_manager import MuMuManager
from core.proxy_pool import (
    ProxyPool,
    load_change_ip_map,
    load_proxy_entries,
    save_proxy_entries,
)
from core.worker_engine import WorkerEngine
from paths import (
    ACCOUNTS_SAMPLES_DIR,
    ACCOUNTS_INPUT_DIR,
    AURORA_APK,
    EXPORT_CLASSIFIED_DIR,
    EXPORT_DIR,
    IH8_MODULE_ZIP,
    KITSUNE_APK,
    NEKOBOX_APK,
    PROXY_FILE,
    ROOT as PROJECT_ROOT,
    DOCS_DIR,
    resolve_export_dir,
)

logger = setup_logger()




def _button_width(text: str) -> int:
    """按可见字数计算 ttk/tk Button width（中文按2格，避免截断）。"""
    n = 0
    for ch in str(text or ""):
        n += 2 if ord(ch) > 127 else 1
    return max(4, n + 1)

class ToolTip:
    """鼠标悬停显示完整说明，不点击。"""

    def __init__(self, widget, text: str, delay_ms: int = 450):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None):
        self._hide()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _show(self):
        if self._tip or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 12
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        except Exception:
            return
        self._tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        try:
            tw.attributes("-topmost", True)
        except Exception:
            pass
        lbl = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#fffde7",
            foreground="#212121",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Microsoft YaHei UI", 9),
            padx=8,
            pady=5,
            wraplength=420,
        )
        lbl.pack()

    def _hide(self, _event=None):
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        if self._tip:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MuMu Venmo 登录器")
        # 窗口恢复上一次大小；排版仍用两行，避免右侧按钮被挡
        self.geometry("1180x820")
        self.minsize(980, 680)

        self.cfg = load_config()
        self.log_queue: queue.Queue[str] = queue.Queue()
        self.store = AccountStore(export_dir=self.cfg.get("export_dir") or None)
        self.store.add_finished_callback(self._on_account_finished)
        self.proxy_pool = ProxyPool()
        self.proxy_pool.load_file(PROXY_FILE)
        ideas = DOCS_DIR / "思路.txt"
        if ideas.exists():
            self.proxy_pool.attach_change_ip(load_change_ip_map(ideas))

        try:
            self.mumu = MuMuManager(
                self.cfg["mumu_manager"],
                self.cfg["adb_path"],
                adb_base_port=int(self.cfg.get("adb_base_port", 16384)),
                adb_port_step=int(self.cfg.get("adb_port_step", 32)),
            )
        except Exception as exc:
            self.mumu = None  # type: ignore
            logger.error("MuMuManager 初始化失败: %s", exc)

        self.engine: WorkerEngine | None = None
        self._busy = False
        self._bg_cancel = threading.Event()
        self._bg_title = ""
        self._stopping_ui = False
        self._stop_job_active = False
        self._proxy_editor_rows: list[dict] = []
        self._proxy_preflight_in_progress = False
        self._proxy_preflight_passed = False
        self._vm_check_vars: dict[int, tk.BooleanVar] = {}
        self._vm_check_widgets: dict[int, object] = {}
        self._vm_meta: dict[int, dict] = {}
        self._build_ui()
        self._bind_logger()
        self.after(200, self._drain_log)
        self.refresh_vms()
        self._log(f"项目目录: {PROJECT_ROOT}")
        self._log(f"代理数量: {len(self.proxy_pool.proxies)} profiles={self.proxy_pool.names()}")
        # 环境变量自动开跑：打开 UI 后导入账号并点开始登录
        if str(os.environ.get("MUMUVENMO_AUTO_START", "")).strip().lower() in ("1", "true", "yes", "on"):
            self.after(900, self._auto_start_if_requested)

    def _auto_start_if_requested(self) -> None:
        """MUMUVENMO_AUTO_START=1 时：可选新建 -> 勾选 VM、导入样本、workers/NekoBox 后 start_login。

        环境变量：
          MUMUVENMO_WORKERS=7
          MUMUVENMO_NEKOBOX=1
          MUMUVENMO_VMS=1,2,3,4,5,6,7
          MUMUVENMO_IMPORT=账号文件路径
          MUMUVENMO_CREATE=6          # >0 时先走 UI「仅新建」同路径，完成后再登录
          MUMUVENMO_CREATE_LAUNCH=0   # >0 时走「新建并启动」装包；默认 0 仅新建后由登录复用启动
        """
        try:
            workers = int(os.environ.get("MUMUVENMO_WORKERS", "7") or 7)
        except Exception:
            workers = 7
        try:
            create_n = int(os.environ.get("MUMUVENMO_CREATE", "0") or 0)
        except Exception:
            create_n = 0
        try:
            create_launch = int(os.environ.get("MUMUVENMO_CREATE_LAUNCH", "0") or 0)
        except Exception:
            create_launch = 0
        use_neko = str(os.environ.get("MUMUVENMO_NEKOBOX", "1")).strip().lower() not in ("0", "false", "no", "off")
        vm_raw = (os.environ.get("MUMUVENMO_VMS", "1,2,3,4,5,6,7") or "1,2,3,4,5,6,7").strip()
        sample = (os.environ.get("MUMUVENMO_IMPORT") or "").strip()
        if not sample:
            sample = str(ACCOUNTS_SAMPLES_DIR / "测试登录的账号 大部分是密码错误.txt")

        self._log(
            f"AUTO_START: workers={workers} nekobox={use_neko} vms={vm_raw} "
            f"create={create_n} create_launch={create_launch} import={sample}"
        )
        try:
            self.var_workers.set(workers)
        except Exception:
            pass
        try:
            self.var_nekobox.set(use_neko)
        except Exception:
            pass
        try:
            self.var_venmo_local.set(True)
        except Exception:
            pass
        if create_n > 0:
            try:
                self.var_create_count.set(create_n)
            except Exception:
                pass
        if create_launch > 0:
            try:
                self.var_create_launch.set(create_launch)
            except Exception:
                pass

        # 勾选指定 VM（新建完成后会再刷新一次）
        want: list[int] = []
        for part in vm_raw.replace("，", ",").split(","):
            part = part.strip()
            if not part:
                continue
            try:
                want.append(int(part))
            except Exception:
                continue
        want = sorted(set(want))
        if want:
            self.var_vms.set(",".join(str(i) for i in want))
            for idx, var in list(self._vm_check_vars.items()):
                try:
                    var.set(idx in want)
                except Exception:
                    pass
            self.cfg["last_selected_vms"] = list(want)
            try:
                save_config(self._collect_cfg())
            except Exception as exc:
                self._log(f"AUTO_START 保存配置警告: {exc}")

        # 导入账号（跳过已明确成功/失败）
        acc_path = Path(sample)
        if not acc_path.exists():
            self._log(f"AUTO_START 失败: 账号文件不存在 {acc_path}")
            return
        try:
            accs = load_accounts_from_file(acc_path)
            n = self.store.load(accs, source_path=acc_path)
            st = getattr(self.store, "last_load_stats", {}) or {}
            self._refresh_import_text()
            self._log(
                f"AUTO_START 导入 | 原始 {st.get('imported', len(accs))} | 跳过 {st.get('skipped', 0)} | 待登录 {n}"
            )
        except Exception as exc:
            self._log(f"AUTO_START 导入失败: {exc}")
            return

        if self.store.remaining() <= 0:
            self._log("AUTO_START: 没有待登录账号，跳过开始")
            return

        def _apply_want_and_start() -> None:
            try:
                self.refresh_vms()
            except Exception as exc:
                self._log(f"AUTO_START 刷新模拟器警告: {exc}")
            if want:
                self.var_vms.set(",".join(str(i) for i in want))
                for idx, var in list(self._vm_check_vars.items()):
                    try:
                        var.set(idx in want)
                    except Exception:
                        pass
                self.cfg["last_selected_vms"] = list(want)
            try:
                self.start_login()
                self._log("AUTO_START: 已调用开始登录（UI 全流程）")
            except Exception as exc:
                self._log(f"AUTO_START 开始登录失败: {exc}")

        # 需要新建：走 UI 同一套 create_vm_only / create_vm_and_launch 按钮路径
        if create_n > 0 and self.mumu:
            if create_launch > 0:
                self._log(f"AUTO_START: 先走 UI「新建并启动」数量={create_n}")
                # 直接复用按钮方法（内部 _run_bg），再轮询等待新建完成
                try:
                    self.create_vm_and_launch()
                except Exception as exc:
                    self._log(f"AUTO_START 新建并启动失败: {exc}")
                    return
            else:
                self._log(f"AUTO_START: 先走 UI「仅新建」数量={create_n}")
                try:
                    self.create_vm_only()
                except Exception as exc:
                    self._log(f"AUTO_START 仅新建失败: {exc}")
                    return

            # 等 UI 后台新建任务真正结束（_busy=False），再开始登录，避免装包未完就开跑
            # 新建并启动+装包较慢：每台最多约 15 分钟预算
            deadline = time.time() + max(600, create_n * 900)
            state = {"tries": 0, "saw_busy": False}

            def _poll_create() -> None:
                state["tries"] += 1
                busy = bool(getattr(self, "_busy", False))
                if busy:
                    state["saw_busy"] = True
                try:
                    exist = set(self.mumu.list_indices()) if self.mumu else set()
                except Exception:
                    exist = set()
                covered = all(i in exist for i in want) if want else bool(exist)
                done = (state["saw_busy"] and not busy) or ((not state["saw_busy"]) and covered and state["tries"] >= 3)
                timed_out = time.time() >= deadline
                if (done and covered) or timed_out:
                    self._log(
                        f"AUTO_START 新建轮询结束 tries={state['tries']} busy={busy} "
                        f"exist={sorted(exist)} covered={covered} timed_out={timed_out}"
                    )
                    _apply_want_and_start()
                    return
                if state["tries"] % 5 == 0:
                    self._log(
                        f"AUTO_START 等待新建/装包... busy={busy} exist={sorted(exist)} want={want}"
                    )
                self.after(2000, _poll_create)

            self.after(1500, _poll_create)
            return

        _apply_want_and_start()
    def _bind_logger(self) -> None:
        bridge = UiLogBridge(lambda m: self.log_queue.put(m))
        if logger.handlers:
            bridge.setFormatter(logger.handlers[0].formatter)
        logger.addHandler(bridge)

    def _log(self, msg: str) -> None:
        logger.info(msg)


    def _build_ui(self) -> None:
        # ===== 顶栏：开始/停止永远在最上方，小窗口也可见 =====
        bar = tk.Frame(self, bg="#1e1e1e", height=40)
        bar.pack(fill=tk.X, side=tk.TOP)
        bar.pack_propagate(False)
        self.btn_start = tk.Button(
            bar,
            text="▶ 开始登录",
            command=self.start_login,
            bg="#2e7d32",
            fg="white",
            activebackground="#1b5e20",
            activeforeground="white",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=10,
            height=1,
            relief=tk.FLAT,
            bd=0,
            padx=8,
        )
        self.btn_start.pack(side=tk.LEFT, padx=(6, 3), pady=5)
        self.btn_stop = tk.Button(
            bar,
            text="■ 停止登录",
            command=self.stop_login,
            state=tk.DISABLED,
            bg="#9e9e9e",
            fg="white",
            activebackground="#b71c1c",
            activeforeground="white",
            disabledforeground="#f5f5f5",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=10,
            height=1,
            relief=tk.FLAT,
            bd=0,
            padx=8,
        )
        self.btn_stop.pack(side=tk.LEFT, padx=3, pady=5)
        self.btn_stop_task = tk.Button(
            bar,
            text="■ 停止任务",
            command=self.stop_task,
            state=tk.DISABLED,
            bg="#9e9e9e",
            fg="white",
            activebackground="#e65100",
            activeforeground="white",
            disabledforeground="#f5f5f5",
            font=("Microsoft YaHei UI", 10, "bold"),
            width=10,
            height=1,
            relief=tk.FLAT,
            bd=0,
            padx=8,
        )
        self.btn_stop_task.pack(side=tk.LEFT, padx=3, pady=5)
        ttk.Button(bar, text="保存设置", width=_button_width("保存设置"), command=self.save_settings).pack(side=tk.LEFT, padx=4, pady=5)
        self.lbl_run_state = tk.Label(
            bar, text="空闲", bg="#1e1e1e", fg="#90caf9",
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        self.lbl_run_state.pack(side=tk.LEFT, padx=8)
        self.lbl_export = tk.Label(
            bar, text=self._export_status_text(), bg="#1e1e1e", fg="#bdbdbd",
            font=("Microsoft YaHei UI", 8),
        )
        self.lbl_export.pack(side=tk.LEFT, padx=4)
        # 兼容旧代码引用的 bottom 按钮（指向同一命令）
        self.btn_start_bottom = self.btn_start
        self.btn_stop_bottom = self.btn_stop

        # ===== 参数两行：避免小屏右侧“超时/永久”等字被挡 =====
        top = ttk.Frame(self, padding=(4, 2, 4, 0))
        top.pack(fill=tk.X)

        ttk.Label(top, text="登录线程").grid(row=0, column=0, sticky=tk.W)
        self.var_workers = tk.IntVar(value=int(self.cfg.get("workers", 3)))
        ttk.Spinbox(top, from_=1, to=32, textvariable=self.var_workers, width=4).grid(row=0, column=1, padx=2)

        ttk.Label(top, text="新建数量").grid(row=0, column=2, sticky=tk.W, padx=(8, 0))
        self.var_create_count = tk.IntVar(value=int(self.cfg.get("create_count", 1)))
        ttk.Spinbox(top, from_=1, to=20, textvariable=self.var_create_count, width=4).grid(row=0, column=3, padx=2)

        ttk.Label(top, text="新建启动线程").grid(row=0, column=4, sticky=tk.W, padx=(8, 0))
        self.var_create_launch = tk.IntVar(value=int(self.cfg.get("create_launch_workers", 2)))
        ttk.Spinbox(top, from_=1, to=16, textvariable=self.var_create_launch, width=4).grid(row=0, column=5, padx=2)

        ttk.Label(top, text="ADB命令并发").grid(row=0, column=6, sticky=tk.W, padx=(8, 0))
        self.var_adb_workflow = tk.IntVar(value=int(self.cfg.get("adb_command_limit", 2) or 2))
        ttk.Spinbox(top, from_=1, to=32, textvariable=self.var_adb_workflow, width=4).grid(row=0, column=7, padx=2)

        self.var_nekobox = tk.BooleanVar(value=bool(self.cfg.get("use_nekobox", True)))
        ttk.Checkbutton(top, text="NekoBox", variable=self.var_nekobox).grid(row=0, column=8, padx=6)

        self.var_sort = tk.BooleanVar(value=bool(self.cfg.get("auto_sort_windows", True)))
        ttk.Checkbutton(top, text="一行排列", variable=self.var_sort).grid(row=0, column=9, padx=4)

        ttk.Label(top, text="定时重启(分,0=永久)").grid(row=1, column=0, sticky=tk.W, pady=(4, 0))
        self.var_restart = tk.DoubleVar(value=float(self.cfg.get("restart_interval_minutes", 0) or 0))
        ttk.Entry(top, textvariable=self.var_restart, width=5).grid(row=1, column=1, padx=2, pady=(4, 0), sticky=tk.W)

        ttk.Label(top, text="登录超时(秒)").grid(row=1, column=2, sticky=tk.W, padx=(8, 0), pady=(4, 0))
        self.var_login_timeout = tk.IntVar(value=int(self.cfg.get("login_timeout_seconds", 90)))
        ttk.Entry(top, textvariable=self.var_login_timeout, width=5).grid(row=1, column=3, padx=2, pady=(4, 0), sticky=tk.W)

        ttk.Label(top, text="启动超时(秒)").grid(row=1, column=4, sticky=tk.W, padx=(8, 0), pady=(4, 0))
        self.var_boot_timeout = tk.IntVar(value=int(self.cfg.get("boot_timeout_seconds", 240)))
        ttk.Entry(top, textvariable=self.var_boot_timeout, width=5).grid(row=1, column=5, padx=2, pady=(4, 0), sticky=tk.W)

        # ===== 安装包 =====
        row_inst = ttk.Frame(self, padding=(4, 0, 4, 0))
        row_inst.pack(fill=tk.X)
        ttk.Label(row_inst, text="默认安装:").pack(side=tk.LEFT)
        ip = dict(self.cfg.get("install_packages") or {})
        self.var_inst_nekobox = tk.BooleanVar(value=bool(ip.get("nekobox", True)))
        self.var_inst_kitsune = tk.BooleanVar(value=bool(ip.get("kitsune", True)))
        self.var_inst_ih8 = tk.BooleanVar(value=bool(ip.get("ih8", True)))
        self.var_inst_aurora = tk.BooleanVar(value=bool(ip.get("aurora", False)))
        self.var_inst_venmo = tk.BooleanVar(value=bool(ip.get("venmo", True)))
        # 默认本地 bundle 安装 Venmo；可选 AuroraStore 安装
        self.var_venmo_local = tk.BooleanVar(
            value=bool(self.cfg.get("venmo_local_install", True))
        )
        self.var_venmo_via_aurora = tk.BooleanVar(
            value=bool(self.cfg.get("prefer_aurora_venmo", False))
        )
        ttk.Checkbutton(row_inst, text="NekoBox", variable=self.var_inst_nekobox).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(row_inst, text="Kitsune面具", variable=self.var_inst_kitsune).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(row_inst, text="ih8模块", variable=self.var_inst_ih8).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(row_inst, text="Aurora商店", variable=self.var_inst_aurora).pack(side=tk.LEFT, padx=2)
        cb_venmo = ttk.Checkbutton(row_inst, text="Venmo", variable=self.var_inst_venmo)
        cb_venmo.pack(side=tk.LEFT, padx=2)
        cb_venmo_local = ttk.Checkbutton(row_inst, text="本地安装Venmo", variable=self.var_venmo_local)
        cb_venmo_local.pack(side=tk.LEFT, padx=2)
        cb_venmo_aurora = ttk.Checkbutton(
            row_inst, text="AuroraStore安装Venmo", variable=self.var_venmo_via_aurora
        )
        cb_venmo_aurora.pack(side=tk.LEFT, padx=2)
        try:
            from app_ui import _tooltip  # may not exist
        except Exception:
            pass
        # tooltip helper if available later via bind
        for w, tip in (
            (cb_venmo, "是否安装 Venmo 客户端"),
            (cb_venmo_local, "默认勾选：用项目 assets/apk/venmo_bundle 本地完整 split 安装（推荐）"),
            (cb_venmo_aurora, "通过 Aurora Store 搜索下载安装 Venmo；需网络。与本地安装同时勾选时优先本地"),
        ):
            try:
                self._bind_tooltip(w, tip)
            except Exception:
                pass
        assets_hint = []
        for label, p in (
            ("NekoBox", NEKOBOX_APK),
            ("Kitsune", KITSUNE_APK),
            ("ih8", IH8_MODULE_ZIP),
            ("Aurora", AURORA_APK),
        ):
            assets_hint.append(f"{label}{'✓' if p.exists() else '×'}")
        self.lbl_assets = ttk.Label(row_inst, text=" ".join(assets_hint))
        self.lbl_assets.pack(side=tk.LEFT, padx=6)

        # ===== SOCKS5 代理池：SOCKS5|change-ip 链接在同一个输入框 =====
        proxy_box = ttk.LabelFrame(
            self,
            text="SOCKS5 代理池（每行：host:port:username:password|刷新链接）",
            padding=(4, 2),
        )
        proxy_box.pack(fill=tk.X, padx=4, pady=(2, 0))
        proxy_head = ttk.Frame(proxy_box)
        proxy_head.pack(fill=tk.X)
        ttk.Label(proxy_head, text="#", width=3).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(
            proxy_head,
            text="SOCKS5|刷新链接（不通则刷新，10 秒后多次复测；可用 IP 先启动）",
            anchor=tk.W,
        ).grid(
            row=0, column=1, sticky=tk.EW
        )
        proxy_head.columnconfigure(1, weight=1)
        ttk.Button(
            proxy_head,
            text="保存代理",
            width=_button_width("保存代理"),
            command=lambda: self._save_proxy_editor(show_message=True),
        ).grid(row=0, column=2, padx=(4, 1))
        ttk.Button(
            proxy_head,
            text="+",
            width=3,
            command=self._add_proxy_editor_row,
        ).grid(row=0, column=3, padx=(1, 0))

        self.proxy_canvas = tk.Canvas(proxy_box, height=92, highlightthickness=0)
        proxy_scroll = ttk.Scrollbar(
            proxy_box, orient=tk.VERTICAL, command=self.proxy_canvas.yview
        )
        self.proxy_rows_frame = ttk.Frame(self.proxy_canvas)
        self._proxy_canvas_window = self.proxy_canvas.create_window(
            (0, 0), window=self.proxy_rows_frame, anchor=tk.NW
        )
        self.proxy_rows_frame.bind(
            "<Configure>",
            lambda _e: self.proxy_canvas.configure(
                scrollregion=self.proxy_canvas.bbox("all")
            ),
        )
        self.proxy_canvas.bind(
            "<Configure>",
            lambda e: self.proxy_canvas.itemconfigure(
                self._proxy_canvas_window, width=e.width
            ),
        )
        self.proxy_canvas.configure(yscrollcommand=proxy_scroll.set)
        self.proxy_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        proxy_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        entries = load_proxy_entries(PROXY_FILE)
        if not entries:
            entries = [("", "")]
        for proxy_text, change_url in entries:
            self._add_proxy_editor_row(proxy_text, change_url)

        # ===== 导出 =====
        row_exp = ttk.Frame(self, padding=(4, 0, 4, 0))
        row_exp.pack(fill=tk.X)
        ttk.Label(row_exp, text="导出").pack(side=tk.LEFT)
        default_exp = (self.cfg.get("export_dir") or "").strip() or str(EXPORT_CLASSIFIED_DIR)
        self.var_export_dir = tk.StringVar(value=default_exp)
        ttk.Entry(row_exp, textvariable=self.var_export_dir).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(row_exp, text="浏览目录", width=_button_width("浏览目录"), command=self.browse_export_dir).pack(side=tk.LEFT, padx=1)
        ttk.Button(row_exp, text="应用导出", width=_button_width("应用导出"), command=self.apply_export_dir).pack(side=tk.LEFT, padx=1)
        ttk.Button(row_exp, text="打开目录", width=_button_width("打开目录"), command=self.open_export_dir).pack(side=tk.LEFT, padx=1)

        # ===== 模拟器操作（两行完整文字，右侧不再被挡）=====
        row3 = ttk.Frame(self, padding=(4, 2, 4, 0))
        row3.pack(fill=tk.X)
        ttk.Label(row3, text="VM索引").pack(side=tk.LEFT)
        last_vms = self.cfg.get("last_selected_vms") or []
        try:
            last_txt = ",".join(str(int(x)) for x in last_vms)
        except Exception:
            last_txt = ""
        self.var_vms = tk.StringVar(value=last_txt)
        ttk.Entry(row3, textvariable=self.var_vms, width=16).pack(side=tk.LEFT, padx=3)

        btn_rows = (
            (
                ("刷新列表", self.refresh_vms, "刷新模拟器列表状态"),
                ("全部勾选", self.select_all_vms, "勾选全部模拟器"),
                ("取消勾选", self.select_no_vms, "取消全部勾选"),
                ("勾选已启动", self.select_running_vms, "只勾选当前已启动 Android 的模拟器"),
                ("新建模拟器", self.create_vm_only, "按新建数量创建模拟器(竖屏/省电/小磁盘/ROOT)"),
                ("新建并启动", self.create_vm_and_launch, "新建后立刻启动模拟器"),
            ),
            (
                ("启动模拟器", self.launch_selected, "启动已勾选的模拟器"),
                ("一字排列", self.sort_windows, "按模拟器数量与电脑分辨率从左上角一字紧贴排列：无缝隙、保持竖屏比例减少黑边"),
                ("重启设备", self.restart_selected, "仅使用 MuMu restart device 重启设备"),
                ("关闭模拟器", self.shutdown_selected, "关闭已勾选模拟器"),
                ("删除模拟器", self.delete_selected, "结束进程并删除已勾选模拟器"),
                ("修复设置", self.fix_settings_selected, "修复分辨率/ROOT/可写系统盘等设置"),
            ),
        )
        # 第一行：索引框后继续放前半按钮
        for txt, cmd, tip in btn_rows[0]:
            b = ttk.Button(row3, text=txt, width=_button_width(txt), command=cmd)
            b.pack(side=tk.LEFT, padx=1)
            ToolTip(b, tip)
        # 第二行：完整放下半按钮，保证“修复设置”等四字完整可见
        row3b = ttk.Frame(self, padding=(4, 0, 4, 0))
        row3b.pack(fill=tk.X)
        for txt, cmd, tip in btn_rows[1]:
            b = ttk.Button(row3b, text=txt, width=_button_width(txt), command=cmd)
            b.pack(side=tk.LEFT, padx=1)
            ToolTip(b, tip)

        # 勾选模拟器（更矮）
        vm_box = ttk.LabelFrame(self, text="勾选模拟器（登录复用已有，不自动新建）", padding=2)
        vm_box.pack(fill=tk.X, padx=4, pady=(2, 0))
        self.frm_vm_checks_canvas = tk.Canvas(vm_box, height=42, highlightthickness=0)
        self.frm_vm_checks_scroll = ttk.Scrollbar(
            vm_box, orient=tk.HORIZONTAL, command=self.frm_vm_checks_canvas.xview
        )
        self.frm_vm_checks = ttk.Frame(self.frm_vm_checks_canvas)
        self.frm_vm_checks.bind(
            "<Configure>",
            lambda e: self.frm_vm_checks_canvas.configure(
                scrollregion=self.frm_vm_checks_canvas.bbox("all")
            ),
        )
        self.frm_vm_checks_canvas.create_window((0, 0), window=self.frm_vm_checks, anchor=tk.NW)
        self.frm_vm_checks_canvas.configure(xscrollcommand=self.frm_vm_checks_scroll.set)
        self.frm_vm_checks_canvas.pack(side=tk.TOP, fill=tk.X, expand=True)
        self.frm_vm_checks_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # ===== 中部：账号 + 日志（占满剩余空间）=====
        mid = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        mid.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        left = ttk.Frame(mid)
        right = ttk.Frame(mid)
        mid.add(left, weight=1)
        mid.add(right, weight=1)

        acc_bar = ttk.Frame(left)
        acc_bar.pack(fill=tk.X, pady=1)
        for txt, cmd in (
            ("导入", self.import_accounts),
            ("文本加载", self.load_from_text),
            ("导出全部", self.export_all),
            ("导出目录", self.open_export_dir),
            ("重载代理", self.reload_proxies),
        ):
            ttk.Button(acc_bar, text=txt, command=cmd).pack(side=tk.LEFT, padx=1)

        self.lbl_stats = ttk.Label(left, text="账号: -")
        self.lbl_stats.pack(fill=tk.X)

        self.txt_accounts = tk.Text(left, height=12, wrap=tk.NONE, font=("Consolas", 9))
        yscroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.txt_accounts.yview)
        self.txt_accounts.configure(yscrollcommand=yscroll.set)
        self.txt_accounts.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(right, text="实时日志").pack(anchor=tk.W)
        self.txt_log = tk.Text(right, height=12, wrap=tk.WORD, font=("Consolas", 9))
        log_scroll = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=log_scroll.set)
        self.txt_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.lbl_vms = ttk.Label(self, text="模拟器: -", padding=(4, 0, 4, 2))
        self.lbl_vms.pack(fill=tk.X)

        # 控件悬停完整中文说明
        try:
            ToolTip(self.btn_start, "开始登录：复用已勾选模拟器，自动分配账号与 SOCKS5，不会多机同号")
            ToolTip(
                self.btn_stop,
                "停止：必须等当前账号登录完成后再关模拟器；超时未完成不关机。再点一次=强制停止（约12秒内打断并关机）",
            )
            ToolTip(
                self.btn_stop_task,
                "停止任务：强制中断当前后台任务（新建模拟器/装包/启动/删除/排列等）。立即发取消信号，正在进行的步骤会尽快退出；登录请用【停止登录】",
            )
        except Exception:
            pass


    def _add_proxy_editor_row(
        self,
        proxy_text: str = "",
        change_url: str = "",
    ) -> None:
        """GUI 增加一行 ``SOCKS5|刷新链接``；新增行右侧显示减号。"""
        row_frame = ttk.Frame(self.proxy_rows_frame)
        row_frame.pack(fill=tk.X, pady=1)
        row_frame.columnconfigure(1, weight=1)
        pair_text = ""
        if proxy_text or change_url:
            pair_text = f"{proxy_text}|{change_url}"
        row = {
            "frame": row_frame,
            "index": ttk.Label(row_frame, text="", width=3),
            "pair_var": tk.StringVar(value=pair_text),
            "minus": None,
        }
        row["index"].grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(row_frame, textvariable=row["pair_var"]).grid(
            row=0, column=1, sticky=tk.EW
        )
        minus = ttk.Button(
            row_frame,
            text="-",
            width=3,
            command=lambda current=row: self._remove_proxy_editor_row(current),
        )
        minus.grid(row=0, column=2, padx=(4, 1))
        row["minus"] = minus
        # 与标题行“保存代理”“+”两列对齐，占位。
        ttk.Label(row_frame, text="", width=3).grid(row=0, column=3)
        self._proxy_editor_rows.append(row)
        self._renumber_proxy_editor_rows()
        try:
            self.proxy_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def _remove_proxy_editor_row(self, row: dict) -> None:
        if row not in self._proxy_editor_rows or len(self._proxy_editor_rows) <= 1:
            return
        self._proxy_editor_rows.remove(row)
        try:
            row["frame"].destroy()
        except Exception:
            pass
        self._renumber_proxy_editor_rows()

    def _renumber_proxy_editor_rows(self) -> None:
        for i, row in enumerate(self._proxy_editor_rows, 1):
            row["index"].configure(text=str(i))
            # 第一套固定保留；点 + 新增的其余套均有 - 可删除。
            row["minus"].configure(state=(tk.DISABLED if i == 1 else tk.NORMAL))

    def _proxy_editor_values(self) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        for row_no, row in enumerate(self._proxy_editor_rows, 1):
            pair_text = str(row["pair_var"].get() or "").strip()
            if not pair_text:
                out.append(("", ""))
                continue
            if pair_text.count("|") != 1:
                raise ValueError(
                    f"第 {row_no} 行格式错误，必须用一个 | 分割 SOCKS5 和刷新链接"
                )
            proxy_text, change_url = (
                part.strip() for part in pair_text.split("|", 1)
            )
            if not proxy_text or not change_url:
                raise ValueError(
                    f"第 {row_no} 行格式错误，| 左边写 SOCKS5，右边写刷新链接"
                )
            out.append((proxy_text, change_url))
        return out

    def _replace_proxy_editor_rows(self, entries: list[tuple[str, str]]) -> None:
        for row in list(self._proxy_editor_rows):
            try:
                row["frame"].destroy()
            except Exception:
                pass
        self._proxy_editor_rows.clear()
        for proxy_text, change_url in (entries or [("", "")]):
            self._add_proxy_editor_row(proxy_text, change_url)

    def _save_proxy_editor(self, *, show_message: bool = False) -> bool:
        """校验 GUI 内容、保存成对代理并立即重载运行时代理池。"""
        try:
            n = save_proxy_entries(self._proxy_editor_values(), PROXY_FILE)
            n2 = self.proxy_pool.load_file(PROXY_FILE)
            ideas = DOCS_DIR / "思路.txt"
            if ideas.exists():
                self.proxy_pool.attach_change_ip(load_change_ip_map(ideas))
            self.proxy_pool.configure(
                min_refresh_interval_seconds=float(
                    self.cfg.get("proxy_refresh_min_interval_seconds", 180)
                ),
                refresh_wait_seconds=float(
                    self.cfg.get("proxy_refresh_wait_seconds", 5)
                ),
            )
        except Exception as exc:
            self._log(f"代理池保存失败: {exc}")
            messagebox.showerror("代理池格式错误", str(exc))
            return False
        self._log(f"代理池已保存并重载: {n} 套，运行时={n2}")
        if show_message:
            messagebox.showinfo("代理池", f"已保存 {n} 套 SOCKS5 + 刷新链接")
        return True

    def _begin_proxy_preflight(self) -> bool:
        """保存代理池；实际连通门禁由各 Worker 并发执行，避免慢代理阻塞可用代理。"""
        if self._proxy_preflight_in_progress:
            return True
        if not self._save_proxy_editor(show_message=False):
            return True
        if not bool(self.var_nekobox.get()):
            return False
        profiles = list(self.proxy_pool.proxies)
        if not profiles:
            messagebox.showerror("代理池", "启用 NekoBox 时至少需要一套有效 SOCKS5 + 刷新链接")
            return True
        self.proxy_pool.configure(
            min_refresh_interval_seconds=180.0,
            refresh_wait_seconds=10.0,
        )
        self._log(
            f"启动前代理并发门禁已准备: {len(profiles)} 套；"
            "各 Worker 独立检查，可用 IP 立即继续，不通 IP 刷新后每 10 秒多次复测"
        )
        return False


    def _bind_tooltip(self, widget, text: str) -> None:
        """鼠标悬停显示完整说明（不缩写）。"""
        tip = {"win": None}

        def on_enter(_e=None):
            if tip["win"] is not None:
                return
            try:
                x = widget.winfo_rootx() + 12
                y = widget.winfo_rooty() + widget.winfo_height() + 6
            except Exception:
                return
            win = tk.Toplevel(self)
            win.wm_overrideredirect(True)
            win.wm_geometry(f"+{x}+{y}")
            try:
                win.attributes("-topmost", True)
            except Exception:
                pass
            lbl = ttk.Label(
                win,
                text=text,
                justify=tk.LEFT,
                background="#ffffe0",
                relief=tk.SOLID,
                borderwidth=1,
                padding=(6, 3),
                wraplength=420,
            )
            lbl.pack()
            tip["win"] = win

        def on_leave(_e=None):
            w = tip.get("win")
            tip["win"] = None
            if w is not None:
                try:
                    w.destroy()
                except Exception:
                    pass

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def _drain_log(self) -> None:
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.txt_log.insert(tk.END, msg + "\n")
                self.txt_log.see(tk.END)
        except queue.Empty:
            pass
        self._update_stats()
        self.after(300, self._drain_log)

    def _update_stats(self) -> None:
        st = self.store.stats()
        self.lbl_stats.configure(
            text=(
                f"账号 total={st.get('total', 0)} remaining≈{self.store.remaining()} "
                f"running={st.get('running', 0)} success={st.get('success', 0)} "
                f"risk={st.get('risk_control', 0)} wrong={st.get('wrong_password', 0)} "
                f"nonet={st.get('no_network', 0)} error={st.get('error', 0)}"
            )
        )
        if not (self.engine and (self.engine.running or self.engine.alive_workers() > 0)):
            self.lbl_export.configure(text=self._export_status_text())

    def _collect_cfg(self) -> dict:
        self.cfg["workers"] = int(self.var_workers.get())
        self.cfg["max_active_vms"] = 8
        self.cfg["adb_command_limit"] = min(
            32, max(1, int(self.var_adb_workflow.get() or 2))
        )
        # 登录线程与 Worker 数量一致，不限制模拟器/账号流程数量。旧字段写成同值
        # 仅用于兼容旧配置；ADB命令并发可在1–32间独立设置，由共享命令队列治理。
        self.cfg["adb_workflow_limit"] = max(1, int(self.var_workers.get() or 1))
        # 全部 VM 快速错峰派发；坏代理独立复测/换绑，不再阻塞后续健康 VM。
        self.cfg["startup_wave_size"] = 1
        self.cfg["startup_wave_settle_seconds"] = 8
        # 代理池允许自动复用：代理少于 Worker 时按池顺序均衡分配，
        # 代理可复用；ADB命令与整套登录工作流分别限流，模拟器数量不再硬截断。
        self.cfg["allow_proxy_reuse"] = True
        self.cfg["create_count"] = int(self.var_create_count.get())
        self.cfg["create_launch_workers"] = int(self.var_create_launch.get())
        self.cfg["use_nekobox"] = bool(self.var_nekobox.get())
        self.cfg["auto_sort_windows"] = bool(self.var_sort.get())
        self.cfg["restart_interval_minutes"] = float(self.var_restart.get() or 0)
        self.cfg["login_timeout_seconds"] = int(self.var_login_timeout.get())
        self.cfg["boot_timeout_seconds"] = int(self.var_boot_timeout.get())
        # change-ip 固定 3 分钟冷却；GUI/WorkerEngine 共用该值。
        self.cfg["proxy_refresh_min_interval_seconds"] = 180
        self.cfg["proxy_refresh_wait_seconds"] = 10
        self.cfg["proxy_startup_check_rounds"] = 5
        self.cfg["proxy_startup_check_gap_seconds"] = 10
        venmo_local = bool(self.var_venmo_local.get()) if hasattr(self, "var_venmo_local") else True
        venmo_aurora = bool(self.var_venmo_via_aurora.get()) if hasattr(self, "var_venmo_via_aurora") else False
        # 勾选 AuroraStore 安装 Venmo 时，确保也装 Aurora 商店
        inst_aurora = bool(self.var_inst_aurora.get()) or venmo_aurora
        self.cfg["install_packages"] = {
            "nekobox": bool(self.var_inst_nekobox.get()),
            "kitsune": bool(self.var_inst_kitsune.get()),
            "ih8": bool(self.var_inst_ih8.get()),
            "aurora": inst_aurora,
            "venmo": bool(self.var_inst_venmo.get()) or venmo_local or venmo_aurora,
        }
        self.cfg["venmo_local_install"] = venmo_local
        # 默认本地；仅当勾选 AuroraStore 且未勾选本地时优先 Aurora
        self.cfg["prefer_aurora_venmo"] = bool(venmo_aurora and not venmo_local)
        self.cfg["export_dir"] = (self.var_export_dir.get() or "").strip()
        # 勾选优先写入 last_selected_vms
        checked = self._checked_indices()
        if checked:
            self.cfg["last_selected_vms"] = list(checked)
        else:
            parsed = self._parse_vm_text()
            if parsed:
                self.cfg["last_selected_vms"] = list(parsed)
        return self.cfg

    def _validate_unique_proxy_capacity(self, ids: list[int], cfg: dict) -> tuple[bool, str]:
        """校验代理池；复用模式只要求至少一套完整代理。"""
        required = min(max(1, int(cfg.get("workers", 1) or 1)), len(ids))
        if not bool(cfg.get("use_nekobox", True)):
            return True, f"NekoBox未启用，Worker={required}"
        profiles = list(getattr(self.proxy_pool, "proxies", []) or [])
        unique: set[tuple] = set()
        with_refresh = 0
        for profile in profiles:
            refresh = str(getattr(profile, "change_ip_url", "") or "").strip()
            if not refresh:
                continue
            with_refresh += 1
            unique.add(
                (
                    str(getattr(profile, "host", "") or "").strip().lower(),
                    int(getattr(profile, "port", 0) or 0),
                    str(getattr(profile, "username", "") or ""),
                    str(getattr(profile, "password", "") or ""),
                    refresh,
                )
            )
        available = len(unique)
        allow_reuse = bool(cfg.get("allow_proxy_reuse", True))
        if allow_reuse:
            if available < 1:
                return (
                    False,
                    f"已选 {len(ids)} 台、登录线程 {required}，但没有带刷新链接的有效代理"
                    f"（已解析 {len(profiles)} 套，带链接 {with_refresh} 套）。",
                )
            return (
                True,
                f"代理池容量通过: Worker={required} available={available} reuse=True；"
                "代理将自动均衡分配",
            )
        if available < required:
            return (
                False,
                f"已选 {len(ids)} 台、登录线程 {required}，但只有 {available} 套"
                f"带刷新链接的唯一代理（已解析 {len(profiles)} 套，带链接 {with_refresh} 套）。"
                f"按不复用规则还需补 {required - available} 套。",
            )
        return (
            True,
            f"唯一代理容量通过: Worker={required} available={available} reuse=False",
        )

    def _parse_vm_text(self) -> list[int]:
        raw = (self.var_vms.get() or "").strip()
        if not raw:
            return []
        out: list[int] = []
        for part in re.split(r"[,\s]+", raw):
            part = part.strip()
            if part.isdigit():
                idx = int(part)
                if idx not in out:
                    out.append(idx)
        return out

    def _checked_indices(self) -> list[int]:
        out: list[int] = []
        for idx in sorted(self._vm_check_vars.keys()):
            var = self._vm_check_vars.get(idx)
            if var is not None and bool(var.get()):
                out.append(int(idx))
        return out

    def _sync_vm_text_from_checks(self) -> None:
        checked = self._checked_indices()
        self.var_vms.set(",".join(str(i) for i in checked))

    def _on_vm_check_changed(self) -> None:
        self._sync_vm_text_from_checks()

    def _rebuild_vm_checkboxes(
        self,
        indices: list[int],
        info: dict | None = None,
        *,
        prefer_checked: list[int] | None = None,
    ) -> None:
        """按当前模拟器列表重建勾选框，尽量保留原勾选 / last_selected。"""
        if prefer_checked is None:
            prev = self._checked_indices()
            if prev:
                prefer_checked = prev
            else:
                parsed = self._parse_vm_text()
                if parsed:
                    prefer_checked = parsed
                else:
                    prefer_checked = [
                        int(x)
                        for x in (self.cfg.get("last_selected_vms") or [])
                        if str(x).isdigit() or isinstance(x, int)
                    ]

        prefer_set = set(int(x) for x in prefer_checked)
        info = info if isinstance(info, dict) else {}

        for child in list(self.frm_vm_checks.winfo_children()):
            try:
                child.destroy()
            except Exception:
                pass
        self._vm_check_vars.clear()
        self._vm_check_widgets.clear()
        self._vm_meta.clear()

        if not indices:
            ttk.Label(self.frm_vm_checks, text="(无模拟器，请先新建)").pack(side=tk.LEFT, padx=4)
            self.frm_vm_checks_canvas.configure(scrollregion=self.frm_vm_checks_canvas.bbox("all"))
            return

        for i in indices:
            node = {}
            if isinstance(info, dict):
                node = info.get(str(i), {}) or info.get(i, {}) or {}
                if not isinstance(node, dict):
                    node = {}
            name = str(node.get("name") or f"VM{i}")
            if node.get("is_android_started"):
                state = "ON"
            elif node.get("is_process_started"):
                state = f"PROC:{node.get('player_state') or '?'}"
            else:
                state = "OFF"
            self._vm_meta[i] = {
                "name": name,
                "state": state,
                "is_android_started": bool(node.get("is_android_started")),
                "is_process_started": bool(node.get("is_process_started")),
                "node": node,
            }
            var = tk.BooleanVar(value=(i in prefer_set) if prefer_set else False)
            self._vm_check_vars[i] = var
            label = f"{i}:{name}[{state}]"
            cb = ttk.Checkbutton(
                self.frm_vm_checks,
                text=label,
                variable=var,
                command=self._on_vm_check_changed,
            )
            cb.pack(side=tk.LEFT, padx=4, pady=2)
            self._vm_check_widgets[i] = cb

        # 若 prefer 全都不在列表且用户未勾选，默认勾选全部（便于直接启动复用）
        if prefer_set and not any(i in prefer_set for i in indices):
            # last_selected 已失效：默认勾选已启动的，没有则勾全部
            running = [i for i in indices if self._vm_meta.get(i, {}).get("is_android_started")]
            targets = running or list(indices)
            for i in targets:
                if i in self._vm_check_vars:
                    self._vm_check_vars[i].set(True)
        elif not prefer_set:
            # 首次：默认勾选已启动；没有则勾全部
            running = [i for i in indices if self._vm_meta.get(i, {}).get("is_android_started")]
            targets = running or list(indices)
            for i in targets:
                if i in self._vm_check_vars:
                    self._vm_check_vars[i].set(True)

        self._sync_vm_text_from_checks()
        try:
            self.frm_vm_checks.update_idletasks()
            self.frm_vm_checks_canvas.configure(
                scrollregion=self.frm_vm_checks_canvas.bbox("all")
            )
        except Exception:
            pass

    def _visible_vm_window_indices(self) -> set[int]:
        """读取当前真实可见的数字标题 MuMu 窗口，不调用 MuMuManager/ADB。"""
        if os.name != "nt":
            return set()
        found: set[int] = set()
        try:
            import ctypes

            user32 = ctypes.windll.user32
            enum_proc_type = ctypes.WINFUNCTYPE(
                ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p
            )

            def _visit(hwnd, _lparam):
                try:
                    if not user32.IsWindowVisible(hwnd):
                        return True
                    length = int(user32.GetWindowTextLengthW(hwnd) or 0)
                    if length <= 0 or length > 16:
                        return True
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = str(buf.value or "").strip()
                    if title.isdigit():
                        index = int(title)
                        if index in self._vm_meta:
                            found.add(index)
                except Exception:
                    pass
                return True

            callback = enum_proc_type(_visit)
            user32.EnumWindows(callback, 0)
        except Exception:
            return set()
        return found

    def _refresh_live_vm_task_status(
        self,
        visible_indices: set[int] | None = None,
    ) -> dict[int, str]:
        """运行期间轻量刷新 VM 标签，且不重建勾选框/不改变用户选择。

        状态优先级：LOGIN（当前正在处理账号） > ON（真实窗口存在） >
        START（Worker 已分配、窗口尚未出现） > refresh_vms 保存的实际快照。
        """
        eng = self.engine
        active: set[int] = set()
        login: set[int] = set()
        if eng and (eng.running or eng.alive_workers() > 0):
            try:
                active = {int(x) for x in eng.active_vm_indices()}
            except Exception:
                active = set()
            try:
                for worker_id in eng.current_logins().keys():
                    match = re.search(r"(?:worker-|VM-?)(\d+)", str(worker_id), re.I)
                    if match:
                        login.add(int(match.group(1)))
            except Exception:
                login = set()
        visible = (
            {int(x) for x in visible_indices}
            if visible_indices is not None
            else self._visible_vm_window_indices()
        )
        display: dict[int, str] = {}
        parts: list[str] = []
        for index in sorted(self._vm_meta):
            meta = self._vm_meta.get(index) or {}
            base_state = str(meta.get("state") or "OFF")
            if index in login:
                state = "LOGIN"
            elif index in visible:
                state = "ON"
            elif index in active:
                state = "START"
            else:
                state = base_state
            display[index] = state
            meta["live_state"] = state
            name = str(meta.get("name") or index)
            text = f"{index}:{name}[{state}]"
            parts.append(text)
            widget = self._vm_check_widgets.get(index)
            if widget is not None:
                try:
                    widget.configure(text=text)
                except Exception:
                    pass
        try:
            self.lbl_vms.configure(
                text="模拟器: " + (" | ".join(parts) if parts else "(无)")
            )
        except Exception:
            pass
        return display

    def select_all_vms(self) -> None:
        for var in self._vm_check_vars.values():
            var.set(True)
        self._sync_vm_text_from_checks()

    def select_no_vms(self) -> None:
        for var in self._vm_check_vars.values():
            var.set(False)
        self._sync_vm_text_from_checks()

    def select_running_vms(self) -> None:
        any_on = False
        for idx, var in self._vm_check_vars.items():
            meta = self._vm_meta.get(idx, {})
            live_state = str(meta.get("live_state") or "")
            on = live_state in ("ON", "LOGIN") or bool(
                meta.get("is_android_started")
            )
            var.set(on)
            any_on = any_on or on
        if not any_on and self._vm_check_vars:
            # 没有已启动时不误清空提示
            self._log("当前没有已启动(Android)的模拟器")
        self._sync_vm_text_from_checks()

    def refresh_vms(self) -> None:
        if not self.mumu:
            self.lbl_vms.configure(text="模拟器: MuMuManager 不可用")
            return
        try:
            indices = self.mumu.list_indices()
            info: dict = {}
            try:
                raw = self.mumu.info("all")
                if isinstance(raw, dict):
                    info = raw
            except Exception as exc:
                self._log(f"info all 失败(仍用列表): {exc}")
            parts = []
            for i in indices:
                node = info.get(str(i), {}) if isinstance(info, dict) else {}
                if not isinstance(node, dict):
                    node = {}
                name = node.get("name", "")
                if node.get("is_android_started"):
                    started = "ON"
                elif node.get("is_process_started"):
                    started = f"PROC:{node.get('player_state') or '?'}"
                else:
                    started = "OFF"
                parts.append(f"{i}:{name}[{started}]")
            self.lbl_vms.configure(text="模拟器: " + (" | ".join(parts) if parts else "(无)"))
            self._rebuild_vm_checkboxes(indices, info)
            self._log(f"刷新模拟器 {len(indices)} 个")
        except Exception as exc:
            self.lbl_vms.configure(text=f"模拟器刷新失败: {exc}")
            self._log(f"刷新模拟器失败: {exc}")

    def _selected_indices(self, *, for_login: bool = False) -> list[int]:
        """选择顺序: 勾选 > 文本框 > last_selected_vms(仍存在) > 全部。

        for_login=True 时: 只复用已有实例；已启动优先；按 workers 截取。
        """
        if not self.mumu:
            return []
        try:
            all_ids = list(self.mumu.list_indices())
        except Exception:
            all_ids = list(self._vm_check_vars.keys())
        all_set = set(all_ids)

        checked = [i for i in self._checked_indices() if i in all_set]
        text_ids = [i for i in self._parse_vm_text() if i in all_set]
        last_ids = []
        for x in self.cfg.get("last_selected_vms") or []:
            try:
                i = int(x)
            except Exception:
                continue
            if i in all_set and i not in last_ids:
                last_ids.append(i)

        if checked:
            selected = checked
            src = "勾选"
        elif text_ids:
            selected = text_ids
            src = "文本框"
        elif last_ids:
            selected = last_ids
            src = "上次选择"
        else:
            selected = list(all_ids)
            src = "全部"

        if for_login:
            # 已启动优先排序（不新建）
            running = []
            offline = []
            for i in selected:
                meta = self._vm_meta.get(i) or {}
                if meta.get("is_android_started") or meta.get("is_process_started"):
                    running.append(i)
                else:
                    offline.append(i)
            ordered = running + offline
            workers = max(1, int(self.var_workers.get() or 1))
            if len(ordered) > workers:
                self._log(
                    f"登录选用模拟器({src}): 共{len(ordered)}台, workers={workers}, "
                    f"截取前{workers}台(已启动优先)={ordered[:workers]}"
                )
                ordered = ordered[:workers]
            else:
                self._log(f"登录选用模拟器({src}): {ordered}")
            return ordered

        return selected

    def _task_cancelled(self) -> bool:
        """后台任务是否已被【停止任务】强制取消。"""
        ev = getattr(self, "_bg_cancel", None)
        return bool(ev is not None and ev.is_set())

    def _set_bg_task_button(self, busy: bool, title: str = "") -> None:
        """刷新【停止任务】按钮：有后台任务时可点。"""
        btn = getattr(self, "btn_stop_task", None)
        if btn is None:
            return

        def _apply() -> None:
            try:
                if busy:
                    btn.configure(state=tk.NORMAL, bg="#e65100", text="■ 停止任务")
                    lbl = getattr(self, "lbl_run_state", None)
                    eng = getattr(self, "engine", None)
                    login_active = bool(eng and (eng.running or eng.is_stopping()))
                    if lbl is not None and not login_active:
                        t = title or getattr(self, "_bg_title", "") or "后台任务"
                        lbl.configure(text=f"后台:{t}")
                else:
                    btn.configure(state=tk.DISABLED, bg="#9e9e9e", text="■ 停止任务")
                    lbl = getattr(self, "lbl_run_state", None)
                    eng = getattr(self, "engine", None)
                    login_active = bool(eng and (eng.running or eng.is_stopping()))
                    if lbl is not None and not login_active and not getattr(self, "_stopping_ui", False):
                        lbl.configure(text="空闲")
            except Exception:
                pass

        try:
            self.after(0, _apply)
        except Exception:
            _apply()

    def stop_task(self) -> None:
        """强制中断后台任务（新建/装包/启动/删除/排列等），立即发取消信号并杀 adb。"""
        if not getattr(self, "_busy", False):
            self._log("停止任务: 当前没有后台任务")
            return
        title = getattr(self, "_bg_title", "") or "后台任务"
        try:
            self._bg_cancel.set()
        except Exception as exc:
            self._log(f"停止任务: 发送取消信号失败: {exc}")
            return
        # instant-stop-v2: 立刻 + 脉冲打断卡住的 adb install/push/ui dump
        try:
            from core.adb_client import AdbClient
            AdbClient.request_cancel_all()
            killed = AdbClient.interrupt_all()
            self._log(f"[停止任务] 已中断活动 ADB 进程 killed={killed}")
        except Exception as exc:
            self._log(f"[停止任务] 中断 ADB 失败: {exc}")
        self._log(f"[停止任务] 已强制中断 → {title}（目标 <1s 退出当前步骤）")

        def _pulse_kill() -> None:
            try:
                from core.adb_client import AdbClient as _Adb
            except Exception:
                return
            for _i in range(40):  # ~12s
                try:
                    if not getattr(self, "_busy", False):
                        break
                    ev = getattr(self, "_bg_cancel", None)
                    if ev is None or not ev.is_set():
                        break
                    _Adb.request_cancel_all()
                    _Adb.interrupt_all()
                except Exception:
                    pass
                time.sleep(0.3)

        try:
            threading.Thread(target=_pulse_kill, name="stop-task-pulse", daemon=True).start()
        except Exception:
            pass
        btn = getattr(self, "btn_stop_task", None)
        if btn is not None:
            try:
                btn.configure(state=tk.DISABLED, bg="#bf360c", text="■ 停止中...")
            except Exception:
                pass
        lbl = getattr(self, "lbl_run_state", None)
        if lbl is not None:
            try:
                eng = getattr(self, "engine", None)
                if not (eng and (eng.running or eng.is_stopping())):
                    lbl.configure(text=f"强制停止:{title}")
            except Exception:
                pass

    def _run_bg(self, title: str, fn) -> None:
        if self._busy:
            messagebox.showwarning("忙", "已有后台任务在执行，请稍候；可先点【停止任务】强制中断")
            return
        self._busy = True
        self._bg_title = str(title or "后台任务")
        # zombie-cancel-v2: 每次任务换新 Event + 代际号。
        # 旧任务 Event 保持 set；即便 clear_cancel_all，旧线程因 bg_gen 不匹配也会退出。
        self._bg_gen = int(getattr(self, "_bg_gen", 0) or 0) + 1
        self._bg_cancel = threading.Event()
        cancel_ev = self._bg_cancel
        bg_gen = self._bg_gen
        try:
            from core.adb_client import AdbClient
            AdbClient.clear_cancel_all()
        except Exception:
            pass
        self._log(f"[{title}] 开始...（可点顶栏【■ 停止任务】强制中断）")
        self._set_bg_task_button(True, title)

        def runner() -> None:
            cancelled = False
            try:
                if cancel_ev.is_set():
                    cancelled = True
                    self._log(f"[{title}] 启动前已取消")
                else:
                    fn()
                    cancelled = cancel_ev.is_set()
            except Exception as exc:
                if cancel_ev.is_set() or "cancel" in str(exc).lower():
                    cancelled = True
                    self._log(f"[{title}] 已强制停止: {exc}")
                else:
                    self._log(f"[{title}] 失败: {exc}")
                    try:
                        self.after(0, lambda: messagebox.showerror(title, str(exc)))
                    except Exception:
                        pass
            finally:
                if cancelled:
                    self._log(f"[{title}] 已由【停止任务】强制结束")
                    try:
                        cancel_ev.set()
                    except Exception:
                        pass
                else:
                    self._log(f"[{title}] 结束")
                self._busy = False
                self._bg_title = ""
                self._set_bg_task_button(False)
                try:
                    self.after(0, self.refresh_vms)
                except Exception:
                    pass

        threading.Thread(target=runner, name=title, daemon=True).start()

    def create_vm_only(self) -> None:
        if not self.mumu:
            messagebox.showerror("错误", "MuMuManager 不可用")
            return
        n = max(1, int(self.var_create_count.get() or 1))
        defaults = self.cfg.get("create_defaults", {})

        def job() -> None:
            if self._task_cancelled():
                self._log("仅新建: 已取消")
                return
            new_ids = self.mumu.create_configured(
                n,
                defaults,
                name_prefix="venmo",
                log=self._log,
                cancel_check=self._task_cancelled,
            )
            if self._task_cancelled():
                self._log(f"仅新建: 强制停止，已创建 {new_ids}")
                return
            self._log(f"新建完成: {new_ids}")
            if new_ids:
                cur = self.var_vms.get().strip()
                add = ",".join(str(i) for i in new_ids)

                def _set() -> None:
                    self.var_vms.set(f"{cur},{add}".strip(",") if cur else add)

                self.after(0, _set)

        self._run_bg("仅新建", job)

    def create_vm_and_launch(self) -> None:
        if not self.mumu:
            messagebox.showerror("错误", "MuMuManager 不可用")
            return
        n = max(1, int(self.var_create_count.get() or 1))
        workers = max(1, int(self.var_create_launch.get() or 1))
        boot_timeout = max(60, int(self.var_boot_timeout.get() or 240))
        defaults = self.cfg.get("create_defaults", {})
        venmo_local = bool(self.var_venmo_local.get()) if hasattr(self, "var_venmo_local") else True
        venmo_aurora = bool(self.var_venmo_via_aurora.get()) if hasattr(self, "var_venmo_via_aurora") else False
        install_opts = {
            "nekobox": bool(self.var_inst_nekobox.get()),
            "kitsune": bool(self.var_inst_kitsune.get()),
            "ih8": bool(self.var_inst_ih8.get()),
            "aurora": bool(self.var_inst_aurora.get()) or venmo_aurora,
            "venmo": (bool(self.var_inst_venmo.get()) if hasattr(self, "var_inst_venmo") else True)
            or venmo_local
            or venmo_aurora,
        }
        # 默认本地安装；仅 AuroraStore安装Venmo 勾选且本地未勾选时走 Aurora
        prefer_aurora = bool(venmo_aurora and not venmo_local)

        def job() -> None:
            if self._task_cancelled():
                self._log("新建并启动: 已取消")
                return
            result = self.mumu.create_and_launch(
                number=n,
                defaults=defaults,
                name_prefix="venmo",
                launch_workers=workers,
                boot_timeout=boot_timeout,
                log=self._log,
                cancel_check=self._task_cancelled,
            )
            if self._task_cancelled():
                self._log(f"新建并启动: 创建/启动阶段被强制停止: {result}")
                return
            self._log(f"新建并启动结果: {result}")
            new_ids = result.get("new_ids") or []
            boot = result.get("boot") or {}
            try:
                ids_int = [int(i) for i in new_ids]
                self.cfg["last_selected_vms"] = ids_int
                from core.config_store import save_config
                save_config(self._collect_cfg() if hasattr(self, "_collect_cfg") else self.cfg)
                self._log(f"已选中新建VM: {ids_int}")
            except Exception as exc:
                self._log(f"更新 last_selected_vms 失败: {exc}")

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
            from concurrent.futures import ThreadPoolExecutor, as_completed

            if self._task_cancelled():
                self._log("装包阶段: 已强制停止，跳过 provision")
                return
            # 启动失败的也进装包池：provision 内会再 wait boot，避免 10 台只剩 4~8 台在跑
            booted = [idx for idx in new_ids if boot.get(idx, True)]
            slow = [idx for idx in new_ids if not boot.get(idx, True)]
            for idx in slow:
                self._log(f"VM={idx} 启动未在限时内完成，仍进入装包线程二次等待")
            todo = list(new_ids)
            if len(todo) != len(new_ids):
                self._log(f"装包列表异常 todo={todo} new_ids={new_ids}")
            prov_workers = max(1, min(int(workers), len(todo) or 1))
            self._log(
                f"并行装包/provision: todo={todo} booted={booted} slow={slow} "
                f"线程={prov_workers}/{workers} create_count目标并行 opts={install_opts} aurora={prefer_aurora}"
            )
            if prov_workers < len(todo):
                self._log(
                    f"警告: 装包线程 {prov_workers} < 待装 {len(todo)}，"
                    f"请把【新建启动线程】调到 >= 新建数量以实现同步安装"
                )

            # 捕获本轮任务取消令牌，避免新任务替换 self._bg_cancel 后旧装包线程复活
            task_cancel_ev = getattr(self, "_bg_cancel", None) or threading.Event()
            task_bg_gen = int(getattr(self, "_bg_gen", 0) or 0)

            def _job_cancelled() -> bool:
                try:
                    if task_cancel_ev.is_set():
                        return True
                except Exception:
                    pass
                try:
                    return int(getattr(self, "_bg_gen", 0) or 0) != task_bg_gen
                except Exception:
                    return False

            def _prov(idx: int, order: int = 0):
                if _job_cancelled():
                    return idx, {"cancelled": True}, None
                try:
                    # 轻微错峰：保持近乎同时，但避免 10 路同一毫秒打满 adb
                    if order:
                        end = time.time() + min(4.0, 0.45 * order)
                        while time.time() < end:
                            if _job_cancelled():
                                return idx, {"cancelled": True}, None
                            time.sleep(0.05)
                    self._log(
                        f"VM={idx} 装包线程启动 order={order+1}/{len(todo)} "
                        f"workers={prov_workers}"
                    )
                    out = self._provision_new_vm(
                        idx,
                        boot_timeout=boot_timeout,
                        install_opts=install_opts,
                        prefer_aurora=prefer_aurora,
                    )
                    return idx, out, None
                except BaseException as exc:
                    # TaskCancelled 继承 BaseException；停止时不当成普通失败
                    try:
                        from core.root_setup import TaskCancelled
                        if isinstance(exc, TaskCancelled) or _job_cancelled():
                            return idx, {"cancelled": True, "status": "cancelled"}, None
                    except Exception:
                        if _job_cancelled():
                            return idx, {"cancelled": True, "status": "cancelled"}, None
                    if isinstance(exc, Exception):
                        return idx, None, exc
                    raise

            if todo and not self._task_cancelled():
                from concurrent.futures import wait, FIRST_COMPLETED
                ex = ThreadPoolExecutor(max_workers=prov_workers)
                futs = []
                try:
                    futs = [ex.submit(_prov, i, n) for n, i in enumerate(todo)]
                    pending = set(futs)
                    # instant-stop-v2: 不再用 as_completed 死等；0.3s 轮询取消
                    while pending:
                        if _job_cancelled() or self._task_cancelled():
                            self._log("装包: 检测到停止任务，立即取消线程池/打断 ADB...")
                            try:
                                from core.adb_client import AdbClient
                                AdbClient.request_cancel_all()
                                AdbClient.interrupt_all()
                            except Exception:
                                pass
                            for f in list(pending):
                                try:
                                    f.cancel()
                                except Exception:
                                    pass
                            break
                        done, pending = wait(pending, timeout=0.3, return_when=FIRST_COMPLETED)
                        if not done:
                            continue
                        for fut in done:
                            try:
                                idx, out, exc = fut.result(timeout=0)
                            except Exception as exc2:
                                self._log(f"装包 future 异常: {exc2}")
                                continue
                            if exc is not None:
                                self._log(f"VM={idx} 新建装包异常: {exc}")
                            else:
                                st = ""
                                try:
                                    st = str((out or {}).get("status") or "")
                                except Exception:
                                    st = ""
                                if st == "cancelled":
                                    self._log(f"VM={idx} 新建装包已取消")
                                else:
                                    self._log(f"VM={idx} 新建装包完成: {str(out)[:220]}")
                finally:
                    try:
                        # immediate-stop-v1/v2: 不要 wait=True 卡死在 adb install 上
                        ex.shutdown(wait=False, cancel_futures=True)
                    except TypeError:
                        try:
                            ex.shutdown(wait=False)
                        except Exception:
                            pass
                    except Exception as exc:
                        self._log(f"装包线程池关闭警告: {exc}")
            if new_ids and self._task_cancelled():
                self._log("装包后收尾已跳过（任务已停止）")
            if new_ids and not self._task_cancelled():
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

        self._run_bg("新建并启动", job)

    def _provision_new_vm(
        self,
        vmindex: int,
        *,
        boot_timeout: int = 240,
        install_opts: dict | None = None,
        prefer_aurora: bool = False,
    ) -> dict:
        """单台新建模拟器：装包 + Kitsune DirectInstall + Zygisk/Hide/SuList + ih8 + Venmo。"""
        from core.root_setup import RootSetup

        # zombie-cancel-v2: 捕获本任务 Event+代际；新任务/停止都不会让本线程复活
        cancel_ev = getattr(self, "_bg_cancel", None) or threading.Event()
        bg_gen = int(getattr(self, "_bg_gen", 0) or 0)

        def _cancelled() -> bool:
            try:
                if cancel_ev.is_set():
                    return True
            except Exception:
                pass
            try:
                return int(getattr(self, "_bg_gen", 0) or 0) != bg_gen
            except Exception:
                return False

        if _cancelled():
            self._log(f"VM={vmindex} provision 已取消")
            return {"vmindex": str(vmindex), "status": "cancelled"}
        self._log(f"VM={vmindex} 开始新建装包 provision ...")
        try:
            self.mumu.adb_connect(vmindex)
        except Exception as exc:
            self._log(f"VM={vmindex} adb_connect: {exc}")
        if _cancelled():
            return {"vmindex": str(vmindex), "status": "cancelled"}
        adb = self.mumu.adb_for(vmindex)
        try:
            adb.set_cancel_check(_cancelled)
        except Exception:
            pass
        try:
            adb.connect()
            adb.wait_device(timeout=min(90, boot_timeout))
        except Exception as exc:
            self._log(f"VM={vmindex} wait_device: {exc}")
        if _cancelled():
            return {"vmindex": str(vmindex), "status": "cancelled"}
        # RootSetup(mumu, adb) — 顺序不可反；APK/模块路径用内置 defaults
        rs = RootSetup(self.mumu, adb)
        try:
            rs.set_cancel_check(_cancelled)
        except Exception:
            pass
        out = rs.provision_new_vm(
            vmindex,
            log=self._log,
            boot_timeout=boot_timeout,
            install_packages=install_opts or {},
            prefer_aurora_venmo=prefer_aurora,
            restart_after_module=True,
        )
        if _cancelled():
            out = dict(out or {})
            out["status"] = "cancelled"
        self._log(f"VM={vmindex} provision 结果: {out}")
        return out

    def launch_selected(self) -> None:
        if not self.mumu:
            return
        ids = self._selected_indices()
        if not ids:
            messagebox.showwarning("提示", "没有选中的模拟器")
            return
        workers = max(1, int(self.var_create_launch.get() or 1))
        boot_timeout = max(60, int(self.var_boot_timeout.get() or 240))
        defaults = self.cfg.get("create_defaults", {})

        def job() -> None:
            from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

            if self._task_cancelled():
                self._log("启动选中: 已取消")
                return
            self._log(f"启动选中 VM={ids} 线程={workers}")

            def one(idx: int) -> tuple[int, bool]:
                if self._task_cancelled():
                    return idx, False
                ok = self.mumu.launch_and_wait(
                    idx,
                    timeout=boot_timeout,
                    defaults=defaults,
                    log=self._log,
                    ensure_settings=True,
                    cancel_check=self._task_cancelled,
                )
                return idx, ok

            ex = ThreadPoolExecutor(max_workers=min(workers, len(ids)))
            try:
                futs = [ex.submit(one, i) for i in ids]
                pending = set(futs)
                while pending:
                    if self._task_cancelled():
                        self._log("启动选中: 检测到停止，立即结束等待")
                        for f in list(pending):
                            try:
                                f.cancel()
                            except Exception:
                                pass
                        break
                    done, pending = wait(pending, timeout=0.3, return_when=FIRST_COMPLETED)
                    if not done:
                        continue
                    for fut in done:
                        try:
                            idx, ok = fut.result(timeout=0)
                            self._log(f"启动结果 VM={idx} android={ok}")
                        except Exception as exc:
                            self._log(f"启动 future 异常: {exc}")
            finally:
                try:
                    ex.shutdown(wait=False, cancel_futures=True)
                except TypeError:
                    ex.shutdown(wait=False)
            if self._task_cancelled():
                self._log("启动选中: 已停止，跳过排列")
                return
            if self.var_sort.get():
                try:
                    self.mumu.layout_row_from_top_left(
                        ids,
                        auto_fit=bool(self.cfg.get("window_auto_fit", True)),
                        margin=0 if bool(self.cfg.get("window_auto_fit", True)) else int(self.cfg.get("window_margin", 0) or 0),
                    )
                except Exception as exc:
                    self._log(f"排列警告: {exc}")

        self._run_bg("启动选中", job)

    def fix_settings_selected(self) -> None:
        if not self.mumu:
            return
        ids = self._selected_indices()
        if not ids:
            messagebox.showwarning("提示", "没有选中的模拟器")
            return
        defaults = self.cfg.get("create_defaults", {})

        def job() -> None:
            for idx in ids:
                self.mumu.apply_create_defaults(idx, defaults, log=self._log, force_offline=True)

        self._run_bg("修复配置", job)

    def shutdown_selected(self) -> None:
        if not self.mumu:
            return

        def job() -> None:
            for idx in self._selected_indices():
                try:
                    self.mumu.shutdown(idx)
                    self._log(f"shutdown VM={idx}")
                except Exception as exc:
                    self._log(f"shutdown 失败 {idx}: {exc}")

        self._run_bg("关机选中", job)


    def delete_selected(self) -> None:
        """勾选/索引选中的模拟器：先结束进程(shutdown)再删除实例。"""
        if not self.mumu:
            return
        ids = self._selected_indices()
        if not ids:
            messagebox.showwarning("提示", "请先勾选或填写要删除的模拟器索引")
            return
        ids = sorted(set(int(x) for x in ids))
        tip = "、".join(str(i) for i in ids[:20])
        if len(ids) > 20:
            tip += f"… 共{len(ids)}台"
        ok = messagebox.askyesno(
            "确认删除模拟器",
            f"将结束进程并永久删除以下模拟器：\n\n{tip}\n\n"
            f"此操作不可恢复。确定删除？",
            icon=messagebox.WARNING,
        )
        if not ok:
            self._log("已取消删除")
            return

        def job() -> None:
            if self._task_cancelled():
                self._log("删除选中: 已取消")
                return
            self._log(f"开始删除模拟器: {ids}（先 shutdown 再 delete）")
            try:
                result = self.mumu.delete_vms(
                    ids,
                    shutdown_first=True,
                    wait_after_shutdown=2.0,
                    log=self._log,
                )
            except Exception as exc:
                self._log(f"删除流程异常: {exc}")
                result = {"ok": [], "fail": {"*": str(exc)}, "deleted": []}

            # 清理 kitsune 状态缓存
            try:
                from paths import DATA_STATE_DIR
                for idx in result.get("deleted") or result.get("ok") or []:
                    p = DATA_STATE_DIR / f"kitsune_ok_vm{int(idx)}.json"
                    if p.exists():
                        p.unlink(missing_ok=True)
                        self._log(f"已清理 kitsune 缓存: {p.name}")
            except Exception as exc:
                self._log(f"清理 kitsune 缓存警告: {exc}")

            # 从 last_selected / 勾选中移除
            deleted = set(int(x) for x in (result.get("deleted") or result.get("ok") or []))
            fail = result.get("fail") or {}
            self._log(
                f"删除完成: ok={sorted(deleted)} fail={fail}"
            )
            try:
                last = [int(x) for x in (self.cfg.get("last_selected_vms") or []) if int(x) not in deleted]
                self.cfg["last_selected_vms"] = last
                self.var_vms.set(",".join(str(x) for x in last))
            except Exception:
                pass

            def after() -> None:
                try:
                    self.refresh_vms()
                except Exception as exc:
                    self._log(f"删除后刷新失败: {exc}")
                if deleted and not fail:
                    messagebox.showinfo("删除完成", f"已删除模拟器: {sorted(deleted)}")
                elif deleted and fail:
                    messagebox.showwarning(
                        "部分删除",
                        f"成功: {sorted(deleted)}\n失败: {fail}",
                    )
                elif fail:
                    messagebox.showerror("删除失败", str(fail))

            self.after(0, after)

        self._run_bg("删除选中模拟器", job)


    def sort_windows(self) -> None:
        """按数量+屏幕分辨率一字紧贴排列（无缝隙、9:16 防黑边）。不调用 MuMu 网格 sort。"""
        if not self.mumu:
            return

        def job() -> None:
            try:
                ids = self._selected_indices()
                if not ids:
                    # 未勾选时：优先已启动进程，否则全部
                    try:
                        info = self.mumu.info("all") or {}
                    except Exception:
                        info = {}
                    running = []
                    all_ids = []
                    for k, v in (info.items() if isinstance(info, dict) else []):
                        if not str(k).isdigit():
                            continue
                        idx = int(k)
                        all_ids.append(idx)
                        if isinstance(v, dict) and (
                            v.get("is_process_started") or v.get("is_android_started")
                        ):
                            running.append(idx)
                    ids = sorted(running) if running else sorted(all_ids)
                if not ids:
                    self._log("一字排列：没有可排列的模拟器")
                    return
                auto_fit = bool(self.cfg.get("window_auto_fit", True))
                # 自动适配时忽略旧固定宽高与 margin，强制无缝隙
                if auto_fit:
                    layout = self.mumu.layout_row_from_top_left(
                        ids,
                        auto_fit=True,
                        margin=0,
                        start_x=0,
                        start_y=0,
                    )
                else:
                    layout = self.mumu.layout_row_from_top_left(
                        ids,
                        width=int(self.cfg.get("window_width", 360)),
                        height=int(self.cfg.get("window_height", 640)),
                        margin=int(self.cfg.get("window_margin", 0) or 0),
                        auto_fit=False,
                        start_x=0,
                        start_y=0,
                    )
                self._log(
                    "一字排列完成: "
                    f"vms={layout.get('indices')} "
                    f"size={layout.get('width')}x{layout.get('height')} "
                    f"step_x={layout.get('step_x')} chrome={layout.get('chrome_w')}x{layout.get('chrome_h')} "
                    f"margin={layout.get('margin')} auto_fit={layout.get('auto_fit')} tile={layout.get('tile')}"
                )
            except Exception as exc:
                self._log(f"排列失败: {exc}")

        self._run_bg("一字排列", job)

    def restart_selected(self) -> None:
        if not self.mumu:
            return

        def job() -> None:
            for idx in self._selected_indices():
                try:
                    self.mumu.restart(idx)
                    self._log(f"restart device VM={idx}")
                except Exception as exc:
                    self._log(f"restart 失败 {idx}: {exc}")

        self._run_bg("重启选中", job)


    def _ensure_import_source(self, text: str, preferred: str | Path | None = None) -> Path:
        """保证有可实时删除的导入源文件；返回 source_path。"""
        from pathlib import Path as _P
        if preferred:
            path = _P(preferred)
        elif getattr(self.store, "source_path", None):
            path = _P(self.store.source_path)
        else:
            path = ACCOUNTS_INPUT_DIR / "import_active.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        body = (text or "").replace("\r\n", "\n").replace("\r", "\n")
        if body and not body.endswith("\n"):
            body += "\n"
        atomic_write_text(path, body, encoding="utf-8")
        self.store.set_source_path(path)
        return path

    def _refresh_import_text(self, log_acc=None) -> None:
        """用待登录账号刷新导入文本框（主线程调用）。"""
        pending = self.store.pending_source_text()
        self.txt_accounts.delete("1.0", tk.END)
        if pending:
            self.txt_accounts.insert(tk.END, pending)
        self._update_stats()
        try:
            self.lbl_export.configure(text=self._export_status_text())
        except Exception:
            pass
        if log_acc is not None:
            a1 = getattr(log_acc, "account1", "") or ""
            st = getattr(log_acc, "status", "") or ""
            self._log(
                f"导入文本已更新: 删除 {a1} ({st})，剩余待登录 {self.store.remaining()} 条"
            )


    def import_accounts(self) -> None:
        path = filedialog.askopenfilename(
            title="选择账号文件",
            initialdir=str(ACCOUNTS_SAMPLES_DIR if ACCOUNTS_SAMPLES_DIR.exists() else PROJECT_ROOT),
            filetypes=[("Text", "*.txt"), ("All", "*.*")],
        )
        if not path:
            return
        accs = load_accounts_from_file(path)
        n = self.store.load(accs, source_path=path)
        st = getattr(self.store, "last_load_stats", {}) or {}
        # 文本框只显示待登录；源文件已删掉明确成功/失败
        self._refresh_import_text()
        self._log(
            f"导入完成 from {path} | 原始 {st.get('imported', len(accs))} 条 | "
            f"跳过已明确成功/失败 {st.get('skipped', 0)} 条 | "
            f"源文件删除 {st.get('pruned', 0)} 行 | 待登录 {n} 条"
        )
        self._log("登录出结果后会实时从导入文本/源文件删除对应账号")

    def load_from_text(self) -> None:
        text = self.txt_accounts.get("1.0", tk.END)
        # 文本加载也落到可实时删除的源文件
        src = self._ensure_import_source(text)
        accs = load_accounts_from_text(text)
        n = self.store.load(accs, source_path=src)
        st = getattr(self.store, "last_load_stats", {}) or {}
        self._refresh_import_text()
        self._log(
            f"从文本框加载 | 原始 {st.get('imported', len(accs))} 条 | "
            f"跳过已明确成功/失败 {st.get('skipped', 0)} 条 | 待登录 {n} 条 | 源={src}"
        )

    def export_all(self) -> None:
        # 只导出会话快照; 四类固定文本已实时叠加, 勿 snapshot 覆盖
        path = self.store.export_all()
        paths = self.store.classified_paths()
        self._log(
            f"会话快照: {path} | 固定叠加: "
            f"{paths.get('correct')} | {paths.get('risk_control')} | {paths.get('wrong_password')} | {paths.get('no_network')}"
        )
        messagebox.showinfo(
            "导出",
            f"会话快照:\n{path}\n\n固定四类(叠加):\n"
            f"{paths.get('correct')}\n{paths.get('risk_control')}\n{paths.get('wrong_password')}\n{paths.get('no_network')}",
        )

    def browse_export_dir(self) -> None:
        d = filedialog.askdirectory(
            title="选择导出目录(四类固定文本)",
            initialdir=(self.var_export_dir.get() or str(EXPORT_CLASSIFIED_DIR)),
        )
        if not d:
            return
        self.var_export_dir.set(d)
        self.apply_export_dir()

    def apply_export_dir(self) -> None:
        raw = (self.var_export_dir.get() or "").strip()
        d = resolve_export_dir(raw or None)
        self.var_export_dir.set(str(d))
        self.store.set_export_dir(d)
        self.cfg["export_dir"] = str(d)
        self.lbl_export.configure(text=self._export_status_text())
        self._log(f"导出目录已应用: {d}")

    def open_export_dir(self) -> None:
        d = resolve_export_dir((self.var_export_dir.get() or "").strip() or None)
        d.mkdir(parents=True, exist_ok=True)
        os.startfile(str(d))

    def _export_status_text(self) -> str:
        p = self.store.classified_paths()
        return (
            f"导出: {p.get('export_dir')} | "
            f"correct / risk_control / wrong_password / no_network"
        )

    def _on_account_finished(self, acc) -> None:
        """登录导出成功/失败后：实时刷新导入文本（源文件已在 store.finish 删除）。"""
        def ui() -> None:
            try:
                self._refresh_import_text(log_acc=acc)
            except Exception as exc:
                self._log(f"刷新待处理账号文本失败: {exc}")

        try:
            self.after(0, ui)
        except Exception:
            try:
                ui()
            except Exception:
                pass

    def reload_proxies(self) -> None:
        n = self.proxy_pool.load_file(PROXY_FILE)
        ideas = DOCS_DIR / "思路.txt"
        if ideas.exists():
            self.proxy_pool.attach_change_ip(load_change_ip_map(ideas))
        self._replace_proxy_editor_rows(load_proxy_entries(PROXY_FILE))
        self._log(f"重载代理 {n} 条 profiles={self.proxy_pool.names()}")

    def save_settings(self) -> None:
        if not self._save_proxy_editor(show_message=False):
            return
        cfg = self._collect_cfg()
        save_config(cfg)
        self._log("配置已保存")
        messagebox.showinfo("保存", "配置已写入 config.json")


    def _set_run_buttons(self, running: bool, stopping: bool = False) -> None:
        """同步顶部/底栏开始与停止按钮外观。"""
        if stopping:
            start_state = tk.DISABLED
            stop_state = tk.NORMAL  # 允许再点一次强制停止
            state_text = "停止中(再点=强制)"
            stop_bg = "#e65100"
        elif running:
            start_state = tk.DISABLED
            stop_state = tk.NORMAL
            state_text = "运行中 — 可点■停止"
            stop_bg = "#c62828"
        else:
            start_state = tk.NORMAL
            stop_state = tk.DISABLED
            state_text = "空闲"
            stop_bg = "#b0b0b0"
        for b in (getattr(self, "btn_start", None), getattr(self, "btn_start_bottom", None)):
            if b is not None:
                try:
                    b.configure(state=start_state)
                except Exception:
                    pass
        for b in (getattr(self, "btn_stop", None), getattr(self, "btn_stop_bottom", None)):
            if b is not None:
                try:
                    conf = {"state": stop_state}
                    # only tk.Button has bg
                    if isinstance(b, tk.Button):
                        conf["bg"] = stop_bg
                        conf["text"] = "■ 强制停止" if stopping else "■ 停止"
                    b.configure(**conf)
                except Exception:
                    pass
        if getattr(self, "lbl_run_state", None) is not None:
            try:
                self.lbl_run_state.configure(text=state_text)
            except Exception:
                pass

    def start_login(self) -> None:
        if not self.mumu:
            messagebox.showerror("错误", "MuMuManager 不可用")
            return
        if self._stopping_ui:
            messagebox.showwarning("提示", "正在停止中，请稍候")
            return
        if self.engine and (self.engine.running or self.engine.is_stopping()):
            messagebox.showwarning("提示", "已在登录中或正在停止，请先等待结束")
            return
        # 刷新列表，确保勾选对应当前已有实例
        try:
            self.refresh_vms()
        except Exception as exc:
            self._log(f"启动前刷新模拟器失败: {exc}")

        cfg = self._collect_cfg()
        # 复用已有模拟器，不自动新建
        cfg["reuse_existing_vms_on_start"] = True
        ids = self._selected_indices(for_login=True)
        if not ids:
            messagebox.showwarning(
                "提示",
                "没有可复用的模拟器。请勾选已有实例，或先用「仅新建/新建并启动」创建后再登录。",
            )
            return

        # 过滤不存在
        try:
            exist = set(self.mumu.list_indices())
        except Exception:
            exist = set(ids)
        ids = [i for i in ids if i in exist]
        if not ids:
            messagebox.showwarning("提示", "勾选的模拟器已不存在，请刷新后重选")
            return

        proxy_capacity_ok, proxy_capacity_msg = self._validate_unique_proxy_capacity(ids, cfg)
        self._log(proxy_capacity_msg)
        if not proxy_capacity_ok:
            messagebox.showwarning("代理池不可用", proxy_capacity_msg)
            return
        self.proxy_pool.allow_reuse = bool(cfg.get("allow_proxy_reuse", True))

        # 容量通过后再测连通性；代理少于 Worker 时由代理池自动均衡复用。
        if self._proxy_preflight_in_progress:
            return
        if self._proxy_preflight_passed:
            # 只放行这一次递归启动；下次点击仍重新做启动前检查。
            self._proxy_preflight_passed = False
        elif self._begin_proxy_preflight():
            return

        self.cfg["last_selected_vms"] = list(ids)
        cfg["last_selected_vms"] = list(ids)
        save_config(cfg)
        self.var_vms.set(",".join(str(i) for i in ids))
        # 同步勾选框
        for idx, var in self._vm_check_vars.items():
            var.set(idx in ids)

        if self.store.remaining() <= 0:
            text = self.txt_accounts.get("1.0", tk.END).strip()
            if text:
                # 启动前确保有导入源，登录出结果后可实时删除
                src = self._ensure_import_source(text, preferred=getattr(self.store, "source_path", None))
                self.store.load(load_accounts_from_text(text), source_path=src)
                self._refresh_import_text()
        if self.store.remaining() <= 0:
            messagebox.showwarning("提示", "没有待登录账号，请先导入")
            return

        # 应用导出目录与安装勾选
        try:
            self.store.set_export_dir(cfg.get("export_dir") or None)
            self.var_export_dir.set(str(self.store.export_dir))
        except Exception as exc:
            self._log(f"应用导出目录警告: {exc}")

        self.engine = WorkerEngine(
            self.mumu,
            self.store,
            self.proxy_pool,
            cfg,
            ui_log=self._log,
        )
        self.engine.start(ids)
        self._set_run_buttons(running=True, stopping=False)
        self._log(f"登录任务已启动(复用已有模拟器, 不新建): VM={ids}")
        self._log("提示: 顶栏红色【■ 停止】可随时停止(等当前账号完成)")
        self.after(1000, self._poll_engine_state)

    def stop_login(self) -> None:
        """停止: 等当前登录完成 → 关闭模拟器。

        第一次：优雅停止。
        第二次（仍在停止中）：强制停止，缩短等待并关机，避免卡死。
        """
        eng = self.engine
        if not eng:
            self._set_run_buttons(running=False, stopping=False)
            self._log("没有运行中的登录引擎")
            self._stopping_ui = False
            self._stop_job_active = False
            return

        # 第二次点击：强制停止
        if self._stopping_ui:
            self._log("检测到再次点击停止 → 强制停止（打断当前 NekoBox/登录等待）")
            self._stop_job_active = True
            try:
                eng.stop()
            except Exception as exc:
                self._log(f"强制停止信号失败: {exc}")
            join_timeout = 20.0
            shutdown_vms = bool(self.cfg.get("stop_shutdown_vms", True))

            def force_job() -> None:
                try:
                    result = eng.stop_and_shutdown(
                        join_timeout=join_timeout,
                        shutdown_vms=shutdown_vms,
                        force=True,
                    )
                except Exception as exc:
                    result = {"ok": False, "error": str(exc), "force": True}
                    self._log(f"强制停止异常: {exc}")
                self.after(0, lambda: self._on_stop_done(result))

            threading.Thread(target=force_job, name="force-stop-login", daemon=True).start()
            return

        self._stopping_ui = True
        self._stop_job_active = True
        self._set_run_buttons(running=True, stopping=True)
        # 停止中仍允许再点一次强制停止
        try:
            if getattr(self, "btn_stop", None) is not None:
                self.btn_stop.configure(state=tk.NORMAL, bg="#e65100", text="■ 强制停止")
        except Exception:
            pass
        try:
            eng.stop()
        except Exception as exc:
            self._log(f"发送停止信号失败: {exc}")

        # 第一次点击只发送“不再领新号”的优雅停止信号。当前账号继续完成并
        # 正常写入分类结果，然后 Worker 退出、模拟器关机。第二次点击才走上面
        # 的 force=True 分支打断 ADB/Venmo。
        join_timeout = float(self.cfg.get("stop_join_timeout_seconds", 1800) or 1800)
        if join_timeout < 30:
            join_timeout = 30.0
        shutdown_vms = bool(self.cfg.get("stop_shutdown_vms", True))
        self._log(
            f"停止中: 等待当前账号完成（最长等待 {join_timeout:.0f}s），"
            f"{'完成后关闭' if shutdown_vms else '完成后不关闭'}模拟器。"
        )

        def job() -> None:
            try:
                result = eng.stop_and_shutdown(
                    join_timeout=join_timeout,
                    shutdown_vms=shutdown_vms,
                    force=False,
                )
            except Exception as exc:
                result = {"ok": False, "error": str(exc), "force": False}
                self._log(f"等待当前账号停止异常: {exc}")
            self.after(0, lambda: self._on_stop_done(result))

        threading.Thread(target=job, name="stop-login-graceful", daemon=True).start()

    def _on_stop_done(self, result: dict | None = None) -> None:
        result = result or {}
        # 被强制停止接管：由 force 路径的 _on_stop_done 收尾
        if result.get("superseded_by_force"):
            self._log("优雅停止已移交强制停止，等待强制停止完成...")
            return
        # 普通停止超时且未关模拟器：保持“停止中”，当前登录继续，可再点强制停止
        if result.get("shutdown_skipped") and not result.get("force"):
            self._stop_job_active = False
            self._stopping_ui = True
            self._set_run_buttons(running=True, stopping=True)
            try:
                if getattr(self, "btn_stop", None) is not None:
                    self.btn_stop.configure(state=tk.NORMAL, bg="#e65100", text="■ 强制停止")
            except Exception:
                pass
            self._log(
                f"当前登录未完成，未关闭模拟器: alive_left={result.get('alive_left')} "
                f"vms={result.get('vms')}。任务会继续跑完；再点【强制停止】才打断关机。"
            )
            self.after(1000, self._poll_engine_state)
            return
        # 强停后仍有 Worker 存活时绝不能提前显示“停止完成”。引擎的
        # stop-reaper 会保留取消信号并等待真实退出；UI 同步等到 workers=0。
        alive_left = int(result.get("alive_left") or 0)
        if result.get("cleanup_pending") or alive_left > 0 or not result.get("joined", False):
            self._stop_job_active = False
            self._stopping_ui = True
            self._set_run_buttons(running=True, stopping=True)
            try:
                if getattr(self, "btn_stop", None) is not None:
                    self.btn_stop.configure(state=tk.DISABLED, bg="#e65100", text="■ 停止收尾中")
            except Exception:
                pass
            self._log(
                f"强制停止收尾中: alive_left={alive_left}。"
                "仍存活的登录线程退出前不会显示停止完成。"
            )
            self.after(300, self._poll_engine_state)
            return
        self._stop_job_active = False
        self._stopping_ui = False
        self._set_run_buttons(running=False, stopping=False)
        if result.get("ok"):
            self._log(
                f"停止完成: joined={result.get('joined')} "
                f"shutdown={result.get('shutdown')} vms={result.get('vms')}"
            )
        else:
            self._log(
                f"停止结束(有警告): joined={result.get('joined')} "
                f"alive_left={result.get('alive_left')} "
                f"shutdown={result.get('shutdown')} "
                f"errors={result.get('shutdown_errors')}"
            )
        try:
            self.refresh_vms()
        except Exception as exc:
            self._log(f"停止后刷新列表失败: {exc}")

    def _poll_engine_state(self) -> None:
        """登录运行期间轮询引擎状态；全部结束后恢复按钮。"""
        eng = self.engine
        if self._stopping_ui:
            # stop_and_shutdown 仍在等待当前账号或正在关机时，即使 Worker 已归零，
            # 也必须等它的完成回调再恢复空闲；旧版会提前显示“停止完成”，随后
            # start_login 又读到旧 stop Event，造成状态自相矛盾。
            if getattr(self, "_stop_job_active", False):
                self.after(300, self._poll_engine_state)
                return
            alive = eng.alive_workers() if eng else 0
            if alive > 0:
                self.after(300, self._poll_engine_state)
                return
            # 所有 Worker 真正退出后才切回空闲并恢复全局 ADB 取消状态。
            try:
                finalize = getattr(eng, "_finalize_stopped_state", None) if eng else None
                if callable(finalize):
                    finalize()
            except Exception as exc:
                self._log(f"停止收尾状态同步警告: {exc}")
            self._stopping_ui = False
            self._stop_job_active = False
            self._set_run_buttons(running=False, stopping=False)
            self._log("强制停止完成: workers=0，实时日志已停止")
            try:
                self.refresh_vms()
            except Exception:
                pass
            return
        if not eng:
            self._set_run_buttons(running=False, stopping=False)
            return
        # running 是本轮已启动标记，不会由最后一个 Worker 自动改回 False；
        # 真实运行态必须以存活 Worker 为准，否则自然结束后会永远被判为登录中。
        if eng.alive_workers() > 0:
            # 可选：状态栏显示当前登录
            try:
                cur = eng.current_logins()
                if cur:
                    self.lbl_export.configure(
                        text="登录中: " + ", ".join(f"{k}={v}" for k, v in list(cur.items())[:4])
                    )
            except Exception:
                pass
            # 不再让 VM 勾选框/底部状态长期停在启动前的 OFF 快照；该刷新只读
            # 当前窗口与 Engine 内存状态，不调用 MuMuManager/ADB，也不改变勾选。
            try:
                self._refresh_live_vm_task_status()
            except Exception:
                pass
            # 登录过程中兜底刷新导入文本（finish 回调为主，轮询防漏）
            try:
                pending = self.store.pending_source_text()
                cur_text = self.txt_accounts.get("1.0", tk.END)
                if (pending or "").strip() != (cur_text or "").strip():
                    self.txt_accounts.delete("1.0", tk.END)
                    if pending:
                        self.txt_accounts.insert(tk.END, pending)
                    self._update_stats()
            except Exception:
                pass
            self.after(1000, self._poll_engine_state)
            return
        # 自然结束：同步归零 Engine 的 running/stopping/stop Event，保证可立即再开。
        try:
            finalize = getattr(eng, "_finalize_stopped_state", None)
            if callable(finalize):
                finalize()
        except Exception as exc:
            self._log(f"登录结束状态同步警告: {exc}")
        self._set_run_buttons(running=False, stopping=False)
        self._log("登录引擎已全部结束")
        try:
            pending = self.store.pending_source_text()
            self.txt_accounts.delete("1.0", tk.END)
            if pending:
                self.txt_accounts.insert(tk.END, pending)
        except Exception:
            pass
        self.lbl_export.configure(text=self._export_status_text())
        try:
            self.refresh_vms()
        except Exception:
            pass



def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()

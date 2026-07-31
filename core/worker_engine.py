# 2026-07-31 immediate-stop-v1: force 停登录时打断 ADB，join 上限 8s
# 2026-07-25 layout-tight-v1: 登录线程一字紧贴排列 auto_fit margin=0
# -*- coding: utf-8 -*-
"""多线程 Worker：启模拟器 -> STEP1 Kitsune -> 装包 -> STEP3 NekoBox代理 -> 登录 -> 导出。
# 2026-07-24 forever-allow-v1: 定时重启0=永不; >0分钟restart后只重开VPN不查Uninstall Magisk
# 2026-07-25 no-tun-refresh-ip-v1: NekoBox无tun时刷绑定刷新链接(3分钟限频)+等5s主机测通后重连/换绑
# 2026-07-25 stop-wait-login-v1: 普通停止必须等当前登录完成才关模拟器；未完成不关机；仅强制停止可超时关机
# 2026-07-25 first-setup-vpn-gate-v1 REVERTED: 恢复 elif，不改原首次setup/STEP3流程

更新记录 2026-07-25:
- proxy-reassign-atomic-v1: 换绑时同步 _vm_proxy/profile_name，SOCKS5+change-ip 整包切换并打日志
- no-net-reassign-v1: no_network 刷IP失败后整包换绑(SOCKS5+change-ip)并重导NekoBox再重试
- no-net-reassign-multi-v2: 无网络刷IP失败后多轮整包换绑；刷IP前同步_vm_proxy；日志校验change-ip随profile切换
更新记录 2026-07-24:
- login-no-reopen-kitsune-v1: 登录缓存命中不打开/不结束 Kitsune，见 Uninstall 即代理登录
- proxy-rebind-no-bare-login-v1: 代理不通换绑；勾选NekoBox禁止无代理登录
- ensure_packages-venmo-v1: 缺包检查阶段勾选 venmo 即装完整 split
- kitsune-login-lite-v1: 登录复用只查 Uninstall Magisk；Settings 仅新建；减少 STEP1 后重复 flags/授权
- priority-check-v1: 启动后第一件事必须 Kitsune；缓存也轻量确认 Uninstall Magisk；NekoBox/代理 UI 严禁抢前
- 登录前不再每次 change-ip
- 仅 RISK_CONTROL / NO_NETWORK 才刷 SOCKS5
- 刷新后等待 5 秒并测连通性；同链接 3 分钟限流
- WRONG_PASSWORD 不刷 IP
- NO_NETWORK 刷 IP 成功后可重试当前账号一次
- 窗口仅 layout_row_from_top_left 单行左上角排列，禁止 MuMu sort 网格
- 按实际 active workers 数量排列，模拟器+SOCKS5+刷新链接会话绑定
- 2026-07-24 网络连通性仅主机检测，禁用模拟器侧 check_device_network
- 2026-07-24 step2: Magisk Direct Install + NekoBox 先加 SOCKS5 再启 VPN 并检测
- 2026-07-24 step3:
  - 启动后优先检查 Kitsune Mask / Magisk
  - step3: Kitsune 检查后 force-stop 其包，避免挡 Venmo
  - NekoBox 已有 Profile 不重复添加，只 Connect
  - 模拟器+SOCKS5+刷新链接会话绑定
  - 每次登录前 pm clear Venmo
  - 仅 risk/no_network 刷绑定 profile 的 IP\n- fix: NekoBox FAB 居中 Connect + release_ui 防卡白; Kitsune 每VM仅首次
- fix2: 每账号/线程结束 release_ui; 首次setup后补验 tun
- 导入 NekoBox 前主机经 SOCKS5 测连通；不通刷 IP 等 5 秒再测，通了才导入
- step4: 停止=等当前登录完成→关模拟器→结束线程; 启动复用已有VM; GUI勾选模拟器
- portrait-lock: ADB就绪/NekoBox后/每次登录前锁定竖屏，禁止自动旋转
- force-stop-fix9: 强制停止 join<=12s；NekoBox 无profile立即 reimport，不空转 Connect
- 2026-07-24 recycle-v1: RISK_CONTROL/NO_NETWORK 连续 N 次(默认5) → 关删模拟器→新建→rebind代理→完整重setup→继续任务
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

from core.account_store import AccountStore, LoginResult
from core.adb_client import AdbClient
from core.mumu_manager import MuMuManager
from core.proxy_pool import (
    ProxyPool,
    ProxyProfile,
    check_host_network,
    check_proxy_profile_host,
    check_socks5_proxy_host,
)
from core.root_setup import RootSetup
from core.venmo_login import VenmoLogin
from paths import DATA_SETUP_DIR, DATA_STATE_DIR, ensure_under_root

logger = logging.getLogger("mumuvenmo")
UiCallback = Optional[Callable[[str], None]]

# 触发刷 IP 的登录结果
REFRESH_ON_RESULTS = {LoginResult.RISK_CONTROL, LoginResult.NO_NETWORK}


class WorkerEngine:
    def __init__(
        self,
        mumu: MuMuManager,
        store: AccountStore,
        proxy_pool: ProxyPool,
        config: dict,
        ui_log: UiCallback = None,
    ):
        self.mumu = mumu
        self.store = store
        self.proxy_pool = proxy_pool
        self.config = config
        self.ui_log = ui_log or (lambda m: None)
        self._stop = threading.Event()
        self._stopping = False
        self._threads: list[threading.Thread] = []
        self._vm_indices: list[int] = []
        self._active_indices: list[int] = []
        self._lock = threading.RLock()
        self._current_login: dict[str, str] = {}  # worker_id -> account summary
        self._restart_thread: Optional[threading.Thread] = None
        self._vm_flags: dict[int, dict] = {}
        self._vm_proxy: dict[int, object] = {}
        self.running = False
        # 全局串行 create/delete，避免多线程同时删建冲突
        self._vm_ops_lock = threading.Lock()
        # 强制停止接管优雅停止等待
        self._force_stop_event = threading.Event()
        # 同步代理池刷新参数
        self._sync_proxy_config()

    def _sync_proxy_config(self) -> None:
        try:
            self.proxy_pool.configure(
                min_refresh_interval_seconds=float(
                    self.config.get("proxy_refresh_min_interval_seconds", 180)
                ),
                refresh_wait_seconds=float(
                    self.config.get("proxy_refresh_wait_seconds", 5)
                ),
            )
        except Exception:
            pass

    def log(self, msg: str) -> None:
        logger.info(msg)
        try:
            self.ui_log(msg)
        except Exception:
            pass

    def stop(self) -> None:
        """发送停止信号：不再领取新账号，当前登录任务会跑完。"""
        self._stopping = True
        self._stop.set()
        self.log("停止信号已发送：等待当前登录任务完成，不再领取新账号...")

    def is_stopping(self) -> bool:
        return bool(self._stopping or self._stop.is_set())

    def active_vm_indices(self) -> list[int]:
        with self._lock:
            return list(self._active_indices or self._vm_indices)

    def alive_workers(self) -> int:
        return sum(1 for t in self._threads if t.is_alive())

    def current_logins(self) -> dict[str, str]:
        with self._lock:
            return dict(self._current_login)

    def stop_and_shutdown(
        self,
        *,
        join_timeout: float = 1800.0,
        shutdown_vms: bool = True,
        stop_event: threading.Event | None = None,
        force: bool = False,
    ) -> dict:
        """停止：等当前登录完成 → 再关闭模拟器。

        普通停止(force=False)：
          - 等待当前登录任务跑完（不再领新号）
          - 未 join 完成则 **不关闭模拟器**，保持 _stopping，可再点强制停止
        强制停止(force=True)：
          - 缩短等待后允许关闭模拟器并清理引擎状态
        """
        result = {
            "ok": True,
            "joined": False,
            "alive_left": 0,
            "shutdown": [],
            "shutdown_errors": [],
            "vms": [],
            "force": bool(force),
            "shutdown_skipped": False,
            "superseded_by_force": False,
        }
        if force:
            try:
                self._force_stop_event.set()
            except Exception:
                pass
            try:
                from core.adb_client import AdbClient
                AdbClient.request_cancel_all()
            except Exception as exc:
                self.log(f"强制停止中断 ADB 失败: {exc}")
            join_timeout = min(float(join_timeout), 8.0)
            self.log(f"强制停止: join_timeout 压缩为 {join_timeout:.0f}s，已请求取消 ADB，超时后仍可关模拟器")
        else:
            # 新一轮优雅停止：清除旧强制标记
            try:
                if not self._force_stop_event.is_set():
                    pass
                else:
                    # 若上一轮强制残留且当前无存活 worker，可清
                    if self.alive_workers() == 0:
                        self._force_stop_event.clear()
            except Exception:
                pass

        self.stop()
        vms = self.active_vm_indices()
        result["vms"] = list(vms)
        self.log(
            f"优雅停止开始: 等待 {len(self._threads)} 个 worker 完成当前登录, "
            f"VM={vms}, join_timeout={join_timeout}s, shutdown_vms={shutdown_vms}, force={bool(force)}"
        )

        # 等线程：当前账号登录中的会自然 finish 后退出 while
        deadline = time.time() + max(5.0, float(join_timeout))
        while time.time() < deadline:
            if stop_event is not None and stop_event.is_set():
                break
            if not force:
                try:
                    if self._force_stop_event.is_set():
                        result["superseded_by_force"] = True
                        result["ok"] = False
                        self.log("优雅停止被【强制停止】接管，本路径退出（不重复关机/清状态）")
                        return result
                except Exception:
                    pass
            alive = [t for t in self._threads if t.is_alive()]
            if not alive:
                break
            cur = self.current_logins()
            if cur:
                self.log(
                    "等待当前登录完成: "
                    + ", ".join(f"{k}={v}" for k, v in list(cur.items())[:8])
                )
            else:
                self.log(f"等待 worker 退出, 剩余={len(alive)}")
            for t in alive:
                t.join(timeout=2.0)
            time.sleep(0.3)

        if not force:
            try:
                if self._force_stop_event.is_set():
                    result["superseded_by_force"] = True
                    result["ok"] = False
                    self.log("优雅停止被【强制停止】接管，本路径退出")
                    return result
            except Exception:
                pass

        alive_left = self.alive_workers()
        result["alive_left"] = alive_left
        result["joined"] = alive_left == 0
        if alive_left:
            self.log(
                f"警告: {alive_left} 个 worker 在超时后仍存活"
                + ("；强制停止将继续关模拟器并结束状态" if force else "；普通停止不关模拟器，请再点【强制停止】或继续等待")
            )
            result["ok"] = False if not force else True
            result["forced_alive"] = alive_left
        else:
            self.log("所有 worker 已结束当前任务")

        # 普通停止：未完成当前登录 → 绝不关模拟器，也不清 worker 状态
        if (not result["joined"]) and (not force):
            result["shutdown_skipped"] = True
            result["ok"] = False
            if shutdown_vms and vms:
                self.log(
                    "当前登录任务尚未完成：跳过关闭模拟器，保持停止信号"
                    "（不再领新号；当前号继续跑完后可再点停止，或点【强制停止】打断）"
                )
            else:
                self.log(
                    "当前登录任务尚未完成：保持 worker 继续跑完"
                    "（不再领新号；可再点【强制停止】打断）"
                )
            # 保持 running=True / _stopping=True / threads
            return result

        if shutdown_vms and vms:
            self.log(f"开始关闭模拟器 VM={vms}")
            for idx in vms:
                if stop_event is not None and stop_event.is_set() and not force:
                    break
                try:
                    self.mumu.shutdown(idx)
                    result["shutdown"].append(idx)
                    self.log(f"已关机 VM={idx}")
                except Exception as exc:
                    result["shutdown_errors"].append(f"{idx}:{exc}")
                    self.log(f"关机失败 VM={idx}: {exc}")
        elif not shutdown_vms:
            self.log("配置为停止后不关闭模拟器")

        with self._lock:
            self._current_login.clear()
            self._threads = []
            self.running = False
            self._stopping = False
        try:
            self._force_stop_event.clear()
        except Exception:
            pass
        self.log(
            f"停止结束: joined={result['joined']} shutdown={result['shutdown']} "
            f"skipped={result.get('shutdown_skipped')} errors={result['shutdown_errors']}"
        )
        return result


    def start(self, vm_indices: list[int]) -> None:
        if self.running:
            self.log("已在运行中")
            return
        self._stop.clear()
        self._stopping = False
        with self._lock:
            self._current_login.clear()
        self.running = True
        self._vm_indices = list(vm_indices)
        self._sync_proxy_config()
        workers = min(int(self.config.get("workers", 3)), len(self._vm_indices) or 1)
        if not self._vm_indices:
            self.log("没有可用模拟器索引，请先选择或新建")
            self.running = False
            return
        use = self._vm_indices[:workers]
        self.log(f"启动 {len(use)} 个工作线程, VM={use}")
        self.log(
            "代理刷新规则: 仅风控/无网络刷 IP; "
            f"间隔>={self.proxy_pool.min_refresh_interval_seconds}s; "
            f"刷新后等待 {self.proxy_pool.refresh_wait_seconds}s 再测网"
        )

        self._active_indices = list(use)
        if self.config.get("auto_sort_windows", True):
            try:
                # 仅单行从电脑左上角排列，禁止 sort 网格覆盖
                self.mumu.layout_row_from_top_left(
                    self._active_indices,
                    auto_fit=bool(self.config.get("window_auto_fit", True)),
                    margin=0 if bool(self.config.get("window_auto_fit", True)) else int(self.config.get("window_margin", 0) or 0),
                )
                self.log(f"窗口单行排列 VM={self._active_indices} (no sort)")
            except Exception as exc:
                self.log(f"窗口排列警告: {exc}")

        self._threads = []
        for i, vmindex in enumerate(use):
            t = threading.Thread(
                target=self._worker_loop,
                name=f"VM-{vmindex}",
                args=(vmindex, f"worker-{i}"),
                daemon=True,
            )
            self._threads.append(t)
            t.start()

        interval = float(self.config.get("restart_interval_minutes", 0) or 0)
        if interval > 0:
            self._restart_thread = threading.Thread(
                target=self._restart_loop,
                name="RestartTimer",
                args=(use, interval),
                daemon=True,
            )
            self._restart_thread.start()

    def join(self, timeout: float | None = None) -> None:
        for t in self._threads:
            t.join(timeout=timeout)
        self.running = any(t.is_alive() for t in self._threads)

    def _restart_loop(self, indices: list[int], minutes: float) -> None:
        """定时重启：0=永不；>0 每N分钟 restart，任务继续，只重开VPN不查Uninstall Magisk。"""
        if float(minutes or 0) <= 0:
            self.log("定时重启=0：永久运行，不自动重启模拟器")
            return
        seconds = max(60.0, float(minutes) * 60.0)
        self.log(
            f"定时重启已启用: 每 {minutes} 分钟 mumu.restart；"
            f"重启后仅重开 VPN，不查 Uninstall Magisk"
        )
        while not self._stop.wait(seconds):
            for idx in indices:
                if self._stop.is_set():
                    break
                try:
                    self.log(f"定时重启模拟器 VM={idx}（任务继续，稍后只重开VPN）")
                    try:
                        with self._lock:
                            flags = self._vm_flags.setdefault(int(idx), {})
                            flags["post_timer_restart"] = True
                            flags["skip_kitsune_once"] = True
                    except Exception:
                        pass
                    self.mumu.restart(idx)
                    try:
                        if hasattr(self.mumu, "wait_android_ready"):
                            self.mumu.wait_android_ready(idx, timeout=180)
                        elif hasattr(self.mumu, "wait_boot"):
                            self.mumu.wait_boot(idx, timeout=180)
                    except Exception:
                        pass
                    try:
                        adb = self.mumu.get_adb(idx) if hasattr(self.mumu, "get_adb") else None
                        if adb is None and hasattr(self.mumu, "adb_client"):
                            adb = self.mumu.adb_client(idx)
                        if adb is not None:
                            adb.connect()
                            adb.wait_device(timeout=120)
                    except Exception as exc:
                        self.log(f"定时重启后 ADB 警告 VM={idx}: {exc}")
                    try:
                        from core.root_setup import RootSetup

                        adb = self.mumu.get_adb(idx) if hasattr(self.mumu, "get_adb") else self.mumu.adb_client(idx)
                        rs = RootSetup(adb=adb, mumu=self.mumu, config=self.config)
                        proxy = None
                        try:
                            with self._lock:
                                proxy = self._vm_proxy.get(int(idx))
                        except Exception:
                            proxy = None
                        if proxy is not None and bool(self.config.get("use_nekobox", True)):
                            pname = getattr(proxy, "profile_name", "") or str(proxy)
                            msg = rs.ensure_nekobox_vpn_only(
                                profile_name=pname,
                                log=lambda m, i=idx: self.log(f"VM={i} 定时重启VPN: {m}"),
                                verify_vpn=True,
                                vpn_wait_seconds=25.0,
                            )
                            self.log(f"定时重启后重开 VPN VM={idx}: {msg}")
                        else:
                            self.log(f"定时重启后无绑定代理，跳过 VPN VM={idx}")
                    except Exception as exc:
                        self.log(f"定时重启后重开 VPN 失败 VM={idx}: {exc}")
                except Exception as exc:
                    self.log(f"重启失败 VM={idx}: {exc}")

    def _make_network_check(self, proxy: ProxyProfile | None = None):
        """返回主机侧网络检测函数。

        有 proxy 时优先经 SOCKS5 测连通；否则退回主机直连 generate_204。
        """

        def _check() -> bool:
            if proxy is not None:
                try:
                    if check_proxy_profile_host(proxy, timeout=10.0):
                        return True
                except Exception:
                    pass
            return check_host_network(timeout=8.0)

        return _check

    def _ensure_proxy_ready_before_import(
        self,
        worker_id: str,
        proxy: ProxyProfile | None,
    ) -> dict:
        """导入/启动 NekoBox 前：主机检查代理连通，不通则刷 IP 等 5 秒再测。"""
        if proxy is None:
            self.log(f"{worker_id} 导入前代理检查跳过: 无代理")
            return {
                "ok": True,
                "status": "no_proxy",
                "proxy_ok": True,
                "proxy_ok_before": True,
                "refreshed": False,
                "profile": "",
            }
        min_iv = float(self.config.get("proxy_refresh_min_interval_seconds", 180))
        wait_s = float(self.config.get("proxy_refresh_wait_seconds", 5))
        max_rounds = int(self.config.get("proxy_import_precheck_refresh_rounds", 1))
        self.log(
            f"{worker_id} 导入前主机测 SOCKS5 profile={proxy.profile_name} "
            f"{proxy.host}:{proxy.port} wait={wait_s}s max_refresh={max_rounds}"
        )
        result = self.proxy_pool.ensure_ready_before_import(
            proxy,
            wait_seconds=wait_s,
            min_interval_seconds=min_iv,
            check_timeout=10.0,
            max_refresh_rounds=max_rounds,
            stop_event=self._stop,
        )
        self.log(
            f"{worker_id} 导入前代理检查 status={result.get('status')} "
            f"ok={result.get('ok')} proxy_ok={result.get('proxy_ok')} "
            f"before={result.get('proxy_ok_before')} refreshed={result.get('refreshed')} "
            f"waited={result.get('waited')} checks={result.get('checks')} "
            f"body={str(result.get('refresh_body', ''))[:100]}"
        )
        return result

    def _refresh_proxy_if_needed(
        self,
        worker_id: str,
        proxy: ProxyProfile | None,
        adb: AdbClient | None = None,
        reason: str = "",
    ) -> dict:
        """仅在风控/无网络场景调用。返回 refresh_and_wait_network 结果字典。

        adb 保留参数兼容旧调用，但网络连通性只走主机检测，不读模拟器。
        """
        if proxy is None:
            self.log(f"{worker_id} 刷IP跳过 reason={reason}: 无代理")
            return {
                "ok": True,
                "status": "no_proxy",
                "network_ok": True,
                "body": "",
                "waited": 0.0,
                "remaining_seconds": 0.0,
                "profile": "",
            }
        if not proxy.change_ip_url:
            self.log(f"{worker_id} 刷IP跳过 reason={reason}: 无 change-ip 链接 profile={proxy.profile_name}")
            return {
                "ok": True,
                "status": "no_change_ip_url",
                "network_ok": True,
                "body": "",
                "waited": 0.0,
                "remaining_seconds": 0.0,
                "profile": proxy.profile_name,
            }

        min_iv = float(self.config.get("proxy_refresh_min_interval_seconds", 180))
        wait_s = float(self.config.get("proxy_refresh_wait_seconds", 5))
        cip = str(getattr(proxy, "change_ip_url", "") or "")
        cip_tail = cip[-40:] if cip else "(none)"
        self.log(
            f"{worker_id} 触发刷IP reason={reason} profile={proxy.profile_name} "
            f"change_ip=...{cip_tail} min_interval={min_iv}s wait={wait_s}s"
        )
        result = self.proxy_pool.refresh_and_wait_network(
            proxy,
            min_interval_seconds=min_iv,
            wait_seconds=wait_s,
            check_fn=self._make_network_check(proxy),
            stop_event=self._stop,
        )
        self.log(
            f"{worker_id} 刷IP结果 status={result.get('status')} "
            f"ok={result.get('ok')} network_ok={result.get('network_ok')} "
            f"waited={result.get('waited')} remaining={result.get('remaining_seconds')} "
            f"body={str(result.get('body', ''))[:120]}"
        )
        return result

    def _recover_nekobox_after_no_tun(
        self,
        worker_id: str,
        vmindex: int,
        rs: "RootSetup",
        proxy: ProxyProfile,
    ) -> tuple[ProxyProfile, bool]:
        """NekoBox 已 Connect 仍无 tun：按规则处理绑定代理。

        1) 用当前 profile 的刷新链接刷 IP（3 分钟限频）
        2) 等待 5 秒后主机测 SOCKS5 连通
        3) 关闭再开启 NekoBox（强制 reimport + Connect）
        4) 仍无 tun：整包换绑（SOCKS5 + change-ip 一起换）再导入连接
        返回 (proxy, tun_ok)
        """
        if proxy is None:
            return proxy, False

        # 1+2) 刷绑定刷新链接并主机测通
        ref = self._refresh_proxy_if_needed(
            worker_id,
            proxy,
            reason="nekobox_no_tun",
        )
        net_ok = bool(ref.get("network_ok") or ref.get("ok"))
        if not net_ok:
            try:
                net_ok = bool(check_proxy_profile_host(proxy, timeout=10.0))
            except Exception:
                net_ok = False
            self.log(
                f"{worker_id} 刷IP后主机复测 profile={proxy.profile_name} "
                f"proxy_ok={net_ok} status={ref.get('status')}"
            )
        else:
            self.log(
                f"{worker_id} 刷IP/主机测通完成 profile={proxy.profile_name} "
                f"status={ref.get('status')} network_ok={ref.get('network_ok')}"
            )

        def _stop_vpn() -> None:
            try:
                msg = rs.stop_nekobox_vpn_ui(log=lambda m: self.log(f"{worker_id} {m}"))
                self.log(f"{worker_id} 刷IP前/换绑前已停 VPN: {str(msg)[:160]}")
            except Exception as exc:
                self.log(f"{worker_id} 停 VPN 异常: {exc}")

        def _reimport_connect(p: ProxyProfile, tag: str) -> bool:
            _stop_vpn()
            try:
                msg = rs.ensure_auth_then_connect(
                    p.profile_name,
                    p.host,
                    int(p.port),
                    p.username,
                    p.password,
                    log=lambda m: self.log(f"{worker_id} {m}"),
                    verify_vpn=True,
                    vpn_wait_seconds=25.0,
                    force_reimport=True,
                )
                self.log(f"{worker_id} {tag} NekoBox reimport+connect: {str(msg)[:300]}")
            except Exception as exc:
                self.log(f"{worker_id} {tag} NekoBox reimport+connect 失败: {exc}")
            try:
                ok = bool(rs.is_vpn_active(skip_ui=True))
            except Exception:
                ok = False
            self.log(f"{worker_id} {tag} tun_active={ok} profile={p.profile_name}")
            return ok

        # 3) 当前绑定代理：关再开
        if _reimport_connect(proxy, "刷IP后"):
            return proxy, True

        # 4) 整包换绑
        tried = {str(getattr(proxy, "profile_name", "") or "")}
        max_try = max(1, len(getattr(self.proxy_pool, "proxies", []) or []))
        for _i in range(max_try):
            if self._stop.is_set():
                break
            try:
                alt = self.proxy_pool.reassign(
                    f"vm-{vmindex}",
                    exclude_names=tried,
                )
            except Exception as rexc:
                self.log(f"{worker_id} no_tun 换绑失败: {rexc}")
                break
            if alt is None:
                self.log(
                    f"{worker_id} no_tun 无空闲代理可换绑，保留 profile="
                    f"{proxy.profile_name} 再刷一次自己的 change-ip"
                )
                ref2 = self._refresh_proxy_if_needed(
                    worker_id,
                    proxy,
                    reason="nekobox_no_tun_keep",
                )
                if ref2.get("network_ok") or ref2.get("ok"):
                    if _reimport_connect(proxy, "保留代理再刷后"):
                        return proxy, True
                break

            old_name = str(getattr(proxy, "profile_name", "") or "")
            old_cip = str(getattr(proxy, "change_ip_url", "") or "")
            proxy = alt
            tried.add(str(proxy.profile_name or ""))
            try:
                with self._lock:
                    self._vm_proxy[int(vmindex)] = proxy
            except Exception:
                pass
            cip = str(getattr(proxy, "change_ip_url", "") or "")
            self.log(
                f"{worker_id} no_tun 整包换绑 {old_name} -> {proxy.profile_name} "
                f"endpoint={proxy.host}:{proxy.port} "
                f"cip_changed={old_cip != cip} (SOCKS5+刷新链接一起换)"
            )
            pre = self._ensure_proxy_ready_before_import(worker_id, proxy)
            if not pre.get("ok"):
                self.log(
                    f"{worker_id} 换绑后主机仍不通 profile={proxy.profile_name} "
                    f"status={pre.get('status')}，继续尝试下一条"
                )
                continue
            if _reimport_connect(proxy, "换绑后"):
                return proxy, True

        return proxy, False


    def _update_active_index(self, old_idx: int, new_idx: int) -> list[int]:
        """用 new_idx 替换 active 列表中的 old_idx，并返回最新列表。"""
        with self._lock:
            cur = list(self._active_indices or self._vm_indices or [])
            if old_idx in cur:
                cur = [new_idx if x == old_idx else x for x in cur]
            elif new_idx not in cur:
                cur.append(new_idx)
            # 去重保持顺序
            seen: set[int] = set()
            out: list[int] = []
            for x in cur:
                if x in seen:
                    continue
                seen.add(x)
                out.append(x)
            self._active_indices = out
            # 同步 _vm_indices 中同位置替换
            vms = list(self._vm_indices or [])
            if old_idx in vms:
                self._vm_indices = [new_idx if x == old_idx else x for x in vms]
            return list(self._active_indices)

    def _layout_active_row(self) -> None:
        try:
            indices = self.active_vm_indices()
            if not indices:
                return
            self.mumu.layout_row_from_top_left(
                    indices,
                    auto_fit=bool(self.config.get("window_auto_fit", True)),
                    margin=0 if bool(self.config.get("window_auto_fit", True)) else int(self.config.get("window_margin", 0) or 0),
                )
            self.log(f"窗口单行排列 VM={indices} (recycle/layout)")
        except Exception as exc:
            self.log(f"窗口排列警告(recycle): {exc}")

    def _clear_vm_setup_state(self, vmindex: int, *, reason: str = "") -> None:
        """删除/重建模拟器后清理本机 setup 标记，避免 index 复用走登录轻量路径。

        必须清掉:
        - data/setup_flags/setup_vm_{n}.flag  （否则 is_first_setup=False → 跳过 15-19）
        - data/state/kitsune_ok_vm{n}.json   （否则 Kitsune 缓存误判已完成）
        """
        idx = int(vmindex)
        removed: list[str] = []
        try:
            flag = ensure_under_root(DATA_SETUP_DIR / f"setup_vm_{idx}.flag")
            if flag.exists():
                flag.unlink()
                removed.append(flag.name)
        except Exception as exc:
            self.log(f"[RECYCLE] 清理 setup flag VM={idx} 警告: {exc}")
        try:
            state = ensure_under_root(DATA_STATE_DIR / f"kitsune_ok_vm{idx}.json")
            if state.exists():
                state.unlink()
                removed.append(state.name)
        except Exception as exc:
            self.log(f"[RECYCLE] 清理 kitsune 状态 VM={idx} 警告: {exc}")
        why = f" reason={reason}" if reason else ""
        self.log(
            f"[RECYCLE] 已清理 VM={idx} setup 状态 removed={removed or ['(none)']}{why}"
        )

    def _recycle_vm(
        self,
        worker_id: str,
        old_vmindex: int,
        proxy: ProxyProfile | None,
    ) -> int | None:
        """连续风控/无网：结束进程并删除旧模拟器，新建后迁移代理绑定。

        返回新 vmindex；失败返回 None。
        全局 _vm_ops_lock 串行 create/delete。
        """
        limit = int(self.config.get("consecutive_risk_nonet_limit", 5) or 5)
        self.log(
            f"{worker_id} [RECYCLE] 连续{limit}次 RISK/NO_NET → "
            f"关删 VM={old_vmindex} 并新建迁移任务"
        )
        new_idx: int | None = None
        with self._vm_ops_lock:
            try:
                del_ret = self.mumu.delete_vms(
                    [int(old_vmindex)],
                    shutdown_first=True,
                    wait_after_shutdown=2.0,
                    log=lambda m: self.log(f"{worker_id} {m}"),
                )
                self.log(f"{worker_id} [RECYCLE] delete_vms 结果: {del_ret}")
            except Exception as exc:
                self.log(f"{worker_id} [RECYCLE] 删除旧模拟器异常: {exc}")

            defaults = self.config.get("create_defaults", {}) or {}
            try:
                new_ids = self.mumu.create_configured(
                    1,
                    defaults=defaults,
                    name_prefix="venmo-r",
                    log=lambda m: self.log(f"{worker_id} {m}"),
                )
            except Exception as exc:
                self.log(f"{worker_id} [RECYCLE] 新建模拟器异常: {exc}")
                new_ids = []

            if not new_ids:
                self.log(f"{worker_id} [RECYCLE] 新建失败，无新索引")
                # 代理仍挂在旧 key 上，调用方负责 release
                return None

            new_idx = int(new_ids[0])
            # 关键：MuMu 删建常复用同一 index；旧 setup_vm_N.flag / kitsune_ok 不删
            # 会把全新机误判为「登录复用」→ settings_skip_login + ih8_skip，19 步被砍。
            self._clear_vm_setup_state(int(old_vmindex), reason="recycle_old")
            if int(new_idx) != int(old_vmindex):
                self._clear_vm_setup_state(int(new_idx), reason="recycle_new")
            else:
                self.log(
                    f"{worker_id} [RECYCLE] 新 index 与旧相同={new_idx}，"
                    f"已强制清 setup 标记，下一步走完整新建 Kitsune 19 步"
                )
            self._update_active_index(int(old_vmindex), new_idx)
            self.log(
                f"{worker_id} [RECYCLE] 新模拟器 index={new_idx} "
                f"active={self.active_vm_indices()}"
            )

            # 迁移 sticky SOCKS5 绑定（模拟器+代理+刷新链接一体）
            try:
                if hasattr(self.proxy_pool, "rebind"):
                    rebound = self.proxy_pool.rebind(
                        f"vm-{old_vmindex}", f"vm-{new_idx}"
                    )
                else:
                    # 兼容：先 release 再 assign 同 profile 不保证 sticky，尽量手动
                    rebound = proxy
                    try:
                        self.proxy_pool.release(f"vm-{old_vmindex}")
                    except Exception:
                        pass
                    if rebound is not None:
                        with self.proxy_pool._lock:  # type: ignore[attr-defined]
                            self.proxy_pool._assigned[f"vm-{new_idx}"] = rebound  # type: ignore[attr-defined]
                self.log(
                    f"{worker_id} [RECYCLE] 代理 rebind "
                    f"vm-{old_vmindex} -> vm-{new_idx} "
                    f"profile={(rebound.profile_name if rebound else None)}"
                )
            except Exception as exc:
                self.log(f"{worker_id} [RECYCLE] 代理 rebind 警告: {exc}")

        self._layout_active_row()
        return new_idx

    def _worker_loop(self, vmindex: int, worker_id: str) -> None:
        self.log(f"{worker_id} 绑定模拟器 index={vmindex}")
        # 仅内存预绑定 SOCKS5 配置，绝不在此打开 NekoBox/代理 UI
        proxy = self.proxy_pool.assign(f"vm-{vmindex}")
        try:
            with self._lock:
                self._vm_proxy[int(vmindex)] = proxy
        except Exception:
            pass
        profile_name = proxy.profile_name if proxy else ""
        if proxy:
            self.log(
                f"{worker_id} 预绑定SOCKS5配置(仅内存，未打开代理UI) "
                f"profile={profile_name} ({proxy.masked()})"
            )
        else:
            self.log(f"{worker_id} 无可用 SOCKS5 代理配置")

        defaults = self.config.get("create_defaults", {}) or {}
        boot_timeout = int(self.config.get("boot_timeout_seconds", 240))
        # 更新 2026-07-24(adb-false-ready-v2):
        # launch 后若 ADB 未就绪，强制再 launch_and_wait（修复 VM5 假就绪后半残继续）
        android_ok = False
        adb_ok = False
        serial = ""
        adb = None
        for boot_round in range(1, 4):
            if self._stop.is_set():
                break
            try:
                ok = self.mumu.launch_and_wait(
                    vmindex,
                    timeout=boot_timeout,
                    defaults=defaults,
                    log=lambda m: self.log(f"{worker_id} {m}"),
                    ensure_settings=True,
                )
                android_ok = bool(ok)
                if not ok:
                    self.log(f"{worker_id} Android 启动失败/超时 round={boot_round}/3")
                else:
                    self.log(f"{worker_id} Android 已启动 round={boot_round}")
            except Exception as exc:
                self.log(f"{worker_id} 启动异常 round={boot_round}: {exc}")
                android_ok = False

            try:
                serial = self.mumu.adb_host_port(vmindex)
            except Exception:
                serial = serial or ""
            try:
                self.mumu.adb_connect(vmindex)
            except Exception:
                pass
            adb = AdbClient(self.config.get("adb_path"), serial)
            try:
                adb.connect()
            except Exception:
                pass
            if adb.wait_device(timeout=min(90, boot_timeout)):
                adb_ok = True
                self.log(f"{worker_id} ADB 就绪 serial={serial} round={boot_round}")
                break
            self.log(
                f"{worker_id} ADB 设备未就绪: {serial} round={boot_round}/3 "
                f"(将强制重新 launch，禁止半残继续)"
            )
            adb_ok = False
            time.sleep(2.0)

        if adb is None:
            serial = self.mumu.adb_host_port(vmindex)
            adb = AdbClient(self.config.get("adb_path"), serial)
        if not adb_ok:
            self.log(f"{worker_id} ADB 最终未就绪 serial={serial} android_ok={android_ok}，worker 提前结束")
            if proxy:
                try:
                    self.proxy_pool.release(f"vm-{vmindex}")
                except Exception:
                    pass
            return

        try:
            lp = adb.lock_portrait()
            self.log(
                f"{worker_id} 锁定竖屏: {(lp or '').replace(chr(10), ' ')[:160]} | "
                f"{adb.display_rotation()}"
            )
        except Exception as exc:
            self.log(f"{worker_id} 锁定竖屏失败(继续): {exc}")
        try:
            self.mumu.setting(vmindex, "window_auto_rotate", "false")
        except Exception:
            pass

        use_nekobox = bool(self.config.get("use_nekobox", True))
        setup_done_flag = ensure_under_root(DATA_SETUP_DIR / f"setup_vm_{vmindex}.flag")
        rs = RootSetup(
            self.mumu,
            adb,
            nekobox_pkg=self.config.get("nekobox_package", "moe.nb4a"),
            kitsune_pkg=self.config.get("kitsune_package", "io.github.huskydg.magisk"),
        )
        rs.set_cancel_check(lambda: self._stop.is_set())

        # 新建机 STEP1 前先装缺失的 Kitsune，避免 kitsune_pkg_missing 空跑
        try:
            install_opts_pre = dict(self.config.get("install_packages") or {})
            want_kitsune_pre = bool(install_opts_pre.get("kitsune", True))
            if want_kitsune_pre and not adb.package_installed(
                self.config.get("kitsune_package", "io.github.huskydg.magisk")
            ):
                self.log(f"{worker_id} [STEP1] Kitsune 包缺失，先安装再检查 Uninstall Magisk")
                pre_pkg = rs.ensure_packages(
                    vmindex,
                    install_nekobox=False,
                    install_kitsune=True,
                    install_ih8=False,
                )
                self.log(f"{worker_id} [STEP1] 预装 Kitsune: {pre_pkg}")
        except Exception as exc:
            self.log(f"{worker_id} [STEP1] 预装 Kitsune 警告: {exc}")

        # ===== STEP1: 启动后第一件事必须 Kitsune Mask（严禁 NekoBox/代理抢前）=====
        # 新建(无 setup flag)=可进 Settings；登录复用=只查 Uninstall Magisk
        is_first_setup = not setup_done_flag.exists()
        kitsune_step_ok = False
        skip_kitsune_once = False
        try:
            with self._lock:
                fl = self._vm_flags.setdefault(int(vmindex), {})
                skip_kitsune_once = bool(fl.pop("skip_kitsune_once", False))
                fl.pop("post_timer_restart", None)
        except Exception:
            skip_kitsune_once = False
        try:
            self.log(
                f"{worker_id} [STEP1] 优先检查 Kitsune Mask"
                f"（{'新建设置' if is_first_setup else '登录仅查Uninstall'}，代理尚未打开）"
            )
            if skip_kitsune_once:
                self.log(f"{worker_id} [STEP1] 定时重启后跳过 Uninstall Magisk，仅恢复 VPN")
                mag = {
                    "installed": True,
                    "detail": "skip_kitsune_after_timer_restart",
                    "skipped_cached": True,
                }
                kitsune_step_ok = True
            else:
                mag = rs.ensure_kitsune_priority_check(
                    vmindex,
                    log=lambda m: self.log(f"{worker_id} {m}"),
                    boot_timeout=boot_timeout,
                    configure_settings=bool(is_first_setup),
                )
            self.log(f"{worker_id} [STEP1] Kitsune 结果: {mag}")
            if mag.get("rebooted"):
                try:
                    serial2 = self.mumu.adb_host_port(vmindex)
                    if serial2:
                        adb.serial = serial2
                    self.mumu.adb_connect(vmindex)
                    adb.connect()
                    adb.wait_device(timeout=min(90, boot_timeout))
                except Exception:
                    pass
                rs = RootSetup(
                    self.mumu,
                    adb,
                    nekobox_pkg=self.config.get("nekobox_package", "moe.nb4a"),
                    kitsune_pkg=self.config.get("kitsune_package", "io.github.huskydg.magisk"),
                )
                rs.set_cancel_check(lambda: self._stop.is_set())
            # 登录复用：只确认 Uninstall Magisk，不再二次打开 Superuser/Settings
            # 新建：flags/授权已在 ensure_* 内按 configure_settings 处理，这里不重复开关
            if mag.get("installed") or mag.get("skipped_cached"):
                kitsune_step_ok = True
                if is_first_setup:
                    if mag.get("settings_done"):
                        self.log(f"{worker_id} [STEP1] 新建 Settings 已在 Kitsune 步骤完成")
                    elif not mag.get("skipped_cached"):
                        self.log(
                            f"{worker_id} [STEP1] 新建 Magisk 完成，Settings 将由 full_first_time_setup 兜底"
                        )
                else:
                    self.log(
                        f"{worker_id} [STEP1] 登录路径：已确认 Uninstall Magisk，跳过 Settings/重复授权"
                    )
            else:
                self.log(f"{worker_id} [STEP1] Kitsune 未确认生效(将下次再试): {mag.get('detail')}")
        except Exception as exc:
            self.log(f"{worker_id} [STEP1] Kitsune 检查异常(继续): {exc}")

        # Kitsune 绝不可占前台。登录缓存命中时从未打开，不 force-stop（避免反复打开/结束观感）。
        # 仅在本轮实际打开过 Kitsune 时 force-stop 并回桌面（绝不停 NekoBox）。
        try:
            mag_local = locals().get("mag") or {}
            login_cached_skip = (
                (not is_first_setup)
                and bool(mag_local.get("skipped_cached"))
                and str(mag_local.get("detail") or "").startswith("login_skip_open_kitsune")
            )
            if login_cached_skip:
                self.log(
                    f"{worker_id} [STEP1] 登录缓存命中：跳过 force-stop Kitsune，直接装包/代理"
                )
            else:
                kpkg = self.config.get("kitsune_package", "io.github.huskydg.magisk")
                adb.force_stop(kpkg)
                adb.shell("input", "keyevent", "3", timeout=10)
                try:
                    adb.release_ui_control(home=False)
                except Exception:
                    pass
                self.log(f"{worker_id} [STEP1] 已 force-stop Kitsune 并回桌面(已释放UI)")
        except Exception as exc:
            self.log(f"{worker_id} force-stop Kitsune 警告: {exc}")

        # 复用/首次共用：按 UI 勾选只装缺失的 APP（已装则 already_installed）
        try:
            install_opts = dict(self.config.get("install_packages") or {})
            want_neko = bool(install_opts.get("nekobox", True)) and bool(use_nekobox)
            want_kitsune = bool(install_opts.get("kitsune", True))
            want_ih8 = bool(install_opts.get("ih8", True))
            want_venmo_pkg = bool(install_opts.get("venmo", True))
            pkg_out = rs.ensure_packages(
                vmindex,
                install_nekobox=want_neko,
                install_kitsune=want_kitsune,
                install_ih8=want_ih8,
                install_venmo=want_venmo_pkg,
                prefer_aurora_venmo=bool(self.config.get("prefer_aurora_venmo", False)),
                log=lambda m: self.log(f"{worker_id} {m}"),
            )
            self.log(f"{worker_id} 缺包安装检查: {pkg_out}")
        except Exception as exc:
            self.log(f"{worker_id} 缺包安装检查异常: {exc}")

        # 首次完整安装（包/模块）仅一次
        if not setup_done_flag.exists():
            try:
                # STEP3 首次 setup：导入 NekoBox 前主机测 SOCKS5（STEP1 Kitsune 已完成）
                self.log(f"{worker_id} [STEP3] 首次 setup 前主机测代理（Kitsune 已完成 ok={kitsune_step_ok})")
                pre = self._ensure_proxy_ready_before_import(worker_id, proxy)
                nekobox_now = bool(use_nekobox and proxy is not None and pre.get("ok"))
                if use_nekobox and proxy is not None and not pre.get("ok"):
                    self.log(
                        f"{worker_id} 导入前代理未通 status={pre.get('status')}，"
                        f"首次 setup 暂不导入 NekoBox（包/ROOT 仍继续）"
                    )
                install_opts = dict(self.config.get("install_packages") or {})
                out = rs.full_first_time_setup(
                    vmindex,
                    nekobox_now,
                    proxy if nekobox_now else None,
                    log=lambda m: self.log(f"{worker_id} {m}"),
                    boot_timeout=boot_timeout,
                    install_packages=install_opts,
                )
                self.log(f"{worker_id} 首次安装/ROOT: {out}")
                try:
                    self.mumu.adb_connect(vmindex)
                    adb.connect()
                    adb.wait_device(timeout=min(90, boot_timeout))
                except Exception:
                    pass
                setup_done_flag.write_text("ok\n", encoding="utf-8")
                # 首次 setup 后强制再验一次 VPN/tun（setup 里可能只写了 profile）
                if use_nekobox and proxy is not None:
                    try:
                        if not rs.is_vpn_active(skip_ui=True):
                            self.log(f"{worker_id} 首次后无 tun，补 Connect")
                            msg2 = rs.ensure_nekobox_vpn_only(
                                proxy.profile_name,
                                log=lambda m: self.log(f"{worker_id} {m}"),
                                verify_vpn=True,
                                vpn_wait_seconds=25.0,
                                max_connect_rounds=3,
                            )
                            self.log(f"{worker_id} 首次后 NekoBox: {msg2[:300]}")
                        else:
                            self.log(f"{worker_id} 首次后 NekoBox tun 已激活")
                    except Exception as exc_v:
                        self.log(f"{worker_id} 首次后 VPN 校验异常: {exc_v}")
                try:
                    adb.release_ui_control(home=False)
                    self.log(f"{worker_id} 首次 setup 后已释放 UIAutomator")
                except Exception:
                    pass
            except Exception as exc:
                self.log(f"{worker_id} 首次安装异常(继续登录): {exc}")
        # 原流程：首次 setup 走上面分支；已 setup 的复用机走 elif STEP3。勿改成 if 破坏原流程。
        elif use_nekobox and proxy is not None:
            # STEP3：仅在 STEP1 Kitsune 之后才允许打开 NekoBox/代理 UI
            self.log(
                f"{worker_id} [STEP3] 开始 NekoBox/代理（STEP1 Kitsune 已完成 ok={kitsune_step_ok})"
            )
            # 会话：NekoBox 已有 profile 则只 Connect；否则导入后 Connect
            # 模拟器 + SOCKS5 + 刷新链接绑定在本 worker 的 proxy 上
            try:
                self.log(
                    f"{worker_id} [STEP3] NekoBox 绑定 profile={proxy.profile_name} "
                    f"endpoint={proxy.host}:{proxy.port} change_ip={'yes' if proxy.change_ip_url else 'no'}"
                )
                # 导入 NekoBox 前：主机经 SOCKS5 测连通，不通则刷 IP 等 5 秒再测
                pre = self._ensure_proxy_ready_before_import(worker_id, proxy)
                if not pre.get("ok"):
                    # 当前 profile 不通：
                    # 1) 优先整包换绑到空闲代理（SOCKS5 + 对应 change-ip 一起换）
                    # 2) 无空闲且未超配时不抢别人的代理，继续刷自己的 change-ip
                    tried = {str(getattr(proxy, "profile_name", "") or "")}
                    rebound = False
                    max_try = max(1, len(getattr(self.proxy_pool, "proxies", []) or []))
                    for _try in range(max_try):
                        if self._stop.is_set():
                            break
                        try:
                            alt = self.proxy_pool.reassign(
                                f"vm-{vmindex}",
                                exclude_names=tried,
                            )
                        except Exception as rexc:
                            self.log(f"{worker_id} 换绑代理失败: {rexc}")
                            break
                        if alt is None:
                            self.log(
                                f"{worker_id} 无空闲代理可换绑，保留 profile="
                                f"{getattr(proxy, 'profile_name', '')} 并继续刷自己的 change-ip"
                            )
                            # 再强刷当前 profile 自己的刷新链接 1 轮
                            try:
                                r2 = self.proxy_pool.ensure_ready_before_import(
                                    proxy,
                                    wait_seconds=float(self.config.get("proxy_refresh_wait_seconds", 5)),
                                    min_interval_seconds=float(
                                        self.config.get("proxy_refresh_min_interval_seconds", 180)
                                    ),
                                    check_timeout=10.0,
                                    max_refresh_rounds=1,
                                    stop_event=self._stop,
                                    force_refresh=True,
                                )
                                self.log(
                                    f"{worker_id} 保留原代理再刷 status={r2.get('status')} "
                                    f"ok={r2.get('ok')} profile={proxy.profile_name}"
                                )
                                if r2.get("ok"):
                                    pre = r2
                            except Exception as exc2:
                                self.log(f"{worker_id} 保留原代理再刷失败: {exc2}")
                            break
                        # 整包换绑：SOCKS5 + change-ip 刷新链接随 ProxyProfile 一起切换
                        old_name = sorted(x for x in tried if x)
                        old_proxy = proxy
                        old_cip = str(getattr(old_proxy, "change_ip_url", "") or "") if old_proxy else ""
                        proxy = alt
                        profile_name = str(proxy.profile_name or "")
                        try:
                            with self._lock:
                                self._vm_proxy[int(vmindex)] = proxy
                        except Exception:
                            pass
                        tried.add(str(proxy.profile_name))
                        rebound = True
                        cip = str(getattr(proxy, "change_ip_url", "") or "")
                        cip_tail = cip[-48:] if cip else "(none)"
                        self.log(
                            f"{worker_id} 代理不通，整包换绑 "
                            f"from={old_name} -> profile={proxy.profile_name} "
                            f"endpoint={proxy.host}:{proxy.port} "
                            f"user={proxy.username} "
                            f"change_ip=...{cip_tail} "
                            f"cip_changed={old_cip != cip} "
                            f"cip_has_profile={proxy.profile_name in cip if cip else False} "
                            f"(SOCKS5与刷新链接已一起更换)"
                        )
                        pre = self._ensure_proxy_ready_before_import(worker_id, proxy)
                        if pre.get("ok"):
                            break
                    if not pre.get("ok"):
                        self.log(
                            f"{worker_id} 导入前代理未通 status={pre.get('status')}，"
                            f"已尝试 profiles={sorted(x for x in tried if x)}；勾选NekoBox时禁止无代理登录"
                        )
                        raise RuntimeError(
                            f"proxy_not_ready:{pre.get('status')}"
                        )
                    if rebound:
                        self.log(
                            f"{worker_id} 换绑后代理可用 profile={proxy.profile_name} "
                            f"change_ip_bound={bool(getattr(proxy, 'change_ip_url', ''))}"
                        )
                msg = rs.setup_nekobox_socks5(
                    proxy.profile_name,
                    proxy.host,
                    proxy.port,
                    proxy.username,
                    proxy.password,
                    log=lambda m: self.log(f"{worker_id} {m}"),
                    verify_vpn=True,
                )
                self.log(f"{worker_id} NekoBox: {msg[:400]}")
                if "vpn_active=True" not in msg:
                    if "need_import" in msg or "select_miss=" in msg or "abort_no_profile" in msg:
                        self.log(f"{worker_id} NekoBox 无 profile，强制 URI 导入后重连")
                        try:
                            msg2 = rs.ensure_auth_then_connect(
                                proxy.profile_name,
                                proxy.host,
                                int(proxy.port),
                                proxy.username,
                                proxy.password,
                                log=lambda m: self.log(f"{worker_id} {m}"),
                                verify_vpn=True,
                                vpn_wait_seconds=25.0,
                                force_reimport=True,
                            )
                            self.log(f"{worker_id} NekoBox reimport+connect: {msg2[:300]}")
                            msg = msg + " | " + msg2
                        except Exception as exc2:
                            self.log(f"{worker_id} NekoBox reimport 失败: {exc2}")
                    else:
                        self.log(f"{worker_id} NekoBox VPN 未真开，强制 Connect 多轮验证 tun")
                        try:
                            msg2 = rs.ensure_nekobox_vpn_only(
                                proxy.profile_name,
                                log=lambda m: self.log(f"{worker_id} {m}"),
                                verify_vpn=True,
                                vpn_wait_seconds=25.0,
                                max_connect_rounds=3,
                            )
                            self.log(f"{worker_id} NekoBox retry: {msg2[:300]}")
                            msg = msg + " | " + msg2
                        except Exception as exc2:
                            self.log(f"{worker_id} NekoBox retry 失败: {exc2}")
                # 最终以 tun 为准
                try:
                    tun = rs.is_vpn_active(skip_ui=True)
                    self.log(f"{worker_id} NekoBox 最终 tun_active={tun}")
                    if not tun:
                        self.log(f"{worker_id} 警告: 无 tun0，将额外 force Connect 一轮")
                        try:
                            msg3 = rs.ensure_nekobox_vpn_only(
                                proxy.profile_name,
                                log=lambda m: self.log(f"{worker_id} {m}"),
                                verify_vpn=True,
                                vpn_wait_seconds=30.0,
                                max_connect_rounds=4,
                            )
                            self.log(f"{worker_id} NekoBox force: {msg3[:300]}")
                            tun = rs.is_vpn_active(skip_ui=True)
                        except Exception as exc3:
                            self.log(f"{worker_id} NekoBox force 失败: {exc3}")
                        if not tun:
                            self.log(
                                f"{worker_id} 无 tun0：按规则刷绑定刷新链接"
                                f"(3分钟限频)+等5s主机测通后重连；仍失败则整包换绑"
                            )
                            proxy, tun = self._recover_nekobox_after_no_tun(
                                worker_id,
                                vmindex,
                                rs,
                                proxy,
                            )
                            try:
                                with self._lock:
                                    self._vm_proxy[int(vmindex)] = proxy
                            except Exception:
                                pass
                            if not tun:
                                self.log(
                                    f"{worker_id} 致命: 刷IP/换绑后仍无 tun0，"
                                    f"本 worker 不进入登录 profile="
                                    f"{getattr(proxy, 'profile_name', '')}"
                                )
                                return
                            self.log(
                                f"{worker_id} 恢复 tun 成功 profile="
                                f"{getattr(proxy, 'profile_name', '')}，继续登录"
                            )
                except Exception as exc3:
                    self.log(f"{worker_id} tun 检测异常: {exc3}")
                try:
                    adb.release_ui_control(home=False)
                    self.log(f"{worker_id} NekoBox 后已释放 UIAutomator")
                except Exception:
                    pass
            except Exception as exc:
                self.log(f"{worker_id} NekoBox 配置异常: {exc}")
                if use_nekobox:
                    # 勾选 NekoBox 时代理/VPN 失败则本轮不裸奔登录
                    self.log(f"{worker_id} 勾选NekoBox但代理未就绪，本 worker 结束（不无代理登录）")
                    try:
                        self.proxy_pool.release(f"vm-{vmindex}")
                    except Exception:
                        pass
                    return
        elif use_nekobox and proxy is None:
            self.log(f"{worker_id} 勾选 NekoBox 但无 SOCKS5 可分配，本 worker 结束（不无代理登录）")
            return
        if self.config.get("auto_sort_windows", True):
            try:
                row = getattr(self, "_active_indices", None) or self._vm_indices[
                    : int(self.config.get("workers", 4))
                ]
                self.mumu.layout_row_from_top_left(
                    list(row),
                    auto_fit=bool(self.config.get("window_auto_fit", True)),
                    margin=0 if bool(self.config.get("window_auto_fit", True)) else int(self.config.get("window_margin", 0) or 0),
                )
            except Exception:
                pass

        # 按 UI 勾选安装缺失包：Aurora / Venmo 完整 split（禁止单 base.apk）
        try:
            from core.venmo_install import ensure_venmo_ready, venmo_split_info, ensure_aurora

            install_opts = dict(self.config.get("install_packages") or {})
            want_aurora = bool(install_opts.get("aurora", False))
            want_venmo = bool(install_opts.get("venmo", True))
            if want_aurora:
                try:
                    ok_a = ensure_aurora(adb, log=lambda m: self.log(f"{worker_id} {m}"))
                    self.log(f"{worker_id} Aurora 缺装检查 ok={ok_a}")
                except Exception as exc:
                    self.log(f"{worker_id} Aurora 安装警告: {exc}")
            elif not want_venmo:
                self.log(f"{worker_id} UI 未勾选 Aurora/Venmo，跳过应用商店相关安装")

            if want_venmo:
                prefer_aurora = bool(self.config.get("prefer_aurora_venmo", False)) or want_aurora
                self.log(
                    f"{worker_id} 缺装检查 Venmo prefer_aurora={prefer_aurora} "
                    f"(本地bundle优先，除非勾选Aurora)"
                )
                vr = ensure_venmo_ready(
                    adb,
                    log=lambda m: self.log(f"{worker_id} {m}"),
                    prefer_aurora=prefer_aurora,
                )
                self.log(
                    f"{worker_id} Venmo ready ok={vr.get('ok')} method={vr.get('method')} "
                    f"splits={(vr.get('info') or {}).get('split_count')}"
                )
                if not vr.get("ok"):
                    info = venmo_split_info(adb)
                    self.log(
                        f"{worker_id} Venmo 安装不完整 incomplete splits={info.get('split_count')} "
                        f"paths={info.get('paths')}"
                    )
            else:
                self.log(f"{worker_id} UI 未勾选 Venmo，跳过 Venmo 安装")
        except Exception as exc:
            self.log(f"{worker_id} 检查/安装 Venmo 异常: {exc}")

        venmo = VenmoLogin(
            adb,
            package=self.config.get("venmo_package", "com.venmo"),
            login_timeout=int(self.config.get("login_timeout_seconds", 90)),
            log=lambda m: self.log(f"{worker_id} {m}"),
        )
        max_no_net_retry = int(self.config.get("no_network_retry_after_refresh", 1))
        consecutive_limit = int(self.config.get("consecutive_risk_nonet_limit", 5) or 5)
        consecutive_bad = 0  # RISK_CONTROL / NO_NETWORK 连续计数
        try:
            lp = adb.lock_portrait()
            self.log(
                f"{worker_id} 登录循环前锁定竖屏: "
                f"{(lp or '').replace(chr(10), ' ')[:120]} | {adb.display_rotation()}"
            )
            # 回桌面，避免 NekoBox 前台横屏占屏
            adb.shell("input", "keyevent", "3", timeout=10)
            adb.release_ui_control(home=False)
        except Exception as exc:
            self.log(f"{worker_id} 登录循环前锁定竖屏警告: {exc}")

        while not self._stop.is_set():
            acc = self.store.claim_next(worker_id, vm_index=vmindex, profile=profile_name)
            if acc is None:
                self.log(f"{worker_id} 无更多账号，线程退出")
                break
            self.log(f"{worker_id} 领取账号 line={acc.line_no} a1={acc.account1}")
            with self._lock:
                self._current_login[worker_id] = f"line={acc.line_no} a1={acc.account1}"
            # 注意：登录前不再无条件 change-ip；仅风控/无网络后刷
            try:
                try:
                    lp = adb.lock_portrait()
                    self.log(
                        f"{worker_id} 登录前锁定竖屏: "
                        f"{(lp or '').replace(chr(10), ' ')[:120]} | {adb.display_rotation()}"
                    )
                except Exception as exc_lp:
                    self.log(f"{worker_id} 登录前锁定竖屏警告: {exc_lp}")
                outcome = venmo.login_with_fallback(acc.account1, acc.password, acc.account2)
                # NO_NETWORK：刷 IP（限流+等5秒+测网）成功后重试当前账号
                if (
                    outcome.result == LoginResult.NO_NETWORK
                    and max_no_net_retry > 0
                    and not self._stop.is_set()
                ):
                    for attempt in range(max_no_net_retry):
                        if self._stop.is_set():
                            break
                        # 始终用当前 VM 绑定的整包代理（SOCKS5+change-ip），避免旧引用
                        try:
                            with self._lock:
                                bound = self._vm_proxy.get(int(vmindex))
                            if bound is not None:
                                proxy = bound
                                profile_name = str(proxy.profile_name or "")
                        except Exception:
                            pass
                        r = self._refresh_proxy_if_needed(
                            worker_id, proxy, adb, reason=f"no_network_retry#{attempt+1}"
                        )
                        if not r.get("ok"):
                            # 当前 profile 刷IP/测网失败：多轮整包换绑（SOCKS5+对应刷新链接一起换）
                            self.log(
                                f"{worker_id} 无网络刷IP失败 status={r.get('status')} "
                                f"profile={getattr(proxy, 'profile_name', '')}，"
                                f"change_ip_profile_in_url="
                                f"{('yes' if proxy and proxy.profile_name and proxy.profile_name in str(getattr(proxy,'change_ip_url','') or '') else 'no')}，"
                                f"尝试整包换绑"
                            )
                            tried = {str(getattr(proxy, "profile_name", "") or "")}
                            rebound_ok = False
                            max_try = max(1, len(getattr(self.proxy_pool, "proxies", []) or []))
                            for _try in range(max_try):
                                if self._stop.is_set():
                                    break
                                try:
                                    alt = self.proxy_pool.reassign(
                                        f"vm-{vmindex}",
                                        exclude_names=tried,
                                    )
                                except Exception as rexc:
                                    self.log(f"{worker_id} 无网络换绑异常: {rexc}")
                                    alt = None
                                if alt is None:
                                    self.log(
                                        f"{worker_id} 无网络重试中止: 刷IP/测网失败且无可用换绑 "
                                        f"status={r.get('status')} tried={sorted(x for x in tried if x)}"
                                    )
                                    break
                                old_name = str(getattr(proxy, "profile_name", "") or "")
                                old_cip = str(getattr(proxy, "change_ip_url", "") or "")
                                proxy = alt
                                profile_name = str(proxy.profile_name or "")
                                tried.add(profile_name)
                                try:
                                    with self._lock:
                                        self._vm_proxy[int(vmindex)] = proxy
                                except Exception:
                                    pass
                                cip = str(getattr(proxy, "change_ip_url", "") or "")
                                cip_tail = cip[-48:] if cip else "(none)"
                                self.log(
                                    f"{worker_id} 无网络整包换绑 "
                                    f"from={old_name} -> profile={proxy.profile_name} "
                                    f"endpoint={proxy.host}:{proxy.port} "
                                    f"user={proxy.username} "
                                    f"change_ip=...{cip_tail} "
                                    f"cip_changed={old_cip != cip} "
                                    f"cip_has_profile={proxy.profile_name in cip if cip else False} "
                                    f"(SOCKS5与刷新链接已一起更换)"
                                )
                                try:
                                    pre = self._ensure_proxy_ready_before_import(worker_id, proxy)
                                except Exception as prexc:
                                    self.log(f"{worker_id} 换绑后预检异常: {prexc}")
                                    pre = {"ok": False, "status": f"precheck_exc:{prexc}"}
                                if not pre.get("ok"):
                                    self.log(
                                        f"{worker_id} 无网络换绑后代理仍不通 "
                                        f"profile={proxy.profile_name} status={pre.get('status')}，继续换下一个"
                                    )
                                    continue
                                if self.config.get("use_nekobox", True):
                                    try:
                                        msg = rs.setup_nekobox_socks5(
                                            proxy.profile_name,
                                            proxy.host,
                                            proxy.port,
                                            proxy.username,
                                            proxy.password,
                                            log=lambda m: self.log(f"{worker_id} {m}"),
                                            verify_vpn=True,
                                        )
                                        self.log(f"{worker_id} 无网络换绑后 NekoBox: {str(msg)[:300]}")
                                    except Exception as nexc:
                                        self.log(f"{worker_id} 无网络换绑后 NekoBox 失败: {nexc}，继续换下一个")
                                        continue
                                rebound_ok = True
                                break
                            if not rebound_ok:
                                break
                        self.log(
                            f"{worker_id} 无网络已刷IP/测网/换绑通过，重试登录 "
                            f"#{attempt+1}/{max_no_net_retry} "
                            f"profile={getattr(proxy, 'profile_name', '')}"
                        )
                        outcome = venmo.login_with_fallback(
                            acc.account1, acc.password, acc.account2
                        )
                        if outcome.result != LoginResult.NO_NETWORK:
                            break

                # RISK_CONTROL：账号已判定正确+风控，导出后刷 IP 供后续账号使用
                # WRONG_PASSWORD / SUCCESS / 其他：不刷
                if (
                    outcome.result == LoginResult.RISK_CONTROL
                    and not self._stop.is_set()
                ):
                    self._refresh_proxy_if_needed(
                        worker_id, proxy, adb, reason="risk_control"
                    )

                self.store.finish(
                    acc,
                    outcome.result,
                    message=outcome.message,
                    used_account=outcome.used_account,
                    wrong_account=outcome.wrong_account,
                    masked_phone=outcome.masked_phone,
                )
                self.log(
                    f"{worker_id} 完成 line={acc.line_no} status={outcome.result.value} "
                    f"phone={outcome.masked_phone} msg={outcome.message[:80]}"
                )
                # 连续 RISK_CONTROL / NO_NETWORK 计数（最终 outcome）
                if outcome.result in REFRESH_ON_RESULTS:
                    consecutive_bad += 1
                else:
                    consecutive_bad = 0
                self.log(
                    f"{worker_id} consecutive_risk_nonet="
                    f"{consecutive_bad}/{consecutive_limit}"
                )
                with self._lock:
                    self._current_login.pop(worker_id, None)
                # 连续 N 次风控/无网：关删建模拟器，任务迁到新 VM 完整重setup
                if consecutive_bad >= consecutive_limit and not self._stop.is_set():
                    self.log(
                        f"{worker_id} 触发删建迁移: 连续{consecutive_bad}次 "
                        f"RISK/NO_NET on VM={vmindex}"
                    )
                    try:
                        adb.release_ui_control(home=True)
                    except Exception:
                        pass
                    new_idx = self._recycle_vm(worker_id, vmindex, proxy)
                    if new_idx is None:
                        self.log(f"{worker_id} 删建迁移失败，线程结束 VM={vmindex}")
                        try:
                            self.proxy_pool.release(f"vm-{vmindex}")
                        except Exception:
                            pass
                        with self._lock:
                            self._current_login.pop(worker_id, None)
                        self.log(f"{worker_id} 线程结束 VM={vmindex}")
                        self.log(f"{worker_id} 结束")
                        return
                    self.log(
                        f"{worker_id} 迁移成功 old=VM{vmindex} -> new=VM{new_idx}，"
                        f"重新完整 setup 后继续任务"
                    )
                    # rebind 已迁移代理，旧 key 不再 release
                    return self._worker_loop(new_idx, worker_id)
            except Exception as exc:
                self.store.finish(acc, LoginResult.ERROR, message=str(exc)[:200])
                consecutive_bad = 0
                with self._lock:
                    self._current_login.pop(worker_id, None)
                self.log(f"{worker_id} 异常: {exc}")
            finally:
                # 每账号结束后释放 UI，避免人工一点就卡白
                try:
                    adb.release_ui_control(home=False)
                except Exception:
                    pass
            time.sleep(1.0)

        try:
            adb.release_ui_control(home=True)
        except Exception:
            pass
        with self._lock:
            self._current_login.pop(worker_id, None)
        self.proxy_pool.release(f"vm-{vmindex}")
        self.log(f"{worker_id} 线程结束 VM={vmindex}")
        self.log(f"{worker_id} 结束")



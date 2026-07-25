# 2026-07-25 desktop-empty-soft-pull-v1: _wait_third_direct 掉桌面/空dump 软拉回再点Install，避免空等~40s；max_kill不变
# 2026-07-25 install-tap-reopen-v3: 二次打开必点首页Install；bounds/regex/rid/坐标兜底；仅见Patch长等后再杀
# 2026-07-25 desktop-no-blind-tap-v1b: drop-to-desktop soft relaunch; no blind Install coords; coord fallback only on Magisk home with Install signal; no attempt force True
# 2026-07-25 direct-install-wait-v2: wait longer for method_direct_system; only-patch poll+refresh before kill
# 2026-07-25 grant-to-settings-fast-v1: GRANT后Settings: UI优先，跳过易挂死的magisk sqlite长超时；Settings点开关加速
# 2026-07-25 kitsune-cache-recreate-v1: 新建/索引复用时失效旧 kitsune 缓存；create 必须 bin+settings 才跳过
# 2026-07-25 lets-go-then-shell-v1: LETS GO then first restart, then shell/GRANT; no su before reboot
# 2026-07-25 grant-only-when-popup-v1: Hide/打开首页不点GRANT；仅弹窗可见才授权
# 2026-07-25 grant-no-home-coord-v1: Install 排除 WebView/PP赞助；GRANT 坐标仅真实 SuRequest
# 2026-07-25 shell-grant-popup-first-v2: 全路径GRANT弹窗优先(Remember forever+Allow/Grant)；Superuser右侧开关仅失败兜底；configure_flags/provision不再直进Superuser
# 2026-07-25 pkg-serial-all-v2: 同VM串行装齐勾选APK(adb优先)，避免MuMu -201；跨VM仍可并行
# 2026-07-25 pkg-parallel-v1: ensure_packages 并行装勾选 APK；登录 magisk -v 可用即跳过 UI
# 2026-07-25 only-patch-or-true-fix: 去掉 only_patch or True 误强制重启 Magisk
# -*- coding: utf-8 -*-
# 2026-07-25 shareduid-grant-click-v1: GRANT弹窗失败重试+识别 magisk_grant 成功
# 2026-07-25 soft-no-thrash-v2: 软重试不杀进程；仅掉桌面软拉回；无第3项才杀进程最多1次；禁止反复重启Kitsune
# 2026-07-25 only-patch-instant-reopen-v1: 点Install后无第3项Direct Install则瞬间重启Magisk再点Install
# 2026-07-25 hide-install PASS-verified-20260725: VM2 create+provision Hide->Install->reopen1->DirectInstall3->Uninstall+settings+ih8+venmo
# 2026-07-25 hide-then-install-v2: 点完Hide立刻点Install，禁止双reopen
# 2026-07-25 settings-back-once-ih8-v1: Settings三项后只BACK一次，同会话进Modules装ih8后restart，不结束Magisk进程
# 2026-07-25 kitsune-soft-open-v1: 首次/重启后优先软开不 force-stop；Store dismiss 只1次
# 2026-07-25 no-force-stop-after-uninstall-v1: 见Uninstall/Shell授权 reuse_session 绝不 force-stop Magisk
# 2026-07-25 create-fast-one-session-v3: 去掉 binary 假阴性 8s 白等；Install 可见即点
# 2026-07-25 create-fast-one-session-v2: 再压前台检测/打开等待；见Uninstall同会话授权不杀Magisk
# 2026-07-25 create-fast-one-session-v1: 新建加速；见Uninstall同会话直接Shell授权不杀Magisk；status默认不跑binary；provision一次会话
# 2026-07-24 no-uninstall-tap-v1: 禁止点 Uninstall Magisk；Install 必须精确匹配
# 2026-07-24 kitsune-login-lite-v1: 登录复用只查 Uninstall Magisk；设置仅新建；减少 force-stop 重开
# 2026-07-24 forever-allow-v2: Install后su空返回不提前停；_is_real_grant接受forever|Allow；仅改授权轮询
# 2026-07-24 kitsune-one-session-v1: 新建后一次打开 Kitsune 连续完成 Shell授权+Settings三项+ih8，中途不 force-stop
# 2026-07-24 create1-live-v2: 新建机 Direct Install 仅 Patch 时更快重开；首次 setup 等待加长；cached 跳过重复 flags
# 2026-07-24 ih8-restart-v1: 新装 ih8SecureLock 成功后必须 mumu.restart；ok_already 不重启
# 2026-07-24 right-switch-v1: Superuser 点右侧 Switch；勿点左边 Shell 文字
# 2026-07-25 create-direct-kill-reopen-v1: 新建无第3项Direct Install直接结束Kitsune再开再点Install；去掉soft-first；Settings三项后BACK一次→Modules装ih8→restart

# priority-check-v1: 启动后 STEP1 必须先 Kitsune（缓存也轻量确认 Uninstall Magisk），再允许 NekoBox
# step3fix12 Kitsune: 无Uninstall先点Install，点完再查Direct Install；仅点过Install仍找不到才杀进程重开
# step3fix11 GRANT-first + Magisk done markers; step3fix10: Kitsune missing Direct Install -> force-stop process and reopen; no 90s wait if method_ok=False
# step3fix2: kitsune_once + DirectInstall + NekoBox FAB居中Connect/tun + release_ui防卡白
# step3fix3: 成功=Uninstall Magisk可见; VPN=tun0; FAB底部居中; 操作后release_ui
# step3fix4: NekoBox Username 校验(qq...qiang15_pp) 错则 Edit/重导
# 2026-07-25 grant-no-deny-v1: Shell GRANT 弹窗多轮精确点 GRANT，失败落盘 UI，禁止 deny 猜点
# step3fix5: URI导入自带用户名; 开启前auth校验; 改配置先Stop再Connect
# step3fix7: 复用缺装NekoBox; 禁盲点FAB; documentsui回收; 前台校验Connect
# step3fix8: VPN授权弹窗点OK/Allow; 禁止在授权期间HOME; Venmo缺装
# step3fix9: UI精确可见为准; 无profile禁止点FAB; 清本地陈旧sager_net.db防exists误报; 取消可打断VPN循环
# su-grant: Magisk [SharedUID] Shell 点Grant文字 + Kitsune Superuser页授权 + policies
# 2026-07-24 neko-wipe-v1: 每次打开 NekoBox 先 Stop+删除全部 profile，再按当前分配代理 URI 重新导入，避免多代理叠加
# 2026-07-24 nemu-su-forever-v1: MuMu SuperUser Forever→Allow 用 rid/坐标，Install 等待 20s
# 2026-07-24 login-no-reopen-kitsune-v1: 登录有缓存不打开Kitsune；仅查Uninstall后直接代理
# 2026-07-24 ensure_packages-venmo-v1: 勾选 venmo 时 ensure_packages 一并装完整 split
# 2026-07-24 one-session-no-kill-v2: 新建流程 Settings/ih8 同会话完成；DirectInstall 无第3项直接杀进程重开最多1次
"""ROOT / Kitsune Mask / NekoBox / ih8SecureLock 安装与开关。

更新 2026-07-24 step2:
- Kitsune: 打开 Kitsune Mask 见到 Uninstall Magisk = 已安装，不点 Install；
  仅当只有 Install（无 Uninstall Magisk）才点
  Install -> Direct Install (modify /system directly) -> 模拟器 restart
- NekoBox: 先打开 App 添加 SOCKS5 配置/导入 profile，再启动 VPN，并检测真实 VPN/tun
- 绝不 force-stop NekoBox（会掐 VPN）

更新 2026-07-24 step3fix5:
- SOCKS URI 导入直接带 Username/Password（主路径，不优先 UI 手填）
- 开启 VPN 前必须 auth 校验通过
- 改配置：先 Stop VPN，再重导/修复，再 Connect（改后需重开才生效）
- UI 填 Username 仅作导入失败兜底

更新 2026-07-24 step3fix4:
- NekoBox Profile 存在不等于配置正确：必须校验 socksBean 内 Username
- Username=完整代理用户名(qq1254870524.qiang15_pp)，Profile Name=短名(qiang15)
- 缺/错用户名时走 Edit 页写入并 Apply，失败则 Remove 后 URI 重导
- Kryo 序列化最后字符高位 0x80，字符串匹配需解码

更新 2026-07-24 step2-neko-fix:
- SOCKS URI 含 # 密码/fragment 必须 base64 shell 传，避免 adb shell 当注释截断
- 导入确认点 YES（不是 OK/Import）
- 启 VPN 点 content-desc Connect / FAB；已 Connected/Stop 则不再点断
- UI 单次 dump 多标签匹配，避免 uiautomator 连环超时挂死
- kitsune magisk --sqlite 用 base64 su 脚本，修复 unexpected '('

更新 2026-07-24 neko-wipe-v1:
- 每次 setup/重导：Stop VPN → 删除列表全部 profile → socks:// 导入当前分配代理 → Connect
- 避免 NekoBox 内历史代理叠加，只保留当前 worker 绑定的一条
"""
# update: hide-then-install-v2 - Hide then Install, no double reopen
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
import logging
import time
import urllib.parse
from pathlib import Path
from typing import Callable, Optional

from core.adb_client import AdbClient
from core.mumu_manager import MuMuManager
from paths import DATA_NEKO_DIR, DATA_STATE_DIR, IH8_MODULE_ZIP, KITSUNE_APK, NEKOBOX_APK, ensure_under_root

logger = logging.getLogger("mumuvenmo")
LogFn = Optional[Callable[[str], None]]


class RootSetup:
    def __init__(
        self,
        mumu: MuMuManager,
        adb: AdbClient,
        nekobox_apk: Path = NEKOBOX_APK,
        kitsune_apk: Path = KITSUNE_APK,
        ih8_zip: Path = IH8_MODULE_ZIP,
        nekobox_pkg: str = "moe.nb4a",
        kitsune_pkg: str = "io.github.huskydg.magisk",
    ):
        self.mumu = mumu
        self.adb = adb
        self.nekobox_apk = Path(nekobox_apk)
        self.kitsune_apk = Path(kitsune_apk)
        self.ih8_zip = Path(ih8_zip)
        self.nekobox_pkg = nekobox_pkg
        self.kitsune_pkg = kitsune_pkg
        self._cancel_check = None  # callable -> bool, worker 停止信号

    def set_cancel_check(self, fn) -> None:
        """由 Worker 注入停止检查，避免 VPN 死循环无法退出。"""
        self._cancel_check = fn

    def _cancelled(self) -> bool:
        try:
            return bool(self._cancel_check and self._cancel_check())
        except Exception:
            return False

    def _log(self, log: LogFn, msg: str) -> None:
        logger.info(msg)
        if log:
            try:
                log(msg)
            except Exception:
                pass


    # ------------------------------------------------------------------ Kitsune once-per-VM state
    def kitsune_state_path(self, vmindex: int) -> Path:
        return ensure_under_root(DATA_STATE_DIR / f"kitsune_ok_vm{int(vmindex)}.json")

    def is_kitsune_done(self, vmindex: int) -> bool:
        """每台模拟器只检查/安装 Kitsune 一次（成功后写状态文件）。"""
        p = self.kitsune_state_path(vmindex)
        if not p.exists():
            return False
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return bool(data.get("ok"))
        except Exception:
            return False

    def mark_kitsune_done(self, vmindex: int, detail: str = "", settings_ok: bool | None = None) -> None:
        p = self.kitsune_state_path(vmindex)
        p.parent.mkdir(parents=True, exist_ok=True)
        prev = {}
        try:
            if p.exists():
                prev = json.loads(p.read_text(encoding="utf-8")) or {}
        except Exception:
            prev = {}
        payload = {
            "ok": True,
            "vmindex": int(vmindex),
            "ts": time.time(),
            "detail": (detail or "")[:800],
        }
        if settings_ok is None:
            if "settings_ok" in prev:
                payload["settings_ok"] = bool(prev.get("settings_ok"))
        else:
            payload["settings_ok"] = bool(settings_ok)
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def is_kitsune_settings_done(self, vmindex: int) -> bool:
        p = self.kitsune_state_path(vmindex)
        if not p.exists():
            return False
        try:
            data = json.loads(p.read_text(encoding="utf-8")) or {}
            if bool(data.get("settings_ok")):
                return True
            detail = str(data.get("detail") or "")
            return ("flags=" in detail) and ("flags=skipped_login_only" not in detail)
        except Exception:
            return False

    def clear_kitsune_done(self, vmindex: int) -> None:
        p = self.kitsune_state_path(vmindex)
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass

    def _force_stop_kitsune_home(self) -> None:
        """检查完 Kitsune 后 force-stop 回桌面，避免占 UIAutomator 导致人工点白屏。"""
        try:
            self.adb.force_stop(self.kitsune_pkg)
        except Exception:
            pass
        try:
            self.adb.shell("input", "keyevent", "3", timeout=8)
        except Exception:
            pass
        try:
            self.adb.release_ui_control(home=False)
        except Exception:
            pass


    # ------------------------------------------------------------------ MuMu Store first-boot
    MUMU_STORE_PKG = "com.mumu.store"

    def _focused_package(self) -> str:
        try:
            out = self.adb.shell(
                "dumpsys", "window", "windows", timeout=12
            ) or self.adb.shell("dumpsys", "window", timeout=12) or ""
        except Exception:
            out = ""
        for pat in (
            r"mCurrentFocus=Window\{[^ ]+ u0 ([^/}\s]+)",
            r"mFocusedApp=ActivityRecord\{[^ ]+ u0 ([^/}\s]+)",
            r"topResumedActivity=ActivityRecord\{[^ ]+ u0 ([^/}\s]+)",
        ):
            m = re.search(pat, out)
            if m:
                return m.group(1).strip()
        return ""

    def _ui_looks_like_mumu_store(self, text: str = "") -> bool:
        low = (text or "").lower()
        keys = (
            "mumu store",
            "search games",
            "search for games",
            "suggested for you",
            "mumu exclusive",
            "app cloner",
            "exclusive gift",
        )
        return any(k in low for k in keys)

    def _mumu_store_busy_ui(self, text: str = "") -> bool:
        low = (text or "").lower()
        busy = (
            "syncing",
            "synchroniz",
            "downloading",
            "download",
            "installing",
            "updating",
            "please wait",
            "loading",
            "正在同步",
            "正在下载",
            "正在安装",
            "同步中",
            "下载中",
            "安装中",
            "更新中",
            "请稍候",
            "loading resources",
        )
        return any(k in low for k in busy)

    def dismiss_mumu_store(self, log: LogFn = None, times: int = 1) -> str:
        """强制结束 MuMu Store 并回桌面，避免抢焦点干扰 Kitsune/NekoBox。"""
        notes = []
        for i in range(max(1, times)):
            try:
                self.adb.shell("am", "force-stop", self.MUMU_STORE_PKG, timeout=12)
                notes.append("force-stop")
            except Exception as exc:
                notes.append(f"fs_err={exc}")
            try:
                # 禁掉自启组件（失败忽略）
                self.adb.shell(
                    "pm", "disable-user", "--user", "0",
                    f"{self.MUMU_STORE_PKG}/.MainActivity",
                    timeout=12,
                )
            except Exception:
                pass
            try:
                self.adb.shell("input", "keyevent", "3", timeout=8)
                notes.append("home")
            except Exception:
                pass
            time.sleep(0.8)
            pkg = self._focused_package()
            if pkg and pkg != self.MUMU_STORE_PKG and "mumu.store" not in pkg:
                break
            try:
                ui = (self.adb.ui_full_text() or "").lower()
            except Exception:
                ui = ""
            if not self._ui_looks_like_mumu_store(ui):
                break
        self._log(log, f"dismiss MuMu Store: {';'.join(notes)[:160]} focus={self._focused_package()}")
        return "|".join(notes)[:200]

    def wait_mumu_store_sync(
        self,
        *,
        log: LogFn = None,
        timeout: int = 180,
        idle_stable_seconds: float = 8.0,
        force_close_after: bool = True,
    ) -> str:
        """新建模拟器首启门禁（用户指定顺序）：

        1) 先结束 MuMu Store 进程（force-stop）
        2) 同时/随后等待系统同步安装 APP 完成（package installer / 忙碌 UI 结束）
        3) 期间若弹 Magisk su：Remember choice forever → Allow
        4) 结束后再强制关掉商店，避免抢焦点
        """
        import time as _t

        # 1) 先结束 MuMu Store 进程
        self._log(log, "MuMu Store: 先 force-stop 结束进程")
        try:
            self.adb.shell("am", "force-stop", self.MUMU_STORE_PKG, timeout=12)
        except Exception as exc:
            self._log(log, f"MuMu Store force-stop err: {exc}")
        try:
            self.adb.shell("input", "keyevent", "3", timeout=8)
        except Exception:
            pass
        time.sleep(1.0)

        t0 = _t.time()
        idle_since = None
        last = ""
        saw_busy = False
        while _t.time() - t0 < max(20, int(timeout)):
            if self._cancelled():
                return "cancelled"

            # 商店若又被拉起，立即再杀
            pkg = self._focused_package()
            if pkg and "mumu.store" in pkg:
                try:
                    self.adb.shell("am", "force-stop", self.MUMU_STORE_PKG, timeout=12)
                    self.adb.shell("input", "keyevent", "3", timeout=8)
                    self._log(log, "MuMu Store 再次被拉起 → force-stop")
                except Exception:
                    pass

            try:
                ui = self.adb.ui_full_text() or ""
            except Exception:
                ui = ""
            low = ui.lower()
            busy = self._mumu_store_busy_ui(low)
            if pkg and (
                "packageinstaller" in (pkg or "")
                or "com.android.packageinstaller" in (pkg or "")
                or "com.google.android.packageinstaller" in (pkg or "")
            ):
                busy = True
            # 轻量检测安装会话（禁止 dumpsys package install，体积过大且易误判/拖死）
            try:
                sess = (self.adb.shell("pm", "list", "sessions", timeout=8) or "").lower()
            except Exception:
                sess = ""
            if sess and any(k in sess for k in ("session", "active", "install")) and "no sessions" not in sess:
                # 仅当输出像真实会话列表时 busy
                if re.search(r"session\s*id|install\s*session|isactive\s*=\s*true", sess):
                    busy = True

            # Magisk su：Remember forever → Allow
            try:
                hit = self.adb.dismiss_magisk_su_dialog()
                if hit:
                    self._log(log, f"MuMu Store wait 期间 su 授权: {hit}")
            except Exception:
                pass

            if busy:
                saw_busy = True
                idle_since = None
            else:
                if idle_since is None:
                    idle_since = _t.time()
                elif _t.time() - idle_since >= idle_stable_seconds:
                    break

            status = f"pkg={pkg or '-'} busy={busy} saw_busy={saw_busy}"
            if status != last:
                self._log(log, f"APP sync wait: {status} ui={(ui or '')[:80]!r}")
                last = status
            _t.sleep(0.9 if busy else 0.6)

        detail = f"saw_busy={saw_busy} elapsed={int(_t.time()-t0)}s last={last}"
        if force_close_after:
            d = self.dismiss_mumu_store(log=log, times=1)
            detail += f" dismiss={d}"
        # 再清一次可能残留的 su 弹窗
        try:
            hit = self.adb.dismiss_magisk_su_dialog()
            if hit:
                detail += f" su={hit}"
                self._log(log, f"门禁结束前 su 授权: {hit}")
        except Exception:
            pass
        self._log(log, f"MuMu Store/APP sync gate done: {detail}")
        return detail


    # ------------------------------------------------------------------ packages
    def ensure_packages(
        self,
        vmindex: int,
        install_nekobox: bool = True,
        install_kitsune: bool = True,
        install_ih8: bool = True,
        install_venmo: bool = False,
        install_aurora: bool = False,
        prefer_aurora_venmo: bool = False,
        log: LogFn = None,
    ) -> dict[str, str]:
        """按 UI 勾选安装内置 APK/模块（assets 打包）。

        2026-07-24: 勾选 venmo 时一并装完整 split bundle（禁止单 base.apk）。
        2026-07-25: 同 VM 串行装齐勾选包（adb 优先，MuMu install 兜底），避免并行 -201。
        跨多台模拟器的并行由 create/provision 线程池负责。
        """
        result: dict[str, str] = {}

        def _install_one(kind: str, pkg: str, apk: Path) -> str:
            try:
                if self.adb.package_installed(pkg):
                    return "already_installed"
                if not apk.exists():
                    return "missing_apk"
                self._log(log, f"VM={vmindex} 安装 {kind}: {apk.name}")
                logger.info("安装 %s: %s", kind, apk.name)
                # 同 VM 串行：先 adb（稳定），失败再 MuMu manager
                out = ""
                try:
                    out2 = self.adb.install(apk)
                    out = str(out2)
                except Exception as exc:
                    out = f"adb_err:{exc}"
                if self.adb.package_installed(pkg):
                    return (out.strip()[:200] or "installed_ok_adb")
                try:
                    cp = self.mumu.install_apk(vmindex, apk)
                    out_m = ((cp.stdout or "") + (cp.stderr or "")).strip()
                    out = (out + "\n" + out_m).strip()
                except Exception as exc:
                    out = (out + f"\nmumu_err:{exc}").strip()
                if self.adb.package_installed(pkg):
                    return (out.strip()[:200] or "installed_ok_mumu")
                return (out.strip()[:300] or "install_failed")
            except Exception as exc:
                return f"err:{exc}"[:200]

        # 勾选的包同一轮按序装齐（Kitsune -> NekoBox -> Aurora）
        jobs: list[tuple[str, str, Path]] = []
        if install_kitsune:
            jobs.append(("kitsune", self.kitsune_pkg, self.kitsune_apk))
        else:
            result["kitsune"] = "skipped_by_ui"
        if install_nekobox:
            jobs.append(("nekobox", self.nekobox_pkg, self.nekobox_apk))
        else:
            result["nekobox"] = "skipped_by_ui"
        if install_aurora:
            try:
                from core.venmo_install import AURORA_APK, AURORA_PKG

                jobs.append(("aurora", AURORA_PKG, AURORA_APK))
            except Exception:
                # 回退 assets 路径
                aurora_apk = Path(__file__).resolve().parents[1] / "assets" / "apk" / "AuroraStore-4.8.3.apk"
                jobs.append(("aurora", "com.aurora.store", aurora_apk))
        else:
            result["aurora"] = "skipped_by_ui"

        for kind, pkg, apk in jobs:
            msg = _install_one(kind, pkg, apk)
            result[kind] = msg
            self._log(log, f"VM={vmindex} 装包 {kind}={str(msg)[:120]}")

        result["ih8_wanted"] = "yes" if install_ih8 else "no"

        # Venmo：勾选后缺装即补完整 split（本地 bundle 优先，除非 prefer_aurora）
        if install_venmo:
            try:
                from core.venmo_install import ensure_venmo_ready, venmo_split_info

                def _vlog(m: str) -> None:
                    if log:
                        try:
                            log(m)
                        except Exception:
                            pass
                    logger.info("%s", m)

                vr = ensure_venmo_ready(
                    self.adb,
                    log=_vlog,
                    prefer_aurora=bool(prefer_aurora_venmo),
                )
                info = vr.get("info") or venmo_split_info(self.adb)
                result["venmo"] = (
                    f"ok={vr.get('ok')} method={vr.get('method')} "
                    f"splits={info.get('split_count')}"
                )[:300]
                self._log(log, f"VM={vmindex} 装包 venmo={result['venmo'][:120]}")
            except Exception as exc:
                result["venmo"] = f"err:{exc}"[:200]
                logger.warning("ensure_packages venmo: %s", exc)
        else:
            result["venmo"] = "skipped_by_ui"

        return result


    def install_ih8_module_ui(self, log: LogFn = None, reuse_session: bool = False) -> str:
        """Modules -> Install from storage -> 选 ih8SecureLock-v8.zip。

        reuse_session=True：不 force-stop Kitsune，从当前会话直接进 Modules。
        """
        notes: list[str] = []
        if not self.ih8_zip.exists():
            return "ih8_missing"
        remote = "/sdcard/Download/ih8SecureLock-v8.zip"
        try:
            self.adb.shell("mkdir", "-p", "/sdcard/Download")
            self.adb.push(self.ih8_zip, remote)
            notes.append("pushed")
        except Exception as exc:
            notes.append(f"push_fail:{exc}")
        for pkg in ("com.android.documentsui", "com.google.android.documentsui"):
            try:
                self.adb.shell("am", "force-stop", pkg, timeout=10)
            except Exception:
                pass
        try:
            self.open_kitsune(force_relaunch=not reuse_session)
            time.sleep(0.5 if reuse_session else 0.9)
            if reuse_session:
                notes.append("reuse_session")
        except Exception as exc:
            return "open_fail:" + str(exc)[:80] + "|" + "|".join(notes)

        def _dump() -> str:
            try:
                return self.adb.uiautomator_dump(force=True) or ""
            except Exception:
                return ""

        def _tap_exact_text(xml: str, label: str, y_min: int = 0, y_max: int = 99999) -> bool:
            for m in re.finditer(
                r'text="([^"]+)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                xml,
                re.I,
            ):
                t = (m.group(1) or "").strip()
                if t.lower() != label.lower():
                    continue
                b = tuple(map(int, m.groups()[1:]))
                cy = (b[1] + b[3]) // 2
                if cy < y_min or cy > y_max:
                    continue
                self.adb.tap_bounds(b)
                return True
            for m in re.finditer(
                r'content-desc="([^"]+)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                xml,
                re.I,
            ):
                t = (m.group(1) or "").strip()
                if t.lower() != label.lower():
                    continue
                b = tuple(map(int, m.groups()[1:]))
                cy = (b[1] + b[3]) // 2
                if cy < y_min or cy > y_max:
                    continue
                self.adb.tap_bounds(b)
                return True
            if label.lower() == "modules":
                b = self.adb.find_node_bounds(resource_id="modulesFragment", xml=xml)
                if b and ((b[1] + b[3]) // 2) >= y_min:
                    self.adb.tap_bounds(b)
                    return True
            return False

        def _module_present(xml: str) -> bool:
            return "ih8securelock" in xml.lower()

        def _module_enabled(xml: str) -> bool:
            m = re.search(
                r'text="ih8SecureLock"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                xml,
                re.I,
            )
            if not m:
                return False
            y = (int(m.group(2)) + int(m.group(4))) // 2
            for na in re.findall(r"<node\b([^>]*)/>", xml):
                if "module_indicator" not in na and "Switch" not in na:
                    continue
                bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', na)
                if not bm:
                    continue
                x1, y1, x2, y2 = map(int, bm.groups())
                cy = (y1 + y2) // 2
                if abs(cy - y) > 180:
                    continue
                return 'checked="true"' in na
            return False

        xml = _dump()
        if not _tap_exact_text(xml, "Modules", y_min=2100):
            self.adb.tap(1260, 2440)
            notes.append("modules_coord")
        else:
            notes.append("modules_tap")
        time.sleep(1.1)
        xml = _dump()

        if _module_present(xml) and _module_enabled(xml):
            notes.append("already_installed_on")
            self._log(log, "ih8 UI: already installed and enabled")
            return "ok_already:" + "|".join(notes)[:200]

        if not _tap_exact_text(xml, "Install from storage"):
            b = self.adb.find_node_bounds(text_substr="Install from storage", xml=xml)
            if b:
                self.adb.tap_bounds(b)
                notes.append("install_storage_sub")
            else:
                notes.append("install_storage_miss")
                return "no_install_from_storage|" + "|".join(notes)
        else:
            notes.append("install_storage_tap")
        time.sleep(1.4)
        xml = _dump()

        picked = False
        for label in ("ih8SecureLock-v8.zip", "ih8SecureLock"):
            m = re.search(
                rf'text="([^"]*{re.escape(label)}[^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                xml,
                re.I,
            )
            if m:
                b = tuple(map(int, m.groups()[1:]))
                self.adb.tap((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)
                notes.append(f"pick={m.group(1)[:48]}")
                picked = True
                break
        if not picked:
            b = self.adb.find_node_bounds(content_desc="Show roots", xml=xml)
            if b:
                self.adb.tap_bounds(b)
                notes.append("show_roots")
                time.sleep(0.8)
                xml = _dump()
                for root_name in ("Downloads", "Download", "MuMu shared", "Internal storage"):
                    if _tap_exact_text(xml, root_name) or self.adb.tap_text(root_name):
                        notes.append(f"root={root_name}")
                        time.sleep(1.0)
                        xml = _dump()
                        break
            m = re.search(
                r'text="(ih8SecureLock[^"]*\.zip)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                xml,
                re.I,
            )
            if m:
                b = tuple(map(int, m.groups()[1:]))
                self.adb.tap((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)
                notes.append(f"pick2={m.group(1)}")
                picked = True
        if not picked:
            notes.append("zip_not_in_picker")
            try:
                self.adb.shell("input", "keyevent", "4", timeout=5)
            except Exception:
                pass
            return "zip_pick_fail|" + "|".join(notes)

        installed = False
        for i in range(24):
            time.sleep(1.0)
            xml = _dump()
            low = xml.lower()
            for btn in ("OK", "Done", "Close"):
                if _tap_exact_text(xml, btn):
                    notes.append(f"btn={btn}")
                    time.sleep(0.5)
                    xml = _dump()
                    break
            if _module_present(xml):
                if not _module_enabled(xml):
                    m = re.search(
                        r'text="ih8SecureLock"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                        xml,
                        re.I,
                    )
                    if m:
                        y = (int(m.group(2)) + int(m.group(4))) // 2
                        for na in re.findall(r"<node\b([^>]*)/>", xml):
                            if "module_indicator" not in na and "Switch" not in na:
                                continue
                            bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', na)
                            if not bm:
                                continue
                            x1, y1, x2, y2 = map(int, bm.groups())
                            cy = (y1 + y2) // 2
                            if abs(cy - y) > 180:
                                continue
                            if 'checked="false"' in na:
                                self.adb.tap((x1 + x2) // 2, cy)
                                notes.append("enabled_switch")
                                time.sleep(0.5)
                            break
                installed = True
                notes.append("list_ok")
                break
            if "documentsui" in low and "ih8" in low and i < 4:
                m = re.search(
                    r'text="(ih8SecureLock[^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                    xml,
                    re.I,
                )
                if m:
                    b = tuple(map(int, m.groups()[1:]))
                    self.adb.tap((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)
                    notes.append("repick")
            if "all done" in low or "done!" in low or "installation done" in low:
                notes.append("console_done")
                for btn in ("OK", "Close", "Done"):
                    if _tap_exact_text(xml, btn):
                        break
                try:
                    self.open_kitsune(force_relaunch=False)
                except Exception:
                    pass
                time.sleep(0.8)
                xml = _dump()
                _tap_exact_text(xml, "Modules", y_min=2100)
                time.sleep(1.0)

        try:
            ls = self.adb.shell_su("ls /data/adb/modules 2>/dev/null", timeout=15) or ""
            notes.append("dir=" + ls.replace("\n", ",")[:80])
            if "ih8" in ls.lower() or "secure" in ls.lower():
                installed = True
        except Exception as exc:
            notes.append(f"dir_err={exc}")

        self._log(log, "ih8 UI: " + "|".join(notes)[:240])
        if installed:
            return "ok_ui:" + "|".join(notes)[:220]
        return "ui_fail:" + "|".join(notes)[:280]

    def _ih8_result_needs_restart(self, result: str) -> bool:
        """新装成功才需要 restart；already/失败不重启。"""
        s = str(result or "").strip().lower()
        if not s.startswith("ok"):
            return False
        if s.startswith("ok_already"):
            return False
        # ok_ui / ok_cli / ok_cli_banner / ok_dir 等新装路径
        return True

    def restart_vm_and_wait(
        self,
        vmindex: int,
        log: LogFn = None,
        boot_timeout: int = 180,
        reason: str = "",
    ) -> str:
        """仅用 MuMu restart（禁止 adb reboot），等待 Android+ADB 就绪。"""
        tag = f"VM={vmindex}"
        why = f" ({reason})" if reason else ""
        self._log(log, f"{tag} MuMu restart device{why}")
        try:
            if hasattr(self.mumu, "restart"):
                self.mumu.restart(vmindex)
            elif hasattr(self.mumu, "restart_device"):
                self.mumu.restart_device(vmindex)
            else:
                return "err:no_restart_api"
        except Exception as exc:
            self._log(log, f"{tag} restart 失败: {exc}")
            return f"err:{exc}"

        # 给进程退出一点时间，再轮询 boot
        time.sleep(6.0)
        deadline = time.time() + max(90, int(boot_timeout or 180))
        last_err = ""
        while time.time() < deadline:
            try:
                node = self.mumu._node(vmindex)
                if node.get("is_android_started"):
                    try:
                        self.mumu.adb_connect(vmindex)
                    except Exception as exc:
                        last_err = f"adb_connect:{exc}"
                    try:
                        self.adb.connect()
                    except Exception:
                        pass
                    if self.adb.wait_device(timeout=20):
                        self._log(log, f"{tag} restart 后 Android/ADB 就绪")
                        return "ok"
            except Exception as exc:
                last_err = str(exc)[:120]
            time.sleep(3)
        self._log(log, f"{tag} restart 后等待超时 last={last_err}")
        return f"timeout:{last_err}" if last_err else "timeout"

    def install_ih8_module(
        self,
        log: LogFn = None,
        vmindex: int | None = None,
        restart: bool = True,
        boot_timeout: int = 180,
        reuse_session: bool = False,
    ) -> str:
        """优先 Modules UI 安装 ih8；失败再 CLI magisk --install-module。

        新装成功（ok_ui/ok_cli/ok_dir…）且 restart=True、vmindex 给定时：
        必须 mumu.restart 等 boot 后模块才生效。
        ok_already 已装启用则不重启。
        """
        result = ""
        try:
            ui = self.install_ih8_module_ui(log=log, reuse_session=reuse_session)
            if str(ui).startswith("ok"):
                result = str(ui)
            else:
                ui_note = str(ui)[:160]
        except Exception as exc:
            ui_note = f"ui_err:{exc}"
            result = ""

        if not result:
            if not self.ih8_zip.exists():
                return "ih8_missing|" + ui_note
            remote = "/sdcard/Download/ih8SecureLock-v8.zip"
            try:
                self.adb.shell("mkdir", "-p", "/sdcard/Download")
                self.adb.push(self.ih8_zip, remote)
            except Exception as exc:
                return f"push_fail:{exc}|{ui_note}"
            cmds = [
                f"magisk --install-module {remote}",
                f"/data/adb/magisk/magisk64 --install-module {remote}",
                f"su -c 'magisk --install-module {remote}'",
            ]
            outs = [ui_note]
            for c in cmds:
                try:
                    if c.startswith("su "):
                        o = self.adb.shell_su(f"magisk --install-module {remote}", timeout=90)
                    else:
                        if c.startswith("magisk ") or c.startswith("/data/adb"):
                            o = self.adb.shell_su(c, timeout=90)
                        else:
                            o = self.adb.shell(*c.split())
                    outs.append((o or "").strip()[:160])
                    low = (o or "").lower()
                    if o and (
                        "success" in low
                        or "installed" in low
                        or "ih8securelock" in low
                        or "done" in low
                        or "powered by mag" in low
                    ):
                        try:
                            ls = self.adb.shell_su("ls /data/adb/modules 2>/dev/null", timeout=15) or ""
                        except Exception:
                            ls = ""
                        if "ih8" in ls.lower() or "securelock" in ls.lower() or "ih8securelock" in low:
                            result = "ok_cli:" + outs[-1][:120]
                            break
                        result = "ok_cli_banner:" + outs[-1][:120]
                        break
                except Exception as exc:
                    outs.append(str(exc)[:80])
            if not result:
                try:
                    ls = self.adb.shell_su("ls /data/adb/modules 2>/dev/null", timeout=15) or ""
                    if "ih8" in ls.lower() or "secure" in ls.lower():
                        result = "ok_dir:" + ls.replace("\n", " ")[:120]
                except Exception:
                    pass
            if not result:
                return "try:" + " | ".join(outs)[:350]

        # 新装成功 -> MuMu restart（模块需重启生效）
        if self._ih8_result_needs_restart(result):
            if restart and vmindex is not None:
                rr = self.restart_vm_and_wait(
                    int(vmindex),
                    log=log,
                    boot_timeout=boot_timeout,
                    reason="ih8 module installed",
                )
                result = f"{result}|restart={rr}"
            elif restart and vmindex is None:
                result = f"{result}|restart=skip_no_vmindex"
                self._log(log, "ih8 新装成功但无 vmindex，跳过 restart（调用方需自行 restart）")
            else:
                result = f"{result}|restart=skip_disabled"
        else:
            result = f"{result}|restart=skip_already"
        return result

    def grant_shell_prefer_popup(self, log: LogFn = None) -> str:
        """先发起 su/shell 触发 GRANT 弹窗，弹窗出现后再点 GRANT。

        硬规则 grant-only-when-popup-v2:
        1) 不先乱点；没有弹窗绝不点
        2) 只有脚本执行 su/shell 才会弹出 GRANT
        3) 成功判据：su probe 含 uid=0
        4) 只点 GRANT/Allow，绝不点 Deny
        """
        outs: list[str] = []
        probe = ""
        for attempt in range(3):
            if self._cancelled():
                break
            self._log(log, f"Shell GRANT: 第{attempt+1}次发起 su 触发弹窗（不弹就不点）")
            try:
                # shell_su 内部会并行 auto-grant；仅在弹窗可见时点 GRANT
                probe = self.adb.shell_su("id", timeout=22) or ""
                outs.append(f"probe{attempt+1}={(probe or '').strip()[:120]}")
                self._log(log, f"Shell GRANT su结果#{attempt+1}: {(probe or '')[:160]}")
            except Exception as exc:
                outs.append(f"probe{attempt+1}_err={exc}")
                self._log(log, f"Shell GRANT 触发su失败#{attempt+1}: {exc}")
            if "uid=0" in (probe or ""):
                break
            # su 超时/拒绝后：仅当 UI 已见 GRANT/Allow 才补点一次
            try:
                xml = self.adb.uiautomator_dump(force=True) or ""
            except Exception:
                xml = ""
            low = (xml or "").lower()
            if any(k in low for k in ("id/grant", 'text="grant"', "remember choice forever", "requesting superuser")):
                try:
                    hit2 = self.adb.dismiss_magisk_su_dialog()
                except Exception:
                    hit2 = ""
                if hit2:
                    outs.append(f"mid{attempt+1}={hit2}")
                    self._log(log, f"Shell GRANT 弹窗可见后点击: {hit2}")
                    try:
                        probe2 = self.adb.shell_su("id", timeout=14) or ""
                        outs.append(f"reprobe{attempt+1}={(probe2 or '').strip()[:80]}")
                        if "uid=0" in probe2:
                            probe = probe2
                            break
                    except Exception:
                        pass
            else:
                outs.append(f"mid{attempt+1}=no_popup")
                self._log(log, f"Shell GRANT: 未见弹窗，不点击，准备重试发起 su")
            time.sleep(0.35)

        # 仅残留弹窗可见时再处理一次
        try:
            xmlp = self.adb.uiautomator_dump(force=True) or ""
        except Exception:
            xmlp = ""
        lowp = (xmlp or "").lower()
        if any(k in lowp for k in ("id/grant", 'text="grant"', "remember choice forever", "requesting superuser")):
            try:
                hit3 = self.adb.dismiss_magisk_su_dialog()
                if hit3:
                    outs.append(f"post={hit3}")
                    self._log(log, f"SharedUID Shell GRANT弹窗(post可见): {hit3}")
                    try:
                        probe = self.adb.shell_su("id", timeout=12) or probe
                        outs.append(f"probe_final={(probe or '').strip()[:80]}")
                    except Exception:
                        pass
            except Exception:
                pass

        # 失败落盘 UI，方便核对是否点到 Deny
        if "uid=0" not in (probe or ""):
            try:
                from paths import LOG_DIR
                dump_dir = Path(LOG_DIR) / "run"
                dump_dir.mkdir(parents=True, exist_ok=True)
                xml = self.adb.uiautomator_dump(force=True) or ""
                fp = dump_dir / "grant_fail_ui.xml"
                fp.write_text(xml, encoding="utf-8")
                outs.append("dump=grant_fail_ui.xml")
                self._log(log, f"GRANT失败 UI 已保存: {fp}")
            except Exception as exc:
                outs.append(f"dump_err={exc}")

        low = " | ".join(outs).lower()
        # 严格：只有 uid=0 才算弹窗授权成功；避免误点 Deny 后凭 magisk_grant 字样误判
        ok = "uid=0" in (probe or "")
        if not ok:
            # 若明确 grant 命中且后续 probe 还没来得及，再最后一次 probe
            if any(k in low for k in ("magisk_grant", "grant_fast", "allow_nemu", "allow_rid", "|allow", "exact=grant")) and "via_deny" not in low:
                try:
                    probe = self.adb.shell_su("id", timeout=12) or probe
                    outs.append(f"probe_strict={(probe or '').strip()[:80]}")
                    ok = "uid=0" in (probe or "")
                except Exception:
                    pass
        tag = "popup_grant_ok" if ok else "popup_grant_incomplete"
        return f"{tag}|{'|'.join(outs)}"[:480]

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

        # 3) 短超时 probe + db
        try:
            probe = self.adb.shell_su("id", timeout=12)
            outs.append(f"probe={(probe or '').strip()[:80]}")
            self._log(log, f"su probe: {(probe or '')[:100]}")
        except Exception as exc:
            outs.append(f"probe_err={exc}")
        try:
            db = self.adb.grant_shell_superuser_db()
            outs.append(f"db={(db or '')[:80]}")
            self._log(log, f"grant shell su policy: {(db or '')[:120]}")
        except Exception as exc:
            outs.append(f"db_err={exc}")
        try:
            hit2 = self.adb.dismiss_magisk_su_dialog()
            if hit2:
                outs.append(f"tap2={hit2}")
        except Exception:
            pass
        try:
            sw = self._tap_superuser_shell_switch()
            self._log(log, f"Shell RIGHT Switch(grant_shell_superuser): {sw}")
            outs.append(f"switch={sw}")
        except Exception as _e:
            self._log(log, f"Shell RIGHT Switch fail: {_e}")
            outs.append(f"switch_err={_e}")
        return " | ".join(outs)[:450]


    def _tap_superuser_shell_switch(self, xml: str = "") -> str:
        """点 Superuser 列表 [SharedUID] Shell 行右侧 Switch（policy_indicator）。

        正确：右侧开关 bounds 约 [1120,416][1312,608] 中心 (1216,512)
        错误：点左边 [SharedUID] Shell 文字行
        """
        xml = xml or (self.adb.uiautomator_dump(force=True) or "")
        if not xml:
            return "no_xml"

        # Shell 行 Y 中心
        shell_y = None
        shell_patterns = (
            r'text="(\[SharedUID\]\s*Shell)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
            r'text="([^"]*SharedUID[^"]*Shell[^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
            r'text="(com\.android\.shell)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
            r'text="([^"]*\bShell\b[^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
        )
        for pat in shell_patterns:
            m = re.search(pat, xml, re.I)
            if m:
                shell_y = (int(m.group(3)) + int(m.group(5))) // 2
                break

        # 收集 Switch（含 policy_indicator）
        switches: list[tuple[int, int, int, int, str, str]] = []
        node_re = re.compile(r"<node\b([^>]*)/>")
        for nm in node_re.finditer(xml):
            attrs = nm.group(1)
            if "Switch" not in attrs and "policy_indicator" not in attrs:
                continue
            if "class=" in attrs and "Switch" not in attrs and "policy_indicator" not in attrs:
                continue
            bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', attrs)
            if not bm:
                continue
            x1, y1, x2, y2 = map(int, bm.groups())
            cm = re.search(r'checked="(true|false)"', attrs)
            checked = cm.group(1) if cm else "false"
            rid = ""
            rm = re.search(r'resource-id="([^"]*)"', attrs)
            if rm:
                rid = rm.group(1)
            # 只要 Switch 或 policy_indicator
            if "Switch" not in attrs and "policy_indicator" not in rid:
                continue
            switches.append((x1, y1, x2, y2, checked, rid))

        if not switches:
            # 兜底：右侧固定区域点击（1440 宽）
            if shell_y is not None:
                cx, cy = 1216, shell_y
                self.adb.tap(cx, cy)
                time.sleep(0.8)
                return f"fallback_right_tap center=({cx},{cy})"
            return "no_switch"

        # 优先 policy_indicator，且 y 贴近 Shell 行，再选更靠右的
        def score(sw):
            x1, y1, x2, y2, checked, rid = sw
            cy = (y1 + y2) // 2
            y_pen = abs(cy - shell_y) if shell_y is not None else 0
            rid_bonus = -1000 if "policy_indicator" in (rid or "") else 0
            right_bonus = -x2  # 更靠右更好（负数排序用）
            return (y_pen, rid_bonus, right_bonus)

        switches.sort(key=score)
        x1, y1, x2, y2, checked, rid = switches[0]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        if checked == "true":
            return f"already_on center=({cx},{cy}) bounds=[{x1},{y1}][{x2},{y2}] rid={rid}"
        self.adb.tap(cx, cy)
        time.sleep(0.9)
        # 复查
        xml2 = self.adb.uiautomator_dump(force=True) or ""
        if 'policy_indicator' in xml2 and 'checked="true"' in xml2:
            return f"toggled_on_ok center=({cx},{cy}) bounds=[{x1},{y1}][{x2},{y2}]"
        # 再点一次
        self.adb.tap(cx, cy)
        time.sleep(0.7)
        return f"toggled_on center=({cx},{cy}) bounds=[{x1},{y1}][{x2},{y2}] rid={rid}"

    def grant_shell_via_kitsune_superuser(self, log: LogFn = None, reuse_session: bool = False) -> str:
        """打开 Kitsune Mask → Superuser → 打开 [SharedUID] Shell 右侧开关授权。

        关键：只点右侧 Switch（policy_indicator），不要点左边 Shell 文字行。
        reuse_session=True：不 force-stop，复用当前已打开的 Kitsune。
        """
        steps: list[str] = []
        pkg = self.kitsune_pkg
        try:
            if not reuse_session:
                try:
                    self.adb.force_stop(pkg)
                except Exception:
                    pass
                time.sleep(0.25)
                try:
                    self.adb.shell("input", "keyevent", "3", timeout=5)
                except Exception:
                    pass
                time.sleep(0.2)
                self.open_kitsune(force_relaunch=True)
                time.sleep(0.55)
                steps.append("opened")
            else:
                # 见 Uninstall Magisk 后同会话直接授权：不 force-stop、尽量不重开
                already = False
                try:
                    dump = self.adb.shell("dumpsys", "activity", "activities", timeout=3) or ""
                    already = any(
                        "topResumedActivity" in ln and pkg in ln for ln in dump.splitlines()
                    )
                except Exception:
                    already = False
                if already:
                    steps.append("reuse_same_session_no_reopen")
                else:
                    self.open_kitsune(force_relaunch=False)
                    time.sleep(0.3)
                    steps.append("reuse_opened")

            super_labels = ("Superuser", "超级用户", "超级权限", "授权", "SU")
            tapped_tab = False
            for _ in range(6):
                if self._cancelled():
                    steps.append("cancelled")
                    return "|".join(steps)
                xml = self.adb.uiautomator_dump(force=True) or ""
                low = xml.lower()
                # 已在 Superuser 列表且能看到 Shell
                if ("shareduid" in low or "com.android.shell" in low or "[shareduid] shell" in low) and (
                    "superuser" in low or "policy_indicator" in low or "shell" in low
                ):
                    tapped_tab = True
                    steps.append("already_superuser_list")
                    break
                hit = self.adb.tap_any(list(super_labels), xml=xml, match_desc=True, match_text=True)
                if hit:
                    steps.append(f"tab={hit}")
                    tapped_tab = True
                    time.sleep(0.4)
                    break
                # 底部导航兜底
                for x in (360, 540, 720, 900):
                    try:
                        self.adb.tap(x, 2480)
                    except Exception:
                        pass
                    time.sleep(0.08)
                time.sleep(0.2)

            if not tapped_tab:
                steps.append("tab_miss")

            # 核心：点右侧 Switch，绝不先点左边 Shell 文字
            switched = False
            for attempt in range(5):
                if self._cancelled():
                    steps.append("cancelled")
                    return "|".join(steps)
                xml = self.adb.uiautomator_dump(force=True) or ""
                sw = self._tap_superuser_shell_switch(xml)
                steps.append(f"switch#{attempt+1}={sw}")
                self._log(log, f"Shell RIGHT Switch: {sw}")
                if sw.startswith("already_on") or "toggled_on" in sw or sw.startswith("fallback_right_tap"):
                    switched = True
                    if sw.startswith("already_on"):
                        break
                    time.sleep(0.5)
                    # 确认 checked
                    xml3 = self.adb.uiautomator_dump(force=True) or ""
                    if 'policy_indicator' in xml3 and re.search(
                        r'policy_indicator[^>]*checked="true"|checked="true"[^>]*policy_indicator',
                        xml3,
                    ):
                        steps.append("switch_confirmed")
                        break
                    if 'checked="true"' in xml3 and "Switch" in xml3:
                        steps.append("switch_checked_true")
                        break
                # 列表没找到就滚动
                try:
                    self.adb.shell("input", "swipe", "720", "1800", "720", "900", "300", timeout=8)
                except Exception:
                    pass
                time.sleep(0.5)

            if not switched:
                steps.append("switch_miss_try_detail")
                # 兜底：进详情页 Grant（次选）
                xml = self.adb.uiautomator_dump(force=True) or ""
                for key in ("[SharedUID] Shell", "SharedUID", "com.android.shell", "Shell"):
                    b = self.adb.find_node_bounds(text_substr=key, xml=xml)
                    if b:
                        self.adb.tap_bounds(b)
                        steps.append(f"row_detail={key}")
                        time.sleep(0.9)
                        break
                xml2 = self.adb.uiautomator_dump(force=True) or ""
                for lab in ("Forever", "永久", "Always", "始终"):
                    b = self.adb.find_node_bounds(text_substr=lab, xml=xml2)
                    if b:
                        self.adb.tap_bounds(b)
                        steps.append(f"dur={lab}")
                        time.sleep(0.35)
                        xml2 = self.adb.uiautomator_dump(force=True) or ""
                        break
                allow_hit = self.adb.tap_any(
                    ["Allow", "Grant", "允许", "同意", "Approve", "Permanent"],
                    xml=xml2,
                    match_desc=True,
                    match_text=True,
                )
                if allow_hit:
                    steps.append(f"policy={allow_hit}")
                else:
                    hit = self.adb.dismiss_magisk_su_dialog()
                    if hit:
                        steps.append(f"dialog={hit}")

            # 退出：reuse_session 时绝不 force-stop，见 Uninstall 后同会话继续 Settings/ih8
            try:
                self.adb.shell("input", "keyevent", "4", timeout=5)
            except Exception:
                pass
            if reuse_session:
                steps.append("keep_session_no_force_stop")
                return "|".join(steps)
            time.sleep(0.25)
            try:
                self._force_stop_kitsune_home()
            except Exception:
                pass
            steps.append("done")
            return "|".join(steps)
        except Exception as exc:
            steps.append(f"err={exc}")
            return "|".join(steps)


    def configure_kitsune_settings_ui(self, log: LogFn = None, reuse_session: bool = False) -> str:
        """打开 Kitsune Settings，只开启 Zygisk / MagiskHide / Enforce SuList。

        reuse_session=True：不 force-stop 重开，直接在当前 Kitsune 点齿轮。
        """
        notes: list[str] = []
        try:
            self.open_kitsune(force_relaunch=not reuse_session)
            time.sleep(0.25 if reuse_session else 0.45)
            if reuse_session:
                notes.append("reuse_session")
        except Exception as exc:
            return f"open_fail={exc}"
        try:
            xml = self.adb.uiautomator_dump(force=True) or ""
        except Exception:
            xml = ""
        b = self.adb.find_node_bounds(content_desc="Settings", xml=xml) or self.adb.find_node_bounds(
            resource_id="action_settings", xml=xml
        )
        if not b:
            self.adb.tap(1344, 208)
            notes.append("settings_coord")
        else:
            self.adb.tap_bounds(b)
            notes.append("settings_tap")
        time.sleep(0.45)
        # 仅当看到文件选择器时才清理，避免每次 force-stop 拖慢
        try:
            xml_pre = self.adb.uiautomator_dump(force=True) or ""
        except Exception:
            xml_pre = ""
        if any(k in (xml_pre or "").lower() for k in ("documentsui", "open from", "downloads", "recent")):
            for pkg in ("com.android.documentsui", "com.google.android.documentsui"):
                try:
                    self.adb.shell("am", "force-stop", pkg, timeout=6)
                except Exception:
                    pass
            time.sleep(0.2)
            try:
                xml_pre = self.adb.uiautomator_dump(force=True) or ""
            except Exception:
                xml_pre = ""
        xml_chk = xml_pre
        # 确认进了 Settings：没有 Zygisk/Magisk 设置项就重开齿轮
        if not re.search(r'text="(Zygisk|MagiskHide|System|App)"', xml_chk, re.I):
            notes.append("settings_retry")
            try:
                # 同会话：BACK 回首页再点齿轮；reuse_session 时绝不 force-stop
                for _ in range(2):
                    try:
                        self.adb.shell("input", "keyevent", "4", timeout=5)
                    except Exception:
                        pass
                    time.sleep(0.2)
                self.open_kitsune(force_relaunch=not bool(reuse_session))
                time.sleep(0.4)
                xml2 = self.adb.uiautomator_dump(force=True) or ""
                b2 = self.adb.find_node_bounds(content_desc="Settings", xml=xml2) or self.adb.find_node_bounds(
                    resource_id="action_settings", xml=xml2
                )
                if b2:
                    self.adb.tap_bounds(b2)
                else:
                    self.adb.tap(1344, 208)
                time.sleep(0.45)
            except Exception as exc:
                notes.append(f"settings_retry_err={exc}")

        targets = ("Zygisk", "MagiskHide", "Enforce SuList")
        forbidden_sub = (
            "configure magiskhide",
            "configure denylist",
            "this feature need",
            "need magiskhide",
            "hidelist",
        )
        done = {k: False for k in targets}

        def _exact_label_bounds(xml: str, label: str):
            """只接受 text 精确等于 label 的节点。"""
            for m in re.finditer(
                r'text="([^"]+)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                xml,
                re.I,
            ):
                t = (m.group(1) or "").strip()
                if t.lower() != label.lower():
                    continue
                low = t.lower()
                if any(f in low for f in forbidden_sub):
                    continue
                return tuple(map(int, m.groups()[1:]))
            for m in re.finditer(
                r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*text="([^"]+)"',
                xml,
                re.I,
            ):
                t = (m.group(5) or "").strip()
                if t.lower() != label.lower():
                    continue
                low = t.lower()
                if any(f in low for f in forbidden_sub):
                    continue
                return tuple(map(int, m.groups()[:4]))
            return None

        def _toggle_from_xml(xml: str) -> None:
            low_all = xml.lower()
            if ("configure magiskhide" in low_all or "hidelist" in low_all) and (
                "enforce sulist" not in low_all and 'text="Zygisk"' not in xml
            ):
                notes.append("escape_configure_page")
                try:
                    self.adb.shell("input", "keyevent", "4", timeout=5)
                except Exception:
                    pass
                time.sleep(0.6)
                return
            for label in targets:
                if done[label]:
                    continue
                lb = _exact_label_bounds(xml, label)
                if not lb:
                    continue
                y = (lb[1] + lb[3]) // 2
                best = None
                for na in re.findall(r"<node\b([^>]*)/>", xml):
                    if (
                        "Switch" not in na
                        and "CheckBox" not in na
                        and "selector_indicator" not in na
                        and "policy_indicator" not in na
                    ):
                        continue
                    if "Configure" in na:
                        continue
                    bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', na)
                    if not bm:
                        continue
                    x1, y1, x2, y2 = map(int, bm.groups())
                    cy = (y1 + y2) // 2
                    if abs(cy - y) > 90:
                        continue
                    cm = re.search(r'checked="(true|false)"', na)
                    checked = cm.group(1) if cm else "?"
                    best = ((x1 + x2) // 2, cy, checked)
                    break
                if not best:
                    self.adb.tap(1216, y)
                    time.sleep(0.28)
                    notes.append(f"{label}=right_tap")
                    done[label] = True
                    continue
                cx, cy, checked = best
                if checked == "true":
                    notes.append(f"{label}=already_on")
                    done[label] = True
                else:
                    self.adb.tap(cx, cy)
                    time.sleep(0.32)
                    notes.append(f"{label}=on")
                    done[label] = True

        # 先扫当前页；只有缺项才上滑/下滑找
        for page in range(4):
            try:
                xml = self.adb.uiautomator_dump(force=True) or ""
            except Exception:
                xml = ""
            if re.search(r'text="Configure MagiskHide"', xml, re.I):
                notes.append("seen_configure_label_skip")
            _toggle_from_xml(xml)
            if all(done.values()):
                notes.append("all_three_on")
                break
            # 首轮未见 Zygisk 时先上滑回顶部；否则向下翻
            try:
                if page == 0 and not re.search(r'text="Zygisk"', xml or "", re.I):
                    self.adb.shell("input", "swipe", "720", "900", "720", "1900", "180", timeout=6)
                else:
                    self.adb.shell("input", "swipe", "720", "1900", "720", "850", "180", timeout=6)
            except Exception:
                pass
            time.sleep(0.22)

        notes.append("done=" + ",".join(f"{k}:{done[k]}" for k in targets))
        self._log(log, f"Kitsune settings UI: {' | '.join(notes)[:240]}")
        # 三项开完只返回一次，保留当前 Kitsune 会话给 Modules/ih8
        try:
            self.adb.shell("input", "keyevent", "4", timeout=5)
            notes.append("back_once")
        except Exception as exc:
            notes.append(f"back_err={exc}")
        time.sleep(0.25)
        return "|".join(notes)[:360]

    def configure_kitsune_flags(self, log: LogFn = None, reuse_session: bool = False) -> str:
        """开启 Zygisk / MagiskHide / Enforce SuList。

        grant-to-settings-fast-v1:
        1) 若 su 未通，先 Shell 授权
        2) 先走 UI Settings 开关（可靠且快）
        3) sqlite/config 仅短超时 best-effort（旧逻辑 35s 挂死会卡死 STEP14→15）
        4) 返回后由 install_ih8_module 走 Modules -> Install from storage
        """
        outs: list[str] = []
        # 已有 root 就不要反复走完整 UI 授权，避免耗时
        su_ok = False
        try:
            so = (self.adb.shell_su("id", timeout=6) or "")
            su_ok = "uid=0" in so
            outs.append("su_ok" if su_ok else f"su={(so or '')[:40]}")
        except Exception as exc:
            outs.append(f"su_err={exc}")
        if not su_ok:
            try:
                # always GRANT popup first; Superuser only fallback
                popup = self.grant_shell_prefer_popup(log=log)
                outs.append(f"popup={str(popup)[:100]}")
                popup_ok = str(popup).startswith("popup_grant_ok") or "uid=0" in str(popup)
                if popup_ok:
                    g = popup
                    self._log(log, f"configure_flags Shell GRANT弹窗成功，跳过 Superuser: {str(popup)[:120]}")
                else:
                    self._log(log, f"configure_flags Shell GRANT未确认，Superuser兜底 reuse={reuse_session}")
                    g = self.grant_shell_via_kitsune_superuser(log=log, reuse_session=bool(reuse_session))
                outs.append(f"grant={str(g)[:80]}")
            except Exception as exc:
                outs.append(f"grant_err={exc}")
        # UI 开关优先（可靠）；reuse_session 时不重开 Kitsune。禁止先跑易挂死的 sqlite。
        ui = ""
        try:
            ui = self.configure_kitsune_settings_ui(log=log, reuse_session=reuse_session)
            outs.append("ui=" + ui[:160])
        except Exception as exc:
            outs.append(f"ui_err={exc}")
        # sqlite 仅作 best-effort 补强，短超时；UI 已 all_three_on 时更可跳过长等
        ui_ok = "all_three_on" in (ui or "") or (
            "Zygisk:True" in (ui or "") and "MagiskHide:True" in (ui or "") and "Enforce SuList:True" in (ui or "")
        )
        if not ui_ok:
            script = r"""
set +e
magisk --sqlite "INSERT OR REPLACE INTO settings (key,value) VALUES('zygisk','1');" 2>/dev/null
magisk --sqlite "INSERT OR REPLACE INTO settings (key,value) VALUES('magiskhide','1');" 2>/dev/null
magisk --sqlite "INSERT OR REPLACE INTO settings (key,value) VALUES('sulist','1');" 2>/dev/null
magisk --sqlite "INSERT OR REPLACE INTO settings (key,value) VALUES('denylist_enforced','0');" 2>/dev/null
magisk --sqlite "INSERT OR REPLACE INTO policies (uid,package_name,policy,until,logging,notification) VALUES(2000,'com.android.shell',2,0,1,0);" 2>/dev/null
magisk --sqlite "INSERT OR REPLACE INTO policies (uid,package_name,policy,until,logging,notification) VALUES(2000,'shell',2,0,1,0);" 2>/dev/null
mkdir -p /data/adb/magisk 2>/dev/null
mkdir -p /data/adb/magisk/.magisk 2>/dev/null
echo zygisk=1 >> /data/adb/magisk/.magisk/config 2>/dev/null
echo FLAGS_DONE
"""
            try:
                o = self.adb.shell_su_script(script, timeout=6)
                outs.append("sql=" + (o or "ok").strip().replace("\n", " ")[:120])
            except Exception as exc:
                outs.append(f"sql_skip={type(exc).__name__}")
        else:
            outs.append("sql=skip_ui_ok")
        return " | ".join(outs)[:450]
    # ------------------------------------------------------------------ Magisk
    def magisk_binary_ok(self) -> bool:
        """magisk 已装入系统/ramdisk：命令可用。优先普通 shell（无需 su）。"""
        probes = [
            ("magisk", "-v"),
            ("magisk", "-V"),
            ("/data/adb/magisk/magisk64", "-v"),
        ]
        # 1) 普通 adb shell（MuMu 已 root 时 magisk 在 PATH）
        for args in probes:
            try:
                out = (self.adb.shell(*args, timeout=8) or "").strip()
                low = out.lower()
                if out and "not found" not in low and "inaccessible" not in low and "no such" not in low:
                    if any(ch.isdigit() for ch in out) or "magisk" in low:
                        return True
            except Exception:
                continue
        # 2) su 兜底
        for args in probes:
            try:
                out = (self.adb.shell_su(" ".join(args)) or "").strip()
                if out and "not found" not in out.lower() and "no such" not in out.lower():
                    # 版本号或输出非空
                    if any(ch.isdigit() for ch in out) or "magisk" in out.lower() or len(out) >= 1:
                        # 过滤明显失败
                        if "Permission denied" in out and "magisk" not in out.lower():
                            continue
                        if out and not out.startswith("su:"):
                            return True
            except Exception:
                continue
        # 目录存在也算部分就绪
        try:
            out = self.adb.shell_su("ls /data/adb/magisk 2>/dev/null | head")
            if out and ("magisk" in out or "modules" in out or "busybox" in out):
                # 再试一次 version
                ver = self.adb.shell_su("magisk -v 2>/dev/null || true")
                if ver and "not found" not in ver.lower() and ver.strip():
                    return True
        except Exception:
            pass
        return False

    def open_kitsune(self, force_relaunch: bool = True) -> str:
        """打开 Kitsune Mask 首页并确保前台可见。

        force_relaunch=False：若已在前台则复用当前会话，不 force-stop。
        """
        outs: list[str] = []

        def _top_is_kitsune() -> bool:
            try:
                dump = self.adb.shell("dumpsys", "activity", "activities", timeout=3) or ""
            except Exception:
                return False
            for ln in dump.splitlines():
                if "topResumedActivity" in ln and self.kitsune_pkg in ln:
                    return True
            return False

        try:
            self.adb.shell("am", "force-stop", self.MUMU_STORE_PKG, timeout=12)
            outs.append("store_fs")
        except Exception as exc:
            outs.append(f"store={exc}")
        for pkg in ("com.android.documentsui", "com.google.android.documentsui"):
            try:
                self.adb.shell("am", "force-stop", pkg, timeout=10)
            except Exception:
                pass

        if not force_relaunch and _top_is_kitsune():
            outs.append("reuse_fg")
            for _ in range(3):
                try:
                    hit = self.adb.dismiss_magisk_su_dialog()
                    if hit:
                        outs.append(f"su={hit}")
                        time.sleep(0.35)
                except Exception:
                    pass
            try:
                self.dismiss_kitsune_notice_hide()
            except Exception:
                pass
            return "|".join(outs)[:240]

        if force_relaunch:
            try:
                self.adb.force_stop(self.kitsune_pkg)
            except Exception:
                pass
            time.sleep(0.25)
            outs.append("force_relaunch")
        else:
            outs.append("soft_launch")

        launched = False
        # monkey 比 am start 更稳（am start 可能 translucent 不在前台）
        try:
            o = self.adb.shell(
                "monkey",
                "-p",
                self.kitsune_pkg,
                "-c",
                "android.intent.category.LAUNCHER",
                "1",
                timeout=20,
            ) or ""
            outs.append("monkey=" + o.replace("\n", " ")[:80])
            launched = "Events injected" in o or "injected" in o.lower()
        except Exception as exc:
            outs.append(f"monkey_err={exc}")
        if not launched:
            for comp in (
                f"{self.kitsune_pkg}/com.topjohnwu.magisk.ui.MainActivity",
                f"{self.kitsune_pkg}/.ui.MainActivity",
            ):
                try:
                    o = self.adb.shell("am", "start", "-n", comp, timeout=20) or ""
                    if "Error" not in o and "Exception" not in o:
                        outs.append(f"am={comp.split('/')[-1]}")
                        launched = True
                        break
                except Exception as exc:
                    outs.append(str(exc)[:60])
        time.sleep(0.55)

        # 等待前台确实是 Kitsune（实测：第一次 monkey 后常仍是桌面，需再拉一次）
        fg_ok = False
        for i in range(5):
            if _top_is_kitsune():
                fg_ok = True
                break
            try:
                self.adb.shell(
                    "monkey",
                    "-p",
                    self.kitsune_pkg,
                    "-c",
                    "android.intent.category.LAUNCHER",
                    "1",
                    timeout=12,
                )
            except Exception:
                pass
            time.sleep(0.35 if i < 2 else 0.45)
        outs.append("fg_ok" if fg_ok else "fg_fail")

        # su: 只处理真正的 SuRequest，绝不因 Kitsune 首页误触 BACK
        for _ in range(4):
            try:
                hit = self.adb.dismiss_magisk_su_dialog()
                if hit:
                    outs.append(f"su={hit}")
                    time.sleep(0.45)
                    # 授权后确认仍在 Kitsune
                    if not _top_is_kitsune():
                        try:
                            self.adb.shell(
                                "monkey",
                                "-p",
                                self.kitsune_pkg,
                                "-c",
                                "android.intent.category.LAUNCHER",
                                "1",
                                timeout=15,
                            )
                        except Exception:
                            pass
                        time.sleep(1.0)
                else:
                    break
            except Exception as exc:
                outs.append(f"su_err={exc}")
                break

        # 警告卡片 Hide（内部也会在掉桌面时重开）
        hide_hit = self.dismiss_kitsune_notice_hide()
        if hide_hit:
            outs.append(f"hide={hide_hit}")

        # UI 信号：必须真有 Magisk/Install/Uninstall，不能只靠桌面图标名
        for _ in range(5):
            if not _top_is_kitsune():
                try:
                    self.adb.shell(
                        "monkey",
                        "-p",
                        self.kitsune_pkg,
                        "-c",
                        "android.intent.category.LAUNCHER",
                        "1",
                        timeout=15,
                    )
                except Exception:
                    pass
                time.sleep(0.9)
                continue
            try:
                ui = (self.adb.ui_full_text() or "").lower()
            except Exception:
                ui = ""
            if (
                "uninstall magisk" in ui
                or "home_magisk" in ui
                or ("magisk" in ui and "install" in ui)
                or "unofficial version of magisk" in ui
            ):
                outs.append("ui_ok")
                break
            time.sleep(0.5)
        return " | ".join(outs)[:400]

    def dismiss_kitsune_notice_hide(self) -> str:
        """首页 WARNING 卡点 Hide（resource-id home_notice_hide）。

        硬规则 hide-then-install-v2:
        1) 点到 Hide / 已无警告卡且见 Install|Uninstall -> 立刻返回，禁止再 reopen
        2) 整次最多 monkey 重开 1 次；已见首页 Install/Uninstall 后 0 次 reopen
        3) 用户观感: 点完 Hide 应马上点 Install，不能再“重启两次”
        """
        notes: list[str] = []
        reopen_used = 0
        max_reopen = 1

        def _top_is_kitsune() -> bool:
            try:
                dump = self.adb.shell("dumpsys", "activity", "activities", timeout=6) or ""
            except Exception:
                return False
            for ln in dump.splitlines():
                if "topResumedActivity" in ln and self.kitsune_pkg in ln:
                    return True
            return False

        def _home_ready(low: str) -> bool:
            if not low:
                return False
            if "uninstall magisk" in low or "卸载 magisk" in low:
                return True
            if "home_magisk" in low:
                return True
            if "home_magisk_button" in low:
                return True
            # 首页 Install（排除 Direct Install 方法页）
            if "magisk" in low and "install" in low and "direct install" not in low:
                return True
            return False

        def _has_notice(low: str) -> bool:
            return (
                "home_notice" in low
                or "home_notice_hide" in low
                or "unofficial version of magisk" in low
            )

        def _reopen_if_needed(reason: str) -> bool:
            nonlocal reopen_used
            if reopen_used >= max_reopen:
                notes.append(f"reopen_cap:{reason}")
                return False
            reopen_used += 1
            notes.append(reason)
            try:
                self.adb.shell("am", "force-stop", self.MUMU_STORE_PKG, timeout=10)
            except Exception:
                pass
            try:
                self.adb.shell(
                    "monkey",
                    "-p",
                    self.kitsune_pkg,
                    "-c",
                    "android.intent.category.LAUNCHER",
                    "1",
                    timeout=15,
                )
            except Exception:
                pass
            time.sleep(0.9)
            return True

        for attempt in range(4):
            # Hide 阶段不点 GRANT：GRANT 只在弹窗真正出现后点（重启后 / Install 触发后）
            try:
                xml = self.adb.uiautomator_dump(force=True) or ""
            except Exception:
                xml = ""
            low = (xml or "").lower()

            # 已见首页 Install/Uninstall：立刻结束，绝不 reopen
            if _home_ready(low) and not _has_notice(low):
                notes.append("no_notice" if attempt == 0 else "hide_done_go_install")
                break

            on_desktop = (
                "io.github.huskydg.magisk:id/" not in low
                and (
                    "mumu store" in low
                    or "app cloner" in low
                    or "search games" in low
                    or "lawnchair" in low
                )
            )
            if on_desktop or not xml.strip() or not _top_is_kitsune():
                if _home_ready(low):
                    notes.append("hide_done_go_install")
                    break
                why = f"refocus{attempt}" if not _top_is_kitsune() else f"desktop{attempt}"
                if not _reopen_if_needed(why):
                    notes.append("miss_no_more_reopen")
                    break
                continue

            # 优先 resource-id
            b = None
            for node in self._iter_ui_nodes(xml) or []:
                rid = (node.attrib.get("resource-id") or "").lower()
                text = (node.attrib.get("text") or "").strip()
                if rid.endswith("home_notice_hide") or (
                    text.lower() == "hide" and "notice" in rid
                ):
                    b = self.adb._parse_bounds(node.attrib.get("bounds") or "")
                    if b:
                        break
            if not b:
                # 文本 Hide 且靠近警告区（上半屏），排除底部导航
                for node in self._iter_ui_nodes(xml) or []:
                    text = (node.attrib.get("text") or "").strip()
                    rid = (node.attrib.get("resource-id") or "").lower()
                    if text.lower() != "hide":
                        continue
                    if "navigation" in rid or "nav" in rid:
                        continue
                    bb = self.adb._parse_bounds(node.attrib.get("bounds") or "")
                    if bb and bb[1] < 1600:
                        b = bb
                        break

            if not b:
                if _home_ready(low):
                    notes.append("no_notice")
                    break
                if not _has_notice(low):
                    notes.append(f"miss_ui{attempt}")
                    if not _reopen_if_needed(f"miss_reopen{attempt}"):
                        break
                    continue
                notes.append(f"miss{attempt}")
                time.sleep(0.35)
                continue

            x1, y1, x2, y2 = b
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            self.adb.tap(cx, cy)
            notes.append(f"tap_hide@{cx},{cy}")
            time.sleep(0.55)
            # 点 Hide 后立刻检查首页：必须仍在 Kitsune 且见 Install/Uninstall 才算成功
            try:
                xml2 = self.adb.uiautomator_dump(force=True) or ""
            except Exception:
                xml2 = ""
            low2 = (xml2 or "").lower()
            kitsune_ui = (
                "io.github.huskydg.magisk:id/" in low2
                or "com.topjohnwu.magisk:id/" in low2
                or "home_magisk" in low2
            )
            if kitsune_ui and _home_ready(low2) and not _has_notice(low2):
                notes.append("hidden")
                notes.append("hide_done_go_install")
                break
            if kitsune_ui and (not _has_notice(low2)) and (
                "install" in low2 or "uninstall" in low2 or "home_magisk" in low2
            ):
                notes.append("hidden_no_notice")
                notes.append("hide_done_go_install")
                break
            # 仍有警告卡则再点一次 Hide；绝不因此 force-stop/reopen Kitsune
            notes.append("hide_retry_same_session")
            time.sleep(0.25)
        return "|".join(notes)[:280]

    def kitsune_ui_status(self, check_binary: bool = False, force_dump: bool = True) -> dict:
        """解析 Kitsune UI：已安装会出现 Uninstall Magisk；未安装只有 Install。

        check_binary 默认 False：避免每次 UI 识别都跑 magisk_binary_ok（极慢）。
        仅在重启后校验等需要时显式 check_binary=True。
        """
        try:
            xml = self.adb.uiautomator_dump(force=bool(force_dump)) or ""
        except Exception:
            xml = ""
        try:
            texts = re.findall(r'text="([^"]*)"', xml or "")
            descs = re.findall(r'content-desc="([^"]*)"', xml or "")
            ui = "\n".join([t for t in texts if t] + [d for d in descs if d])
        except Exception:
            ui = ""
        if not ui:
            try:
                ui = self.adb.ui_full_text() or ""
            except Exception:
                ui = ""
        low = ui.lower()
        has_uninstall = ("uninstall magisk" in low) or ("卸载 magisk" in low) or ("卸载magisk" in low)
        has_install = ("\ninstall\n" in f"\n{low}\n") or low.strip().startswith("install") or (
            " install" in low and "direct install" not in low and not has_uninstall
        )
        if has_uninstall:
            has_install = False
        if "uninstall magisk" in low:
            has_uninstall = True
            has_install = False
        binary_ok = False
        if check_binary:
            try:
                binary_ok = bool(self.magisk_binary_ok())
            except Exception:
                binary_ok = False
        return {
            "ui": ui[:500],
            "has_uninstall_magisk": has_uninstall,
            "has_install_button": has_install and not has_uninstall,
            "binary_ok": binary_ok,
        }

    def _iter_ui_nodes(self, xml: str):
        if not (xml or "").strip():
            return
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return
        for node in root.iter("node"):
            yield node

    def _find_text_bounds_exclude(
        self,
        xml: str,
        *,
        must_contain: str,
        exclude_any: tuple[str, ...] = (),
        exact_text: bool = False,
    ):
        """在 UI dump 中找文本节点；可排除含指定子串的节点。返回 bounds 或 None。"""
        needle = (must_contain or "").lower().strip()
        if not needle:
            return None
        excludes = tuple(x.lower() for x in exclude_any if x)
        best = None
        best_y = 10**9
        for node in self._iter_ui_nodes(xml) or []:
            text = (node.attrib.get("text") or "").strip()
            desc = (node.attrib.get("content-desc") or "").strip()
            blob = f"{text} {desc}".strip()
            if not blob:
                continue
            low = blob.lower()
            if excludes and any(ex in low for ex in excludes):
                continue
            if exact_text:
                if text.lower() != needle and desc.lower() != needle:
                    continue
            else:
                if needle not in low:
                    continue
            b = self.adb._parse_bounds(node.attrib.get("bounds") or "")
            if not b:
                continue
            y = b[1]
            if y < best_y:
                best_y = y
                best = b
        return best

    def _find_kitsune_home_install_bounds(self, xml: str):
        """定位首页 Magisk 区 Install 按钮（优先 home_magisk_button）。

        install-tap-reopen-v3：
        - 绝不返回 Uninstall Magisk 相关节点
        - ET 解析失败时用 regex 兜底取 text="Install" 的 bounds
        - home_magisk_button 文本为空也可点（Kitsune 常见：父节点空字，子节点 Install）
        - 若页面已有 Uninstall Magisk，返回 None（表示已安装，禁止点 Install）
        """
        raw = xml or ""
        try:
            full = raw.lower()
            if "uninstall magisk" in full or "卸载 magisk" in full or "卸载magisk" in full:
                return None
        except Exception:
            pass

        def _ok_home_install_bounds(b):
            if not b or len(b) != 4:
                return False
            # 首页 Magisk 卡 Install：上半屏偏上；排除底部导航/赞助
            return 150 <= b[1] <= 1900 and b[3] <= 2200 and b[2] > b[0] and b[3] > b[1]

        # 1) resource-id home_magisk_button（父按钮，text 常为空）
        for node in self._iter_ui_nodes(raw) or []:
            rid = (node.attrib.get("resource-id") or "").lower()
            text = (node.attrib.get("text") or "").strip()
            desc = (node.attrib.get("content-desc") or "").strip()
            if self.adb._is_forbidden_uninstall_target(text, desc, rid):
                continue
            if rid.endswith("home_magisk_button"):
                tlow = text.lower()
                if tlow and tlow not in ("install",) and "uninstall" in tlow:
                    continue
                if tlow and tlow not in ("", "install") and "uninstall" in tlow:
                    continue
                if tlow and tlow not in ("", "install") and tlow != "install":
                    # 非空且不是 Install → 跳过（例如其它按钮）
                    if "install" not in tlow or "uninstall" in tlow or "direct" in tlow:
                        continue
                b = self.adb._parse_bounds(node.attrib.get("bounds") or "")
                if _ok_home_install_bounds(b):
                    return b

        # 2) text 精确 = Install
        candidates = []
        for node in self._iter_ui_nodes(raw) or []:
            text = (node.attrib.get("text") or "").strip()
            desc = (node.attrib.get("content-desc") or "").strip()
            rid = (node.attrib.get("resource-id") or "").lower()
            cls = (node.attrib.get("class") or "").lower()
            if self.adb._is_forbidden_uninstall_target(text, desc, rid):
                continue
            if text.lower() != "install":
                continue
            if "notice" in rid:
                continue
            if "webview" in cls or "paypal" in rid or "donate" in rid:
                continue
            blob = f"{text} {desc} {rid}".lower()
            if "paypal" in blob or "donate" in blob or "magiskdonate" in blob:
                continue
            b = self.adb._parse_bounds(node.attrib.get("bounds") or "")
            if _ok_home_install_bounds(b):
                candidates.append(b)
        if candidates:
            candidates.sort(key=lambda bb: bb[1])
            return candidates[0]

        # 3) regex 兜底：ET 失败或节点树异常时仍能取 Install bounds
        try:
            for m in re.finditer(
                r'text="Install"[^>]*bounds="(\[\d+,\d+\]\[\d+,\d+\])"'
                r'|bounds="(\[\d+,\d+\]\[\d+,\d+\])"[^>]*text="Install"',
                raw,
            ):
                bs = m.group(1) or m.group(2)
                b = self.adb._parse_bounds(bs or "")
                if _ok_home_install_bounds(b):
                    return b
            for m in re.finditer(
                r'resource-id="[^"]*home_magisk_button"[^>]*bounds="(\[\d+,\d+\]\[\d+,\d+\])"'
                r'|bounds="(\[\d+,\d+\]\[\d+,\d+\])"[^>]*resource-id="[^"]*home_magisk_button"',
                raw,
            ):
                bs = m.group(1) or m.group(2)
                b = self.adb._parse_bounds(bs or "")
                if _ok_home_install_bounds(b):
                    return b
        except Exception:
            pass
        return None



    def _find_kitsune_third_direct_install(self, xml: str):
        """只返回第3项 Direct Install (modify /system directly)。

        优先 resource-id=method_direct_system。
        绝不可选 method_direct（Recommended）。
        返回 (bounds, label) 或 (None, "")。
        """
        for node in self._iter_ui_nodes(xml) or []:
            rid = (node.attrib.get("resource-id") or "").lower()
            if rid.endswith("method_direct_system"):
                b = self.adb._parse_bounds(node.attrib.get("bounds") or "")
                if b:
                    label = (node.attrib.get("text") or "").strip() or (
                        "Direct Install (modify /system directly)"
                    )
                    return b, label
        preferred_keys = (
            "direct install (modify /system directly)",
            "modify /system directly",
            "modify /systemdirectly",
            "直接安装（修改 /system）",
            "修改 /system",
        )
        candidates = []
        for node in self._iter_ui_nodes(xml) or []:
            rid = (node.attrib.get("resource-id") or "").lower()
            if rid.endswith("method_direct") and not rid.endswith("method_direct_system"):
                continue
            text = (node.attrib.get("text") or "").strip()
            desc = (node.attrib.get("content-desc") or "").strip()
            label = text or desc
            if not label:
                continue
            low = label.lower().replace("  ", " ")
            if "recommended" in low:
                continue
            if "select and patch" in low or "patch a file" in low:
                continue
            ok = False
            for key in preferred_keys:
                if key in low:
                    ok = True
                    break
            if not ok:
                if (
                    "direct install" in low
                    and "modify" in low
                    and "system" in low
                    and "recommended" not in low
                ):
                    ok = True
            if not ok:
                continue
            b = self.adb._parse_bounds(node.attrib.get("bounds") or "")
            if not b:
                continue
            candidates.append((b[1], b, label))

        if not candidates:
            return None, ""

        def rank(item):
            y, b, label = item
            low = label.lower()
            score = 0
            if "modify /system directly" in low:
                score += 100
            if "modify" in low and "system" in low:
                score += 50
            if "recommended" in low:
                score -= 1000
            return (-score, -y)

        candidates.sort(key=rank)
        _, b, label = candidates[0]
        return b, label

    def complete_kitsune_post_install_session(
        self,
        vmindex: int | None = None,
        log: LogFn = None,
        *,
        configure_settings: bool = True,
        install_ih8: bool = False,
        restart_after_ih8: bool = True,
        boot_timeout: int = 240,
        force_relaunch_once: bool = False,
    ) -> dict:
        """一次打开 Kitsune：先 su 触发 GRANT → Settings三项 → Modules装ih8。中途不 force-stop。仅 LETS GO 后第一次 restart 之后调用。"""
        out: dict = {
            "grant": "",
            "settings": "",
            "ih8": "",
            "settings_done": False,
            "ih8_done": False,
            "rebooted": False,
            "detail": "",
        }
        notes: list[str] = []
        try:
            already_fg = False
            if not force_relaunch_once:
                try:
                    dump = self.adb.shell("dumpsys", "activity", "activities", timeout=3) or ""
                    already_fg = any(
                        "topResumedActivity" in ln and self.kitsune_pkg in ln
                        for ln in dump.splitlines()
                    )
                except Exception:
                    already_fg = False
            if already_fg:
                notes.append("same_session_no_reopen")
                self._log(log, f"VM={vmindex} 见 Uninstall 后同会话继续 Shell/Settings，不结束 Magisk 进程")
            else:
                self.open_kitsune(force_relaunch=bool(force_relaunch_once))
                time.sleep(0.35 if not force_relaunch_once else 0.55)
                notes.append("open_once" if force_relaunch_once else "soft_open")
        except Exception as exc:
            out["detail"] = f"open_fail={exc}"
            self._log(log, f"VM={vmindex} Kitsune 一次会话打开失败: {exc}")
            return out

        try:
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

        if configure_settings:
            try:
                flags = self.configure_kitsune_flags(log=log, reuse_session=True)
                out["settings"] = flags
                out["settings_done"] = True
                notes.append("settings_ok")
                self._log(log, f"VM={vmindex} [STEP15-16] Settings三项+BACK一次: {str(flags)[:160]}")
            except Exception as exc:
                out["settings"] = f"err={exc}"
                notes.append(f"settings_err={exc}")
                self._log(log, f"VM={vmindex} 一次会话 Settings 失败: {exc}")
        else:
            notes.append("settings_skip_login")

        if install_ih8:
            try:
                # Settings 已 BACK 一次；这里不再结束 Magisk，同会话直接 Modules/ih8
                notes.append("ih8_same_session_no_force_stop")
                ih = self.install_ih8_module(
                    log=log,
                    vmindex=None if restart_after_ih8 else vmindex,
                    restart=False,
                    boot_timeout=boot_timeout,
                    reuse_session=True,
                )
                out["ih8"] = ih
                notes.append(f"ih8={str(ih)[:80]}")
                self._log(log, f"VM={vmindex} [STEP17-19] Modules/Install from storage/ih8: {str(ih)[:160]}")
                need_restart = self._ih8_result_needs_restart(str(ih))
                if need_restart:
                    out["ih8_done"] = True
                    if restart_after_ih8 and vmindex is not None:
                        rr = self.restart_vm_and_wait(
                            int(vmindex),
                            log=log,
                            boot_timeout=boot_timeout,
                            reason="ih8 module installed (one-session)",
                        )
                        out["rebooted"] = str(rr).startswith("ok") or rr is True or str(rr) == "ok"
                        out["ih8"] = f"{ih}|restart={rr}"
                        notes.append(f"restart={rr}")
                    else:
                        notes.append("ih8_need_restart_deferred")
                else:
                    out["ih8_done"] = True
                    notes.append("ih8_already")
            except Exception as exc:
                out["ih8"] = f"err={exc}"
                notes.append(f"ih8_err={exc}")
                self._log(log, f"VM={vmindex} 一次会话 ih8 失败: {exc}")
        else:
            notes.append("ih8_skip")

        # 成功装 ih8 会 restart device；未重启也不 force-stop Magisk，只回桌面
        if not out.get("rebooted"):
            try:
                self.adb.shell("input", "keyevent", "3", timeout=8)
                notes.append("home_soft_no_force_stop")
            except Exception:
                pass

        out["detail"] = "|".join(notes)[:400]
        self._log(log, f"VM={vmindex} Kitsune 一次会话完成: {out['detail']}")
        return out

    def ensure_kitsune_priority_check(
        self,
        vmindex: int,
        *,
        log: LogFn = None,
        boot_timeout: int = 240,
        force: bool = False,
        configure_settings: bool = False,
    ) -> dict:
        """启动后第一件事：优先检查 Kitsune Mask。

        顺序保证：本方法必须在任何 NekoBox/代理 UI 之前调用。

        规则：
        - 登录复用（configure_settings=False）：
          只打开一次 Kitsune 看是否有 Uninstall Magisk。
          有 → 已装 Direct Install，直接跳过（不进 Settings，不反复开关）。
          无 → 才 Install → 第3项 Direct Install → Let's Go → restart。
          不检查/不点 Zygisk/MagiskHide/Enforce SuList。
        - 新建机（configure_settings=True）：
          同上完成 Direct Install 后，再做 Shell 授权 + Settings 三项开关。
          Modules/ih8 与 Settings 同属 complete_kitsune_post_install_session（install_ih8=True）。
        - 登录有缓存：绝不打开 Kitsune，直接放行去代理。
        - 新建有缓存且 Settings 已完成：也不打开。
        - 新建有缓存但 Settings 未完成：才打开一次补 Settings。
        - 无缓存/未见 Uninstall：才走 Install/Direct Install。
        """
        result: dict = {
            "needed": False,
            "installed": False,
            "rebooted": False,
            "detail": "",
            "skipped_cached": False,
            "priority_check": True,
            "configure_settings": bool(configure_settings),
        }
        mode = "新建设置" if configure_settings else "登录仅查Uninstall"
        self._log(log, f"VM={vmindex} [STEP1] 优先检查 Kitsune Mask（{mode}，代理未启动）")

        # 登录复用：magisk 命令已可用 = Direct Install 已生效，无需再开 UI 点 Install
        if (not force) and (not configure_settings):
            try:
                pkg_ok = self.adb.package_installed(self.kitsune_pkg)
            except Exception:
                pkg_ok = False
            try:
                bin_ok = self.magisk_binary_ok()
            except Exception:
                bin_ok = False
            if pkg_ok and bin_ok:
                result["installed"] = True
                result["skipped_cached"] = True
                result["detail"] = "login_magisk_binary_ok_skip_ui"
                result["settings_done"] = bool(self.is_kitsune_settings_done(vmindex))
                try:
                    self.mark_kitsune_done(vmindex, result["detail"], settings_ok=result["settings_done"])
                except Exception:
                    pass
                self._log(
                    log,
                    f"VM={vmindex} [STEP1] 登录：magisk 命令可用，跳过 Kitsune UI，直接装包/代理",
                )
                return result

        if not force and self.is_kitsune_done(vmindex):
            try:
                if not self.adb.package_installed(self.kitsune_pkg):
                    self.clear_kitsune_done(vmindex)
                    self._log(log, f"VM={vmindex} [STEP1] 缓存失效：Kitsune 包不存在，改走完整安装")
                else:
                    # 登录复用：有缓存就直接过，不再打开/结束 Kitsune，立刻去代理+Venmo
                    if not configure_settings:
                        result["installed"] = True
                        result["skipped_cached"] = True
                        result["detail"] = "login_skip_open_kitsune_cached_uninstall_ok"
                        result["settings_done"] = bool(self.is_kitsune_settings_done(vmindex))
                        self._log(
                            log,
                            f"VM={vmindex} [STEP1] 登录缓存命中：不打开 Kitsune，直接进入代理/登录",
                        )
                        return result
                    # 新建：Settings 也已完成 → 同样不反复打开
                    if self.is_kitsune_settings_done(vmindex):
                        result["installed"] = True
                        result["skipped_cached"] = True
                        result["settings_done"] = True
                        result["detail"] = "create_skip_open_kitsune_cached_all_done"
                        self._log(
                            log,
                            f"VM={vmindex} [STEP1] 新建缓存命中且 Settings 已完成：跳过打开 Kitsune",
                        )
                        return result
                    # 新建但 Settings 未完成：才打开一次补 Settings
                    try:
                        self.adb.shell("am", "force-stop", self.MUMU_STORE_PKG, timeout=12)
                    except Exception:
                        pass
                    self._log(log, f"VM={vmindex} [STEP1] 缓存命中但 Settings 未完成，打开一次补 Settings")
                    self.open_kitsune(force_relaunch=True)
                    time.sleep(1.4)
                    try:
                        self.dismiss_kitsune_notice_hide()
                    except Exception:
                        pass
                    st = {}
                    try:
                        st = self.kitsune_ui_status() or {}
                    except Exception as exc:
                        self._log(log, f"VM={vmindex} [STEP1] kitsune_ui_status 失败: {exc}")
                    if st.get("has_uninstall_magisk"):
                        result["installed"] = True
                        result["skipped_cached"] = True
                        result["detail"] = "kitsune_cached_ok_verified_uninstall"
                        try:
                            # 新建补齐：同会话完成 GRANT + Settings三项 + Modules/ih8（不反复 kill）
                            sess = self.complete_kitsune_post_install_session(
                                vmindex,
                                log=log,
                                configure_settings=True,
                                install_ih8=True,
                                restart_after_ih8=True,
                                boot_timeout=boot_timeout,
                                force_relaunch_once=False,
                            )
                            detail_s = str(sess.get("detail") or "")
                            result["detail"] += f" one_session={detail_s[:160]}"
                            result["grant"] = sess.get("grant", "")
                            if sess.get("settings_done"):
                                result["settings_done"] = True
                            if sess.get("ih8_done") or sess.get("ih8"):
                                result["ih8_done"] = True
                                result["ih8"] = str(sess.get("ih8") or "")
                            if sess.get("rebooted"):
                                result["rebooted"] = True
                            self.mark_kitsune_done(
                                vmindex,
                                result["detail"],
                                settings_ok=bool(result.get("settings_done")),
                            )
                            self._log(
                                log,
                                f"VM={vmindex} [STEP1] 新建补 Settings+ih8 一次会话: {detail_s[:200]}",
                            )
                        except Exception as exc:
                            result["detail"] += f" one_session_err={exc}"
                            self._log(log, f"VM={vmindex} [STEP1] 新建补会话失败: {exc}")
                        if not result.get("rebooted"):
                            try:
                                self._force_stop_kitsune_home()
                            except Exception:
                                pass
                        return result
                    self.clear_kitsune_done(vmindex)
                    self._log(
                        log,
                        f"VM={vmindex} [STEP1] 缓存命中但未见 Uninstall Magisk，清缓存并完整安装",
                    )
            except Exception as exc:
                self._log(log, f"VM={vmindex} [STEP1] 轻量确认异常，改完整安装: {exc}")
                try:
                    self.clear_kitsune_done(vmindex)
                except Exception:
                    pass

        full = self.ensure_kitsune_magisk_direct_install(
            vmindex,
            log=log,
            boot_timeout=boot_timeout,
            force=force or (not self.is_kitsune_done(vmindex)),
            configure_settings=bool(configure_settings),
            # 新建/RECYCLE：configure_settings=True 时必须连跑 15-19（Settings+Modules/ih8）
            install_ih8=bool(configure_settings),
        )
        full = dict(full or {})
        full["priority_check"] = True
        full["configure_settings"] = bool(configure_settings)
        if full.get("installed") or full.get("skipped_cached"):
            self._log(log, f"VM={vmindex} [STEP1] Kitsune 完成 detail={full.get('detail')}")
        else:
            self._log(log, f"VM={vmindex} [STEP1] Kitsune 未确认 detail={full.get('detail')}")
        return full


    def ensure_kitsune_magisk_direct_install(
        self,
        vmindex: int,
        *,
        log: LogFn = None,
        boot_timeout: int = 240,
        force: bool = False,
        max_reopen: int = 3,
        configure_settings: bool = False,
        install_ih8: bool = False,
    ) -> dict:
        """检查/安装 Kitsune Magisk Direct Install。

        新建硬规则 19 步（create-19steps-v1，禁止擅自改序）：
        1) 打开 Kitsune Mask
        2) 弹出框点 Remember choice forever
        3) 再点 Allow（永久授权；临时授权不会出现第3项）
        4) 点击 Hide
        5) 直接点 Install
        6) 检查 Direct Install (modify /system directly)
        7) 找不到 → 结束 Kitsune Mask 进程
        8) 再打开 Kitsune Mask
        9) 直接点 Install
        10) 再检查；找到第3项 Direct Install (modify /system directly) 就选第3项
            （绝不可选第2项 Direct Install (Recommended)）
        11) 点 LET'S GO
        12) 模拟器 restart device
        13) 再打开 Kitsune Mask
        14) 发起 shell 后，弹出窗口点 GRANT（不点 Deny）
        15) Settings 打开 Zygisk / MagiskHide / Enforce SuList
        16) 直接返回一次（只 BACK 一次，不进 Configure MagiskHide）
        17) 点 Modules
        18) 点 Install from storage
        19) 加载 ih8SecureLock-v8.zip 后 restart device

        其它：
        - 见到 Uninstall Magisk → 已安装，不点 Install
        - configure_settings=True（仅新建）：走 13–19
        - configure_settings=False（登录复用）：只确认 Uninstall / 必要时 Direct Install，不进 Settings/Modules
        """
        result: dict = {
            "needed": False,
            "installed": False,
            "rebooted": False,
            "detail": "",
            "skipped_cached": False,
            "configure_settings": bool(configure_settings),
            "settings_done": False,
        }
        if not force and self.is_kitsune_done(vmindex):
            # 登录可缓存跳过；新建必须 magisk binary + settings 都真完成，否则清缓存重跑
            # 防止删除后索引复用 kitsune_ok_vmN.json 误跳过 Direct Install
            bin_ok = False
            try:
                bin_ok = bool(self.magisk_binary_ok())
            except Exception:
                bin_ok = False
            settings_ok = bool(self.is_kitsune_settings_done(vmindex))
            if configure_settings and not (bin_ok and settings_ok):
                self.clear_kitsune_done(vmindex)
                self._log(
                    log,
                    f"VM={vmindex} 新建 kitsune 缓存失效"
                    f"(bin={bin_ok} settings={settings_ok})，强制完整 Install/Direct Install",
                )
            elif (not configure_settings) or (bin_ok and settings_ok):
                result["installed"] = True
                result["skipped_cached"] = True
                result["settings_done"] = settings_ok
                result["detail"] = (
                    "kitsune_cached_ok_skip"
                    if not configure_settings
                    else "create_cached_ok_bin_settings"
                )
                self._log(
                    log,
                    f"VM={vmindex} Kitsune 已完成首次检查(缓存)，跳过"
                    f" mode={'create' if configure_settings else 'login'} bin={bin_ok} settings={settings_ok}",
                )
                return result

        if not self.adb.package_installed(self.kitsune_pkg):
            result["detail"] = "kitsune_pkg_missing"
            self._log(log, f"VM={vmindex} Kitsune 包未安装")
            return result

        self._log(
            log,
            f"VM={vmindex} 检查 Kitsune Mask / Magisk Direct Install "
            f"(settings={'on' if configure_settings else 'off'})",
        )
        try:
            self.adb.shell("am", "force-stop", self.MUMU_STORE_PKG, timeout=12)
        except Exception:
            pass

        def _kill_reopen(reason: str) -> None:
            """无第3项时瞬间重启 Magisk，再打开准备点 Install。"""
            self._log(log, f"VM={vmindex} 瞬间重启 Magisk 并重开: {reason}")
            try:
                self.adb.force_stop(self.kitsune_pkg)
            except Exception:
                pass
            try:
                self.adb.shell("am", "kill", self.kitsune_pkg, timeout=10)
            except Exception:
                pass
            time.sleep(0.45)
            try:
                self.adb.shell("input", "keyevent", "3", timeout=8)
            except Exception:
                pass
            time.sleep(0.25)
            try:
                # force_relaunch=True 确保干净重开，避免停在方法页/桌面
                self.open_kitsune(force_relaunch=True)
            except Exception as exc:
                self._log(log, f"VM={vmindex} 重开 Kitsune 失败: {exc}")
            time.sleep(0.55)
            try:
                hide = self.dismiss_kitsune_notice_hide()
                if hide:
                    self._log(log, f"VM={vmindex} 重启Magisk后 Hide: {hide}")
            except Exception:
                pass
            try:
                xml0 = self.adb.uiautomator_dump(force=True) or ""
            except Exception:
                xml0 = ""
            low0 = (xml0 or "").lower()
            if any(k in low0 for k in ("id/grant", 'text="grant"', "remember choice forever", "requesting superuser")):
                hit = self.adb.dismiss_magisk_su_dialog()
                if hit:
                    self._log(log, f"VM={vmindex} 重开后 su(弹窗可见): {hit}")

        def _open_once(reason: str, *, force_relaunch: bool = False) -> None:
            """打开 Kitsune。force_relaunch=False 时不 force-stop，复用当前会话。"""
            self._log(
                log,
                f"VM={vmindex} 打开 Kitsune Mask: {reason} "
                f"(force_relaunch={'yes' if force_relaunch else 'no'})",
            )
            try:
                self.open_kitsune(force_relaunch=bool(force_relaunch))
            except Exception as exc:
                self._log(log, f"VM={vmindex} 打开 Kitsune 失败: {exc}")
            time.sleep(0.7 if force_relaunch else 0.35)
            try:
                hide = self.dismiss_kitsune_notice_hide()
                if hide:
                    self._log(log, f"VM={vmindex} Hide 警告卡: {hide}")
            except Exception:
                pass
            # 打开首页阶段不主动点 GRANT；仅当 dump 已见 GRANT/Allow 弹窗才处理一次
            try:
                xml0 = self.adb.uiautomator_dump(force=True) or ""
            except Exception:
                xml0 = ""
            low0 = (xml0 or "").lower()
            if any(k in low0 for k in ("id/grant", 'text="grant"', "remember choice forever", "requesting superuser")):
                hit = self.adb.dismiss_magisk_su_dialog()
                if hit:
                    self._log(log, f"VM={vmindex} Kitsune 打开后 su(弹窗可见): {hit}")

        def _wait_home_ready(timeout: float = 8.0) -> dict:
            t0 = time.time()
            last = {}
            force_next = True
            while time.time() - t0 < timeout:
                if self._cancelled():
                    break
                try:
                    st = self.kitsune_ui_status(check_binary=False, force_dump=force_next)
                except Exception:
                    st = {}
                force_next = False
                last = st
                ui = (st.get("ui") or "").lower()
                if st.get("has_uninstall_magisk") or st.get("has_install_button"):
                    return st
                if "magisk" in ui and ("install" in ui or "uninstall" in ui or "ramdisk" in ui):
                    return st
                time.sleep(0.28)
            return last

        def _tap_home_install(retries: int = 8) -> bool:
            """点首页 Install。二次打开必须点到，禁止空转后直接杀进程。

            install-tap-reopen-v3：bounds → exact text → home_magisk_button rid → 1440x2560 坐标兜底。
            """
            notice_cleared = False
            # 1440x2560 实测 home_magisk_button / Install 中心
            fallback_xy = (1120, 512)

            def _after_install_su(tag: str) -> None:
                try:
                    from paths import LOG_TEST_DIR
                    dump_dir = str(LOG_TEST_DIR)
                except Exception:
                    dump_dir = None
                try:
                    su_hit = self.adb.wait_and_forever_allow_su(
                        timeout=3.5,
                        poll=0.25,
                        dump_dir=dump_dir,
                        tag=tag,
                    )
                except Exception as exc:
                    su_hit = f"wait_err={exc}"
                if su_hit:
                    self._log(log, f"VM={vmindex} Install后永久授权: {su_hit}")
                else:
                    self._log(
                        log,
                        f"VM={vmindex} Install后3.5s内未见su弹窗(可能已永久授权/临时授权残留或稍后弹出)",
                    )
                time.sleep(0.45)

            def _confirm_left_home_or_method() -> bool:
                try:
                    ui_now = (self.adb.ui_full_text() or "").lower()
                except Exception:
                    ui_now = ""
                if "uninstall magisk" in ui_now:
                    return True
                if any(
                    k in ui_now
                    for k in (
                        "direct install",
                        "select and patch",
                        "method_patch",
                        "let's go",
                        "lets go",
                    )
                ):
                    return True
                # 仍停在首页 Install 视为未进入方法页
                if "install" in ui_now and "magisk" in ui_now and "direct install" not in ui_now:
                    return False
                return False

            for attempt in range(max(1, int(retries))):
                if self._cancelled():
                    return False
                try:
                    hit_su = self.adb.dismiss_magisk_su_dialog()
                    if hit_su:
                        self._log(log, f"VM={vmindex} 点首页 Install 前 su: {hit_su}")
                        time.sleep(0.3)
                except Exception:
                    pass

                try:
                    xml = self.adb.uiautomator_dump(force=True) or ""
                except Exception:
                    xml = ""
                low = (xml or "").lower()
                if "uninstall magisk" in low:
                    self._log(log, f"VM={vmindex} 等待点Install时已见 Uninstall Magisk")
                    return False

                # desktop-no-blind-tap-v1: desktop/not-foreground -> soft relaunch, never blind coord
                on_desktop = (
                    "io.github.huskydg.magisk:id/" not in low
                    and (
                        "mumu store" in low
                        or "app cloner" in low
                        or "search games" in low
                        or "lawnchair" in low
                        or ("kitsune mask" in low and "ramdisk" not in low and "home_magisk_button" not in low)
                    )
                )
                top_kitsune = False
                try:
                    dump = self.adb.shell("dumpsys", "activity", "activities", timeout=3) or ""
                    top_kitsune = any(
                        "topResumedActivity" in ln and self.kitsune_pkg in ln
                        for ln in dump.splitlines()
                    )
                except Exception:
                    top_kitsune = False
                has_magisk_ui = (
                    "io.github.huskydg.magisk:id/" in low
                    or "ramdisk" in low
                    or "home_magisk_button" in low
                    or "uninstall magisk" in low
                    or bool(__import__("re").search(r'text="Install"', xml or ""))
                    or "modify /system directly" in low
                    or "method_direct" in low
                )
                if on_desktop or (not top_kitsune and not has_magisk_ui):
                    self._log(
                        log,
                        f"VM={vmindex} 点Install前不在Kitsune首页(desktop={on_desktop} top={top_kitsune} magisk_ui={has_magisk_ui}) → 软拉回 attempt={attempt}",
                    )
                    try:
                        self.open_kitsune(force_relaunch=False)
                    except Exception as exc:
                        self._log(log, f"VM={vmindex} 软拉回Kitsune异常: {exc}")
                    time.sleep(0.55)
                    continue

                # 已在方法页则视为成功
                if any(
                    k in low
                    for k in (
                        "method_direct_system",
                        "modify /system directly",
                        "select and patch a file",
                        "method_patch",
                    )
                ):
                    self._log(
                        log,
                        f"VM={vmindex} 点Install前已在方法页 attempt={attempt}",
                    )
                    return True

                b = self._find_kitsune_home_install_bounds(xml)
                if b:
                    self.adb.tap_bounds(b)
                    self._log(
                        log,
                        f"VM={vmindex} 点首页 Install attempt={attempt} bounds={b} install_tap_immediate",
                    )
                    time.sleep(0.85)
                    _after_install_su(f"vm{vmindex}_install_su")
                    return True

                # 未见 bounds：Hide 一次后再找
                if (not notice_cleared) and (
                    "home_notice" in low
                    or "home_notice_hide" in low
                    or "unofficial version of magisk" in low
                ):
                    try:
                        hide = self.dismiss_kitsune_notice_hide()
                        notice_cleared = True
                        if hide:
                            self._log(log, f"VM={vmindex} 点Install前Hide: {hide}")
                    except Exception as exc:
                        self._log(log, f"VM={vmindex} 点Install前Hide异常: {exc}")
                    try:
                        xml = self.adb.uiautomator_dump(force=True) or ""
                    except Exception:
                        xml = ""
                    low = (xml or "").lower()
                    if "uninstall magisk" in low:
                        self._log(log, f"VM={vmindex} Hide后已见 Uninstall Magisk")
                        return False
                    b = self._find_kitsune_home_install_bounds(xml)
                    if b:
                        self.adb.tap_bounds(b)
                        self._log(
                            log,
                            f"VM={vmindex} 点首页 Install attempt={attempt} bounds={b} hide_done_go_install",
                        )
                        time.sleep(0.85)
                        _after_install_su(f"vm{vmindex}_install_su")
                        return True

                # exact text
                try:
                    if self.adb.tap_exact_text("Install"):
                        self._log(log, f"VM={vmindex} tap_exact Install attempt={attempt}")
                        time.sleep(0.85)
                        _after_install_su(f"vm{vmindex}_install_su_text")
                        return True
                except Exception:
                    pass

                # rid 兜底
                try:
                    if self.adb.tap_id("home_magisk_button") or self.adb.tap_id(
                        "io.github.huskydg.magisk:id/home_magisk_button"
                    ):
                        self._log(
                            log,
                            f"VM={vmindex} tap_id home_magisk_button attempt={attempt}",
                        )
                        time.sleep(0.85)
                        _after_install_su(f"vm{vmindex}_install_su_rid")
                        return True
                except Exception:
                    pass

                # desktop-no-blind-tap-v1: coord fallback only on Magisk home with Install signal
                has_install_text = bool(
                    re.search(r'text="Install"', xml or "")
                    or ("\ninstall\n" in f"\n{low}\n")
                    or ("home_magisk_button" in low and "uninstall magisk" not in low)
                )
                on_magisk_home = (
                    "io.github.huskydg.magisk:id/" in low
                    or ("magisk" in low and ("ramdisk" in low or "zygisk" in low or "home_magisk_button" in low))
                )
                if has_install_text and on_magisk_home:
                    try:
                        self.adb.tap(fallback_xy[0], fallback_xy[1])
                        self._log(
                            log,
                            f"VM={vmindex} 点首页 Install 坐标兜底 attempt={attempt} "
                            f"xy={fallback_xy} has_text={has_install_text}",
                        )
                        time.sleep(0.9)
                        if _confirm_left_home_or_method():
                            _after_install_su(f"vm{vmindex}_install_su_xy")
                            return True
                        self._log(
                            log,
                            f"VM={vmindex} 坐标兜底后未进入方法页，继续 attempt={attempt}",
                        )
                    except Exception as exc:
                        self._log(log, f"VM={vmindex} Install坐标兜底异常: {exc}")
                elif attempt >= 2 and not has_install_text:
                    self._log(
                        log,
                        f"VM={vmindex} 跳过坐标盲点 attempt={attempt} "
                        f"has_text={has_install_text} on_magisk_home={on_magisk_home}",
                    )

                self._log(
                    log,
                    f"VM={vmindex} 本轮未点到 Install attempt={attempt} "
                    f"xml_len={len(xml or '')} has_home_btn={'home_magisk_button' in low} "
                    f"ui_snip={(self.adb.ui_full_text() or '')[:80]!r}",
                )
                time.sleep(0.45)
            return False

        def _wait_third_direct(attempts: int = 12):
            """点完 Install 后轮询第3项 Direct Install (modify /system directly)。

            direct-install-wait-v2（修 only-patch-instant-reopen 秒放弃）：
            - 有 method_direct_system / 第3项文案 → 立刻点
            - 仅见 Patch：先 Forever+Allow，必要时 BACK 再点 Install 刷新方法页，多轮等待
            - dump 为空或方法页未出：继续轮询，不要秒返回
            - 持续多轮仍无第3项才返回 ONLY_PATCH，由外层最多杀进程重开 1 次

            desktop-empty-soft-pull-v1：
            - 掉桌面/空 dump 时不要空等满 attempts（约 40s）
            - 检测桌面特征或 empty_streak>=2 → 软拉回 Kitsune（不 force-stop）并再点首页 Install
            - 不提高外层 max_kill；正常已在方法页时行为不变
            """
            method_label = ""
            last_hint = ""
            saw_only_patch = False
            only_patch_streak = 0
            empty_streak = 0
            desktop_streak = 0
            no_magisk_streak = 0
            soft_pull_count = 0
            saw_desktop = False
            refreshed_after_grant = False
            total = max(8, int(attempts))
            try:
                from paths import LOG_TEST_DIR
                dump_dir = str(LOG_TEST_DIR)
            except Exception:
                dump_dir = None

            def _tap_third(xml_local: str, attempt_i: int, hint: str):
                nonlocal method_label
                b, method_label = self._find_kitsune_third_direct_install(xml_local)
                if not b:
                    try:
                        rid_ok = False
                        if hasattr(self.adb, "tap_resource_id"):
                            rid_ok = bool(
                                self.adb.tap_resource_id("method_direct_system")
                                or self.adb.tap_resource_id(
                                    "io.github.huskydg.magisk:id/method_direct_system"
                                )
                            )
                        if rid_ok:
                            method_label = "Direct Install (modify /system directly)"
                            self._log(
                                log,
                                f"VM={vmindex} 选择第3项 Direct Install (rid method_direct_system) "
                                f"attempt={attempt_i} opts={hint!r}",
                            )
                            time.sleep(1.0)
                            return True
                    except Exception:
                        pass
                    for lab in (
                        "Direct Install (modify /system directly)",
                        "modify /system directly",
                        "modify /systemdirectly",
                    ):
                        try:
                            ok = False
                            if hasattr(self.adb, "tap_exact_text"):
                                ok = bool(self.adb.tap_exact_text(lab))
                            if (not ok) and hasattr(self.adb, "tap_text"):
                                ok = bool(self.adb.tap_text(lab))
                            if ok:
                                method_label = lab
                                self._log(
                                    log,
                                    f"VM={vmindex} 选择第3项 Direct Install (text) "
                                    f"label={lab!r} attempt={attempt_i} opts={hint!r}",
                                )
                                time.sleep(1.0)
                                return True
                        except Exception:
                            continue
                    return False
                x1, y1, x2, y2 = b
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                self.adb.tap(cx, cy)
                self._log(
                    log,
                    f"VM={vmindex} 选择第3项 Direct Install (modify /system directly) "
                    f"label={method_label!r} attempt={attempt_i} center=({cx},{cy}) opts={hint!r}",
                )
                time.sleep(1.0)
                return True

            for attempt in range(total):
                if self._cancelled():
                    break
                try:
                    su_hit = self.adb.dismiss_magisk_su_dialog()
                    if su_hit:
                        self._log(log, f"VM={vmindex} 方法页前 su 授权: {su_hit}")
                        time.sleep(0.45)
                except Exception:
                    pass
                try:
                    xml = self.adb.uiautomator_dump(force=True) or ""
                except Exception:
                    xml = ""
                if len(xml) < 80:
                    empty_streak += 1
                    try:
                        time.sleep(0.35)
                        xml = self.adb.uiautomator_dump(force=True) or xml
                    except Exception:
                        pass
                else:
                    empty_streak = 0

                low_probe = (xml or "").lower()
                has_magisk_markers = (
                    "method_direct" in low_probe
                    or "io.github.huskydg.magisk:id/" in low_probe
                    or "ramdisk" in low_probe
                    or "uninstall magisk" in low_probe
                    or "select and patch" in low_probe
                    or "modify /system" in low_probe
                    or "home_magisk_button" in low_probe
                    or "let's go" in low_probe
                    or "lets go" in low_probe
                )
                on_desktop = (
                    not has_magisk_markers
                    and (
                        "mumu store" in low_probe
                        or "app cloner" in low_probe
                        or "search games" in low_probe
                        or "lawnchair" in low_probe
                        or (
                            "kitsune mask" in low_probe
                            and "ramdisk" not in low_probe
                            and "home_magisk_button" not in low_probe
                        )
                    )
                )
                if on_desktop:
                    saw_desktop = True
                    desktop_streak += 1
                else:
                    desktop_streak = 0

                if has_magisk_markers:
                    no_magisk_streak = 0
                else:
                    no_magisk_streak += 1

                # desktop/empty/no-magisk UI soft pull
                need_soft_pull = (
                    (on_desktop and desktop_streak >= 1)
                    or empty_streak >= 2
                    or no_magisk_streak >= 2
                )
                if need_soft_pull and not self._cancelled():
                    soft_pull_count += 1
                    self._log(
                        log,
                        f"VM={vmindex} 方法页等待掉桌面/空dump → 软拉回Kitsune再点Install "
                        f"attempt={attempt} desktop_streak={desktop_streak} "
                        f"empty_streak={empty_streak} no_magisk_streak={no_magisk_streak} soft_pull={soft_pull_count}",
                    )
                    try:
                        self.open_kitsune(force_relaunch=False)
                    except Exception as exc:
                        self._log(log, f"VM={vmindex} 方法页软拉回Kitsune异常: {exc}")
                    time.sleep(0.45)
                    try:
                        xml_soft = self.adb.uiautomator_dump(force=True) or ""
                    except Exception:
                        xml_soft = ""
                    low_soft = (xml_soft or "").lower()
                    if (
                        "method_direct_system" in low_soft
                        or "modify /system directly" in low_soft
                        or "modify /systemdirectly" in low_soft
                    ):
                        if _tap_third(xml_soft, attempt, last_hint or "soft_pull_third"):
                            return True, method_label, last_hint or "soft_pull_third"
                    b_home_soft = self._find_kitsune_home_install_bounds(xml_soft)
                    if b_home_soft:
                        try:
                            self.adb.tap_bounds(b_home_soft)
                            self._log(
                                log,
                                f"VM={vmindex} 软拉回后点首页 Install attempt={attempt} "
                                f"bounds={b_home_soft}",
                            )
                            time.sleep(0.9)
                        except Exception as exc:
                            self._log(log, f"VM={vmindex} 软拉回后点Install异常: {exc}")
                    else:
                        time.sleep(0.35)
                    # 软拉回后进入下一轮重新 dump，不拉长 only_patch / max_kill
                    continue

                opts = []
                for node in self._iter_ui_nodes(xml) or []:
                    t = (node.attrib.get("text") or "").strip()
                    rid = (node.attrib.get("resource-id") or "")
                    rid_l = rid.lower()
                    if t and (
                        "install" in t.lower()
                        or "patch" in t.lower()
                        or "method" in rid_l
                        or "direct" in t.lower()
                        or "let" in t.lower()
                    ):
                        opts.append(t[:80])
                    if rid_l.endswith("method_direct_system"):
                        opts.append("RID:method_direct_system")
                    if rid_l.endswith("method_direct") and not rid_l.endswith(
                        "method_direct_system"
                    ):
                        opts.append("RID:method_direct(recommended)")
                    if rid_l.endswith("method_patch"):
                        opts.append("RID:method_patch")
                if opts:
                    last_hint = " | ".join(opts[:12])
                low_all = (xml or "").lower()
                has_third = (
                    "method_direct_system" in low_all
                    or "modify /system directly" in low_all
                    or "modify /systemdirectly" in low_all
                )
                only_patch = ("select and patch" in low_all and not has_third)

                if has_third or "RID:method_direct_system" in last_hint:
                    if _tap_third(xml, attempt, last_hint):
                        return True, method_label, last_hint
                    self._log(
                        log,
                        f"VM={vmindex} 已见第3项文案/RID 但点击失败，重试 "
                        f"attempt={attempt} visible={last_hint!r}",
                    )
                    time.sleep(0.5)
                    continue

                b, method_label = self._find_kitsune_third_direct_install(xml)
                if b and _tap_third(xml, attempt, last_hint):
                    return True, method_label, last_hint

                if only_patch:
                    saw_only_patch = True
                    only_patch_streak += 1
                    try:
                        su_hit2 = self.adb.wait_and_forever_allow_su(
                            timeout=2.0 if only_patch_streak <= 2 else 1.2,
                            poll=0.2,
                            dump_dir=dump_dir,
                            tag=f"vm{vmindex}_onlypatch_su{attempt}",
                        )
                        if su_hit2:
                            self._log(
                                log,
                                f"VM={vmindex} 仅见Patch→永久授权: {su_hit2} streak={only_patch_streak}",
                            )
                            time.sleep(0.6)
                    except Exception as exc:
                        self._log(log, f"VM={vmindex} 仅见Patch补授权异常: {exc}")

                    if only_patch_streak in (2, 5, 8) and not self._cancelled():
                        try:
                            self.adb.shell("input", "keyevent", "4", timeout=3)
                            time.sleep(0.55)
                            xml_home = self.adb.uiautomator_dump(force=True) or ""
                            b_home = self._find_kitsune_home_install_bounds(xml_home)
                            if b_home:
                                self.adb.tap_bounds(b_home)
                                refreshed_after_grant = True
                                self._log(
                                    log,
                                    f"VM={vmindex} 仅见Patch→BACK后重进Install刷新方法页 "
                                    f"streak={only_patch_streak}",
                                )
                                time.sleep(1.0)
                                continue
                        except Exception as exc:
                            self._log(log, f"VM={vmindex} 刷新方法页异常: {exc}")

                    if only_patch_streak < 8:
                        self._log(
                            log,
                            f"VM={vmindex} 仅见Patch，继续等第3项 "
                            f"attempt={attempt} streak={only_patch_streak} visible={last_hint!r}",
                        )
                        time.sleep(0.75)
                        continue

                    self._log(
                        log,
                        f"VM={vmindex} 持续仅见Patch无第3项 Direct Install "
                        f"attempt={attempt} streak={only_patch_streak} "
                        f"refreshed={refreshed_after_grant} visible={last_hint!r}",
                    )
                    return False, method_label, f"ONLY_PATCH|{last_hint}"

                only_patch_streak = 0

                b2 = self._find_kitsune_home_install_bounds(xml)
                if b2 and attempt < total - 1:
                    self.adb.tap_bounds(b2)
                    self._log(log, f"VM={vmindex} 方法页未出现，再点 Install attempt={attempt}")
                    time.sleep(0.9)
                    continue

                self._log(
                    log,
                    f"VM={vmindex} 等待方法页第3项 attempt={attempt} "
                    f"empty_streak={empty_streak} visible={last_hint!r}",
                )
                time.sleep(0.7 if empty_streak else 0.55)

            if saw_only_patch:
                return False, method_label, f"ONLY_PATCH|{last_hint}"
            if saw_desktop and not (last_hint or "").strip():
                return False, method_label, f"DESKTOP_EMPTY|soft_pull={soft_pull_count}|{last_hint}"
            if saw_desktop:
                return False, method_label, f"DESKTOP|{last_hint}"
            return False, method_label, last_hint

        def _finish_already_installed(round_i: int) -> dict:
            result["installed"] = True
            result["detail"] = f"already_uninstall_magisk round={round_i}"
            self._log(log, f"VM={vmindex} 已见 Uninstall Magisk → 无需 Install，跳过 Direct Install")
            # 一次会话：Shell授权 + Settings + 可选ih8，中途不反复 force-stop
            try:
                sess = self.complete_kitsune_post_install_session(
                    vmindex,
                    log=log,
                    configure_settings=bool(configure_settings),
                    install_ih8=bool(install_ih8) if configure_settings else False,
                    restart_after_ih8=True,
                    boot_timeout=boot_timeout,
                    force_relaunch_once=False,  # 当前已打开
                )
                detail_s = str(sess.get("detail") or "")
                result["detail"] += f" one_session={detail_s[:160]}"
                result["grant"] = sess.get("grant", "")
                if sess.get("settings_done"):
                    result["settings_done"] = True
                if sess.get("ih8_done") or sess.get("ih8"):
                    result["ih8_done"] = True
                    result["ih8"] = str(sess.get("ih8") or "")
                if sess.get("rebooted"):
                    result["rebooted"] = True
                self._log(log, f"VM={vmindex} 已装路径一次会话: {detail_s[:200]}")
            except Exception as exc:
                result["detail"] += f" one_session_err={exc}"
                self._log(log, f"VM={vmindex} 已装路径一次会话失败: {exc}")
                if configure_settings:
                    try:
                        # GRANT popup first even on fallback path
                        popup = self.grant_shell_prefer_popup(log=log)
                        if str(popup).startswith("popup_grant_ok") or "uid=0" in str(popup):
                            g = popup
                            self._log(log, f"VM={vmindex} 已装路径兜底 GRANT弹窗成功")
                        else:
                            g = self.grant_shell_via_kitsune_superuser(log=log, reuse_session=True)
                            self._log(log, f"VM={vmindex} 已装路径兜底 Superuser: {str(g)[:120]}")
                        result["detail"] += f" grant_fallback={str(g)[:80]}"
                    except Exception as exc2:
                        result["detail"] += f" grant_err={exc2}"
                    try:
                        flags = self.configure_kitsune_flags(log=log, reuse_session=True)
                        result["detail"] += f" flags={str(flags)[:80]}"
                        result["settings_done"] = True
                    except Exception as exc3:
                        result["detail"] += f" flags_err={exc3}"
                    try:
                        if install_ih8:
                            ih = self.install_ih8_module(
                                log=log,
                                vmindex=vmindex,
                                restart=True,
                                boot_timeout=boot_timeout,
                                reuse_session=True,
                            )
                            result["ih8"] = str(ih)
                            result["ih8_done"] = True
                            result["detail"] += f" ih8_fallback={str(ih)[:80]}"
                    except Exception as exc4:
                        result["detail"] += f" ih8_fallback_err={exc4}"
                # 仅在会话完全结束后回桌面；中途不杀
                try:
                    self._force_stop_kitsune_home()
                except Exception:
                    pass
            self.mark_kitsune_done(
                vmindex,
                result["detail"],
                settings_ok=bool(result.get("settings_done")),
            )
            return result

        tapped = False
        method_ok = False
        method_label = ""
        reopen_used = 0
        last_opts = ""
        need_kill_reopen = False
        opened_once = False
        # 用户硬规则 create-direct-kill-reopen-v1：
        # Forever->Allow；Hide->Install；
        # 点完 Install 仍无第3项 Direct Install → 直接结束 Kitsune 进程再开再点 Install
        # 最多杀进程 1 次，禁止反复重启抽风
        max_kill = 1
        total_rounds = max(2, int(max_kill) + 1)

        for round_i in range(total_rounds):
            if self._cancelled():
                result["detail"] = "cancelled"
                return result

            if round_i == 0:
                _open_once("first", force_relaunch=False)
                opened_once = True
            elif need_kill_reopen and reopen_used < max_kill:
                reopen_used += 1
                need_kill_reopen = False
                _kill_reopen(
                    f"第{reopen_used}/{max_kill}次杀进程重开"
                    f"(已点Install后仍未找到 Direct Install；直接结束进程再开再点Install)"
                )
                opened_once = True
            else:
                self._log(
                    log,
                    f"VM={vmindex} round={round_i} 无可用杀进程重开配额，结束 Direct Install 尝试 "
                    f"(reopen_used={reopen_used}/{max_kill} need_kill={need_kill_reopen})",
                )
                break

            st = _wait_home_ready(timeout=8.0)
            # check_binary=False 时 binary_ok 默认 False，不能再据此白等；
            # 只要 UI 已见 Install / Uninstall 就立刻点，无需等 binary。
            if (
                round_i == 0
                and not st.get("has_uninstall_magisk")
                and not st.get("has_install_button")
            ):
                ui0 = (st.get("ui") or "").lower()
                desktop0 = any(
                    k in ui0
                    for k in ("mumu store", "app cloner", "search games", "lawnchair")
                ) and "ramdisk" not in ui0
                if desktop0:
                    self._log(log, f"VM={vmindex} 首页未就绪且在桌面 → 软拉回 Kitsune 再识别 Install")
                    try:
                        self.open_kitsune(force_relaunch=False)
                    except Exception as exc:
                        self._log(log, f"VM={vmindex} 桌面软拉回异常: {exc}")
                    time.sleep(0.8)
                else:
                    self._log(log, f"VM={vmindex} 首页未就绪，短等 2s 再识别 Install")
                    time.sleep(2.0)
                st = _wait_home_ready(timeout=4.0)
            self._log(
                log,
                f"VM={vmindex} Kitsune UI round={round_i} uninstall={st.get('has_uninstall_magisk')} "
                f"install_btn={st.get('has_install_button')} binary={st.get('binary_ok')} "
                f"ui={(st.get('ui') or '')[:100]!r}",
            )

            if st.get("has_uninstall_magisk"):
                return _finish_already_installed(round_i)

            result["needed"] = True
            # 二次打开后必须点到 Install；多轮+坐标兜底，禁止空转直接杀进程
            tapped = _tap_home_install(retries=8 if round_i > 0 else 6)
            if not tapped:
                try:
                    ui_now = (self.adb.ui_full_text() or "").lower()
                except Exception:
                    ui_now = ""
                if any(
                    k in ui_now
                    for k in (
                        "direct install",
                        "method",
                        "select and patch",
                        "let's go",
                        "lets go",
                    )
                ):
                    self._log(log, f"VM={vmindex} 虽未点到Install但已在方法页，继续选第3项")
                    tapped = True
                else:
                    try:
                        st2 = self.kitsune_ui_status() or {}
                        if st2.get("has_uninstall_magisk"):
                            return _finish_already_installed(round_i)
                    except Exception:
                        pass
                    # 同会话再硬点一次（含坐标兜底），避免二次打开空过
                    self._log(
                        log,
                        f"VM={vmindex} round={round_i} 首次未点到 Install，同会话再强制点一次",
                    )
                    tapped = _tap_home_install(retries=6)
                    if not tapped:
                        try:
                            ui_chk = (self.adb.ui_full_text() or "").lower()
                        except Exception:
                            ui_chk = ""
                        can_hard = (
                            "install" in ui_chk
                            and "magisk" in ui_chk
                            and "mumu store" not in ui_chk
                            and "search games" not in ui_chk
                        )
                        if can_hard:
                            try:
                                self.adb.tap(1120, 512)
                                self._log(
                                    log,
                                    f"VM={vmindex} round={round_i} 最终坐标硬点 Install (1120,512) only_on_magisk_home",
                                )
                                time.sleep(1.0)
                                try:
                                    ui_after = (self.adb.ui_full_text() or "").lower()
                                except Exception:
                                    ui_after = ""
                                tapped = any(
                                    k in ui_after
                                    for k in (
                                        "direct install",
                                        "select and patch",
                                        "method",
                                        "let's go",
                                        "lets go",
                                    )
                                )
                                if not tapped:
                                    self._log(
                                        log,
                                        f"VM={vmindex} round={round_i} 最终硬点后仍未进方法页",
                                    )
                            except Exception:
                                tapped = False
                        else:
                            self._log(
                                log,
                                f"VM={vmindex} round={round_i} 非Magisk首页，跳过最终坐标硬点 ui={(ui_chk or '')[:80]!r}",
                            )
                            try:
                                self.open_kitsune(force_relaunch=False)
                            except Exception:
                                pass
                    if not tapped:
                        self._log(
                            log,
                            f"VM={vmindex} round={round_i} 仍未点到首页 Install，"
                            f"按配额结束进程再开再点Install (reopen_used={reopen_used}/{max_kill})",
                        )
                        if reopen_used < max_kill:
                            need_kill_reopen = True
                        else:
                            need_kill_reopen = False
                            break
                        continue

            self._log(log, f"VM={vmindex} [STEP5-6] 已点完 Install，开始检查 Direct Install (modify /system directly)")
            time.sleep(0.45)
            method_ok, method_label, last_opts = _wait_third_direct(attempts=14)
            if method_ok:
                break

            only_patch = str(last_opts or "").startswith("ONLY_PATCH") or (
                "select and patch" in str(last_opts or "").lower()
                and "modify /system" not in str(last_opts or "").lower()
            )
            # 无第3项：直接结束 Kitsune 进程再开再点 Install（不再 soft-first）
            if reopen_used < max_kill:
                need_kill_reopen = True
                why = "仅见Patch/临时授权" if only_patch else "未出现第3项"
                self._log(
                    log,
                    f"VM={vmindex} [STEP7-9] round={round_i} 无第3项 Direct Install "
                    f"({why}) visible={last_opts!r} → 结束Kitsune进程再开再点Install "
                    f"({reopen_used+1}/{max_kill})",
                )
            else:
                need_kill_reopen = False
                self._log(
                    log,
                    f"VM={vmindex} round={round_i} 已用尽重启Magisk配额({max_kill})，"
                    f"visible={last_opts!r} → 结束 Direct Install 尝试",
                )
                break

        if not method_ok:
            result["detail"] = (
                f"direct_install_missing after_reopen={reopen_used} "
                f"tapped_install={tapped} visible={last_opts!r}"
            )
            self._log(
                log,
                f"VM={vmindex} 多次后仍无 Direct Install (modify /system directly)，放弃本次安装",
            )
            try:
                self._force_stop_kitsune_home()
            except Exception:
                pass
            return result

        for label in ("LET'S GO", "Let's go", "LETS GO", "Next", "NEXT", "开始", "确定", "OK"):
            try:
                xml = self.adb.uiautomator_dump(force=True) or ""
                b = self._find_text_bounds_exclude(
                    xml,
                    must_contain=label,
                    exclude_any=("direct install", "recommended", "modify /system", "uninstall"),
                    exact_text=False,
                )
                if b:
                    self.adb.tap_bounds(b)
                    self._log(log, f"VM={vmindex} 点击 {label}")
                    time.sleep(1.5)
                    break
                if self.adb.tap_text(label):
                    self._log(log, f"VM={vmindex} tap_text {label}")
                    time.sleep(1.5)
                    break
            except Exception:
                continue

        time.sleep(2.0)
        for _ in range(8):
            try:
                ui = (self.adb.ui_full_text() or "").lower()
            except Exception:
                ui = ""
            if any(k in ui for k in ("done", "reboot", "complete", "完成", "all done", "installed")):
                self._log(log, f"VM={vmindex} Magisk install progress ui={ui[:140]!r}")
                for lab in ("DONE", "Done", "OK", "CLOSE", "Close", "REBOOT", "Reboot"):
                    try:
                        if self.adb.tap_text(lab):
                            time.sleep(1.0)
                            break
                    except Exception:
                        pass
                break
            time.sleep(1.5)

        result["detail"] = (
            f"tapped_install={tapped} method={method_ok} label={method_label!r} "
            f"reopen={reopen_used} opts={last_opts!r}"
        )
        self._log(log, f"VM={vmindex} [STEP11-12] LETS GO 后 MuMu restart device")
        try:
            if hasattr(self.mumu, "restart"):
                self.mumu.restart(vmindex)
                result["rebooted"] = True
            elif hasattr(self.mumu, "restart_device"):
                self.mumu.restart_device(vmindex)
                result["rebooted"] = True
            else:
                raise RuntimeError("mumu has no restart/restart_device")
        except Exception as exc2:
            result["detail"] += f" restart_err={exc2}"
            self._log(log, f"VM={vmindex} restart 失败: {exc2}")

        try:
            time.sleep(8.0)
            self.mumu.adb_connect(vmindex)
            self.adb.connect()
            self.adb.wait_device(timeout=min(120, int(boot_timeout)))
        except Exception as exc:
            self._log(log, f"VM={vmindex} 重启后 wait 警告: {exc}")

        post_uninstall = False
        binary = False
        try:
            # 重启后只看 UI。禁止这里 su/shell。
            # 规则: 点 LET'S GO 并第一次 restart 完成后，才发起 shell 弹 GRANT。
            _open_once("post_reboot_verify", force_relaunch=False)
            st2 = self.kitsune_ui_status(check_binary=False, force_dump=True)
            post_uninstall = bool(st2.get("has_uninstall_magisk"))
            binary = False
            result["detail"] += (
                f" post_ui uninstall={post_uninstall} install_btn={st2.get('has_install_button')} "
                f"binary=deferred"
            )
            self._log(
                log,
                f"VM={vmindex} 重启后 Kitsune uninstall={post_uninstall} (shell/GRANT later)",
            )
        except Exception as exc:
            result["detail"] += f" post_check_err={exc}"
        # 验证后不 force-stop：一次会话连续 Shell/Settings/ih8

        # Direct Install 重启后: UI 见 Uninstall，或本轮已 method_ok，进入授权会话
        result["installed"] = bool(post_uninstall or method_ok or tapped)
        result["detail"] += f" after_boot uninstall={post_uninstall} method_ok={method_ok}"
        if result["installed"]:
            try:
                self._log(log, f"VM={vmindex} [STEP13-14] first restart done, open Kitsune + shell for GRANT")
                sess = self.complete_kitsune_post_install_session(
                    vmindex,
                    log=log,
                    configure_settings=bool(configure_settings),
                    install_ih8=bool(install_ih8),
                    restart_after_ih8=True,
                    boot_timeout=boot_timeout,
                    force_relaunch_once=False,
                )
                result["detail"] += f" one_session={sess.get('detail','')[:160]}"
                result["grant"] = sess.get("grant", "")
                if sess.get("settings_done"):
                    result["settings_done"] = True
                    result["detail"] += f" flags={str(sess.get('settings',''))[:80]}"
                elif not configure_settings:
                    result["detail"] += " flags=skipped_login_only"
                    self._log(log, f"VM={vmindex} 登录路径跳过 Kitsune Settings")
                if sess.get("ih8_done") or sess.get("ih8"):
                    result["ih8_done"] = True
                    result["ih8"] = str(sess.get("ih8") or "")
                if sess.get("rebooted"):
                    result["rebooted"] = True
                self._log(log, f"VM={vmindex} Direct Install 后一次会话: {sess.get('detail','')[:200]}")
            except Exception as exc:
                result["detail"] += f" one_session_err={exc}"
                self._log(log, f"VM={vmindex} Kitsune 一次会话失败: {exc}")
                try:
                    g = self.grant_shell_superuser(log=log)
                    result["detail"] += f" grant_fallback={g[:80]}"
                except Exception as exc2:
                    result["detail"] += f" grant_err={exc2}"
                if configure_settings:
                    try:
                        flags = self.configure_kitsune_flags(log=log)
                        result["detail"] += f" flags={flags[:80]}"
                        result["settings_done"] = True
                    except Exception as exc3:
                        result["detail"] += f" flags_err={exc3}"
            self.mark_kitsune_done(
                vmindex,
                result["detail"],
                settings_ok=bool(result.get("settings_done")),
            )
            self._log(log, f"VM={vmindex} Kitsune Direct Install 成功并缓存")
        else:
            try:
                self._force_stop_kitsune_home()
            except Exception:
                pass
            self._log(
                log,
                f"VM={vmindex} Kitsune Direct Install 未确认(无 Uninstall Magisk)，不写缓存",
            )
        return result


    def is_vpn_active(self, skip_ui: bool = False) -> bool:
        """检测模拟器内 VPN/tun 是否真实开启。

        严格只认 tun 网卡存在；UI Connected 仅作辅助（skip_ui=True 时不用 UI）。
        不再用宽松 dumpsys connectivity（易假阳性导致跳过 Connect）。
        """
        # 1) /proc/net/dev 必须有 tunN:
        try:
            dev = self.adb.shell("cat", "/proc/net/dev", timeout=8) or ""
            if re.search(r"(?m)^\s*tun\d+:", dev):
                return True
            # 有些输出无前导空白
            if re.search(r"(?m)^tun\d+:", dev):
                return True
        except Exception:
            pass
        # 2) ip link
        try:
            ipa = self.adb.shell("ip", "link", "show", timeout=8) or ""
            if re.search(r"(?m)^\d+:\s*tun\d+:", ipa) or re.search(r"\btun\d+:", ipa):
                return True
        except Exception:
            pass
        # 3) ifconfig (部分镜像)
        try:
            ifc = self.adb.shell("ifconfig", timeout=8) or ""
            if re.search(r"(?m)^tun\d+\b", ifc):
                return True
        except Exception:
            pass
        # 4) UI 辅助：仅当 NekoBox 前台明确 Stop/Connected
        if not skip_ui:
            try:
                xml = self.adb.uiautomator_dump() or ""
                low = xml.lower()
                if "moe.nb4a" in low or "nekobox" in low or "sager_net" in low:
                    if 'content-desc="stop"' in low or "connected, tap" in low:
                        return True
            except Exception:
                pass
        return False

    def _build_socks_uri(
        self, profile_name: str, host: str, port: int, username: str, password: str
    ) -> str:
        """构造 NekoBox 可导入的 SOCKS URI（用户名密码直接编码进 URI）。

        实测（2026-07-24）：
        - NekoBox 只注册 socks:// / ss:// / sn://，**不支持 socks5://**（resolve 无 Activity）
        - 正确格式: socks://user:pass@host:port#profile_name
        - Username=完整代理用户名（如 qq1254870524.qiang15_pp），导入后直接写入，无需 UI 手填
        - Profile Name 用 fragment #qiang15
        - 密码中的 # 等特殊字符必须 percent-encoding（Aa112211### -> %23%23%23）
        """
        user = urllib.parse.quote(username or "", safe="")
        pwd = urllib.parse.quote(password or "", safe="")
        name = urllib.parse.quote(profile_name or "proxy", safe="")
        # 必须用 socks://，不要用 socks5://
        if user or pwd:
            return f"socks://{user}:{pwd}@{host}:{int(port)}#{name}"
        return f"socks://{host}:{int(port)}#{name}"

    def _socks_uri_log_safe(
        self, profile_name: str, host: str, port: int, username: str, password: str
    ) -> str:
        """日志用：显示用户名，隐藏密码。"""
        u = username or ""
        return f"socks://{u}:***@{host}:{int(port)}#{profile_name or 'proxy'}"


    def stop_nekobox_vpn_ui(self, *, log: LogFn = None) -> str:
        """关闭 VPN（点 Stop/FAB），改配置前必须先停再开才会生效。

        绝不 force-stop NekoBox 进程，只点 UI Stop。
        """
        outs: list[str] = []
        try:
            if not self.is_vpn_active(skip_ui=True):
                # 再看 UI 是否显示 Stop
                try:
                    self._open_nekobox_main()
                    xml = self.adb.uiautomator_dump(force=True) or ""
                    low = xml.lower()
                    if 'content-desc="stop"' not in low and "connected, tap" not in low:
                        outs.append("already_stopped")
                        return " | ".join(outs)[:300]
                except Exception:
                    outs.append("already_stopped")
                    return " | ".join(outs)[:300]
        except Exception:
            pass

        self._log(log, "NekoBox 改配置前先 Stop VPN（改后需重开才生效）")
        try:
            self._open_nekobox_main()
            time.sleep(0.8)
        except Exception as exc:
            outs.append(f"open_err={exc}")

        for i in range(6):
            try:
                xml = self.adb.uiautomator_dump(force=True) or ""
            except Exception as exc:
                outs.append(f"dump_err={exc}")
                time.sleep(0.5)
                continue
            low = (xml or "").lower()
            # 已断开
            if 'content-desc="connect"' in low or re.search(r'content-desc="Connect"', xml or ""):
                if not self.is_vpn_active(skip_ui=True):
                    outs.append("stopped_ui_connect")
                    break
            # 点 Stop / FAB
            b = self.adb.find_node_bounds(resource_id="moe.nb4a:id/fab", xml=xml)
            if not b:
                b = self.adb.find_node_bounds(content_desc="Stop", xml=xml)
            if b and (
                'content-desc="stop"' in low
                or "connected, tap" in low
                or self.is_vpn_active(skip_ui=True)
            ):
                self.adb.tap_bounds(b)
                outs.append(f"tap_stop#{i}")
                time.sleep(1.2)
            else:
                # 保险再点一次 FAB（若仍有 tun）
                if self.is_vpn_active(skip_ui=True) and b:
                    self.adb.tap_bounds(b)
                    outs.append(f"tap_fab_force#{i}")
                    time.sleep(1.2)
                else:
                    break
            if not self.is_vpn_active(skip_ui=True):
                outs.append("tun_down")
                break
        still = False
        try:
            still = self.is_vpn_active(skip_ui=True)
        except Exception:
            pass
        outs.append(f"vpn_still={still}")
        self._log(log, f"NekoBox Stop 结果: {'仍开' if still else '已关'} | {outs[-3:]}")
        return " | ".join(outs)[:400]

    def ensure_auth_then_connect(
        self,
        profile_name: str,
        host: str,
        port: int,
        username: str,
        password: str,
        *,
        log: LogFn = None,
        verify_vpn: bool = True,
        vpn_wait_seconds: float = 20.0,
        force_reimport: bool = False,
    ) -> str:
        """开启前校验 auth；不对则先 Stop，再 URI 导入(带用户名)/UI 修复，再 Connect。

        规则:
        1) 导入配置本身带 Username（socks://user:pass@host:port#name），不优先手填
        2) 开启前 auth 不通过则拒绝 Connect
        3) 改配置：必须先 Stop，改完再 Connect 才生效
        4) UI 填 Username 仅在导入失败时兜底
        5) 绝不 force-stop NekoBox
        """
        outs: list[str] = []
        name = (profile_name or "").strip()
        user = (username or "").strip()
        auth_ok = False
        ui_visible = False
        try:
            # 必须以 UI 列表可见 profile 名为准；DB/strings 子串命中不算已导入
            ui_visible = self.nekobox_profile_visible_in_ui(name)
        except Exception as exc:
            outs.append(f"ui_vis_err={exc}")
            ui_visible = False
        outs.append(f"ui_visible={ui_visible}")
        try:
            auth_ok = (
                (not force_reimport)
                and ui_visible
                and self.nekobox_profile_auth_ok(
                    name, user, host=host, password=password
                )
            )
        except Exception as exc:
            outs.append(f"auth_err={exc}")
            auth_ok = False
        # UI 没有列表项时强制重导，禁止误报 auth 后狂点 Connect
        if not ui_visible:
            auth_ok = False
            force_reimport = True
            outs.append("force_reimport=ui_missing")
        outs.append(f"auth_ok_before={auth_ok}")
        outs.append(
            f"uri_preview={self._socks_uri_log_safe(name, host, port, user, password)}"
        )

        if not auth_ok:
            # 改配置前先关 VPN（开启后改配置必须关再开才生效）
            try:
                outs.append("stop=" + self.stop_nekobox_vpn_ui(log=log))
            except Exception as exc:
                outs.append(f"stop_err={exc}")

            exists = False
            try:
                exists = self.nekobox_profile_exists(name)
            except Exception:
                exists = False
            outs.append(f"exists_before={exists}")

            # auth 不对/强制重导：Stop 后先清空全部旧 profile，再只导入当前分配代理
            # 避免 NekoBox 内多条 SOCKS 历史叠加
            if not auth_ok:
                try:
                    wipe = self.delete_all_nekobox_profiles_ui(log=log)
                    outs.append("wipe_all=" + wipe)
                    self._log(log, f"NekoBox 重导前已清空全部旧代理: {wipe[:180]}")
                except Exception as exc:
                    outs.append(f"wipe_all_err={exc}")
                    self._log(log, f"NekoBox 清空全部代理失败(继续单删): {exc}")
                    try:
                        if self.nekobox_profile_exists(name):
                            outs.append(
                                "delete=" + self.delete_nekobox_profile_ui(name)
                            )
                    except Exception as exc2:
                        outs.append(f"delete_err={exc2}")

                self._log(
                    log,
                    "NekoBox socks:// URI 导入(带用户名) "
                    + self._socks_uri_log_safe(name, host, port, user, password),
                )
                try:
                    add_uri = self._import_socks_uri(name, host, port, user, password)
                    outs.append("add_uri=" + add_uri)
                except Exception as exc:
                    outs.append(f"add_uri_err={exc}")

                try:
                    # 导入后先看 UI 列表；刚 URI 导入成功即可视为 auth 可用，避免 DB 延迟误杀
                    vis = self.nekobox_profile_visible_in_ui(name)
                    if vis:
                        auth_ok = True
                        outs.append("auth_ok_after_import=ui_visible")
                    else:
                        auth_ok = self.nekobox_profile_auth_ok(
                            name, user, host=host, password=password
                        )
                        outs.append(f"auth_ok_after_import={auth_ok}")
                except Exception:
                    auth_ok = False
                    outs.append("auth_ok_after_import=False")

            # 仅兜底：导入后仍无用户名才 UI 修
            if not auth_ok and user:
                self._log(log, "NekoBox 导入后 Username 仍不对，UI 兜底写入")
                try:
                    try:
                        outs.append("stop2=" + self.stop_nekobox_vpn_ui(log=log))
                    except Exception:
                        pass
                    # 若 profile 仍不存在，无法 edit；先再试一次导入
                    if not self.nekobox_profile_exists(name):
                        try:
                            outs.append(
                                "add_uri_retry="
                                + self._import_socks_uri(name, host, port, user, password)
                            )
                        except Exception as exc:
                            outs.append(f"add_uri_retry_err={exc}")
                    if self.nekobox_profile_exists(name):
                        fix = self.fix_nekobox_profile_auth_ui(
                            name, host, int(port), user, password
                        )
                        outs.append("fix_ui_fallback=" + fix)
                        try:
                            outs.append("stop_after_ui=" + self.stop_nekobox_vpn_ui(log=log))
                        except Exception as exc:
                            outs.append(f"stop_after_ui_err={exc}")
                        auth_ok = self.nekobox_profile_auth_ok(
                            name, user, host=host, password=password
                        )
                        outs.append(f"auth_ok_after_ui={auth_ok}")
                    else:
                        outs.append("fix_ui_fallback=profile_missing")
                except Exception as exc:
                    outs.append(f"fix_ui_err={exc}")

        if not auth_ok:
            self._log(log, f"NekoBox 开启前 auth 失败，拒绝 Connect profile={name}")
            outs.append("connect_skipped=auth_fail")
            return " | ".join(outs)[:900]

        self._log(
            log,
            f"NekoBox 开启前 auth 通过 profile={name} user={(user or '')[:40]}",
        )
        outs.append("auth_ok_pre_connect=True")

        # 连接（若已连接且配置未改，ensure 会直接复用 tun）
        try:
            vpn_only = self.ensure_nekobox_vpn_only(
                name,
                log=log,
                verify_vpn=verify_vpn,
                vpn_wait_seconds=vpn_wait_seconds,
            )
            outs.append("vpn=" + vpn_only)
            # select_miss / Please select a profile：立即强制 URI 导入后再 Connect 一次
            if ("select_miss=" in (vpn_only or "") or "need_import" in (vpn_only or "")) and not self._cancelled():
                self._log(log, f"NekoBox select_miss，强制 socks:// 导入后重连 profile={name}")
                try:
                    outs.append("stop_for_reimport=" + self.stop_nekobox_vpn_ui(log=log))
                except Exception as exc:
                    outs.append(f"stop_for_reimport_err={exc}")
                try:
                    outs.append(
                        "reimport_uri="
                        + self._import_socks_uri(name, host, port, user, password)
                    )
                except Exception as exc:
                    outs.append(f"reimport_uri_err={exc}")
                try:
                    ui2 = self.nekobox_profile_visible_in_ui(name)
                    outs.append(f"ui_visible_after_reimport={ui2}")
                except Exception:
                    ui2 = False
                if ui2 and not self._cancelled():
                    try:
                        vpn_only2 = self.ensure_nekobox_vpn_only(
                            name,
                            log=log,
                            verify_vpn=verify_vpn,
                            vpn_wait_seconds=vpn_wait_seconds,
                        )
                        outs.append("vpn_after_reimport=" + vpn_only2)
                    except Exception as exc:
                        outs.append(f"vpn_after_reimport_err={exc}")
        except Exception as exc:
            outs.append(f"vpn_err={exc}")
            self._log(log, f"NekoBox Connect 失败: {exc}")
        return " | ".join(outs)[:900]

    def _import_socks_uri(
        self, profile_name: str, host: str, port: int, username: str, password: str
    ) -> str:
        """通过 VIEW socks:// URI 导入 SOCKS（用户名密码直接在 URI 内）。

        实测要点:
        - 必须 socks://（socks5:// 无 Activity）
        - 密码 # 必须 URL 编码
        - 先打开 MainActivity，再投递 VIEW，才能弹出 Import profile 对话框
        - 确认框点 YES
        """
        uri = self._build_socks_uri(profile_name, host, port, username, password)
        outs: list[str] = [f"scheme=socks"]
        # 1) 先打开主界面，保证 intent 投递到前台
        try:
            self._open_nekobox_main()
            time.sleep(0.8)
            outs.append("main_open")
        except Exception as exc:
            outs.append(f"main_err={exc}")

        uri_sh = uri.replace("'", "'\''")
        # 同时带 -n MainActivity，提高投递成功率
        script = (
            f"am start -a android.intent.action.VIEW -d '{uri_sh}' "
            f"-n {self.nekobox_pkg}/io.nekohasekai.sagernet.ui.MainActivity"
        )
        try:
            o = self.adb.shell_script(script, timeout=20)
            outs.append((o or "started").strip().replace("\n", " ")[:140] or "started")
        except Exception as exc:
            outs.append(f"start_err={exc}")
            return " | ".join(outs)[:300]

        time.sleep(1.2)
        confirmed = ""
        for i in range(12):
            try:
                xml = self.adb.uiautomator_dump(force=True) or ""
            except Exception as exc:
                outs.append(f"dump_err={exc}")
                time.sleep(0.5)
                continue
            low = (xml or "").lower()
            if (
                "import profile" in low
                or "confirm you want" in low
                or "confirm you want to import" in low
            ):
                hit = self.adb.tap_any(
                    ["YES", "Yes", "OK", "确定", "Import", "导入"],
                    xml=xml,
                    match_desc=True,
                    match_text=True,
                )
                if hit:
                    confirmed = hit
                    time.sleep(1.0)
                    continue
                b = self.adb.find_node_bounds(text_substr="YES", xml=xml)
                if not b:
                    b = self.adb.find_node_bounds(resource_id="android:id/button1", xml=xml)
                if b:
                    self.adb.tap_bounds(b)
                    confirmed = "YES_bounds"
                    time.sleep(1.0)
                    continue
            else:
                if confirmed:
                    break
                if i < 4:
                    time.sleep(0.6)
                    continue
                confirmed = confirmed or "no_dialog"
                break
            time.sleep(0.4)
        outs.append(f"confirm={confirmed or 'none'}")
        # 对话框仍在则强点 button1
        try:
            xml = self.adb.uiautomator_dump(force=True) or ""
            if "import profile" in (xml or "").lower():
                b = self.adb.find_node_bounds(resource_id="android:id/button1", xml=xml)
                if b:
                    self.adb.tap_bounds(b)
                    outs.append("force_yes")
                    time.sleep(0.8)
        except Exception:
            pass
        # 回到主列表稳定一下，并确认 profile 是否真的出现在列表
        try:
            self._open_nekobox_main()
            time.sleep(0.6)
        except Exception:
            pass
        try:
            vis = self.nekobox_profile_visible_in_ui(profile_name)
            outs.append(f"ui_visible={vis}")
        except Exception as exc:
            outs.append(f"ui_visible_err={exc}")
        return " | ".join(outs)[:360]

    def _write_nekobox_config_files(

        self,
        profile_name: str,
        host: str,
        port: int,
        username: str,
        password: str,
    ) -> str:
        """备用：推送 sing-box JSON（主路径是 socks URI 导入）。"""
        cfg = {
            "dns": {
                "servers": [
                    {"tag": "dns-remote", "address": "8.8.8.8", "detour": "proxy"},
                    {"tag": "dns-direct", "address": "local", "detour": "direct"},
                ]
            },
            "inbounds": [
                {
                    "type": "tun",
                    "tag": "tun-in",
                    "inet4_address": "172.19.0.1/30",
                    "auto_route": True,
                    "strict_route": True,
                    "stack": "system",
                }
            ],
            "outbounds": [
                {
                    "type": "socks",
                    "tag": "proxy",
                    "server": host,
                    "server_port": int(port),
                    "username": username or "",
                    "password": password or "",
                    "version": "5",
                },
                {"type": "direct", "tag": "direct"},
                {"type": "block", "tag": "block"},
            ],
            "route": {"auto_detect_interface": True, "final": "proxy"},
        }
        local_tmp = ensure_under_root(DATA_NEKO_DIR / f"nekobox_{profile_name}.json")
        local_tmp.parent.mkdir(parents=True, exist_ok=True)
        local_tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        remote = f"/sdcard/Download/nekobox_{profile_name}.json"
        try:
            self.adb.shell("mkdir", "-p", "/sdcard/Download", timeout=10)
        except Exception:
            pass
        try:
            push_out = self.adb.push(local_tmp, remote) or ""
        except Exception as exc:
            return f"push_err={exc}"
        return f"pushed={remote} {(push_out or '').strip()[:60]}"

    def _start_nekobox_vpn_ui(self, profile_name: str) -> str:
        """打开 NekoBox，关闭残留导入框，选中 profile，点 Connect/FAB，处理 VPN 授权。

        硬规则:
        - 绝不可盲点底部坐标（1440x2560 的 y≈2380 会点到导航/文件管理器）
        - 点 Connect 前必须前台是 moe.nb4a
        - 若进入 documentsui，BACK/HOME 后重新打开 NekoBox
        - 只点 resource-id=moe.nb4a:id/fab 或 content-desc=Connect
        """
        outs: list[str] = []
        if not self.is_nekobox_installed():
            outs.append("nekobox_not_installed")
            return " | ".join(outs)[:400]
        try:
            if self.is_vpn_active(skip_ui=True):
                outs.append("tun_already")
                return " | ".join(outs)[:400]
        except Exception:
            pass

        if not self.ensure_nekobox_foreground():
            outs.append("fg_fail=" + (self.current_foreground_pkg() or "?"))
            return " | ".join(outs)[:400]
        outs.append("start=fg_ok")

        def _dump() -> str:
            try:
                return self.adb.uiautomator_dump(force=True) or ""
            except Exception as exc:
                outs.append(f"dump_err={exc}")
                return ""

        def _in_nekobox() -> bool:
            pkg = self.current_foreground_pkg().lower()
            return self.nekobox_pkg.lower() in pkg

        def _in_vpn_consent(xml: str = "") -> bool:
            pkg = self.current_foreground_pkg()
            return self._is_vpn_consent_pkg(pkg) or self._xml_looks_like_vpn_consent(xml)

        def _recover_fg() -> bool:
            if _in_nekobox():
                return True
            # VPN 授权中：只点 OK，绝不 HOME
            try:
                xml_now = self.adb.uiautomator_dump(force=True) or ""
            except Exception:
                xml_now = ""
            if _in_vpn_consent(xml_now):
                hit = self.handle_vpn_consent_dialog(xml_now, log=None)
                outs.append(f"consent_in_recover={hit or 'miss'}")
                time.sleep(0.8)
                return _in_nekobox() or bool(hit)
            leave = self._leave_file_manager_and_home()
            outs.append(f"recover={leave}")
            if str(leave).startswith("vpn_consent"):
                hit = self.handle_vpn_consent_dialog(log=None)
                outs.append(f"consent_after_leave={hit or 'miss'}")
                return bool(hit) or _in_nekobox()
            ok = self.ensure_nekobox_foreground()
            outs.append("recover_fg=" + ("ok" if ok else "fail"))
            return ok

        def _dismiss_import(xml: str) -> str:
            low = (xml or "").lower()
            if "import profile" not in low and "confirm you want" not in low:
                return ""
            hit = self.adb.tap_any(
                ["YES", "Yes", "OK", "确定"],
                xml=xml,
                match_text=True,
                match_desc=True,
            )
            if hit:
                time.sleep(0.9)
                return hit
            b = self.adb.find_node_bounds(resource_id="android:id/button1", xml=xml)
            if b:
                self.adb.tap_bounds(b)
                time.sleep(0.9)
                return "button1"
            return "fail"

        def _already_connected(xml: str) -> bool:
            low = (xml or "").lower()
            if 'content-desc="stop"' in low or "connected, tap" in low:
                return True
            if re.search(r'content-desc="Stop"', xml or "", re.I):
                return True
            return False

        def _tap_connect_fab(xml: str) -> str:
            """点真实 FAB/Connect；主列表找不到时 BACK 回列表 + 坐标兜底。"""
            if not _in_nekobox():
                return "skip_not_nekobox:" + (self.current_foreground_pkg() or "?")
            if not (xml or "").strip():
                return "no_xml"
            if _already_connected(xml):
                return "already_stop"

            def _try_fab(x: str) -> str:
                if not (x or "").strip():
                    return ""
                if _already_connected(x):
                    return "already_stop"
                b = self.adb.find_node_bounds(resource_id="moe.nb4a:id/fab", xml=x)
                if not b:
                    b = self.adb.find_node_bounds(resource_id=":id/fab", xml=x)
                if b:
                    x1, y1, x2, y2 = b
                    cy = (y1 + y2) // 2
                    if cy > 2500:
                        cy = min(cy, 2360)
                    self.adb.tap((x1 + x2) // 2, cy)
                    return f"fab:{x1},{y1},{x2},{y2}"
                b = self.adb.find_node_bounds(content_desc="Connect", xml=x)
                if b:
                    self.adb.tap_bounds(b)
                    return "desc:Connect"
                # content-desc 可能带状态：Connect / Connected, tap to stop
                b = self.adb.find_node_bounds(content_desc="connect", xml=x)
                if b and not _already_connected(x):
                    self.adb.tap_bounds(b)
                    return "desc:connect_substr"
                hit = self.adb.tap_any(
                    ["Connect", "连接", "Start", "启动", "Tap to connect", "Not connected"],
                    xml=x,
                    match_desc=True,
                    match_text=True,
                )
                if hit:
                    return f"label:{hit}"
                return ""

            hit0 = _try_fab(xml)
            if hit0:
                return hit0

            low = (xml or "").lower()
            # 选中 profile 后可能误进编辑页（有 Name/Address/OK 无 FAB）→ BACK 回主列表
            looks_editor = (
                ("server" in low and "port" in low)
                or 'text="name"' in low
                or "socks" in low and "username" in low
                or "profile settings" in low
                or "configuration" in low
            )
            looks_main_shell = (
                'resource-id="moe.nb4a:id/fab"' in low
                or 'resource-id="moe.nb4a:id/action_add"' in low
                or 'resource-id="moe.nb4a:id/group_pager"' in low
                or 'text="nekobox"' in low
            )
            if looks_editor or not looks_main_shell:
                try:
                    self.adb.shell("input", "keyevent", "4", timeout=8)  # BACK
                    time.sleep(0.7)
                except Exception:
                    pass
                try:
                    self.ensure_nekobox_foreground(log=None)
                    time.sleep(0.6)
                except Exception:
                    pass
                xml2 = _dump()
                hit1 = _try_fab(xml2)
                if hit1:
                    return "back_then_" + hit1
                xml = xml2
                low = (xml or "").lower()
                looks_main_shell = (
                    'resource-id="moe.nb4a:id/fab"' in low
                    or 'resource-id="moe.nb4a:id/action_add"' in low
                    or 'resource-id="moe.nb4a:id/group_pager"' in low
                    or 'text="nekobox"' in low
                )

            # 主列表 UI 特征在但 dump 丢了 FAB 节点：用历史稳定坐标兜底（1440x2560）
            if looks_main_shell and "please select a profile" not in low:
                # 历史成功 bounds=[608,2272][832,2496]
                self.adb.tap(720, 2384)
                return "fallback_coord:720,2384"
            if looks_main_shell:
                # 即使 snackbar 提示，FAB 仍在底部
                self.adb.tap(720, 2384)
                return "fallback_coord_snack:720,2384"
            return "no_fab"

        xml = _dump()
        if not xml.strip():
            if not _recover_fg():
                return " | ".join(outs + ["ui_empty"])[:400]
            xml = _dump()
            if not xml.strip():
                return " | ".join(outs + ["ui_empty"])[:400]

        d = _dismiss_import(xml)
        if d:
            outs.append(f"dismiss_import={d}")
            xml = _dump()

        if _already_connected(xml):
            outs.append("already_connected")
            return " | ".join(outs)[:400]

        # 选中绑定 profile（必须 UI 列表精确可见；找不到立即返回 need_import，禁止狂点 FAB）
        if profile_name:
            if self._cancelled():
                outs.append("cancelled")
                return " | ".join(outs)[:400]
            visible = self.nekobox_profile_visible_in_ui(profile_name, xml=xml)
            low_all = (xml or "").lower()
            please_select = "please select a profile" in low_all
            b = None
            if visible:
                # 必须精确 text=name，禁止 text_substr 把 username 里的 qiang15 点中
                b = self._find_exact_text_bounds(profile_name, xml)
                if not b:
                    b = self.adb.find_node_bounds(
                        text_substr=profile_name,
                        resource_id="moe.nb4a:id/profile_name",
                        xml=xml,
                    )
                    # 二次确认：命中节点文本必须精确等于 profile 名
                    if b:
                        exact = self._find_exact_text_bounds(profile_name, xml)
                        if exact:
                            b = exact
                        elif not re.search(rf'text="{re.escape(profile_name)}"', xml or ""):
                            b = None
                            visible = False
            if b:
                x1, y1, x2, y2 = b
                cx = min((x1 + x2) // 2, x1 + 120)
                cy = (y1 + y2) // 2
                self.adb.tap(cx, cy)
                outs.append(f"select={profile_name}")
                time.sleep(0.8)
                xml = _dump()
                if _already_connected(xml):
                    outs.append("already_connected")
                    return " | ".join(outs)[:400]
            else:
                outs.append(f"select_miss={profile_name}")
                if please_select:
                    outs.append("please_select_profile")
                outs.append("need_import")
                self._log(None, f"NekoBox 列表无 profile={profile_name}，停止 Connect 等待导入")
                return " | ".join(outs)[:400]

        if self._cancelled():
            outs.append("cancelled")
            return " | ".join(outs)[:400]

        tap = _tap_connect_fab(xml)
        outs.append(f"tap={tap or 'none'}")
        time.sleep(1.6)

        for round_i in range(10):
            if self._cancelled():
                outs.append("cancelled")
                break
            try:
                if self.is_vpn_active(skip_ui=True):
                    outs.append("tun_up")
                    break
            except Exception:
                pass
            xml = _dump()
            # 1) 系统 VPN 授权弹窗：必须点 OK，禁止 HOME
            if _in_vpn_consent(xml):
                hitc = self.handle_vpn_consent_dialog(xml, log=None)
                outs.append(f"vpn_consent#{round_i}={hitc or 'miss'}")
                time.sleep(1.2)
                continue
            if not _in_nekobox():
                if not _recover_fg():
                    # 若 recover 时处理了 consent，继续轮询
                    if self._is_vpn_consent_pkg(self.current_foreground_pkg()):
                        continue
                    outs.append(f"lost_fg#{round_i}")
                    break
                continue
            if not xml.strip():
                time.sleep(0.8)
                continue
            # 若 dump 到的是文件管理器 UI，不点任何东西
            low_xml = (xml or "").lower()
            if "documentsui" in low_xml or "com.android.documentsui" in low_xml:
                outs.append(f"docs_ui#{round_i}")
                if not _recover_fg():
                    break
                continue
            d = _dismiss_import(xml)
            if d:
                outs.append(f"yes_mid={d}")
                time.sleep(0.7)
                continue
            if _already_connected(xml):
                outs.append("connected")
                time.sleep(1.0)
                if self.is_vpn_active(skip_ui=True):
                    outs.append("tun_up")
                break
            # 仅系统 VPN 授权/明确信任对话框才点 OK；禁止在编辑页乱点 OK
            if _in_vpn_consent(xml) or self._xml_looks_like_vpn_consent(xml):
                hitc = self.handle_vpn_consent_dialog(xml, log=None)
                outs.append(f"vpn_consent_loop={hitc or 'miss'}")
                time.sleep(1.1)
                continue
            low_perm = (xml or "").lower()
            if "i trust this application" in low_perm or "connection request" in low_perm:
                hit = self.adb.tap_any(
                    [
                        "OK",
                        "Allow",
                        "允许",
                        "确定",
                        "I trust this application",
                        "Trust this app",
                        "Trust",
                        "YES",
                        "Yes",
                    ],
                    xml=xml,
                    match_desc=True,
                    match_text=True,
                )
                if hit:
                    outs.append(f"perm={hit}")
                    time.sleep(1.1)
                    continue
            if not _already_connected(xml):
                tap2 = _tap_connect_fab(xml)
                if tap2 and tap2 not in ("already_stop", "no_fab") and not str(tap2).startswith("skip_"):
                    outs.append(f"fab_retry={round_i}:{tap2}")
                    time.sleep(1.3)
                    # Connect 后立刻再抓一次授权弹窗
                    time.sleep(0.5)
                    xml2 = _dump()
                    if _in_vpn_consent(xml2):
                        hitc = self.handle_vpn_consent_dialog(xml2, log=None)
                        outs.append(f"vpn_consent_post_fab={hitc or 'miss'}")
                    continue
                if str(tap2).startswith("skip_") or tap2 == "no_fab":
                    outs.append(f"fab_skip={round_i}:{tap2}")
                    # 再 BACK + 回主界面，避免卡在 profile 编辑页
                    try:
                        self.adb.shell("input", "keyevent", "4", timeout=8)
                        time.sleep(0.5)
                    except Exception:
                        pass
                    if not _recover_fg():
                        break
                    continue
            break
        return " | ".join(outs)[:500]


    @staticmethod
    def _kryo_contains(blob: bytes, value: str) -> bool:
        """NekoBox socksBean 使用 Kryo 风格字符串：末字节常带 0x80 高位。"""
        if not value:
            return True
        if not blob:
            return False
        raw = value.encode("utf-8", errors="ignore")
        if raw in blob:
            return True
        if len(raw) >= 1:
            body, last = raw[:-1], bytes([raw[-1] | 0x80])
            if body + last in blob:
                return True
        # 宽松：去高位后子串
        plain = bytes(b & 0x7F if 0x80 <= b <= 0xFF else b for b in blob)
        try:
            plain_s = plain.decode("latin-1", errors="ignore")
        except Exception:
            plain_s = ""
        return value in plain_s

    def _pull_nekobox_db(self) -> Optional[Path]:
        """把 sager_net.db 拉到项目 data/state 做本地解析。

        必须已安装 NekoBox；先删本地/远端缓存，避免 pm clear 后仍用陈旧 DB
        把 qiang15 等名字误判为已存在（导致不导入却狂点 Connect）。
        """
        if not self.is_nekobox_installed():
            return None
        serial = (getattr(self.adb, "serial", None) or "device").replace(":", "_").replace(".", "_")
        local = ensure_under_root(DATA_STATE_DIR / f"sager_net_{serial}.db")
        local.parent.mkdir(parents=True, exist_ok=True)
        # 关键：先删本地，防止 pull 失败时沿用旧文件
        try:
            if local.exists():
                local.unlink()
        except Exception:
            pass
        remote = "/sdcard/Download/sager_net_check.db"
        try:
            self.adb.shell("rm", "-f", remote, timeout=8)
        except Exception:
            pass
        try:
            # shell_su 比 su_script 更稳（部分机型 su_script 写临时文件后输出空）
            self.adb.shell_su(
                f"cp /data/user/0/{self.nekobox_pkg}/databases/sager_net.db {remote}; chmod 666 {remote}",
                timeout=20,
            )
        except Exception:
            return None
        # 远端必须真有文件
        try:
            ls = self.adb.shell("ls", "-l", remote, timeout=8) or ""
            if "No such file" in ls or "No such" in ls or not ls.strip():
                return None
        except Exception:
            return None
        try:
            self.adb.pull(remote, local)
        except Exception:
            return None
        if not local.exists() or local.stat().st_size < 64:
            try:
                if local.exists():
                    local.unlink()
            except Exception:
                pass
            return None
        return local

    def nekobox_list_socks_profiles(self) -> list[dict]:
        """解析 DB 中 SOCKS profile 的可读字段（host/user/pass/name）。"""
        path = self._pull_nekobox_db()
        if not path:
            return []
        try:
            import sqlite3

            con = sqlite3.connect(str(path))
            cur = con.cursor()
            rows = cur.execute(
                "SELECT id, type, socksBean FROM proxy_entities WHERE socksBean IS NOT NULL AND length(socksBean) > 0"
            ).fetchall()
            con.close()
        except Exception:
            return []
        out: list[dict] = []
        for rid, typ, blob in rows:
            raw = blob if isinstance(blob, (bytes, bytearray)) else b""
            strings = self._extract_kryo_strings(bytes(raw))
            # Kryo 字段顺序约: host, (port 可能裂出 #), username, password, profile_name
            # 端口 9093 的 0x23 会被当成字符 #，需过滤
            clean = [s for s in strings if s and s != "#"]
            host = next((s for s in clean if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", s)), "")
            username = next((s for s in clean if "_pp" in s or "@" in s or (s.count(".") >= 1 and not re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", s) and len(s) > 8)), "")
            password = next((s for s in clean if s not in (host, username) and any(c.isdigit() for c in s) and any(c.isalpha() for c in s) and len(s) >= 6 and "_pp" not in s), "")
            # profile 名通常是短标识 qiang15/chong15
            name = next((s for s in clean if re.fullmatch(r"[A-Za-z]+\d+", s)), "")
            if not name and clean:
                name = clean[-1]
            out.append(
                {
                    "id": rid,
                    "type": typ,
                    "name": name,
                    "host": host,
                    "username": username,
                    "password": password,
                    "strings": strings,
                    "blob": bytes(raw),
                }
            )
        return out

    @staticmethod
    def _extract_kryo_strings(blob: bytes) -> list[str]:
        """从 socksBean 提取可打印字符串（处理末字节 0x80 高位）。"""
        if not blob:
            return []
        # 连续可打印 + 可选高位结束字节
        out: list[str] = []
        i = 0
        n = len(blob)
        while i < n:
            # skip non-printable
            if not (0x20 <= blob[i] <= 0x7E):
                i += 1
                continue
            j = i
            while j < n and 0x20 <= blob[j] <= 0x7E:
                j += 1
            # high-bit terminator?
            if j < n and (blob[j] & 0x80) and (0x20 <= (blob[j] & 0x7F) <= 0x7E):
                s = blob[i:j].decode("latin-1", errors="ignore") + chr(blob[j] & 0x7F)
                j += 1
            else:
                s = blob[i:j].decode("latin-1", errors="ignore")
            if len(s) >= 1:
                out.append(s)
            i = max(j, i + 1)
        return out

    def nekobox_profile_auth_ok(
        self,
        profile_name: str,
        username: str,
        *,
        host: str = "",
        password: str = "",
    ) -> bool:
        """Profile 在 UI 列表可见，且 Username/host/password 与代理一致才算 OK。

        硬规则：
        - 禁止用用户名里的 qiang15 子串冒充 profile 名
        - UI 列表没有精确 text=profile_name 时一律 False
        """
        name = (profile_name or "").strip()
        user = (username or "").strip()
        if not name:
            return False
        # UI 列表必须可见精确 profile 名
        if not self.nekobox_profile_visible_in_ui(name):
            return False
        if not user:
            return True

        profiles = self.nekobox_list_socks_profiles()
        for p in profiles:
            blob = p.get("blob") or b""
            strings = list(p.get("strings") or [])
            # 仅精确匹配 profile 名（禁止 name in username）
            parsed_name = (p.get("name") or "").strip()
            name_hit = parsed_name == name or any(s == name for s in strings)
            if not name_hit:
                continue
            user_hit = (
                (p.get("username") or "").strip() == user
                or self._kryo_contains(blob, user)
                or any(s == user for s in strings)
            )
            if not user_hit:
                return False
            if host:
                host_hit = (
                    host in ((p.get("host") or ""))
                    or self._kryo_contains(blob, host)
                    or any(s == host for s in strings)
                )
                if not host_hit:
                    return False
            if password:
                pass_hit = (
                    password in ((p.get("password") or ""))
                    or self._kryo_contains(blob, password)
                    or any(s == password for s in strings)
                )
                if not pass_hit:
                    return False
            return True

        # DB 无精确记录时：Edit 页 Username summary
        try:
            if self._nekobox_username_summary(name) == user:
                return True
        except Exception:
            pass
        return False

    def _nekobox_username_summary(self, profile_name: str) -> str:
        """打开 Edit 页读取 Username (Optional) 的 summary 文案。"""
        self._open_nekobox_main()
        if not self._open_profile_edit(profile_name):
            return ""
        time.sleep(0.8)
        xml = self.adb.uiautomator_dump(force=True) or ""
        # 找 Username (Optional) 后的 summary
        m = re.search(
            r'text="Username \(Optional\)".*?text="([^"]*)"[^>]*resource-id="android:id/summary"',
            xml,
            re.I | re.S,
        )
        if m:
            return (m.group(1) or "").strip()
        # 宽松：summary 节点附近
        m2 = re.search(r'text="Username \(Optional\)"', xml, re.I)
        if m2:
            tail = xml[m2.start() : m2.start() + 1200]
            m3 = re.search(r'resource-id="android:id/summary"[^>]*text="([^"]*)"', tail)
            if not m3:
                m3 = re.search(r'text="([^"]*)"[^>]*resource-id="android:id/summary"', tail)
            if m3:
                return (m3.group(1) or "").strip()
        return ""


    def is_nekobox_installed(self) -> bool:
        try:
            return bool(self.adb.package_installed(self.nekobox_pkg))
        except Exception:
            return False

    def current_foreground_pkg(self) -> str:
        """返回当前前台包名（失败返回空串）。"""
        try:
            out = self.adb.shell("dumpsys", "window", timeout=12) or ""
        except Exception:
            out = ""
        for pat in (
            r"mCurrentFocus=Window\{[^ ]+ u0 ([^/}\s]+)/",
            r"mFocusedApp=ActivityRecord\{[^ ]+ u0 ([^/}\s]+)/",
            r"topResumedActivity=ActivityRecord\{[^ ]+ u0 ([^/}\s]+)/",
        ):
            m = re.search(pat, out)
            if m:
                return (m.group(1) or "").strip()
        try:
            out2 = self.adb.shell("dumpsys", "activity", "activities", timeout=12) or ""
            m2 = re.search(r"mResumedActivity: ActivityRecord\{[^ ]+ u0 ([^/}\s]+)/", out2)
            if m2:
                return (m2.group(1) or "").strip()
        except Exception:
            pass
        return ""

    def _is_file_manager_pkg(self, pkg: str) -> bool:
        p = (pkg or "").lower()
        return (
            "documentsui" in p
            or "filemanager" in p
            or "com.android.documentsui" in p
            or p in {"com.android.documentsui", "com.google.android.documentsui"}
        )

    def _is_vpn_consent_pkg(self, pkg: str) -> bool:
        """系统 VPN 授权/确认界面（绝不可 HOME/BACK 关掉）。"""
        p = (pkg or "").lower()
        if not p:
            return False
        keys = (
            "vpndialogs",
            "vpn_dialog",
            "vpnconfirm",
            "com.android.vpndialogs",
            "android.permissioncontroller",
        )
        return any(k in p for k in keys)

    def _xml_looks_like_vpn_consent(self, xml: str) -> bool:
        low = (xml or "").lower()
        if not low.strip():
            return False
        markers = (
            "connection request",
            "want to set up a vpn",
            "set up a vpn connection",
            "vpn connection",
            "准备建立 vpn",
            "连接请求",
            "是否允许",
            "always-on vpn",
            "i trust this application",
            "trust this application",
        )
        return any(m in low for m in markers)

    def handle_vpn_consent_dialog(self, xml: str | None = None, *, log: LogFn = None) -> str:
        """点掉系统 VPN 授权弹窗的 OK/Allow/确定。成功返回 hit 文案，否则空。"""
        try:
            xml = xml if xml is not None else (self.adb.uiautomator_dump(force=True) or "")
        except Exception:
            xml = xml or ""
        pkg = self.current_foreground_pkg()
        if not (
            self._is_vpn_consent_pkg(pkg)
            or self._xml_looks_like_vpn_consent(xml)
        ):
            return ""
        # 优先明确肯定按钮
        labels = [
            "OK",
            "Ok",
            "Allow",
            "ALLOW",
            "允许",
            "确定",
            "同意",
            "I trust this application",
            "Trust this app",
            "Trust",
            "YES",
            "Yes",
            "Continue",
            "ACCEPT",
            "Accept",
        ]
        hit = self.adb.tap_any(
            labels,
            xml=xml,
            match_text=True,
            match_desc=True,
        )
        if hit:
            self._log(log, f"VPN 授权点击: {hit}")
            time.sleep(1.2)
            return hit
        # button1 通常是正向按钮
        b = self.adb.find_node_bounds(resource_id="android:id/button1", xml=xml)
        if b:
            self.adb.tap_bounds(b)
            self._log(log, "VPN 授权点击: button1")
            time.sleep(1.2)
            return "button1"
        # 再试 button_positive
        b2 = self.adb.find_node_bounds(resource_id="android:id/button_positive", xml=xml)
        if b2:
            self.adb.tap_bounds(b2)
            self._log(log, "VPN 授权点击: button_positive")
            time.sleep(1.2)
            return "button_positive"
        self._log(log, f"VPN 授权界面未找到 OK/Allow fg={pkg}")
        return ""

    def _leave_file_manager_and_home(self) -> str:
        """只离开 documentsui/文件管理器。VPN 授权界面绝不动 HOME/BACK。"""
        outs: list[str] = []
        pkg = self.current_foreground_pkg().lower()
        if self._is_vpn_consent_pkg(pkg):
            return "vpn_consent_keep"
        if self.nekobox_pkg.lower() in (pkg or ""):
            return "already_nekobox"
        if not self._is_file_manager_pkg(pkg):
            return "noop"
        for _ in range(3):
            try:
                self.adb.shell("input", "keyevent", "4", timeout=6)  # BACK
                outs.append("back")
            except Exception:
                pass
            time.sleep(0.25)
            pkg2 = self.current_foreground_pkg().lower()
            if not self._is_file_manager_pkg(pkg2):
                break
            if self._is_vpn_consent_pkg(pkg2):
                return "vpn_consent_after_back|" + "|".join(outs)
        # 仅当仍是文件管理器时才 HOME（不要因 VPN 授权 HOME）
        pkg3 = self.current_foreground_pkg().lower()
        if self._is_file_manager_pkg(pkg3):
            try:
                self.adb.shell("input", "keyevent", "3", timeout=6)
                outs.append("home")
            except Exception:
                pass
            time.sleep(0.4)
        return "|".join(outs) or "noop"

    def ensure_nekobox_foreground(self, *, log: LogFn = None) -> bool:
        """确保 NekoBox 在前台；不在则离开文件管理器并 am start。

        VPN 授权弹窗期间返回 False 但不关闭弹窗（由 handle_vpn_consent_dialog 处理）。
        """
        if not self.is_nekobox_installed():
            self._log(log, "NekoBox 未安装，无法打开前台")
            return False
        pkg0 = self.current_foreground_pkg().lower()
        if self._is_vpn_consent_pkg(pkg0):
            self._log(log, f"前台是 VPN 授权界面，不抢前台: {pkg0}")
            return False
        leave = self._leave_file_manager_and_home()
        if leave not in ("already_nekobox", "noop", "vpn_consent_keep") and not str(leave).startswith("vpn_consent"):
            self._log(log, f"离开文件管理器: {leave}")
        for attempt in range(3):
            pkg = self.current_foreground_pkg().lower()
            if self._is_vpn_consent_pkg(pkg):
                self._log(log, f"出现 VPN 授权界面 attempt={attempt}")
                return False
            if self.nekobox_pkg.lower() in pkg:
                return True
            try:
                # 优先显式 MainActivity，失败再用 LAUNCHER package
                o1 = self.adb.shell(
                    "am",
                    "start",
                    "-n",
                    f"{self.nekobox_pkg}/io.nekohasekai.sagernet.ui.MainActivity",
                    timeout=15,
                ) or ""
                if "Error" in o1 or "does not exist" in o1:
                    o2 = self.adb.shell(
                        "am",
                        "start",
                        "-a",
                        "android.intent.action.MAIN",
                        "-c",
                        "android.intent.category.LAUNCHER",
                        self.nekobox_pkg,
                        timeout=15,
                    ) or ""
                    self._log(log, f"NekoBox am start fallback: {(o2 or '')[:80]}")
                else:
                    self._log(log, f"NekoBox am start: {(o1 or '').strip().replace(chr(10), ' ')[:80]}")
            except Exception as exc:
                self._log(log, f"NekoBox am start err: {exc}")
            time.sleep(1.2)
            pkg = self.current_foreground_pkg().lower()
            if self.nekobox_pkg.lower() in pkg:
                return True
            # 仍在文件管理器则继续离开
            if "documentsui" in pkg or "filemanager" in pkg:
                self._leave_file_manager_and_home()
            self._log(log, f"NekoBox 前台未就绪 attempt={attempt} fg={pkg or '?'}")
        return self.nekobox_pkg.lower() in self.current_foreground_pkg().lower()

    def _open_nekobox_main(self) -> None:
        """打开 NekoBox 主界面；先离开文件管理器，并校验前台。"""
        if not self.is_nekobox_installed():
            return
        self.ensure_nekobox_foreground(log=None)
        time.sleep(0.3)

    def _open_profile_edit(self, profile_name: str) -> bool:
        """在主列表点对应 profile 行的 Edit。"""
        name = (profile_name or "").strip()
        xml = self.adb.uiautomator_dump(force=True) or ""
        if not xml.strip():
            return False
        # 多 profile：按 profile_name 纵坐标匹配 edit
        name_b = self.adb.find_node_bounds(text_substr=name, resource_id="moe.nb4a:id/profile_name", xml=xml)
        if not name_b:
            name_b = self.adb.find_node_bounds(text_substr=name, xml=xml)
        edit_b = None
        if name_b:
            try:
                import xml.etree.ElementTree as ET

                root = ET.fromstring(xml)
                ny = (name_b[1] + name_b[3]) // 2
                best = None
                best_dy = 10**9
                for node in root.iter("node"):
                    rid = node.attrib.get("resource-id") or ""
                    desc = (node.attrib.get("content-desc") or "").lower()
                    if "moe.nb4a:id/edit" not in rid and desc != "edit":
                        continue
                    b = self.adb._parse_bounds(node.attrib.get("bounds") or "")
                    if not b:
                        continue
                    cy = (b[1] + b[3]) // 2
                    dy = abs(cy - ny)
                    if dy < best_dy:
                        best_dy = dy
                        best = b
                if best and best_dy < 200:
                    edit_b = best
            except Exception:
                edit_b = None
        if not edit_b:
            edit_b = self.adb.find_node_bounds(resource_id="moe.nb4a:id/edit", xml=xml)
        if not edit_b:
            edit_b = self.adb.find_node_bounds(content_desc="Edit", xml=xml)
        if not edit_b:
            return False
        self.adb.tap_bounds(edit_b)
        time.sleep(1.0)
        return True

    def _set_preference_text(self, title_substr: str, value: str, xml: str = "") -> str:
        """Preference 列表：点 title 行 -> EditText -> 清空输入 -> OK。"""
        xml = xml or (self.adb.uiautomator_dump(force=True) or "")

        def _find_title_bounds(x: str):
            # 优先 android:id/title 且文本精确/前缀匹配，避免 Server 命中 Server Settings
            try:
                import xml.etree.ElementTree as ET

                root = ET.fromstring(x)
            except Exception:
                return self.adb.find_node_bounds(text_substr=title_substr, xml=x)
            needle = (title_substr or "").strip().lower()
            exact = None
            pref = None
            fuzzy = None
            for node in root.iter("node"):
                rid = (node.attrib.get("resource-id") or "")
                text = (node.attrib.get("text") or "").strip()
                if not text:
                    continue
                low = text.lower()
                b = self.adb._parse_bounds(node.attrib.get("bounds") or "")
                if not b:
                    continue
                if rid.endswith("id/title") or rid == "android:id/title":
                    if low == needle:
                        exact = b
                        break
                    if low.startswith(needle) and (len(low) == len(needle) or low[len(needle):len(needle)+1] in ("", " ")):
                        pref = pref or b
                    # Username (Optional) / Password (Optional)
                    if needle in low and ("optional" in low or low.startswith(needle)):
                        pref = pref or b
                elif needle and needle in low and low != "server settings":
                    fuzzy = fuzzy or b
            return exact or pref or fuzzy

        # 若不可见，上滑/下滑几次
        b = None
        for _ in range(5):
            b = _find_title_bounds(xml)
            if b:
                break
            try:
                self.adb.swipe(720, 2000, 720, 900, 350)
            except Exception:
                pass
            time.sleep(0.5)
            xml = self.adb.uiautomator_dump(force=True) or ""
        if not b:
            return f"miss_title={title_substr}"
        self.adb.tap_bounds(b)
        time.sleep(0.8)
        dlg = self.adb.uiautomator_dump(force=True) or ""
        eb = self.adb.find_node_bounds(resource_id="android:id/edit", class_endswith="EditText", xml=dlg)
        if not eb:
            eb = self.adb.find_node_bounds(class_endswith="EditText", xml=dlg)
        if not eb:
            return "no_edittext"
        self.adb.tap_bounds(eb)
        time.sleep(0.2)
        try:
            self.adb.clear_field(times=max(40, len(value) + 10))
        except Exception:
            pass
        try:
            self.adb.input_text_safe(value)
        except Exception as exc:
            return f"input_err={exc}"
        time.sleep(0.3)
        hit = self.adb.tap_any(["OK", "Ok", "确定", "Apply", "保存"], xml=self.adb.uiautomator_dump(force=True) or "", match_text=True)
        if not hit:
            b1 = self.adb.find_node_bounds(resource_id="android:id/button1")
            if b1:
                self.adb.tap_bounds(b1)
                hit = "button1"
            else:
                return "no_ok"
        time.sleep(0.5)
        return f"set={title_substr}:{hit}"

    def fix_nekobox_profile_auth_ui(
        self,
        profile_name: str,
        host: str,
        port: int,
        username: str,
        password: str,
    ) -> str:
        """Edit 页写入 Server/Port/Username/Password 并 Apply。"""
        outs: list[str] = []
        self._open_nekobox_main()
        if not self._open_profile_edit(profile_name):
            return "edit_open_fail"
        outs.append("edit_open")
        xml = self.adb.uiautomator_dump(force=True) or ""
        if host:
            outs.append(self._set_preference_text("Server", host, xml=xml))
            xml = ""
        if port:
            outs.append(self._set_preference_text("Remote Port", str(int(port)), xml=xml))
            xml = ""
        if username:
            outs.append(self._set_preference_text("Username", username, xml=xml))
            xml = ""
        if password:
            outs.append(self._set_preference_text("Password", password, xml=xml))
            xml = ""
        # Apply
        xml = self.adb.uiautomator_dump(force=True) or ""
        hit = self.adb.tap_any(["Apply", "应用", "Save", "保存"], xml=xml, match_text=True, match_desc=True)
        if not hit:
            # 顶栏 Apply 有时只有 content-desc / text
            b = self.adb.find_node_bounds(text_substr="Apply", xml=xml)
            if b:
                self.adb.tap_bounds(b)
                hit = "Apply_bounds"
        outs.append(f"apply={hit or 'none'}")
        time.sleep(0.8)
        # 回主页
        try:
            self.adb.shell("input", "keyevent", "4", timeout=8)
        except Exception:
            pass
        return " | ".join(outs)[:500]


    def list_nekobox_profile_names_ui(self, xml: str | None = None) -> list[str]:
        """从主列表读取当前可见的 profile 名称（精确 text）。"""
        if xml is None:
            try:
                self._open_nekobox_main()
                time.sleep(0.35)
                xml = self.adb.uiautomator_dump(force=True) or ""
            except Exception:
                return []
        names: list[str] = []
        seen: set[str] = set()
        if not (xml or "").strip():
            return names
        try:
            root = ET.fromstring(xml)
        except Exception:
            # 兜底：regex 抽 profile_name 节点
            for m in re.finditer(
                r'resource-id="moe\.nb4a:id/profile_name"[^>]*text="([^"]+)"',
                xml,
            ):
                n = (m.group(1) or "").strip()
                if n and n not in seen:
                    seen.add(n)
                    names.append(n)
            for m in re.finditer(
                r'text="([^"]+)"[^>]*resource-id="moe\.nb4a:id/profile_name"',
                xml,
            ):
                n = (m.group(1) or "").strip()
                if n and n not in seen:
                    seen.add(n)
                    names.append(n)
            return names
        for node in root.iter("node"):
            rid = node.attrib.get("resource-id") or ""
            if "moe.nb4a:id/profile_name" not in rid:
                continue
            n = (node.attrib.get("text") or "").strip()
            if not n or n in seen:
                continue
            seen.add(n)
            names.append(n)
        return names

    def delete_all_nekobox_profiles_ui(
        self,
        *,
        log: LogFn = None,
        max_rounds: int = 24,
    ) -> str:
        """删除 NekoBox 列表中全部 profile，避免多条 SOCKS 叠加。

        流程：打开主界面 →（尽量）Stop VPN → 循环点 Remove/确认，直到无 remove 或无 profile。
        """
        outs: list[str] = []
        try:
            self._open_nekobox_main()
            time.sleep(0.4)
        except Exception as exc:
            return f"open_err={exc}"

        # 先关 VPN，再删配置
        try:
            stop_msg = self.stop_nekobox_vpn_ui(log=log)
            outs.append(f"stop={stop_msg}")
            self._log(log, f"NekoBox 清空前 Stop: {stop_msg}")
        except Exception as exc:
            outs.append(f"stop_err={exc}")

        deleted = 0
        seen_names: list[str] = []
        for rnd in range(1, max(1, int(max_rounds)) + 1):
            if self._cancelled():
                outs.append("cancelled")
                break
            try:
                self._open_nekobox_main()
            except Exception:
                pass
            time.sleep(0.25)
            xml = ""
            try:
                xml = self.adb.uiautomator_dump(force=True) or ""
            except Exception as exc:
                outs.append(f"dump_err={exc}")
                break

            names = self.list_nekobox_profile_names_ui(xml)
            for n in names:
                if n not in seen_names:
                    seen_names.append(n)

            # 优先点与某个 profile 同行的 Remove
            rem_b = None
            target_name = names[0] if names else ""
            if target_name:
                try:
                    name_b = self._find_exact_text_bounds(target_name, xml)
                    if not name_b:
                        name_b = self.adb.find_node_bounds(
                            text_substr=target_name,
                            resource_id="moe.nb4a:id/profile_name",
                            xml=xml,
                        )
                    if name_b:
                        root = ET.fromstring(xml)
                        ny = (name_b[1] + name_b[3]) // 2
                        best = None
                        best_dy = 10**9
                        for node in root.iter("node"):
                            rid = node.attrib.get("resource-id") or ""
                            desc = (node.attrib.get("content-desc") or "").lower()
                            if "moe.nb4a:id/remove" not in rid and desc != "remove":
                                continue
                            b = self.adb._parse_bounds(node.attrib.get("bounds") or "")
                            if not b:
                                continue
                            cy = (b[1] + b[3]) // 2
                            dy = abs(cy - ny)
                            if dy < best_dy:
                                best_dy = dy
                                best = b
                        if best and best_dy < 220:
                            rem_b = best
                except Exception:
                    rem_b = None

            if not rem_b:
                rem_b = self.adb.find_node_bounds(
                    resource_id="moe.nb4a:id/remove", xml=xml
                )
            if not rem_b:
                # 没有 remove：可能列表已空
                if not names:
                    outs.append(f"empty_round={rnd}")
                    break
                # 有名字但无 remove：尝试按名称走旧删除
                if target_name:
                    try:
                        one = self.delete_nekobox_profile_ui(target_name)
                        outs.append(f"fallback_delete_{target_name}={one}")
                        if one.startswith("removed=") or "tapped" in one:
                            deleted += 1
                            time.sleep(0.45)
                            continue
                    except Exception as exc:
                        outs.append(f"fallback_err={exc}")
                outs.append(f"no_remove names={names[:6]}")
                break

            try:
                self.adb.tap_bounds(rem_b)
            except Exception as exc:
                outs.append(f"tap_remove_err={exc}")
                break
            time.sleep(0.55)
            xml2 = ""
            try:
                xml2 = self.adb.uiautomator_dump(force=True) or ""
            except Exception:
                xml2 = ""
            hit = self.adb.tap_any(
                ["OK", "Yes", "YES", "确定", "删除", "Remove", "Delete"],
                xml=xml2,
                match_text=True,
            )
            if not hit:
                b1 = self.adb.find_node_bounds(
                    resource_id="android:id/button1", xml=xml2
                )
                if b1:
                    self.adb.tap_bounds(b1)
                    hit = "button1"
            deleted += 1
            self._log(
                log,
                f"NekoBox 删除 profile#{deleted} name={target_name or '?'} confirm={hit or 'tapped'}",
            )
            time.sleep(0.45)

        # 终态再确认
        left: list[str] = []
        try:
            self._open_nekobox_main()
            time.sleep(0.3)
            left = self.list_nekobox_profile_names_ui()
        except Exception:
            left = []
        msg = (
            f"deleted={deleted} seen={seen_names[:12]} left={left[:8]} "
            + " | ".join(outs)
        )
        self._log(log, f"NekoBox 清空全部代理: {msg[:240]}")
        return msg[:500]

    def delete_nekobox_profile_ui(self, profile_name: str) -> str:
        """主列表点 Remove 删除指定 profile。"""
        self._open_nekobox_main()
        xml = self.adb.uiautomator_dump(force=True) or ""
        name = (profile_name or "").strip()
        name_b = self.adb.find_node_bounds(text_substr=name, resource_id="moe.nb4a:id/profile_name", xml=xml)
        if not name_b:
            name_b = self.adb.find_node_bounds(text_substr=name, xml=xml)
        rem_b = None
        if name_b:
            try:
                import xml.etree.ElementTree as ET

                root = ET.fromstring(xml)
                ny = (name_b[1] + name_b[3]) // 2
                best = None
                best_dy = 10**9
                for node in root.iter("node"):
                    rid = node.attrib.get("resource-id") or ""
                    desc = (node.attrib.get("content-desc") or "").lower()
                    if "moe.nb4a:id/remove" not in rid and desc != "remove":
                        continue
                    b = self.adb._parse_bounds(node.attrib.get("bounds") or "")
                    if not b:
                        continue
                    cy = (b[1] + b[3]) // 2
                    dy = abs(cy - ny)
                    if dy < best_dy:
                        best_dy = dy
                        best = b
                if best and best_dy < 200:
                    rem_b = best
            except Exception:
                rem_b = None
        if not rem_b:
            rem_b = self.adb.find_node_bounds(resource_id="moe.nb4a:id/remove", xml=xml)
        if not rem_b:
            return "remove_btn_miss"
        self.adb.tap_bounds(rem_b)
        time.sleep(0.7)
        xml2 = self.adb.uiautomator_dump(force=True) or ""
        hit = self.adb.tap_any(["OK", "Yes", "YES", "确定", "删除", "Remove"], xml=xml2, match_text=True)
        if not hit:
            b1 = self.adb.find_node_bounds(resource_id="android:id/button1", xml=xml2)
            if b1:
                self.adb.tap_bounds(b1)
                hit = "button1"
        time.sleep(0.6)
        return f"removed={hit or 'tapped'}"


    def _find_exact_text_bounds(self, text: str, xml: str):
        """在 UIAutomator XML 中找 text/content-desc 完全相等的节点 bounds。"""
        name = (text or "").strip()
        if not name or not (xml or "").strip():
            return None
        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(xml)
        except Exception:
            return None
        for node in root.iter("node"):
            t = (node.attrib.get("text") or "").strip()
            d = (node.attrib.get("content-desc") or "").strip()
            if t != name and d != name:
                continue
            b = self.adb._parse_bounds(node.attrib.get("bounds") or "")
            if b:
                return b
        return None

    def nekobox_profile_visible_in_ui(self, profile_name: str, xml: str | None = None) -> bool:
        """UI 列表是否出现精确的 Profile Name（唯一可信判定）。

        禁止用 username 中的 qiang15 子串、DB strings 模糊命中当作已导入。
        """
        name = (profile_name or "").strip()
        if not name:
            return False
        if xml is None:
            try:
                self._open_nekobox_main()
                time.sleep(0.4)
                xml = self.adb.uiautomator_dump(force=True) or ""
            except Exception:
                return False
        if not (xml or "").strip():
            return False
        # 精确属性值 text="name" / content-desc="name"
        if re.search(rf'text="{re.escape(name)}"', xml) or re.search(
            rf'content-desc="{re.escape(name)}"', xml
        ):
            return True
        # profile_name id 且精确文本
        if self._find_exact_text_bounds(name, xml):
            rid_hit = self.adb.find_node_bounds(
                text_substr=name, resource_id="moe.nb4a:id/profile_name", xml=xml
            )
            if rid_hit:
                return True
            # 无 id 时精确 text 节点也算可见
            return True
        return False

    def nekobox_profile_exists(self, profile_name: str) -> bool:
        """检测 NekoBox 是否已有该 Profile。

        硬规则：
        1) UI 列表精确可见 => True
        2) 能成功 dump 主列表且精确不可见 => False（哪怕 DB/陈旧缓存有名字）
        3) UI 不可用时，DB 仅当 name 字段完全相等才算（禁止 username 子串）
        """
        name = (profile_name or "").strip()
        if not name:
            return False
        ui_ok = False
        try:
            self._open_nekobox_main()
            time.sleep(0.35)
            xml = self.adb.uiautomator_dump(force=True) or ""
            if (xml or "").strip():
                ui_ok = True
                if self.nekobox_profile_visible_in_ui(name, xml=xml):
                    return True
                # 主界面已 dump 到内容，列表无该 profile = 未导入
                low = xml.lower()
                if "moe.nb4a" in low or "nekobox" in low or "please select a profile" in low:
                    return False
        except Exception:
            pass
        if ui_ok:
            return False
        try:
            for p in self.nekobox_list_socks_profiles():
                parsed = (p.get("name") or "").strip()
                if parsed == name:
                    return True
                # 仅精确 name 字符串，禁止 username 包含 qiang15
                strings = p.get("strings") or []
                if any(s == name for s in strings) and parsed in ("", name):
                    return True
        except Exception:
            pass
        return False

    def ensure_nekobox_vpn_only(
        self,
        profile_name: str,
        *,
        log=None,
        verify_vpn: bool = True,
        vpn_wait_seconds: float = 25.0,
        max_connect_rounds: int = 3,
    ) -> str:
        """已有 Profile：必须 Connect 并验证 tun；不得只打开 App。"""
        outs: list[str] = []
        self._log(log, f"NekoBox 复用 profile={profile_name}，强制启 VPN 并验证 tun")
        outs.append(f"reuse_profile={profile_name}")
        try:
            if self.is_vpn_active(skip_ui=True):
                outs.append("sys_vpn_already")
                self._log(log, "NekoBox VPN 已在运行(tun)")
                try:
                    self.adb.shell("input", "keyevent", "3", timeout=8)
                    outs.append("home_ok")
                except Exception:
                    pass
                try:
                    self.adb.release_ui_control(home=False)
                    outs.append("ui_release")
                except Exception:
                    pass
                outs.append("vpn_active=True")
                return " | ".join(outs)[:900]
        except Exception:
            pass

        vpn_ok = False
        for round_i in range(max(1, int(max_connect_rounds))):
            if self._cancelled():
                outs.append("cancelled")
                self._log(log, "NekoBox VPN 循环收到停止信号，退出")
                break
            try:
                vpn_ui = self._start_nekobox_vpn_ui(profile_name)
                outs.append(f"vpn_ui#{round_i}=" + vpn_ui)
                self._log(log, f"NekoBox 启 VPN round={round_i}: {vpn_ui[:160]}")
            except Exception as exc:
                outs.append(f"vpn_ui_err#{round_i}={exc}")
                self._log(log, f"NekoBox 启 VPN 失败: {exc}")
                vpn_ui = ""

            # 无 profile 时禁止继续狂点 Connect，交给上层导入
            if "need_import" in (vpn_ui or "") or "select_miss=" in (vpn_ui or ""):
                outs.append("abort_no_profile")
                self._log(log, f"NekoBox 列表无 profile={profile_name}，中止 Connect 循环")
                break
            if "cancelled" in (vpn_ui or ""):
                outs.append("cancelled")
                break

            if not verify_vpn:
                break
            deadline = time.time() + max(5.0, float(vpn_wait_seconds))
            while time.time() < deadline:
                if self._cancelled():
                    outs.append("cancelled")
                    break
                try:
                    if self.is_vpn_active(skip_ui=True):
                        vpn_ok = True
                        break
                except Exception:
                    pass
                try:
                    xml = self.adb.uiautomator_dump(force=True) or ""
                    low = (xml or "").lower()
                    # 无 profile / Please select：禁止继续点 FAB，交给上层导入
                    if "please select a profile" in low or (
                        profile_name
                        and not self.nekobox_profile_visible_in_ui(profile_name, xml=xml)
                        and self.nekobox_pkg.lower() in (self.current_foreground_pkg() or "").lower()
                    ):
                        outs.append("wait_abort_no_profile")
                        outs.append("need_import")
                        self._log(log, f"NekoBox 等待 tun 时发现无 profile={profile_name}，中止点 Connect")
                        vpn_ok = False
                        break
                    # 优先处理系统 VPN 授权（绝不能 HOME）
                    if self._is_vpn_consent_pkg(self.current_foreground_pkg()) or self._xml_looks_like_vpn_consent(xml):
                        hitc = self.handle_vpn_consent_dialog(xml, log=log)
                        outs.append(f"consent_wait={hitc or 'miss'}")
                        time.sleep(1.0)
                        continue
                    if 'content-desc="stop"' in low or "connected, tap" in low:
                        time.sleep(1.0)
                        if self.is_vpn_active(skip_ui=True):
                            vpn_ok = True
                            break
                    else:
                        # 先 Allow/OK，再 Connect/FAB
                        hit = self.adb.tap_any(
                            ["Allow", "OK", "允许", "确定", "I trust this application", "Trust"],
                            xml=xml,
                            match_desc=True,
                            match_text=True,
                        )
                        if hit:
                            outs.append(f"wait_perm={hit}")
                            time.sleep(1.0)
                            continue
                        hit2 = self.adb.tap_any(
                            ["Connect", "连接"],
                            xml=xml,
                            match_desc=True,
                            match_text=True,
                        )
                        if not hit2:
                            b = self.adb.find_node_bounds(resource_id="moe.nb4a:id/fab", xml=xml)
                            if b and self.nekobox_pkg.lower() in self.current_foreground_pkg().lower():
                                self.adb.tap_bounds(b)
                                outs.append("wait_fab")
                except Exception:
                    pass
                time.sleep(1.3)
            if vpn_ok:
                break
            self._log(log, f"NekoBox round={round_i} 未检测到 tun，重试 Connect")

        outs.append(f"vpn_active={vpn_ok}")
        self._log(log, f"NekoBox VPN active={vpn_ok} profile={profile_name}")
        # 若仍卡在 VPN 授权，最后再试点 OK，不要 HOME 掉授权窗
        try:
            if not vpn_ok and (
                self._is_vpn_consent_pkg(self.current_foreground_pkg())
                or self._xml_looks_like_vpn_consent(self.adb.uiautomator_dump(force=True) or "")
            ):
                hitc = self.handle_vpn_consent_dialog(log=log)
                outs.append(f"consent_final={hitc or 'miss'}")
                time.sleep(1.5)
                if self.is_vpn_active(skip_ui=True):
                    vpn_ok = True
                    outs.append("vpn_active=True")
        except Exception as exc:
            outs.append(f"consent_final_err={exc}")
        try:
            # 仅当不在授权窗时回桌面
            if not self._is_vpn_consent_pkg(self.current_foreground_pkg()):
                self.adb.shell("input", "keyevent", "3", timeout=8)
                outs.append("home_ok")
            else:
                outs.append("home_skipped_vpn_consent")
        except Exception as exc:
            outs.append(f"home_err={exc}")
        try:
            self.adb.release_ui_control(home=False)
            outs.append("ui_release")
        except Exception:
            pass
        return " | ".join(outs)[:900]

    def setup_nekobox_socks5(
        self,
        profile_name: str,
        host: str,
        port: int,
        username: str,
        password: str,
        *,
        log: LogFn = None,
        verify_vpn: bool = True,
        vpn_wait_seconds: float = 20.0,
        write_json_backup: bool = False,
    ) -> str:
        """添加/校验 SOCKS5 后启动 VPN。

        要点（用户要求）:
        1) 每次打开先 Stop + 删除列表全部旧 profile，再只导入当前分配代理
        2) socks:// URI 导入直接带 Username/Password（NekoBox 不支持 socks5://）
        3) 开启 VPN 前必须 auth 校验
        4) 改配置：先 Stop，再导入/修复，再 Connect（改后重开才生效）
        5) UI 填 Username 仅导入失败兜底；绝不 force-stop NekoBox
        """
        outs: list[str] = [f"profile={profile_name}"]
        if not self.is_nekobox_installed():
            self._log(log, "NekoBox 未安装，中止 setup（请先 ensure_packages）")
            outs.append("nekobox_not_installed_abort")
            return " | ".join(outs)[:900]
        self._log(
            log,
            f"NekoBox setup profile={profile_name} {host}:{port} "
            f"user={(username or '')[:40]} uri={self._socks_uri_log_safe(profile_name, host, port, username, password)}",
        )

        # 1) 打开 NekoBox
        try:
            self.adb.shell(
                "am",
                "start",
                "-n",
                f"{self.nekobox_pkg}/io.nekohasekai.sagernet.ui.MainActivity",
                timeout=15,
            )
            time.sleep(0.8)
            outs.append("opened")
            self._log(log, "NekoBox 已打开 MainActivity")
        except Exception as exc:
            outs.append(f"open_err={exc}")
            self._log(log, f"NekoBox 打开失败: {exc}")

        # 2) 可选 JSON 备份（不参与 VPN 启用）
        if write_json_backup:
            try:
                outs.append(
                    "add_cfg="
                    + self._write_nekobox_config_files(
                        profile_name, host, port, username, password
                    )
                )
            except Exception as exc:
                outs.append(f"add_cfg_err={exc}")

        # 3) 每次打开都先清空旧代理再按当前分配导入（force_reimport=True）
        #    ensure_auth_then_connect 内：Stop -> wipe_all -> URI import -> Connect
        try:
            self._log(
                log,
                f"NekoBox 每次打开：清空全部旧 profile 后导入当前代理 profile={profile_name}",
            )
            core = self.ensure_auth_then_connect(
                profile_name,
                host,
                int(port),
                username,
                password,
                log=log,
                verify_vpn=verify_vpn,
                vpn_wait_seconds=vpn_wait_seconds,
                force_reimport=True,
            )
            outs.append(core)
        except Exception as exc:
            outs.append(f"ensure_auth_connect_err={exc}")
            self._log(log, f"NekoBox ensure_auth_then_connect 失败: {exc}")

        # 4) HOME，保持 VPN 后台（绝不 force-stop NekoBox）
        try:
            time.sleep(0.3)
            self.adb.shell("input", "keyevent", "3", timeout=8)
            outs.append("home_ok")
        except Exception as exc:
            outs.append(f"home_err={exc}")
        try:
            self.adb.release_ui_control(home=False)
            outs.append("ui_release")
        except Exception:
            pass

        return " | ".join(outs)[:900]



    def provision_new_vm(
        self,
        vmindex: int,
        *,
        log: LogFn = None,
        boot_timeout: int = 240,
        install_packages: dict | None = None,
        prefer_aurora_venmo: bool = False,
        restart_after_module: bool = True,
    ) -> dict[str, str]:
        """新建模拟器启动后一键装包/ROOT/模块/Venmo（不含 SOCKS 登录）。

        顺序：
        1) 按 UI 勾选装 Kitsune / NekoBox / Aurora
        2) Kitsune Magisk Direct Install (modify /system directly)
        3) Zygisk + MagiskHide + Enforce SuList
        4) Modules: Install from storage -> ih8SecureLock-v8.zip
        5) 仅用模拟器 restart device 重启
        6) 缺包再装；Venmo 完整 split（勾选 Aurora 时优先走 Aurora 商店）
        """
        import time as _time
        from core.venmo_install import ensure_aurora, ensure_venmo_ready

        opts = dict(install_packages or {})
        want_kitsune = bool(opts.get("kitsune", True))
        want_nekobox = bool(opts.get("nekobox", True))
        want_ih8 = bool(opts.get("ih8", True))
        want_aurora = bool(opts.get("aurora", False))
        want_venmo = bool(opts.get("venmo", True))
        out: dict[str, str] = {"vmindex": str(vmindex)}

        self._log(log, f"VM={vmindex} provision 开始 opts={opts}")
        if self._cancelled():
            out["status"] = "cancelled"
            self._log(log, f"VM={vmindex} provision 已取消(开始前)")
            return out
        try:
            self.adb.lock_portrait()
        except Exception as exc:
            out["portrait"] = f"err:{exc}"

        if self._cancelled():
            out["status"] = "cancelled"
            return out
        # 新建机首启：先等 MuMu Store 同步完成，再装包/Kitsune
        try:
            out["mumu_store"] = self.wait_mumu_store_sync(
                log=log,
                timeout=min(240, max(60, int(boot_timeout))),
                idle_stable_seconds=4.0,
                force_close_after=True,
            )
        except Exception as exc:
            out["mumu_store"] = f"err:{exc}"
            try:
                self.dismiss_mumu_store(log=log)
            except Exception:
                pass

        if self._cancelled():
            out["status"] = "cancelled"
            self._log(log, f"VM={vmindex} provision 已取消(MuMu Store后)")
            return out
        out.update(
            self.ensure_packages(
                vmindex,
                install_nekobox=want_nekobox,
                install_kitsune=want_kitsune,
                install_ih8=want_ih8,
                install_venmo=want_venmo,
                install_aurora=want_aurora,
                prefer_aurora_venmo=bool(prefer_aurora_venmo),
                log=log,
            )
        )

        if self._cancelled():
            out["status"] = "cancelled"
            self._log(log, f"VM={vmindex} provision 已取消(装包后)")
            return out
        if want_aurora:
            try:
                ok_a = ensure_aurora(self.adb, log=log)
                out["aurora"] = "ok" if ok_a else "fail"
            except Exception as exc:
                out["aurora"] = f"err:{exc}"
        else:
            out["aurora"] = "skipped_by_ui"

        rebooted = False
        mag: dict = {}
        if want_kitsune:
            if self._cancelled():
                out["status"] = "cancelled"
                self._log(log, f"VM={vmindex} provision 已取消(Kitsune前)")
                return out
            try:
                # 新建：一次会话完成 DirectInstall + Shell授权 + Settings三项 + ih8
                # 见 Uninstall Magisk 后直接授权，中途不 force-stop Magisk 再重开
                mag = self.ensure_kitsune_magisk_direct_install(
                    vmindex,
                    log=log,
                    boot_timeout=boot_timeout,
                    configure_settings=True,
                    install_ih8=bool(want_ih8),
                )
                out["magisk"] = str(mag)[:400]
                rebooted = bool(mag.get("rebooted"))
            except Exception as exc:
                out["magisk"] = f"err:{exc}"
                mag = {}
            if rebooted:
                out.update(
                    self.ensure_packages(
                        vmindex,
                        install_nekobox=want_nekobox,
                        install_kitsune=want_kitsune,
                        install_ih8=want_ih8,
                        install_venmo=want_venmo,
                        install_aurora=want_aurora,
                        prefer_aurora_venmo=bool(prefer_aurora_venmo),
                        log=log,
                    )
                )
            # 已在一次会话完成则绝不重复 force-stop 再开做 flags/grant
            if mag.get("settings_done"):
                out["kitsune_flags"] = "already_done_in_one_session"
            else:
                try:
                    out["kitsune_flags"] = self.configure_kitsune_flags(log=log, reuse_session=True)
                except Exception as exc:
                    out["kitsune_flags"] = f"err:{exc}"
            if mag.get("grant"):
                out["shell_su"] = str(mag.get("grant"))[:200]
            elif mag.get("installed") or mag.get("skipped_cached"):
                out["shell_su"] = "already_done_in_one_session_or_cached"
            else:
                try:
                    # GRANT popup first; Superuser only if popup incomplete
                    popup = self.grant_shell_prefer_popup(log=log)
                    if str(popup).startswith("popup_grant_ok") or "uid=0" in str(popup):
                        out["shell_su"] = str(popup)[:200]
                        self._log(log, f"VM={vmindex} provision Shell GRANT弹窗成功")
                    else:
                        g = self.grant_shell_via_kitsune_superuser(log=log, reuse_session=True)
                        out["shell_su"] = f"{popup}||superuser={g}"[:200]
                        self._log(log, f"VM={vmindex} provision Shell Superuser兜底")
                except Exception as exc:
                    out["shell_su"] = f"err:{exc}"
        else:
            out["magisk"] = "skipped_by_ui"
            out["kitsune_flags"] = "skipped_by_ui"

        if want_ih8:
            if want_kitsune and (mag.get("ih8_done") or mag.get("ih8")):
                out["ih8"] = str(mag.get("ih8") or "already_done_in_one_session")
                ih8s = str(out["ih8"])
                restarted = "|restart=ok" in ih8s or bool(mag.get("rebooted"))
                out["restart_after_ih8"] = (
                    "ok" if restarted
                    else ("skip" if "already" in ih8s else "none")
                )
            else:
                try:
                    # 仅一次会话未完成时才单独装；reuse_session 避免杀 Magisk
                    out["ih8"] = self.install_ih8_module(
                        log=log,
                        vmindex=vmindex,
                        restart=bool(restart_after_module),
                        boot_timeout=boot_timeout,
                        reuse_session=True,
                    )
                except Exception as exc:
                    out["ih8"] = f"err:{exc}"
                ih8s = str(out.get("ih8", ""))
                restarted = "|restart=ok" in ih8s
                out["restart_after_ih8"] = (
                    "ok" if restarted
                    else ("skip" if "|restart=skip" in ih8s else ("err" if "|restart=err" in ih8s or "|restart=timeout" in ih8s else "none"))
                )
            ih8s = str(out.get("ih8", ""))
            # 重启后只补包，不再反复打开 Kitsune 做 flags
            if restart_after_module and not ih8s.startswith("skipped") and not ih8s.startswith("err:"):
                try:
                    out.update(
                        self.ensure_packages(
                            vmindex,
                            install_nekobox=want_nekobox,
                            install_kitsune=want_kitsune,
                            install_ih8=want_ih8,
                            install_venmo=want_venmo,
                            install_aurora=want_aurora,
                            prefer_aurora_venmo=bool(prefer_aurora_venmo),
                            log=log,
                        )
                    )
                    if want_aurora:
                        try:
                            ensure_aurora(self.adb, log=log)
                        except Exception:
                            pass
                except Exception as exc:
                    out["restart_after_ih8_post"] = f"err:{exc}"
        else:
            out["ih8"] = "skipped_by_ui"

        if want_venmo:
            try:
                prefer = bool(prefer_aurora_venmo)
                vr = ensure_venmo_ready(
                    self.adb,
                    log=log,
                    prefer_aurora=prefer,
                )
                out["venmo"] = (
                    f"ok={vr.get('ok')} method={vr.get('method')} "
                    f"splits={((vr.get('info') or {}).get('split_count'))}"
                )[:300]
            except Exception as exc:
                out["venmo"] = f"err:{exc}"
        else:
            out["venmo"] = "skipped_by_ui"

        try:
            self.adb.release_ui_control(home=True)
        except Exception:
            pass
        self._log(log, f"VM={vmindex} provision 完成: {out}")
        return out

    def full_first_time_setup(
        self,
        vmindex: int,
        use_nekobox: bool,
        proxy,
        *,
        log: LogFn = None,
        boot_timeout: int = 240,
        install_packages: dict | None = None,
    ) -> dict[str, str]:
        """首次：按 UI 勾选装包 -> Magisk Direct Install -> 模块/开关 -> NekoBox。"""
        opts = dict(install_packages or {})
        want_kitsune = bool(opts.get("kitsune", True))
        want_nekobox = bool(opts.get("nekobox", True)) and bool(use_nekobox)
        want_ih8 = bool(opts.get("ih8", True))
        out: dict[str, str] = {}
        out.update(
            self.ensure_packages(
                vmindex,
                install_nekobox=want_nekobox,
                install_kitsune=want_kitsune,
                install_ih8=want_ih8,
            )
        )

        mag: dict = {}
        if want_kitsune:
            # 新建完整 setup：一次会话完成 DirectInstall后的 Shell+Settings+ih8
            mag = self.ensure_kitsune_magisk_direct_install(
                vmindex,
                log=log,
                boot_timeout=boot_timeout,
                configure_settings=True,
                install_ih8=want_ih8,
            )
            out["magisk"] = str(mag)[:400]
            if mag.get("rebooted"):
                out.update(
                    self.ensure_packages(
                        vmindex,
                        install_nekobox=want_nekobox,
                        install_kitsune=want_kitsune,
                        install_ih8=want_ih8,
                    )
                )
            if mag.get("settings_done"):
                out["kitsune_flags"] = "already_done_in_one_session"
            elif mag.get("installed") and not mag.get("skipped_cached"):
                out["kitsune_flags"] = self.configure_kitsune_flags(log=log)
            elif mag.get("skipped_cached"):
                if self.is_kitsune_settings_done(vmindex):
                    out["kitsune_flags"] = "skipped_cached_flags_already_set"
                else:
                    try:
                        sess = self.complete_kitsune_post_install_session(
                            vmindex,
                            log=log,
                            configure_settings=True,
                            install_ih8=want_ih8,
                            restart_after_ih8=True,
                            boot_timeout=boot_timeout,
                            force_relaunch_once=True,
                        )
                        out["kitsune_flags"] = str(sess.get("settings") or sess.get("detail") or "one_session")
                        if sess.get("settings_done"):
                            self.mark_kitsune_done(
                                vmindex,
                                str(mag.get("detail") or "flags_after_cached"),
                                settings_ok=True,
                            )
                        if sess.get("ih8_done") or sess.get("ih8"):
                            mag["ih8_done"] = True
                            mag["ih8"] = sess.get("ih8")
                    except Exception as exc:
                        out["kitsune_flags"] = f"cached_flags_err:{exc}"
            else:
                out["kitsune_flags"] = "skipped_not_installed"
        else:
            out["magisk"] = "skipped_by_ui"
            out["kitsune_flags"] = "skipped_by_ui"

        if want_ih8:
            if want_kitsune and mag.get("ih8_done"):
                out["ih8"] = str(mag.get("ih8") or "already_done_in_one_session")
                out["restart_after_ih8"] = (
                    "ok" if "|restart=ok" in str(out["ih8"])
                    else ("skip" if "already" in str(out["ih8"]) else "none")
                )
            else:
                out["ih8"] = self.install_ih8_module(
                    log=log,
                    vmindex=vmindex,
                    restart=True,
                    boot_timeout=boot_timeout,
                )
                out["restart_after_ih8"] = (
                    "ok" if "|restart=ok" in str(out["ih8"])
                    else ("skip" if "|restart=skip" in str(out["ih8"]) else "none")
                )
        else:
            out["ih8"] = "skipped_by_ui"

        if want_nekobox and proxy is not None:
            out["nekobox_proxy"] = self.setup_nekobox_socks5(
                proxy.profile_name,
                proxy.host,
                proxy.port,
                proxy.username,
                proxy.password,
                log=log,
                verify_vpn=True,
            )
        return out

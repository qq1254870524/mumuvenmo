# 2026-08-11 cancellable-install-v1: Aurora/Venmo 全部等待可被强停打断，杜绝关机后继续刷 ADB 日志
# 2026-07-31 play-sign-in-bail-v1: Aurora 误进 Play 登录页立即退出，禁止空转 420s 挡住 Magisk 后半段
# -*- coding: utf-8 -*-
"""Venmo 安装：禁止单包 base.apk，优先完整 split install-multiple，其次 Aurora Store。

更新 2026-07-24 aurora-anonymous-v6:
- 系统安装确认弹窗 text 为 INSTALL/CANCEL（全大写），精确匹配改为大小写不敏感
- 下载/安装中禁止误点 Open；Preparing/Installing 只等待
- App links 永不点击；权限前三项 Grant 后直接 Finish；Anonymous 登录
- 匿名进入后再 market/search 安装完整 Venmo split

更新 2026-07-24 aurora-anonymous-v5:
- Aurora 首次必须走 Welcome -> 权限 Grant -> Finish -> 选择 Anonymous（不要 Google 登录）
- 权限页文字含 Allow installing...，禁止误点描述文字，只点精确 Grant/Finish/Anonymous
- 匿名进入后再 market/search 安装完整 Venmo split

更新 2026-07-24:
- 单独 adb install venmo base.apk 会闪退(Venmo keeps stopping)，缺 split_config.*
- 从完好机拉取 base + en + x86_64 + xxxhdpi，使用 install-multiple
- 已安装但只有 base split 时先卸载再装完整包
- AuroraStore-4.8.3.apk 作为兜底引导安装入口
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Callable, Optional

from paths import APK_DIR

OptionalLog = Optional[Callable[[str], None]]


class VenmoInstallCancelled(BaseException):
    """安装/商店流程收到任务取消；BaseException 可穿透业务层 except Exception。"""


def _cancel_requested(adb) -> bool:
    try:
        fn = getattr(adb, "cancel_requested", None)
        if callable(fn):
            return bool(fn())
        fn = getattr(adb, "_cancel_requested", None)
        return bool(fn()) if callable(fn) else False
    except Exception:
        return False


def _raise_if_cancelled(adb, where: str = "") -> None:
    if _cancel_requested(adb):
        raise VenmoInstallCancelled(
            f"venmo_install_cancelled:{where}" if where else "venmo_install_cancelled"
        )


def _sleep(adb, seconds: float) -> None:
    """最多 0.1 秒响应一次取消，替代安装流程中不可中断的 time.sleep。"""
    deadline = time.monotonic() + max(0.0, float(seconds))
    while True:
        _raise_if_cancelled(adb, "sleep")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(0.1, remaining))

VENMO_PKG = "com.venmo"
AURORA_PKG = "com.aurora.store"
AURORA_APK = APK_DIR / "AuroraStore-4.8.3.apk"
VENMO_BUNDLE_DIR = APK_DIR / "venmo_bundle"
REQUIRED_SPLITS = (
    "base.apk",
    "split_config.en.apk",
    "split_config.x86_64.apk",
    "split_config.xxxhdpi.apk",
)


def _log(log: OptionalLog, msg: str) -> None:
    if log:
        try:
            log(msg)
        except Exception:
            pass


def bundle_files() -> list[Path]:
    files = []
    for name in REQUIRED_SPLITS:
        p = VENMO_BUNDLE_DIR / name
        if p.exists() and p.stat().st_size > 1000:
            files.append(p)
    return files


def venmo_split_info(adb) -> dict:
    """返回 installed / paths / has_base / split_count / complete。"""
    _raise_if_cancelled(adb, "venmo_split_info")
    out = adb.shell("pm", "path", VENMO_PKG, timeout=20) or ""
    paths = []
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("package:"):
            paths.append(line[8:])
    has_base = any(p.endswith("/base.apk") or p.endswith("base.apk") for p in paths)
    has_abi = any("x86_64" in p or "arm64" in p or "armeabi" in p for p in paths)
    has_dpi = any("xxxhdpi" in p or "xxhdpi" in p or "xhdpi" in p or "hdpi" in p for p in paths)
    complete = len(paths) >= 3 and has_base and (has_abi or has_dpi)
    return {
        "installed": bool(paths),
        "paths": paths,
        "split_count": len(paths),
        "has_base": has_base,
        "complete": complete,
        "raw": out[:300],
    }


def uninstall_venmo(adb, log: OptionalLog = None) -> str:
    _raise_if_cancelled(adb, "uninstall_venmo")
    _log(log, "uninstall incomplete com.venmo")
    try:
        msg = adb.shell("pm", "uninstall", VENMO_PKG, timeout=60) or ""
    except Exception as e:
        msg = str(e)
    _log(log, f"uninstall -> {msg[:120]}")
    return msg


def install_venmo_bundle(adb, log: OptionalLog = None) -> dict:
    _raise_if_cancelled(adb, "install_venmo_bundle")
    files = bundle_files()
    if len(files) < 3:
        return {"ok": False, "method": "bundle", "msg": f"bundle incomplete count={len(files)}"}
    _log(log, f"install-multiple venmo splits n={len(files)}")
    try:
        if hasattr(adb, "install_multiple"):
            msg = (adb.install_multiple(files, replace=True) or "").strip()
        else:
            args = ["install-multiple", "-r"] + [str(f) for f in files]
            cp = adb._run(args, timeout=600)
            msg = ((cp.stdout or "") + (cp.stderr or "")).strip()
    except Exception as e:
        msg = str(e)
    info = venmo_split_info(adb)
    ok = info.get("complete") or ("Success" in msg)
    _log(log, f"install-multiple -> {msg[:160]} complete={info.get('complete')} splits={info.get('split_count')}")
    return {"ok": bool(ok), "method": "bundle", "msg": msg[:300], "info": info}


def ensure_aurora(adb, log: OptionalLog = None) -> bool:
    _raise_if_cancelled(adb, "ensure_aurora")
    if adb.package_installed(AURORA_PKG):
        _log(log, "Aurora Store already installed")
        return True
    if not AURORA_APK.exists():
        _log(log, f"missing Aurora apk: {AURORA_APK}")
        return False
    _log(log, f"install Aurora Store: {AURORA_APK.name}")
    msg = adb.install(AURORA_APK)
    _log(log, f"install aurora -> {str(msg)[:160]}")
    return adb.package_installed(AURORA_PKG)


def _dump_xml(adb) -> str:
    _raise_if_cancelled(adb, "dump_xml")
    try:
        return adb.uiautomator_dump(force=True) or ""
    except Exception:
        return ""


def _dump_text(adb) -> str:
    _raise_if_cancelled(adb, "dump_text")
    try:
        return (adb.ui_full_text() or "").lower()
    except Exception:
        return ""


def _tap_exact_text(adb, label: str, xml: str = "", y_min: int = 0, y_max: int = 99999) -> bool:
    """精确 text 匹配点击，避免 'Allow installing...' 误命中 Allow。

    系统 packageinstaller 弹窗按钮是 INSTALL/CANCEL 全大写，故比较忽略大小写；
    仍要求整段 text/content-desc 完全相等（忽略大小写），不会命中 'Allow installing...'。
    """
    xml = xml or _dump_xml(adb)
    label = (label or "").strip()
    if not label:
        return False
    label_l = label.lower()
    patterns = [
        r'text="([^"]+)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
        r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*text="([^"]+)"',
        r'content-desc="([^"]+)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
        r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*content-desc="([^"]+)"',
    ]
    for pat in patterns:
        for m in re.finditer(pat, xml, re.I):
            groups = m.groups()
            if pat.startswith("text=") or pat.startswith("content-desc="):
                t = (groups[0] or "").strip()
                b = tuple(map(int, groups[1:5]))
            else:
                b = tuple(map(int, groups[0:4]))
                t = (groups[4] or "").strip()
            if t.lower() != label_l:
                continue
            cy = (b[1] + b[3]) // 2
            if cy < y_min or cy > y_max:
                continue
            adb.tap_bounds(b)
            return True
    return False


def _tap_first_exact(adb, labels: list[str], xml: str = "") -> str:
    xml = xml or _dump_xml(adb)
    for lab in labels:
        if _tap_exact_text(adb, lab, xml=xml):
            return lab
    return ""


def _iter_switches(xml: str):
    """解析 UI dump 中的 Switch 节点 (checked, bounds)。"""
    for na in re.findall(r"<node\b([^>]*)/?>", xml):
        if "Switch" not in na and "switch" not in na and "CheckBox" not in na:
            # also android.widget.Switch via class=
            if 'class="' in na and "Switch" not in na and "CheckBox" not in na:
                continue
        if "Switch" not in na and "CheckBox" not in na:
            continue
        bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', na)
        if not bm:
            continue
        b = tuple(map(int, bm.groups()))
        checked = 'checked="true"' in na
        yield checked, b, na


def _enable_right_switch(adb, xml: str = "") -> str:
    xml = xml or _dump_xml(adb)
    for checked, b, na in _iter_switches(xml):
        if checked:
            return "already_on"
        adb.tap_bounds(b)
        _sleep(adb, 0.5)
        return "toggled_on"
    # 有些页 Switch 写成 Checkable Image/View，点右侧区域
    m = re.search(
        r'text="(?:Allow access to manage all files|Allow from this source|允许来自此来源|允许管理所有文件)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
        xml,
        re.I,
    )
    if m:
        x1, y1, x2, y2 = map(int, m.groups())
        # 行右侧开关大概在屏幕右 85%
        adb.tap(int(x2 + (x2 - x1) * 0.2 + 80), (y1 + y2) // 2)
        return "tap_row_right"
    return "no_switch"


def _handle_settings_permission_pages(adb, log: OptionalLog = None, rounds: int = 6) -> str:
    """处理 All files / Unknown apps；可选 App links 直接返回。"""
    notes = []
    for i in range(rounds):
        xml = _dump_xml(adb)
        texts = [t.strip() for t in re.findall(r'text="([^"]+)"', xml) if t and t.strip()]
        low = " ".join(texts).lower()
        # 仍在 Aurora 权限列表则结束
        if "installer permission" in low or ("permissions" in low and "aurora store requires" in low):
            break
        # 可选：Open supported links / App links —— 不需要开启，直接 BACK
        if any(k in low for k in (
            "open supported links",
            "allow web links",
            "verified links",
            "add link",
            "opening links",
            "supported links",
        )):
            notes.append(f"applinks_back{i}")
            _log(log, f"app links page -> BACK ui={low[:80]!r}")
            adb.shell("input", "keyevent", "4", timeout=5)
            _sleep(adb, 0.7)
            continue
        # 必须：All files / Unknown apps
        if any(k in low for k in (
            "all files access",
            "allow access to manage all files",
            "install unknown apps",
            "unknown apps",
            "allow from this source",
            "特殊应用权限",
            "所有文件",
            "未知应用",
        )):
            r = _enable_right_switch(adb, xml)
            notes.append(f"sw{i}:{r}")
            _log(log, f"settings page switch -> {r} ui={low[:80]!r}")
            _sleep(adb, 0.7)
            xml2 = _dump_xml(adb)
            for lab in ("Allow", "ALLOW", "OK", "允许", "确定"):
                if _tap_exact_text(adb, lab, xml=xml2):
                    notes.append(f"confirm:{lab}")
                    _sleep(adb, 0.5)
                    break
            adb.shell("input", "keyevent", "4", timeout=5)
            _sleep(adb, 0.7)
            continue
        # 其它系统设置页：尝试开开关，否则 BACK
        if "settings" in low or "android" in low:
            r = _enable_right_switch(adb, xml)
            if r != "no_switch":
                notes.append(f"misc_sw{i}:{r}")
                _sleep(adb, 0.5)
            notes.append(f"misc_back{i}")
            adb.shell("input", "keyevent", "4", timeout=5)
            _sleep(adb, 0.7)
            continue
        break
    return ",".join(notes) if notes else "none"


def _grant_unknown_sources(adb, log: OptionalLog = None) -> str:
    """Settings 里允许 Aurora 安装未知应用。"""
    notes = []
    try:
        adb.shell(
            "am",
            "start",
            "-a",
            "android.settings.MANAGE_UNKNOWN_APP_SOURCES",
            "-d",
            f"package:{AURORA_PKG}",
            timeout=15,
        )
        _sleep(adb, 1.2)
        notes.append(_handle_settings_permission_pages(adb, log=log, rounds=3))
        # 再确保开关
        xml = _dump_xml(adb)
        r = _enable_right_switch(adb, xml)
        notes.append(r)
        _sleep(adb, 0.5)
        adb.shell("input", "keyevent", "4", timeout=5)
    except Exception as e:
        notes.append(f"err:{e}")
    _log(log, "unknown sources: " + ",".join(notes))
    return ",".join(notes)


def _tap_grant_near_label(adb, label_keywords: list[str], xml: str = "") -> bool:
    """点某个权限标题同一行/下方附近的 Grant。"""
    xml = xml or _dump_xml(adb)
    # collect text nodes with bounds
    nodes = []
    for m in re.finditer(
        r'text="([^"]+)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
        xml,
        re.I,
    ):
        nodes.append((m.group(1).strip(), tuple(map(int, m.groups()[1:]))))
    for m in re.finditer(
        r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*text="([^"]+)"',
        xml,
        re.I,
    ):
        nodes.append((m.group(5).strip(), tuple(map(int, m.groups()[:4]))))
    targets = []
    for t, b in nodes:
        tl = t.lower()
        if any(k.lower() in tl for k in label_keywords):
            targets.append((t, b))
    grants = [(t, b) for t, b in nodes if t in ("Grant", "GRANT", "授权")]
    for _, tb in targets:
        ty = (tb[1] + tb[3]) // 2
        # same row-ish grant to the right
        best = None
        best_score = 1e18
        for gt, gb in grants:
            gy = (gb[1] + gb[3]) // 2
            if abs(gy - ty) > 220:
                continue
            score = abs(gy - ty) + max(0, tb[0] - gb[0])
            if score < best_score:
                best_score = score
                best = gb
        if best:
            adb.tap_bounds(best)
            return True
    return False


def setup_aurora_anonymous(adb, log: OptionalLog = None, max_steps: int = 28) -> str:
    """完成 Aurora 首次引导并强制选择 Anonymous。

    实测 Aurora 4.8.3:
    Welcome -> Next
    Permissions: 前三项 Grant(Installer / External storage / Background downloads) -> Finish；App links 不点
    账号页: 点 Anonymous（不要 Google）
    """
    _raise_if_cancelled(adb, "setup_aurora_anonymous")
    notes: list[str] = []
    anonymous_done = False
    for step in range(max_steps):
        xml = _dump_xml(adb)
        texts = [t.strip() for t in re.findall(r'text="([^"]+)"', xml) if t and t.strip()]
        low = " ".join(texts).lower()
        _log(log, f"Aurora setup step{step}: {low[:180]!r}")

        # 已在主页
        if any(k in low for k in ("for you", "games", "search apps", "updates", "library", "apps & games")) and "anonymous" not in low and "welcome" not in low and "permissions" not in low and "how you doing" not in low:
            notes.append("main")
            break

        # 优先 Anonymous
        if "anonymous" in low or "匿名" in low or any(x in texts for x in ("Anonymous", "匿名")):
            hit = _tap_first_exact(adb, ["Anonymous", "匿名"], xml)
            if hit:
                notes.append(f"anon:{hit}")
                anonymous_done = True
                _sleep(adb, 2.2)
                continue

        # 系统设置页
        if (
            any(k in low for k in (
                "all files access",
                "allow access to manage all files",
                "install unknown apps",
                "allow from this source",
                "open supported links",
                "allow web links",
                "verified links",
                "所有文件",
                "未知应用",
            ))
            and "installer permission" not in low
            and "aurora store requires" not in low
        ):
            r = _handle_settings_permission_pages(adb, log=log, rounds=4)
            notes.append("settings:" + r)
            _sleep(adb, 0.8)
            continue

        # 权限页：前三项 Grant 完直接 Finish；App links 永远不点
        # 1 Installer permission  2 External storage manager  3 Background downloads
        if "permissions" in low or "installer permission" in low or "external storage manager" in low:
            # 已看到 Finish 且前三项看起来已处理 -> 直接完成
            need_labels = [
                (["Installer permission", "安装程序权限"], "installer"),
                (["External storage manager", "External storage", "外部存储"], "storage"),
                (["Background downloads", "后台下载", "Background"], "background"),
            ]
            # 统计当前页还剩哪些 Grant（排除 App links 行附近）
            def _label_still_needs_grant(label_keys: list[str]) -> bool:
                # 找标题 y，看附近是否有 Grant 文本（不是 Granted）
                nodes = []
                for m in re.finditer(
                    r'text="([^"]+)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                    xml, re.I,
                ):
                    nodes.append((m.group(1).strip(), tuple(map(int, m.groups()[1:]))))
                title_ys = []
                for t, b in nodes:
                    tl = t.lower()
                    if any(k.lower() in tl for k in label_keys):
                        title_ys.append((b[1] + b[3]) // 2)
                if not title_ys:
                    return False
                for t, b in nodes:
                    if t not in ("Grant", "GRANT"):
                        continue
                    gy = (b[1] + b[3]) // 2
                    if any(abs(gy - ty) <= 220 for ty in title_ys):
                        return True
                return False

            # 绝不点 App links 的 Grant
            for keys, tag in need_labels:
                if _label_still_needs_grant(keys):
                    if _tap_grant_near_label(adb, keys, xml):
                        notes.append(f"grant:{tag}")
                        _sleep(adb, 1.5)
                        r = _handle_settings_permission_pages(adb, log=log, rounds=4)
                        if r != "none":
                            notes.append(r)
                        # 系统弹窗
                        xml3 = _dump_xml(adb)
                        for lab in (
                            "While using the app",
                            "Allow all the time",
                            "Allow only while using the app",
                            "仅在使用该应用时允许",
                            "始终允许",
                            "OK",
                            "允许",
                            "Allow",
                            "ALLOW",
                        ):
                            # 避免权限介绍页误点
                            t3 = " ".join(re.findall(r'text="([^"]+)"', xml3)).lower()
                            if lab in ("Allow", "ALLOW", "允许") and "installer permission" in t3:
                                continue
                            if _tap_exact_text(adb, lab, xml=xml3):
                                notes.append(f"sys:{lab}")
                                _sleep(adb, 0.8)
                                break
                        break  # 每轮只处理一项
            else:
                # 前三项都没有待点 Grant -> Finish（忽略 App links）
                if _tap_exact_text(adb, "Finish", xml=xml) or _tap_exact_text(adb, "FINISH", xml=xml) or _tap_exact_text(adb, "完成", xml=xml):
                    notes.append("finish")
                    _sleep(adb, 1.8)
                else:
                    # Finish 可能因 required 未完成灰掉，再兜底 Grant 非 App links
                    if _tap_grant_near_label(adb, ["Installer permission", "External storage", "Background downloads"], xml):
                        notes.append("grant:retry_non_applinks")
                        _sleep(adb, 1.5)
                        _handle_settings_permission_pages(adb, log=log, rounds=4)
                    else:
                        notes.append("finish_miss")
            continue

        # Welcome
        if "welcome" in low or "how you doing" in low:
            hit = _tap_first_exact(adb, ["Next", "Skip", "下一步", "跳过"], xml)
            if hit:
                notes.append(hit)
                _sleep(adb, 1.2)
                continue

        # 账号选择页可能用 Google / Anonymous 卡片
        if "google" in low and ("anonymous" in low or "登录" in low or "account" in low or "login" in low):
            if _tap_first_exact(adb, ["Anonymous", "匿名"], xml):
                anonymous_done = True
                notes.append("anon:account_page")
                _sleep(adb, 2.0)
                continue
            notes.append("account_page_no_anon")

        # 通用前进（避开 Google）
        hit = _tap_first_exact(
            adb,
            [
                "Next",
                "Continue",
                "Got it",
                "I understand",
                "I agree",
                "Agree",
                "OK",
                "Done",
                "Get started",
                "Start",
                "Finish",
            ],
            xml,
        )
        if hit:
            notes.append(hit)
            _sleep(adb, 1.2)
            continue

        if "session installer" in low or "native installer" in low:
            hit = _tap_first_exact(adb, ["Session Installer", "Save", "保存", "Apply", "Done", "OK"], xml)
            if hit:
                notes.append(hit)
                _sleep(adb, 1.0)
                continue

        notes.append(f"stuck:{low[:40]}")
        break

    if not anonymous_done:
        xml = _dump_xml(adb)
        if _tap_first_exact(adb, ["Anonymous", "匿名"], xml):
            anonymous_done = True
            notes.append("anon:late")
        _sleep(adb, 2.0)

    low = _dump_text(adb)
    if anonymous_done and any(k in low for k in ("for you", "apps", "search", "updates", "library")):
        status = "ok_anonymous_main"
    elif anonymous_done:
        status = "ok_anonymous"
    elif any(k in low for k in ("for you", "apps", "search", "updates", "library")):
        status = "ok_main"
    else:
        status = "ok_maybe"
    _log(log, f"Aurora anonymous setup -> {status} notes={';'.join(notes)[:220]}")
    return status + ":" + ";".join(notes)[:260]


def open_aurora_for_venmo(adb, log: OptionalLog = None) -> str:
    """通过 Aurora Store 匿名模式安装完整 Venmo split。

    步骤：
    1) 安装/打开 Aurora
    2) 强制 Anonymous（不走 Google）
    3) 权限 Grant/Finish / 未知应用
    4) market://details?id=com.venmo 或搜索 Venmo
    5) Install/Update，等完整 split
    """
    _raise_if_cancelled(adb, "open_aurora_for_venmo")
    ensure_aurora(adb, log=log)
    notes: list[str] = []
    try:
        adb.lock_portrait()
    except Exception:
        pass

    def tap_labels(labels: list[str]) -> str:
        xml = _dump_xml(adb)
        hit = _tap_first_exact(adb, labels, xml)
        if hit:
            return hit
        # 子串兜底（仅搜索/安装按钮）
        for lab in labels:
            try:
                b = adb.find_node_bounds(text_substr=lab, xml=xml)
                if b:
                    adb.tap_bounds(b)
                    return lab
            except Exception:
                pass
            try:
                b = adb.find_node_bounds(content_desc=lab, xml=xml)
                if b:
                    adb.tap_bounds(b)
                    return lab
            except Exception:
                pass
        return ""

    def dismiss_runtime() -> str:
        """安装过程中的系统弹窗；不处理 Welcome 描述里的 Allow。

        重点：packageinstaller 确认框是 Do you want to install this app? + INSTALL/CANCEL。
        """
        hits = []
        xml = _dump_xml(adb)
        texts = [t.strip() for t in re.findall(r'text="([^"]+)"', xml) if t and t.strip()]
        low = " ".join(texts).lower()
        # 优先 Anonymous（中途又弹出账号页）
        if "anonymous" in low or "匿名" in low:
            h = _tap_first_exact(adb, ["Anonymous", "匿名"], xml)
            if h:
                hits.append(h)
                _sleep(adb, 1.0)
                xml = _dump_xml(adb)
                texts = [t.strip() for t in re.findall(r'text="([^"]+)"', xml) if t and t.strip()]
                low = " ".join(texts).lower()
        # 系统安装确认弹窗：必须点 INSTALL（大小写不敏感）
        if "do you want to install this app" in low or (
            "packageinstaller" in xml and "install" in low and "cancel" in low
        ):
            h = _tap_first_exact(adb, ["INSTALL", "Install", "安装"], xml)
            if h:
                hits.append("sys:" + h)
                _sleep(adb, 1.2)
                return ",".join(hits)
        # 下载/安装进行中不要点 Open
        busy = any(x in low for x in (
            "preparing to download", "downloading", "installing", "queued", "pending",
            "download", "安装中", "下载",
        ))
        for lab in (
            "While using the app",
            "Allow from this source",
            "允许来自此来源",
            "Allow management of all files",
            "允许管理所有文件",
            "INSTALL",
            "Install",
            "UPDATE",
            "OK",
            "Got it",
            "Continue",
            "Done",
        ):
            if lab.lower() in low:
                # 避免在 Aurora 权限列表误点
                if lab.lower() == "install" and "installer permission" in low and "venmo" not in low:
                    continue
                # 详情页 Install 由主循环点，这里只处理系统确认等
                if lab.lower() == "install" and "do you want to install" not in low and "packageinstaller" not in xml:
                    # 若当前是 Aurora 详情页 Install 按钮，留给主循环
                    if "manual download" in low or "changelog" in low:
                        continue
                h = _tap_first_exact(adb, [lab], xml)
                if h:
                    hits.append(h)
                    _sleep(adb, 0.8)
                    xml = _dump_xml(adb)
                    texts = [t.strip() for t in re.findall(r'text="([^"]+)"', xml) if t and t.strip()]
                    low = " ".join(texts).lower()
        # 安装完成后才可 Open
        if (not busy) and ("open" in low) and ("installed" in low or "success" in low or "打开" in low):
            h = _tap_first_exact(adb, ["Open", "打开"], xml)
            if h:
                hits.append(h)
                _sleep(adb, 0.7)
        # 系统权限 Allow 仅当不像 Aurora 权限介绍页
        if ("allow" in low) and ("installer permission" not in low) and ("allow installing apps from aurora" not in low):
            h = _tap_first_exact(adb, ["Allow", "ALLOW", "允许"], xml)
            if h:
                hits.append(h)
                _sleep(adb, 0.7)
        return ",".join(hits)

    # 打开 Aurora
    try:
        adb.shell("am", "force-stop", AURORA_PKG, timeout=10)
    except Exception:
        pass
    try:
        adb.shell("monkey", "-p", AURORA_PKG, "-c", "android.intent.category.LAUNCHER", "1", timeout=20)
        notes.append("launch")
        _sleep(adb, 2.5)
    except Exception as e:
        notes.append(f"launch_err:{e}")

    setup = setup_aurora_anonymous(adb, log=log)
    notes.append(setup)
    # 未知应用源预授权
    try:
        notes.append("unknown:" + _grant_unknown_sources(adb, log=log))
        # 回到 Aurora
        adb.shell("monkey", "-p", AURORA_PKG, "-c", "android.intent.category.LAUNCHER", "1", timeout=20)
        _sleep(adb, 1.5)
        setup2 = setup_aurora_anonymous(adb, log=log, max_steps=8)
        notes.append("re:" + setup2)
    except Exception as e:
        notes.append(f"unknown_err:{e}")

    # 打开 Venmo 详情
    for args in (
        ["am", "start", "-a", "android.intent.action.VIEW", "-d", "market://details?id=com.venmo", AURORA_PKG],
        ["am", "start", "-a", "android.intent.action.SEARCH", "--es", "query", "Venmo", AURORA_PKG],
    ):
        try:
            adb.shell(*args, timeout=15)
            notes.append("intent:" + args[-2][:30])
            _sleep(adb, 2.2)
            dismiss_runtime()
            ui = _dump_text(adb)
            if "venmo" in ui or "install" in ui or "update" in ui:
                notes.append("page_hit")
                break
        except Exception as e:
            notes.append(str(e)[:60])

    ui = _dump_text(adb)
    if "venmo" not in ui:
        for lab in ("Search", "搜索", "Search apps"):
            if tap_labels([lab]):
                notes.append("tap_search")
                _sleep(adb, 0.8)
                break
        try:
            # 清空并输入
            adb.shell("input", "keyevent", "KEYCODE_CTRL_A", timeout=5)
            adb.shell("input", "text", "Venmo", timeout=10)
            adb.shell("input", "keyevent", "66", timeout=8)
            notes.append("typed_venmo")
            _sleep(adb, 2.0)
        except Exception as e:
            notes.append(f"type_err:{e}")
        try:
            b = adb.find_node_bounds(text_substr="Venmo")
            if b:
                adb.tap_bounds(b)
                notes.append("tap_result_venmo")
                _sleep(adb, 2.0)
        except Exception:
            pass

    # 安装循环（play-sign-in-bail-v1: 误进 Play 登录页立刻退出，默认最多 90s）
    deadline = time.time() + 90
    last_tap = ""
    play_signin_hits = 0
    while time.time() < deadline:
        info = venmo_split_info(adb)
        if info.get("complete"):
            _log(log, f"Aurora install complete splits={info.get('split_count')}")
            try:
                adb.release_ui_control(home=True)
            except Exception:
                pass
            return "ok:" + ";".join(notes)[:260]

        d = dismiss_runtime()
        if d:
            notes.append("d:" + d[:40])
        # 账号页再次 Anonymous
        ui = _dump_text(adb)
        # Play Store 登录页：不是 Aurora，空转无意义
        if any(k in ui for k in ("sign in", "sign-in", "add account", "google play", "使用 google 账号")) or (
            "com.android.vending" in ui and "venmo" not in ui
        ):
            play_signin_hits += 1
            notes.append("play_signin")
            try:
                adb.shell("am", "force-stop", "com.android.vending", timeout=5)
                adb.shell("input", "keyevent", "3", timeout=5)
            except Exception:
                pass
            if play_signin_hits >= 2:
                _log(log, "Aurora path hit Play Store sign-in -> bail (not blocking Magisk)")
                break
            _sleep(adb, 0.8)
            continue
        if "anonymous" in ui or "匿名" in ui:
            if _tap_first_exact(adb, ["Anonymous", "匿名"]):
                notes.append("anon_again")
                _sleep(adb, 1.5)
                continue

        # 系统安装确认弹窗优先
        if "do you want to install this app" in ui or ("install" in ui and "cancel" in ui and "manual download" not in ui and "changelog" not in ui):
            h = _tap_first_exact(adb, ["INSTALL", "Install", "安装"])
            if h:
                notes.append("sys_install:" + h)
                _sleep(adb, 2.0)
                continue

        if any(x in ui for x in (
            "preparing to download", "downloading", "installing", "下载", "安装中",
            "queued", "pending", "percent", "%", "preparing",
        )):
            notes.append("progress")
            _sleep(adb, 4.0)
            continue

        hit = tap_labels(
            [
                "INSTALL",
                "Install",
                "Update",
                "Get",
                "Download",
                "安装",
                "更新",
                "重新安装",
                "Reinstall",
            ]
        )
        if hit:
            last_tap = hit
            notes.append(f"tap:{hit}")
            _sleep(adb, 2.5)
            dismiss_runtime()
            continue

        xml = _dump_xml(adb)
        for key in ("Install", "Update", "Get", "安装"):
            b = adb.find_node_bounds(content_desc=key, xml=xml) or adb.find_node_bounds(
                text_substr=key, xml=xml
            )
            if b:
                adb.tap_bounds(b)
                notes.append(f"bounds:{key}")
                _sleep(adb, 2.0)
                break
        else:
            _sleep(adb, 3.0)

    info = venmo_split_info(adb)
    _log(log, f"Aurora wait end complete={info.get('complete')} splits={info.get('split_count')} last={last_tap}")
    try:
        adb.release_ui_control(home=True)
    except Exception:
        pass
    return ("ok" if info.get("complete") else "timeout") + ":" + ";".join(notes)[:260]


def ensure_venmo_ready(adb, log: OptionalLog = None, prefer_aurora: bool = False) -> dict:
    """确保 Venmo 为完整 split 安装，可启动。

    prefer_aurora=True 时优先走 Aurora 匿名安装；否则优先本地 venmo_bundle install-multiple。
    禁止安装单 base.apk。
    """
    _raise_if_cancelled(adb, "ensure_venmo_ready")
    info = venmo_split_info(adb)
    if info.get("complete"):
        _log(log, f"Venmo complete already splits={info.get('split_count')}")
        return {"ok": True, "method": "already", "info": info}

    if info.get("installed") and not info.get("complete"):
        _log(log, f"Venmo incomplete splits={info.get('split_count')} -> uninstall")
        uninstall_venmo(adb, log=log)

    results = []
    if prefer_aurora:
        msg = open_aurora_for_venmo(adb, log=log)
        info = venmo_split_info(adb)
        if info.get("complete"):
            return {"ok": True, "method": "aurora", "msg": msg, "info": info}
        results.append({"method": "aurora", "msg": msg, "info": info})

    if len(bundle_files()) >= 3:
        r = install_venmo_bundle(adb, log=log)
        results.append(r)
        if r.get("ok"):
            return r

    if not prefer_aurora:
        msg = open_aurora_for_venmo(adb, log=log)
        info = venmo_split_info(adb)
        if info.get("complete"):
            return {"ok": True, "method": "aurora", "msg": msg, "info": info}
        results.append({"method": "aurora", "msg": msg, "info": info})

    info = venmo_split_info(adb)
    return {"ok": bool(info.get("complete")), "method": "failed", "results": results, "info": info}

# - welcome-bounce-v1: 提交后回欢迎页快速恢复/失败，禁止验证候选后再 resubmit
# -*- coding: utf-8 -*-
"""Venmo 登录：清数据 -> 欢迎页点 Log in -> 输账密 -> 识别红框结果。
- fix-false-success-v1: early-lock 仅红框(wrong/risk/no_net)；SUCCESS 不 early-lock；登录表单在前台禁止 SUCCESS
- mask-phone-full-v3: 节点级提取完整手机掩码(3**) ***-**80；拒绝单独 *****95
- submit-no-forgot-v3: 填密后先收键盘再单次点 nextButton，禁止滑到 Forgot password\n- submit-lock-result-v4: 提交中出现风控/错密/无网红框立即锁定结果，禁止反复重提
- result-then-next-v5: 红框结果后禁止再点密码/ENTER/Forgot；立刻返回切下一账号；提交后先等结果再考虑 ENTER 兜底


更新记录 2026-07-24:
- mask-timeout-retry-v2: 识别验证页/掩码；禁止验证页打勾resubmit；超时重登直到出结果
- 适配欢迎页 welcome_login_button 再进表单
- 用真实 resource-id 定位邮箱/密码/登录按钮
- 每步日志 + 超时截图/UI dump
- 特殊字符密码安全输入
- step3: 登录前 force-stop Kitsune/Magisk（绝不停 NekoBox）；识别 Magisk UI 抢前台并重拉 Venmo
- step3fix: uiautomator null root 不 HOME；启动后按 focus/空 dump 重拉 Venmo
- step3 submit: hide kb + multi tap Log in/nextButton; resubmit while form remains
- step3 anti-freeze: poll 3.5s; launcher 只重拉; force-stop 少 HOME
- step3 nav: recover from launcher after welcome tap; re-tap welcome Log in
- portrait-lock: clear_and_start 前锁定竖屏，避免横竖屏狂切导致点错坐标
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from core.account_store import LoginResult, classify_ui_text
from core.adb_client import AdbClient
from paths import LOG_TEST_DIR, SCREENSHOTS_DIR

logger = logging.getLogger("mumuvenmo")
OptionalLog = Optional[Callable[[str], None]]

# 实测 resource-id
ID_WELCOME_LOGIN = "com.venmo:id/welcome_login_button"
ID_EMAIL = "com.venmo:id/publicCredentialInputEditText"
ID_PASSWORD = "com.venmo:id/primaryEditText"
ID_LOGIN_BTN = "com.venmo:id/nextButton"

# 会抢前台、必须 force-stop 的包（绝不要包含 NekoBox moe.nb4a）
PKG_KITSUNE = "io.github.huskydg.magisk"
PKG_MAGISK_OFFICIAL = "com.topjohnwu.magisk"
PKG_NEKOBOX = "moe.nb4a"
BLOCKER_PACKAGES = (PKG_KITSUNE, PKG_MAGISK_OFFICIAL)


@dataclass
class LoginOutcome:
    result: LoginResult
    message: str = ""
    masked_phone: str = ""
    used_account: str = ""
    wrong_account: str = ""
    ui_snippet: str = ""


# success-candidate-timeout-v1: 见验证页不因 dump 卡死 timeout 重登
class VenmoLogin:
    def __init__(
        self,
        adb: AdbClient,
        package: str = "com.venmo",
        login_timeout: int = 90,
        log: OptionalLog = None,
    ):
        self.adb = adb
        self.package = package
        self.login_timeout = login_timeout
        self.log = log or (lambda m: logger.info(m))
        # 提交过程中短暂弹出的红框结果（风控/错密/无网）必须锁定，禁止反复重提
        self._early_result: LoginResult | None = None
        self._early_message: str = ""

    def _log(self, msg: str) -> None:
        try:
            self.log(str(msg).encode("utf-8", "replace").decode("utf-8"))
        except Exception:
            try:
                self.log(repr(msg))
            except Exception:
                pass

    def _save_debug(self, tag: str) -> str:
        ts = time.strftime("%Y%m%d_%H%M%S")
        xml_path = LOG_TEST_DIR / f"ui_{tag}_{ts}.xml"
        png_path = SCREENSHOTS_DIR / f"{tag}_{ts}.png"
        try:
            xml = self.adb.uiautomator_dump() or ""
            xml_path.write_text(xml, encoding="utf-8")
        except Exception as e:
            self._log(f"save xml fail: {e}")
            xml = ""
        try:
            self.adb.screencap(png_path)
        except Exception as e:
            self._log(f"screencap fail: {e}")
        return xml

    def _force_stop_blockers(self) -> None:
        """把抢前台的 Kitsune/Magisk force-stop；绝不 force-stop NekoBox。

        减少 HOME/BACK 轰炸，避免 UIAutomator/输入通道被占导致人工点白屏。
        """
        for pkg in BLOCKER_PACKAGES:
            if pkg == PKG_NEKOBOX:
                continue
            try:
                out = self.adb.force_stop(pkg)
                self._log(f"force-stop blocker {pkg} -> {(out or '').strip()[:60]}")
            except Exception as e:
                self._log(f"force-stop {pkg}: {e}")
        try:
            self.adb.shell("input", "keyevent", "3", timeout=8)  # HOME once
        except Exception as e:
            self._log(f"home key: {e}")
        time.sleep(0.2)


    def _release_ui(self) -> None:
        """登录步骤间释放 UIAutomator，降低人工点白屏概率。"""
        try:
            self.adb.release_ui_control(home=False)
        except Exception as e:
            self._log(f"release_ui: {e}")


    def _is_magisk_ui(self, ui: str) -> bool:
        low = (ui or "").lower()
        if any(k in low for k in ("log in", "sign up", "email, username", "pay for everything", "venmo")):
            return False
        markers = (
            "uninstall magisk", "io.github.huskydg.magisk", "v27.2-kitsune",
            "kitsune mask", "zygisk", "ramdisk",
        )
        # 纯 Magisk 首页常以 Magisk 标题开头
        if "magisk" in low and any(m in low for m in ("install", "zygisk", "uninstall", "superuser", "modules")):
            return True
        return any(m in low for m in markers)

    def _is_launcher_ui(self, ui: str) -> bool:
        low = (ui or "").lower()
        if self._is_magisk_ui(ui):
            return True
        launcher_keys = (
            "mumu store", "app cloner", "kitsune mask", "lawnchair",
            "search games", "folder: gadget", "gallery", "chromium",
        )
        venmo_keys = (
            "log in", "sign up", "email, username", "password",
            "pay for everything", "pay your people", "forgot password",
            "create account", "publiccredential",
        )
        has_launcher = any(k in low for k in launcher_keys)
        has_venmo = any(k in low for k in venmo_keys)
        return has_launcher and not has_venmo

    def _on_credential_form(self, xml: str | None = None) -> bool:
        xml = xml if xml is not None else (self.adb.uiautomator_dump() or "")
        if self.adb.find_node_bounds(resource_id=ID_EMAIL, xml=xml):
            return True
        low = (self.adb.ui_full_text() or "").lower()
        return "email, username" in low and "password" in low

    def clear_and_start(self) -> None:
        try:
            lp = self.adb.lock_portrait()
            self._log(
                f"lock portrait before clear: "
                f"{(lp or '').replace(chr(10), ' ')[:140]} | {self.adb.display_rotation()}"
            )
        except Exception as e:
            self._log(f"lock portrait warn: {e}")
        self._log(f"pm clear {self.package}")
        self._force_stop_blockers()
        try:
            self.adb.force_stop(self.package)
        except Exception as e:
            self._log(f"force_stop venmo: {e}")
        out = self.adb.pm_clear(self.package)
        self._log(f"clear -> {(out or chr(32)).strip()[:120]}")
        time.sleep(1.0)
        self._log("start app")
        # 亮屏，避免 null root / 空 dump
        try:
            self.adb.shell("input", "keyevent", "224", timeout=5)
        except Exception:
            pass
        out2 = self.adb.start_app(self.package)
        self._log(f"start -> {(out2 or chr(32)).replace(chr(10), chr(32))[:160]}")
        for i in range(10):
            time.sleep(1.8)
            # 空 dump / 焦点丢失：不 HOME，直接重拉 Venmo
            try:
                focus = self.adb.shell("dumpsys", "window", timeout=15) or ""
            except Exception:
                focus = ""
            if "com.venmo" not in focus and i >= 1:
                self._log(f"venmo not focused attempt={i+1}, restart app")
                try:
                    self.adb.start_app(self.package)
                except Exception as e:
                    self._log(f"restart: {e}")
                time.sleep(1.2)
            try:
                ui = self.adb.ui_full_text() or ""
            except Exception:
                ui = ""
            low = ui.lower()
            keys = (
                "log in", "sign up", "email, username", "password",
                "pay your people", "pay for everything", "venmo",
            )
            if any(k in low for k in keys) and not self._is_launcher_ui(ui):
                self._log(f"venmo foreground ok attempt={i+1}")
                break
            if not ui.strip() and i >= 2:
                self._log(f"empty UI dump attempt={i+1}, wake+restart venmo")
                try:
                    self.adb.shell("input", "keyevent", "224", timeout=5)
                    self.adb.start_app(self.package)
                except Exception as e:
                    self._log(f"empty recover: {e}")
            if self._is_magisk_ui(ui):
                self._log(f"Magisk/Kitsune still front, force-stop kitsune + restart venmo attempt={i+1}")
                self._force_stop_blockers()
                try:
                    out2 = self.adb.start_app(self.package)
                    self._log(f"restart venmo -> {(out2 or chr(32)).replace(chr(10), chr(32))[:120]}")
                except Exception as e:
                    self._log(f"restart venmo fail: {e}")
            elif "nekobox" in low or "add profile" in low or "please select a profile" in low or "moe.nb4a" in low:
                # 不 force-stop NekoBox，只 HOME 后重拉 Venmo
                self._log(f"NekoBox still front, HOME + restart venmo attempt={i+1}")
                try:
                    self.adb.shell("input", "keyevent", "3", timeout=10)
                except Exception:
                    pass
                time.sleep(0.4)
                try:
                    out2 = self.adb.start_app(self.package)
                    self._log(f"restart venmo -> {(out2 or chr(32)).replace(chr(10), chr(32))[:120]}")
                except Exception as e:
                    self._log(f"restart venmo fail: {e}")
            elif self._is_launcher_ui(ui):
                self._log(f"on launcher, restart venmo attempt={i+1}")
                try:
                    self.adb.start_app(self.package)
                except Exception:
                    pass
            else:
                try:
                    self.adb.start_app(self.package)
                except Exception:
                    pass
        time.sleep(1.2)


    def _ime_shown(self) -> bool:
        try:
            out = self.adb.shell("dumpsys", "input_method", timeout=6) or ""
        except Exception:
            return False
        if "mInputShown=true" in out:
            return True
        compact = out.lower().replace(" ", "")
        return "minputshown=true" in compact or "misinputviewshown=true" in compact

    def _dismiss_ime_keep_form(self) -> None:
        """轻量收键盘：只用 ESC，禁止纵向 swipe（会滚到 Forgot password）。"""
        try:
            self.adb.shell("input", "keyevent", "111", timeout=5)  # KEYCODE_ESCAPE
        except Exception as e:
            self._log(f"esc dismiss ime: {e}")
        time.sleep(0.2)

    def _hide_keyboard(self) -> None:
        """兼容旧调用名。"""
        self._dismiss_ime_keep_form()

    def _still_on_login_form(self, ui: str = "", xml: str = "") -> bool:
        ui = ui or ""
        try:
            from core.account_store import _is_verification_or_masked_ui
            if _is_verification_or_masked_ui(ui):
                return False
        except Exception:
            low0 = ui.lower()
            if any(k in low0 for k in (
                "verify it", "text you a code", "text me a code",
                "remember this device", "enter the code", "verification",
            )):
                return False
        low = ui.lower()
        # 无网/WebView 错误页不算还在登录表单，交给 classify 出 NO_NETWORK
        if any(k in low for k in (
            "webpage not available",
            "net::err",
            "err_connection",
            "err_proxy",
            "err_name_not_resolved",
            "err_timed_out",
            "unable to connect",
            "could not connect",
            "something went wrong",
            "having some trouble completing your request",
            "incorrect login",
        )):
            return False
        if "email, username" in low or "forgot password" in low:
            return True
        if "password" in low and "log in" in low:
            if "pay your people" not in low and "pay for everything" not in low:
                return True
        if xml:
            try:
                if self.adb.find_node_bounds(resource_id=ID_EMAIL, xml=xml):
                    try:
                        from core.account_store import _is_verification_or_masked_ui
                        if _is_verification_or_masked_ui(ui):
                            return False
                    except Exception:
                        pass
                    return True
                if self.adb.find_node_bounds(resource_id=ID_PASSWORD, xml=xml):
                    return True
                if self.adb.find_node_bounds(resource_id=ID_LOGIN_BTN, xml=xml):
                    if "password" in low or "email" in low:
                        return True
            except Exception:
                pass
        return False


    def _tap_login_submit(self, reason: str = "submit") -> bool:
        """提交登录：先收键盘，再单次点 Log in/nextButton。禁止滑动，避免误进 Forgot password。

        顺序：
        1) ESC 收起键盘（键盘会挡住底部 Log in，点坐标会点到键盘）
        2) force dump 取 nextButton 中心，单次点击
        3) 仍在表单则密码框 + ENTER 一次
        4) 若误进 Forgot password 页面则 BACK 返回后重点 Log in
        """
        clicked = False

        def _left_form_or_result() -> bool:
            try:
                ui_mid = self.adb.ui_full_text() or ""
            except Exception:
                ui_mid = ""
            low_mid = ui_mid.lower()
            # 误进找回密码页不算成功离开登录
            if self._on_forgot_password_page(ui_mid):
                self._log(f"{reason}: on forgot-password page")
                return False
            res_mid, msg_mid = classify_ui_text(ui_mid)
            # 只 early-lock 红框结果；SUCCESS 必须等 poll 稳定确认（防登录表单误判）
            if res_mid in (
                LoginResult.WRONG_PASSWORD,
                LoginResult.RISK_CONTROL,
                LoginResult.NO_NETWORK,
            ):
                self._early_result = res_mid
                self._early_message = msg_mid or res_mid.value
                self._log(f"{reason}: got result: {res_mid.value} (locked, no resubmit)")
                return True
            if res_mid == LoginResult.SUCCESS:
                self._saw_success_candidate = True
                try:
                    self._success_candidate_phone = self._extract_masked_phone(ui_mid)
                except Exception:
                    self._success_candidate_phone = ""
                self._log(
                    f"{reason}: saw success candidate, wait poll confirm msg={msg_mid} phone={getattr(self, '_success_candidate_phone', '')!r}"
                )
                return True  # 已离开/进验证页，停止连点，但不锁定 SUCCESS
            if not self._still_on_login_form(ui_mid):
                self._log(f"{reason}: left form ui={ui_mid[:120]!r}")
                return True
            return False

        def _recover_forgot() -> None:
            try:
                ui_f = self.adb.ui_full_text() or ""
            except Exception:
                ui_f = ""
            if not self._on_forgot_password_page(ui_f):
                return
            self._log(f"{reason}: recover from Forgot password via BACK")
            try:
                self.adb.input_keyevent(4)  # BACK
            except Exception:
                try:
                    self.adb.shell("input", "keyevent", "4", timeout=5)
                except Exception:
                    pass
            time.sleep(1.0)

        # 0) 欢迎页则先进入表单
        try:
            ui0 = (self.adb.ui_full_text() or "").lower()
        except Exception:
            ui0 = ""
        if ("pay your people" in ui0 or "pay for everything" in ui0) and "email, username" not in ui0:
            self._log(f"{reason}: on welcome before submit, re-enter form")
            try:
                xml_w = self.adb.uiautomator_dump(force=True) or ""
            except Exception:
                xml_w = ""
            self._tap_welcome_login(xml_w)
            time.sleep(2.0)

        # 1) 必须先收键盘，否则 Log in 在键盘后面
        for _ in range(2):
            if self._ime_shown():
                self._dismiss_ime_keep_form()
                time.sleep(0.35)
            else:
                break
        # 额外 BACK 一次仅用于收键盘；若已在表单且无键盘则不动
        if self._ime_shown():
            try:
                self.adb.input_keyevent(4)
            except Exception:
                pass
            time.sleep(0.4)

        _recover_forgot()

        xml = ""
        try:
            xml = self.adb.uiautomator_dump(force=True) or ""
        except Exception as e:
            self._log(f"submit dump fail: {e}")

        def _tap_next_button_once(source_xml: str, tag: str) -> bool:
            btn = None
            try:
                if source_xml:
                    btn = self.adb.find_node_bounds(resource_id=ID_LOGIN_BTN, xml=source_xml)
            except Exception:
                btn = None
            if not btn:
                # 文本 Log in（排除 welcome）
                try:
                    welcome_b = self.adb.find_node_bounds(resource_id=ID_WELCOME_LOGIN, xml=source_xml) if source_xml else None
                except Exception:
                    welcome_b = None
                for needle in ("Log in", "Log In"):
                    try:
                        b = self.adb.find_node_bounds(text_substr=needle, clickable_only=True, xml=source_xml)
                    except Exception:
                        b = None
                    if not b:
                        continue
                    if welcome_b and b == welcome_b:
                        continue
                    # 避免点到 Forgot 附近：要求 y 中心偏下（Log in 在底部）
                    x1, y1, x2, y2 = b
                    cy = (y1 + y2) // 2
                    if cy < 1400:
                        self._log(f"{reason}: skip high Log in text bounds={b} (可能是误匹配)")
                        continue
                    btn = b
                    break
            if not btn:
                return False
            x1, y1, x2, y2 = btn
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            # Forgot password 约在 y=1156-1385；Log in 约 y=2079+。拒绝点到 Forgot 带
            if cy < 1600:
                self._log(f"{reason}: refuse tap y={cy} (forgot zone), bounds={btn}")
                return False
            self._log(f"{reason}: {tag} nextButton/LogIn bounds={btn} center=({cx},{cy}) single-tap")
            self.adb.tap(cx, cy)
            time.sleep(0.9)
            return True

        # 2) 单次点 nextButton，然后优先等待红框/加载，禁止立刻再点密码（会滚到 Forgot password）
        if _tap_next_button_once(xml, "after-ime"):
            clicked = True
            # 提交后轮询结果：有红框/验证/加载就立刻停，绝不再 focus 密码框
            for wait_i in range(6):
                time.sleep(0.45 if wait_i == 0 else 0.55)
                if _left_form_or_result():
                    return True
                try:
                    ui_w = self.adb.ui_full_text() or ""
                except Exception:
                    ui_w = ""
                low_w = ui_w.lower()
                try:
                    from core.account_store import _is_login_loading_text
                    loading_w = _is_login_loading_text(ui_w)
                except Exception:
                    loading_w = ("this may take a few seconds" in low_w) or ("may take a few seconds" in low_w)
                if loading_w:
                    self._log(f"{reason}: submitting/loading after Log in, wait result (no password tap)")
                    # 继续等结果，不进密码 ENTER
                    for _ in range(20):
                        time.sleep(0.8)
                        if _left_form_or_result():
                            return True
                        try:
                            ui2 = self.adb.ui_full_text() or ""
                        except Exception:
                            ui2 = ""
                        try:
                            from core.account_store import _is_login_loading_text
                            if not _is_login_loading_text(ui2) and self._still_on_login_form(ui2):
                                break
                        except Exception:
                            if self._still_on_login_form(ui2) and "this may take a few seconds" not in ui2.lower():
                                break
                    if _left_form_or_result():
                        return True
                    break
                if self._on_forgot_password_page(ui_w):
                    self._log(f"{reason}: landed on Forgot page after Log in, BACK then stop extra taps")
                    _recover_forgot()
                    if _left_form_or_result():
                        return True
                    break

        # 3) 仅当第一次点后仍明确停在登录表单、且无加载/无红框时，才用密码框 ENTER 兜底一次
        #    禁止在已出红框后点密码，否则会滑到 Forgot password
        try:
            ui_before_enter = self.adb.ui_full_text() or ""
        except Exception:
            ui_before_enter = ""
        if _left_form_or_result():
            return True
        still_form = self._still_on_login_form(ui_before_enter)
        try:
            from core.account_store import _is_login_loading_text
            loading_before = _is_login_loading_text(ui_before_enter)
        except Exception:
            loading_before = "this may take a few seconds" in (ui_before_enter or "").lower()
        if still_form and not loading_before and self._early_result is None:
            try:
                xml2 = self.adb.uiautomator_dump(force=True) or ""
            except Exception:
                xml2 = xml
            # 优先再点一次底部 Log in，而不是点密码框（点密码框容易滚到 Forgot）
            if _tap_next_button_once(xml2, "retry-before-enter"):
                clicked = True
                time.sleep(1.0)
                if _left_form_or_result():
                    return True
            else:
                try:
                    pw = self.adb.find_node_bounds(resource_id=ID_PASSWORD, xml=xml2) if xml2 else None
                    if not pw and xml2:
                        pw = self.adb.find_node_bounds(password=True, xml=xml2)
                    if pw:
                        # 只 ENTER，不再 tap 密码框中心（避免页面滚动/焦点到 Forgot）
                        self._log(f"{reason}: ENTER once without re-focus password (avoid Forgot scroll)")
                        self.adb.input_keyevent(66)
                        clicked = True
                        time.sleep(1.2)
                        if _left_form_or_result():
                            return True
                        _recover_forgot()
                except Exception as e:
                    self._log(f"{reason}: enter fallback: {e}")
        else:
            self._log(
                f"{reason}: skip password/ENTER fallback still_form={still_form} "
                f"loading={loading_before} early={getattr(self._early_result, 'value', None)}"
            )

        # 4) 再收一次键盘后重点一次
        if self._ime_shown():
            self._dismiss_ime_keep_form()
            time.sleep(0.3)
        try:
            xml3 = self.adb.uiautomator_dump(force=True) or ""
        except Exception:
            xml3 = ""
        if _tap_next_button_once(xml3, "retry"):
            clicked = True
            if _left_form_or_result():
                return True
            _recover_forgot()

        self._log(f"{reason}: submit done clicked={clicked}")
        return clicked

    def _on_forgot_password_page(self, ui: str = "") -> bool:
        """是否在找回/重置密码页（不是登录表单上的 Forgot password? 链接可见）。"""
        low = (ui or "").lower()
        if not low:
            return False
        # 登录表单本身也有 "Forgot password?" 链接，需结合其它文案
        forgot_page_keys = (
            "reset your password",
            "reset password",
            "forgot your password",
            "send reset link",
            "we'll send you a link",
            "we will send you a link",
            "create a new password",
            "recover your account",
        )
        if any(k in low for k in forgot_page_keys):
            return True
        # 仅有 Forgot 文案且没有 Password 输入/Log in 按钮语义时，也可能是找回页
        if "forgot password" in low and "email, username" not in low and "log in" not in low:
            if "password" not in low or "new password" in low:
                return True
        return False


    def _wait_any_text(self, needles: list[str], timeout: float = 25.0) -> str:
        deadline = time.time() + timeout
        last = ""
        while time.time() < deadline:
            try:
                last = self.adb.ui_full_text()
            except Exception as e:
                self._log(f"ui wait fail: {e}")
                time.sleep(1.5)
                continue
            low = last.lower()
            for n in needles:
                if n.lower() in low:
                    return last
            time.sleep(1.0)
        return last

    def _tap_welcome_login(self, xml: str) -> bool:
        if self.adb.find_node_bounds(resource_id=ID_WELCOME_LOGIN, xml=xml):
            self._log("tap welcome Log in (id)")
            return bool(self.adb.tap_id(ID_WELCOME_LOGIN))
        for label in ("Log in", "Log In", "Sign in"):
            b = self.adb.find_node_bounds(text_substr=label, clickable_only=True, xml=xml)
            if b:
                self._log(f"tap welcome text clickable {label}")
                self.adb.tap_bounds(b)
                return True
            if self.adb.tap_text(label):
                self._log(f"tap welcome text {label}")
                return True
        return False

    def _dismiss_system_dialogs(self) -> None:
        try:
            xml_d = self.adb.uiautomator_dump()
            for key in (
                "While using the app", "Allow", "ONLY THIS TIME",
                "OK", "Continue", "Not now", "Don't allow",
            ):
                b = self.adb.find_node_bounds(text_substr=key, xml=xml_d)
                if b:
                    ui = (self.adb.ui_full_text() or "").lower()
                    if self._is_launcher_ui(ui):
                        return
                    self.adb.tap_bounds(b)
                    self._log(f"dismiss {key}")
                    time.sleep(0.45)
                    xml_d = self.adb.uiautomator_dump()
        except Exception:
            pass

    def _try_go_to_login_form_once(self, attempt: int) -> bool:
        ui = self._wait_any_text(
            ["Log in", "Email, username", "Sign up", "publicCredential", "Password", "Pay your people", "Pay for everything"],
            timeout=14,
        )
        self._log(f"after start texts attempt={attempt} {ui[:180]!r}")

        low0 = (ui or "").lower()
        if self._is_magisk_ui(ui or ""):
            self._log("login form blocked by Magisk/Kitsune UI, force-stop + recover")
            self._force_stop_blockers()
            try:
                self.adb.start_app(self.package)
                time.sleep(3.0)
            except Exception as e:
                self._log(f"magisk recover: {e}")
            ui = self._wait_any_text(
                ["Log in", "Email, username", "Sign up", "publicCredential", "Password", "Pay your people", "Pay for everything"],
                timeout=16,
            )
            self._log(f"after magisk recover texts={ui[:180]!r}")

        low0 = (ui or "").lower()
        if "nekobox" in low0 or "add profile" in low0 or "please select a profile" in low0:
            # 不 force-stop NekoBox，仅 HOME 后重拉 Venmo
            self._log("login form blocked by NekoBox UI, HOME recover")
            try:
                self.adb.shell("input", "keyevent", "3", timeout=10)
            except Exception:
                pass
            time.sleep(0.4)
            try:
                self.adb.start_app(self.package)
                time.sleep(3.0)
            except Exception as e:
                self._log(f"recover: {e}")
            ui = self._wait_any_text(
                ["Log in", "Email, username", "Sign up", "publicCredential", "Password", "Pay your people", "Pay for everything"],
                timeout=16,
            )
            self._log(f"after nekobox recover texts={ui[:180]!r}")

        if self._is_launcher_ui(ui or ""):
            self._log("still on launcher/magisk before form nav, will restart")
            return False

        xml = self.adb.uiautomator_dump() or ""
        if self._on_credential_form(xml):
            self._log("already on credential form")
            return True

        if not self._tap_welcome_login(xml):
            xml = self.adb.uiautomator_dump() or ""
            if self._on_credential_form(xml):
                return True
            self._log("welcome Log in control not found")
        time.sleep(2.2)
        self._dismiss_system_dialogs()

        deadline = time.time() + 18.0
        drop_recoveries = 0
        while time.time() < deadline:
            try:
                ui2 = self.adb.ui_full_text() or ""
            except Exception:
                ui2 = ""
            if self._is_launcher_ui(ui2):
                drop_recoveries += 1
                self._log(f"dropped to launcher after welcome tap recover#{drop_recoveries}")
                if drop_recoveries > 2:
                    return False
                self._force_stop_blockers()
                try:
                    self.adb.start_app(self.package)
                except Exception as e:
                    self._log(f"recover start: {e}")
                time.sleep(2.5)
                try:
                    xml_r = self.adb.uiautomator_dump() or ""
                except Exception:
                    xml_r = ""
                if self._on_credential_form(xml_r):
                    self._log("form ready after launcher recover")
                    return True
                if not self._tap_welcome_login(xml_r):
                    try:
                        size = self.adb.shell("wm", "size", timeout=8) or ""
                        m = re.search(r"(\d+)\s*x\s*(\d+)", size)
                        if m:
                            w, h = int(m.group(1)), int(m.group(2))
                            self._log(f"welcome fallback tap {w//2},{int(h*0.62)}")
                            self.adb.tap(w // 2, int(h * 0.62))
                    except Exception as e:
                        self._log(f"welcome fallback: {e}")
                time.sleep(2.0)
                continue
            xml2 = self.adb.uiautomator_dump() or ""
            if self._on_credential_form(xml2):
                self._log(f"form ready=True texts={ui2[:180]!r}")
                return True
            low = ui2.lower()
            if "email, username" in low or "forgot password" in low:
                self._log(f"form ready by text texts={ui2[:180]!r}")
                return True
            if ("pay your people" in low or "pay for everything" in low) and "log in" in low:
                self._log("still on welcome, re-tap Log in")
                self._tap_welcome_login(xml2)
                time.sleep(1.5)
            time.sleep(1.0)

        ui2 = ""
        try:
            ui2 = self.adb.ui_full_text() or ""
        except Exception:
            pass
        self._log(f"form ready=False texts={ui2[:180]!r}")
        return False

    def _go_to_login_form(self) -> bool:
        """Enter email/password form; restart Venmo if dropped to launcher."""
        for attempt in range(1, 4):
            if self._try_go_to_login_form_once(attempt):
                return True
            self._log(f"login form miss attempt={attempt}/3, force restart venmo")
            self._force_stop_blockers()
            try:
                self.adb.force_stop(self.package)
            except Exception:
                pass
            time.sleep(0.6)
            try:
                self.adb.start_app(self.package)
            except Exception as e:
                self._log(f"restart after form miss: {e}")
            time.sleep(2.5)
        self._save_debug("no_login_form")
        return False

    def _fill_credentials(self, account: str, password: str) -> bool:
        if not self._go_to_login_form():
            return False

        xml = self.adb.uiautomator_dump()
        email_b = self.adb.find_node_bounds(resource_id=ID_EMAIL, xml=xml)
        if not email_b:
            email_b = self.adb.find_node_bounds(text_substr="Email, username", xml=xml)
        if not email_b:
            email_b = self.adb.find_node_bounds(class_endswith="EditText", password=False, xml=xml)
        if not email_b:
            self._log("email field not found")
            self._save_debug("no_email_field")
            return False

        self._log("fill email")
        self.adb.tap_bounds(email_b)
        time.sleep(0.25)
        self.adb.clear_field(50)
        self.adb.input_text_safe(account)
        time.sleep(0.4)

        # 更新 2026-07-24: 密码框可能在输入邮箱后短暂不可见，多策略+重试
        pw_b = None
        for attempt in range(1, 5):
            xml = self.adb.uiautomator_dump() or ""
            pw_b = self.adb.find_node_bounds(resource_id=ID_PASSWORD, xml=xml)
            if not pw_b:
                pw_b = self.adb.find_node_bounds(content_desc="Password", xml=xml)
            if not pw_b:
                pw_b = self.adb.find_node_bounds(text_substr="Password", class_endswith="EditText", xml=xml)
            if not pw_b:
                pw_b = self.adb.find_node_bounds(password=True, class_endswith="EditText", xml=xml)
            if not pw_b:
                # 取第二个 EditText 作为密码框
                try:
                    import re as _re
                    edits = list(_re.finditer(r'class="[^"]*EditText"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml))
                    if len(edits) >= 2:
                        g = edits[1].groups()
                        pw_b = (int(g[0]), int(g[1]), int(g[2]), int(g[3]))
                except Exception:
                    pw_b = None
            if pw_b:
                break
            self._log(f"password field wait attempt={attempt}")
            # 点击 Password 文案区域尝试聚焦
            try:
                self.adb.tap_text("Password")
            except Exception:
                pass
            time.sleep(0.7)
        if not pw_b:
            self._log("password field not found")
            self._save_debug("no_password_field")
            return False

        self._log("fill password")
        self.adb.tap_bounds(pw_b)
        time.sleep(0.25)
        self.adb.clear_field(30)
        self.adb.input_text_safe(password)
        time.sleep(0.35)
        # 填完密码立刻收键盘，避免页面被顶到 Forgot password 区域，并露出 Log in
        self._dismiss_ime_keep_form()
        time.sleep(0.35)

        # 提交：收键盘后单次点 Log in（禁止 swipe）
        self._early_result = None
        self._early_message = ""
        self._tap_login_submit(reason="first_submit")
        time.sleep(1.0)
        # 提交过程中已锁定红框结果（风控/错密/无网）→ 禁止二次提交
        if self._early_result is not None and self._early_result != LoginResult.PENDING:
            self._log(
                f"first_submit locked result={self._early_result.value}, skip second submit"
            )
            return True
        try:
            ui_chk = self.adb.ui_full_text() or ""
            xml_chk = self.adb.uiautomator_dump(force=True) or ""
        except Exception:
            ui_chk, xml_chk = "", ""
        # 再扫一次红框（toast 可能稍晚出现）
        res_chk, msg_chk = classify_ui_text(ui_chk)
        if res_chk in (
            LoginResult.WRONG_PASSWORD,
            LoginResult.RISK_CONTROL,
            LoginResult.NO_NETWORK,
        ):
            self._early_result = res_chk
            self._early_message = msg_chk or res_chk.value
            self._log(f"post-submit locked result={res_chk.value}, skip second submit")
            return True
        if res_chk == LoginResult.SUCCESS:
            self._saw_success_candidate = True
            try:
                self._success_candidate_phone = self._extract_masked_phone(ui_chk)
            except Exception:
                self._success_candidate_phone = ""
            self._log(
                f"post-submit success candidate msg={msg_chk}, phone={getattr(self, '_success_candidate_phone', '')!r}, skip second submit wait poll"
            )
            return True
        if self._on_forgot_password_page(ui_chk):
            self._log("landed on forgot page after submit, BACK + resubmit")
            try:
                self.adb.input_keyevent(4)
            except Exception:
                pass
            time.sleep(0.8)
            self._tap_login_submit(reason="after_forgot_recover")
        elif self._still_on_login_form(ui_chk, xml_chk):
            # 仅当从未见过红框时才二次提交一次（网络慢）
            # 先短等并再 dump：提交后常见 This may take a few seconds，误点会打断
            try:
                from core.account_store import _is_login_loading_text
            except Exception:
                _is_login_loading_text = None
            _loading = False
            if _is_login_loading_text is not None:
                try:
                    _loading = _is_login_loading_text(ui_chk) or _is_login_loading_text(xml_chk or "")
                except Exception:
                    _loading = False
            if not _loading:
                low0 = (ui_chk or "").lower()
                _loading = ("this may take a few seconds" in low0) or ("may take a few seconds" in low0)
            if not _loading:
                time.sleep(2.0)
                try:
                    xml2 = self.adb.uiautomator_dump(force=True) or xml_chk
                except Exception:
                    xml2 = xml_chk
                try:
                    ui2 = self.adb.ui_full_text() or ui_chk
                except Exception:
                    ui2 = ui_chk
                ui_chk, xml_chk = ui2, xml2
                if _is_login_loading_text is not None:
                    try:
                        _loading = _is_login_loading_text(ui_chk) or _is_login_loading_text(xml_chk or "")
                    except Exception:
                        _loading = False
                if not _loading:
                    low2 = (ui_chk or "").lower()
                    _loading = ("this may take a few seconds" in low2) or ("may take a few seconds" in low2)
                # 等待期间若已出结果，直接锁
                try:
                    res2, msg2 = classify_ui_text(ui_chk)
                except Exception:
                    res2, msg2 = LoginResult.PENDING, ""
                if res2 in (
                    LoginResult.RISK_CONTROL,
                    LoginResult.WRONG_PASSWORD,
                    LoginResult.NO_NETWORK,
                    LoginResult.ERROR,
                ):
                    self._early_result = res2
                    self._early_message = msg2 or res2.value
                    self._log(f"post-submit delayed lock result={res2.value}, skip second submit")
                    return True
                if res2 == LoginResult.SUCCESS:
                    self._saw_success_candidate = True
                    try:
                        self._success_candidate_phone = self._extract_masked_phone(ui_chk)
                    except Exception:
                        self._success_candidate_phone = ""
                    self._log(
                        f"post-submit delayed success candidate phone={getattr(self, '_success_candidate_phone', '')!r}"
                    )
                    return True
            if _loading:
                self._log("post-submit loading (This may take a few seconds), skip second submit wait poll")
            else:
                self._log("still on form after first submit, second submit once")
                self._tap_login_submit(reason="second_submit")
        return True


    def _extract_masked_phone(self, ui_text: str) -> str:
        """提取完整掩码手机/邮箱。

        优先：
        1) 完整掩码邮箱 na*****95@gmail.com
        2) 带括号手机 (3**) ***-**80 / (***) ***-*612
        3) 节点级文本拼接后的完整形态
        拒绝单独 *****95 / *****80 作为最终结果（除非真无更长候选）。
        """
        raw = ui_text or ""
        drop = {
            "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",
            "\u200e", "\u200f", "\u2066", "\u2067", "\u2068", "\u2069",
        }
        raw = "".join(ch for ch in raw if ch not in drop)
        raw = raw.replace("\u2018", "'").replace("\u2019", "'")
        raw = raw.replace("\u00a0", " ")

        # 额外：从当前 UI dump 节点列表提取（避免拼接丢失空格/分段）
        node_texts: list[str] = []
        try:
            node_texts = list(self.adb.ui_texts() or [])
        except Exception:
            node_texts = []
        # 也从传入 ui_text 按行拆
        line_texts = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        pieces = []
        for t in node_texts + line_texts:
            t = (t or "").strip()
            if t and t not in pieces:
                pieces.append(t)

        candidates: list[str] = []

        def add_cand(s: str) -> None:
            s = re.sub(r"[ \t]+", " ", (s or "").strip())
            if not s:
                return
            candidates.append(s)

        # A) 单节点/单行直接匹配
        email_re = re.compile(
            r"([A-Za-z0-9._%+\-]*\*+[A-Za-z0-9._%+\-]*@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})"
        )
        # (3**) ***-**80 / (***) ***-*612 / (8**)***-**12
        phone_paren_re = re.compile(
            r"(\(\s*[\d*xX]{1,3}\s*\)\s*[\d*xX*\-.\s]{2,}\d{1,4})"
        )
        # 310-***-**80 / ***-***-1234
        phone_dash_re = re.compile(
            r"((?:\d{0,3}\*{2,}|\*{2,}\d{0,3}|\d{3})[\-.\s]+(?:\*{2,}|\d{3})[\-.\s]+\d{2,4})"
        )
        short_star_re = re.compile(r"(\*{3,}\d{1,4})")

        sources = pieces + [raw, " ".join(pieces)]
        # 相邻节点拼接：处理 "(3**)" + "***-**80"
        for i in range(len(pieces)):
            for j in range(i + 1, min(i + 4, len(pieces) + 1)):
                sources.append(" ".join(pieces[i:j]))

        for src in sources:
            if not src:
                continue
            for m in email_re.finditer(src):
                add_cand(m.group(1))
            for m in phone_paren_re.finditer(src):
                add_cand(re.sub(r"\s+", " ", m.group(1)))
            for m in phone_dash_re.finditer(src):
                add_cand(re.sub(r"\s+", " ", m.group(1)))
            for m in short_star_re.finditer(src):
                add_cand(m.group(1))

        # ending in XX
        m_end = re.search(r"ending in\s*(\d{2,4})", raw, re.I)
        ending = m_end.group(1) if m_end else ""

        # 去重
        uniq: list[str] = []
        seen = set()
        for c in candidates:
            if c in seen:
                continue
            seen.add(c)
            uniq.append(c)

        if not uniq:
            if ending:
                return "****%s" % ending
            return ""

        def is_short_star(s: str) -> bool:
            return bool(re.fullmatch(r"\*+\d{1,4}", s))

        def is_full_email(s: str) -> bool:
            return "@" in s and "*" in s

        def is_full_phone(s: str) -> bool:
            if "(" in s and ")" in s and "*" in s:
                return True
            # 310-***-**80 类
            if re.search(r"[\d*]{2,}[\-.\s]+[\d*]{2,}[\-.\s]+\d{2,4}", s) and "*" in s:
                return True
            return False

        def score(s: str) -> tuple:
            # 更高更好
            full_email = 1 if is_full_email(s) else 0
            full_phone = 1 if is_full_phone(s) else 0
            has_star = 1 if "*" in s else 0
            short = 1 if is_short_star(s) else 0
            # 短星号强降权
            return (full_email, full_phone, has_star, -short, len(s))

        uniq.sort(key=score, reverse=True)
        best = uniq[0]

        # 若最佳是短星号，尝试用更长候选替换
        if is_short_star(best):
            for c in uniq:
                if not is_short_star(c) and (best in c or best[-2:] in c):
                    return c
            # 拼接：若有 (3**) 与 ***-**80 分段
            left = [p for p in pieces if re.fullmatch(r"\(\s*[\d*xX]{1,3}\s*\)", p or "")]
            right = [p for p in pieces if re.search(r"\*{2,}[\-.\s]*\*{0,}\d{1,4}$", p or "")]
            if left and right:
                return re.sub(r"\s+", " ", f"{left[0]} {right[0]}").strip()
            if ending and best.endswith(ending):
                return best  # 无更好选择
            return best

        # 过滤：不要返回明显被截断的邮箱尾巴
        if is_short_star(best):
            for c in uniq:
                if is_full_email(c):
                    return c
        return best


    def attempt_login(self, account: str, password: str) -> LoginOutcome:
        self._log("登录尝试 account=%s" % account)
        self._saw_success_candidate = False
        self._success_candidate_phone = ""
        self._welcome_bounce_count = 0
        self.clear_and_start()
        filled = self._fill_credentials(account, password)
        if not filled:
            xml = self._save_debug("fill_failed")
            self._release_ui()
            return LoginOutcome(
                result=LoginResult.ERROR,
                message="cannot_reach_login_form",
                ui_snippet=(xml or "")[:500],
            )

        # 提交阶段已锁红框：立刻返回切下一账号，禁止再 poll/点表单/滑到 Forgot
        if self._early_result in (
            LoginResult.WRONG_PASSWORD,
            LoginResult.RISK_CONTROL,
            LoginResult.NO_NETWORK,
        ):
            result = self._early_result
            msg = self._early_message or result.value
            phone = ""
            try:
                last_ui = self.adb.ui_full_text() or ""
                phone = self._extract_masked_phone(last_ui)
            except Exception:
                last_ui = ""
            self._log(
                "识别结果(early-lock-immediate): %s phone=%s msg=%s" % (result.value, phone, msg)
            )
            self._save_debug("result_%s" % result.value)
            try:
                self.adb.shell("am", "force-stop", self.package, timeout=10)
            except Exception:
                pass
            self._release_ui()
            return LoginOutcome(
                result=result,
                message=msg,
                masked_phone=phone,
                used_account=account if result in (LoginResult.SUCCESS, LoginResult.RISK_CONTROL) else "",
                wrong_account=account if result == LoginResult.WRONG_PASSWORD else "",
                ui_snippet=(last_ui or "")[:800],
            )

        deadline = time.time() + self.login_timeout
        last_ui = ""
        resubmit_count = 0
        last_resubmit = 0.0
        # 提交阶段已见成功候选：立刻 force dump 确认，避免多线程下 dump 卡死空等到 timeout
        if getattr(self, "_saw_success_candidate", False):
            try:
                self.adb.uiautomator_dump(force=True)
                last_ui = self.adb.ui_full_text() or ""
            except Exception as exc:
                self._log("success-candidate immediate dump fail: %s" % exc)
                last_ui = ""
            res0, msg0 = classify_ui_text(last_ui)
            phone0 = ""
            try:
                phone0 = self._extract_masked_phone(last_ui) or getattr(self, "_success_candidate_phone", "") or ""
            except Exception:
                phone0 = getattr(self, "_success_candidate_phone", "") or ""
            self._log(
                "success-candidate immediate poll ui=%r res=%s phone=%r"
                % (last_ui[:160], res0.value, phone0)
            )
            if res0 == LoginResult.SUCCESS:
                self._save_debug("result_success_immediate")
                self._release_ui()
                return LoginOutcome(
                    result=LoginResult.SUCCESS,
                    message=msg0 or "verification_or_masked_contact",
                    masked_phone=phone0,
                    used_account=account,
                    ui_snippet=last_ui[:800],
                )
        while time.time() < deadline:
            # 红框已锁：零等待返回，避免界面停在表单上再被点到 Forgot password
            if self._early_result in (
                LoginResult.WRONG_PASSWORD,
                LoginResult.RISK_CONTROL,
                LoginResult.NO_NETWORK,
            ):
                result = self._early_result
                msg = self._early_message or result.value
                try:
                    last_ui = self.adb.ui_full_text() or ""
                except Exception:
                    last_ui = ""
                phone = ""
                try:
                    phone = self._extract_masked_phone(last_ui)
                except Exception:
                    phone = ""
                self._log(
                    "识别结果(early-lock): %s phone=%s msg=%s" % (result.value, phone, msg)
                )
                self._save_debug("result_%s" % result.value)
                try:
                    self.adb.shell("am", "force-stop", self.package, timeout=10)
                except Exception:
                    pass
                self._release_ui()
                return LoginOutcome(
                    result=result,
                    message=msg,
                    masked_phone=phone,
                    used_account=account if result in (LoginResult.SUCCESS, LoginResult.RISK_CONTROL) else "",
                    wrong_account=account if result == LoginResult.WRONG_PASSWORD else "",
                    ui_snippet=last_ui[:800],
                )
            time.sleep(2.0 if getattr(self, "_saw_success_candidate", False) else 3.5)
            try:
                last_ui = self.adb.ui_full_text()
            except Exception as exc:
                self._log("ui dump 失败: %s" % exc)
                continue
            self._log("poll ui=%r" % (last_ui[:160],))

            if self._is_magisk_ui(last_ui):
                self._log("poll: Kitsune/Magisk 抢前台，force-stop 后重拉 Venmo")
                self._force_stop_blockers()
                try:
                    self.adb.start_app(self.package)
                except Exception:
                    pass
                time.sleep(2.0)
                continue
            if self._is_launcher_ui(last_ui):
                self._log("poll: launcher front, re-start Venmo only")
                try:
                    self.adb.start_app(self.package)
                except Exception:
                    pass
                time.sleep(2.0)
                continue

            # 强制 dump 后重新取全文，尽量拿到完整掩码节点
            try:
                self.adb.uiautomator_dump(force=True)
                last_ui = self.adb.ui_full_text() or last_ui
            except Exception:
                pass
            phone = self._extract_masked_phone(last_ui)
            # 短星号时再拼节点重试一次
            if phone and re.fullmatch(r"\*+\d{1,4}", phone):
                try:
                    joined = "\n".join(self.adb.ui_texts() or [])
                    phone2 = self._extract_masked_phone(joined)
                    if phone2 and not re.fullmatch(r"\*+\d{1,4}", phone2):
                        phone = phone2
                except Exception:
                    pass
            # 提交阶段已锁定红框结果 → 直接返回，禁止 poll 再点 Log in
            # SUCCESS 不 early-lock；若历史值误写 SUCCESS 则忽略，走下方 classify
            if self._early_result in (
                LoginResult.WRONG_PASSWORD,
                LoginResult.RISK_CONTROL,
                LoginResult.NO_NETWORK,
            ):
                result = self._early_result
                msg = self._early_message or result.value
                self._log(
                    "识别结果(early-lock): %s phone=%s msg=%s" % (result.value, phone, msg)
                )
                self._save_debug("result_%s" % result.value)
                self._release_ui()
                return LoginOutcome(
                    result=result,
                    message=msg,
                    masked_phone=phone,
                    used_account=account if result in (LoginResult.SUCCESS, LoginResult.RISK_CONTROL) else "",
                    wrong_account=account if result == LoginResult.WRONG_PASSWORD else "",
                    ui_snippet=last_ui[:800],
                )
            result, msg = classify_ui_text(last_ui)
            if result != LoginResult.PENDING:
                if result == LoginResult.SUCCESS and not phone:
                    phone = getattr(self, "_success_candidate_phone", "") or ""
                self._log("识别结果: %s phone=%s msg=%s" % (result.value, phone, msg))
                self._save_debug("result_%s" % result.value)
                self._release_ui()
                return LoginOutcome(
                    result=result,
                    message=msg,
                    masked_phone=phone,
                    used_account=account if result in (LoginResult.SUCCESS, LoginResult.RISK_CONTROL) else "",
                    wrong_account=account if result == LoginResult.WRONG_PASSWORD else "",
                    ui_snippet=last_ui[:800],
                )

            low = last_ui.lower()
            verify_keys = (
                "verify it", "text you a code", "text me a code", "remember this device",
                "enter the code", "verification", "send a code", "two-step",
                "security code", "confirm it",
            )
            from core.account_store import _still_on_login_form_text, _is_verification_or_masked_ui
            on_form = _still_on_login_form_text(last_ui)
            if on_form:
                # 登录表单仍在：绝不当成功；短掩码也忽略（可能是密码点）
                phone = ""
            elif (any(k in low for k in verify_keys) or phone) and (
                _is_verification_or_masked_ui(last_ui) or bool(phone)
            ):
                # 验证页若掩码仍是短星号，多等一轮拿完整节点（最多额外 2 次由外循环承担）
                if phone and re.fullmatch(r"\*+\d{1,4}", phone) and (deadline - time.time()) > 8:
                    self._log("verification page short mask=%r, wait fuller text" % (phone,))
                    time.sleep(2.0)
                    continue
                self._log("verification/masked page detected phone=%r" % (phone,))
                self._save_debug("verification")
                self._release_ui()
                return LoginOutcome(
                    result=LoginResult.SUCCESS,
                    message="verification_or_masked_contact",
                    masked_phone=phone,
                    used_account=account,
                    ui_snippet=last_ui[:800],
                )
            now = time.time()
            # 提交后若弹回欢迎页：不要空等到 timeout
            # - 见过验证候选：再点一次欢迎页 Log in，尝试回到验证页
            # - 否则快速记 bounce，超过 2 次直接 ERROR 让外层清数据重登
            is_welcome = (
                ("log in" in low or "sign up" in low)
                and any(
                    k in low
                    for k in (
                        "do more, earn more",
                        "pay your people",
                        "pay for everything",
                        "make your next move with venmo",
                        "score cash back",
                    )
                )
            )
            if is_welcome:
                self._welcome_bounce_count = int(getattr(self, "_welcome_bounce_count", 0) or 0) + 1
                self._log(
                    "poll: bounced to welcome count=%s saw_success=%s"
                    % (self._welcome_bounce_count, bool(getattr(self, "_saw_success_candidate", False)))
                )
                if getattr(self, "_saw_success_candidate", False) and self._welcome_bounce_count <= 2:
                    try:
                        xml_w = self.adb.uiautomator_dump(force=True) or ""
                    except Exception:
                        xml_w = ""
                    self._tap_welcome_login(xml_w)
                    time.sleep(2.0)
                    continue
                if self._welcome_bounce_count >= 2:
                    self._save_debug("welcome_bounce")
                    self._release_ui()
                    return LoginOutcome(
                        result=LoginResult.ERROR,
                        message="bounced_to_welcome_after_submit",
                        ui_snippet=last_ui[:800],
                    )
                try:
                    xml_w = self.adb.uiautomator_dump(force=True) or ""
                except Exception:
                    xml_w = ""
                self._tap_welcome_login(xml_w)
                time.sleep(1.5)
                continue

            # 已锁定红框结果 或 验证页 不再重提
            if self._early_result is not None and self._early_result != LoginResult.PENDING:
                continue
            # 已见过验证候选时禁止 resubmit，避免把验证页打回欢迎页
            if getattr(self, "_saw_success_candidate", False):
                continue
            # 加载中（This may take a few seconds）禁止 resubmit，等红框/验证页
            try:
                from core.account_store import _is_login_loading_text
                loading_now = _is_login_loading_text(last_ui)
            except Exception:
                loading_now = ("this may take a few seconds" in low) or ("may take a few seconds" in low)
            if loading_now:
                if int(getattr(self, "_loading_log_ts", 0) or 0) != int(now // 5):
                    self._loading_log_ts = int(now // 5)
                    self._log("poll: login submitting/loading, wait result (no resubmit)")
                continue
            if self._still_on_login_form(last_ui) and resubmit_count < 2 and (now - last_resubmit) >= 10.0:
                if "email, username" in low or "forgot password" in low or (
                    "password" in low and "log in" in low
                ):
                    resubmit_count += 1
                    last_resubmit = now
                    self._log("poll still on form, resubmit #%s" % resubmit_count)
                    self._tap_login_submit(reason="poll_resubmit_%s" % resubmit_count)
                    # 重提后若立刻锁到红框，下一轮 early-lock 返回
        # 已见验证/掩码成功候选时，超时也按成功输出，避免无意义清数据重登
        if getattr(self, "_saw_success_candidate", False):
            phone = ""
            try:
                phone = self._extract_masked_phone(last_ui) or getattr(self, "_success_candidate_phone", "") or ""
            except Exception:
                phone = getattr(self, "_success_candidate_phone", "") or ""
            self._log(
                "login_timeout but saw success candidate, classify SUCCESS phone=%r"
                % (phone,)
            )
            self._save_debug("success_timeout_fallback")
            self._release_ui()
            return LoginOutcome(
                result=LoginResult.SUCCESS,
                message="verification_or_masked_contact",
                masked_phone=phone,
                used_account=account,
                ui_snippet=last_ui[:800],
            )
        self._save_debug("login_timeout")
        self._release_ui()
        return LoginOutcome(
            result=LoginResult.ERROR,
            message="login_timeout",
            ui_snippet=last_ui[:800],
        )

    def login_with_fallback(self, account1: str, password: str, account2: str = "") -> LoginOutcome:
        """账号1失败则试账号2；超时则清数据重登，直到出明确结果。mask-timeout-retry-v2"""
        max_timeout_rounds = 8
        last = None
        for round_i in range(1, max_timeout_rounds + 1):
            self._log("login_with_fallback round=%s/%s a1=%s" % (round_i, max_timeout_rounds, account1))
            first = self.attempt_login(account1, password)
            last = first
            if first.result in (LoginResult.SUCCESS, LoginResult.RISK_CONTROL):
                first.used_account = account1
                return first
            if first.result == LoginResult.NO_NETWORK:
                return first
            if first.result == LoginResult.WRONG_PASSWORD:
                break
            if first.result == LoginResult.ERROR and first.message in (
                "login_timeout", "cannot_reach_login_form", "bounced_to_welcome_after_submit",
            ):
                self._log("timeout/error=%s, re-login round=%s" % (first.message, round_i))
                continue
            if first.result == LoginResult.ERROR and round_i < max_timeout_rounds:
                self._log("error=%s, re-login round=%s" % (first.message, round_i))
                continue
            break

        if last is None:
            return LoginOutcome(result=LoginResult.ERROR, message="no_attempt")

        if last.result == LoginResult.WRONG_PASSWORD and account2:
            self._log("账号1密码错误，改用账号2: %s" % account2)
            for round_i in range(1, max_timeout_rounds + 1):
                second = self.attempt_login(account2, password)
                last = second
                if second.result in (LoginResult.SUCCESS, LoginResult.RISK_CONTROL):
                    second.used_account = account2
                    second.wrong_account = account1
                    return second
                if second.result == LoginResult.NO_NETWORK:
                    return second
                if second.result == LoginResult.WRONG_PASSWORD:
                    second.wrong_account = account2
                    second.message = (second.message or "") + " | both_wrong a1=%s" % account1
                    return second
                if second.result == LoginResult.ERROR and second.message in (
                    "login_timeout", "cannot_reach_login_form", "bounced_to_welcome_after_submit",
                ):
                    self._log("a2 timeout/error=%s, re-login round=%s" % (second.message, round_i))
                    continue
                if second.result == LoginResult.ERROR and round_i < max_timeout_rounds:
                    continue
                break
            return last

        return last


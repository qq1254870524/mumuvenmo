from pathlib import Path
ROOT = Path(r"C:\Users\zhang\Desktop\mumuvenmo")
p = ROOT / "core" / "root_setup.py"
text = p.read_text(encoding="utf-8")
orig = text
if "hide-install-once-kill-v1" not in text:
    text = text.replace(
        "# 2026-07-25 only-patch-instant-reopen-v1:",
        "# 2026-07-25 hide-install-once-kill-v1: Hide后同会话直接Install；仅无Direct第3项才杀进程重启1次；禁止反复重启Kitsune\n# 2026-07-25 only-patch-instant-reopen-v1:",
        1,
    )
text = text.replace(
    "        - 点过 Install 仍无第3项：先同会话软重试(BACK+Forever授权)；最多杀进程重开 1 次\n",
    "        - 点过 Install 仍无第3项：先同会话软重试1次(BACK+Forever授权，不杀进程)；仍无第3项才杀进程重开，最多 1 次\n",
    1,
)
old_loop = """        need_kill_reopen = False
        opened_once = False
        soft_retry_used = 0
        # only-patch 时用户要求瞬间重启 Magisk 再点 Install；允许最多 3 次杀进程
        max_kill = 3
        total_rounds = max(5, int(max_reopen) + 3)

        for round_i in range(total_rounds):
            if self._cancelled():
                result[\"detail\"] = \"cancelled\"
                return result

            if round_i == 0:
                _open_once(\"first\", force_relaunch=False)
                opened_once = True
            elif need_kill_reopen and reopen_used < max_kill:
                reopen_used += 1
                need_kill_reopen = False
                _kill_reopen(
                    f\"第{reopen_used}/{max_kill}次杀进程重开\"
                    f\"(已点Install后仍未找到 Direct Install；仅允许最多{max_kill}次)\"
                )
                opened_once = True
            else:
                # 同会话软重试：BACK 回首页，不 force-stop
                soft_retry_used += 1
                self._log(
                    log,
                    f\"VM={vmindex} 同会话软重试 round={round_i} soft={soft_retry_used} \"
                    f\"（不杀 Kitsune 进程）\",
                )
"""
new_loop = """        need_kill_reopen = False
        opened_once = False
        soft_retry_used = 0
        # 用户硬规则：Forever->Allow 不杀进程；Hide->Install 同会话；
        # 仅 Install 后找不到 Direct Install 第3项才杀进程重启，最多 1 次
        max_kill = 1
        max_soft = 1
        total_rounds = max(3, int(max_kill) + int(max_soft) + 1)

        for round_i in range(total_rounds):
            if self._cancelled():
                result[\"detail\"] = \"cancelled\"
                return result

            if round_i == 0:
                _open_once(\"first\", force_relaunch=False)
                opened_once = True
            elif need_kill_reopen and reopen_used < max_kill:
                reopen_used += 1
                need_kill_reopen = False
                _kill_reopen(
                    f\"第{reopen_used}/{max_kill}次杀进程重开\"
                    f\"(已点Install后仍未找到 Direct Install；仅允许最多{max_kill}次)\"
                )
                opened_once = True
            else:
                # 同会话软重试：BACK 回首页，不 force-stop；超过 max_soft 仍无第3项才允许 kill
                soft_retry_used += 1
                self._log(
                    log,
                    f\"VM={vmindex} 同会话软重试 round={round_i} soft={soft_retry_used}/{max_soft} \"
                    f\"（不杀 Kitsune 进程）\",
                )
"""
if old_loop not in text:
    raise SystemExit("root_setup loop block not found")
text = text.replace(old_loop, new_loop, 1)
old_only = """            only_patch = str(last_opts or \"\").startswith(\"ONLY_PATCH\") or (
                \"select and patch\" in str(last_opts or \"\").lower()
                and \"modify /system\" not in str(last_opts or \"\").lower()
            )
            # 无第3项 Direct Install：瞬间重启 Magisk，不软等、不 BACK 空转
            if only_patch:
                if reopen_used < max_kill:
                    need_kill_reopen = True
                    self._log(
                        log,
                        f\"VM={vmindex} round={round_i} 无第3项 Direct Install \"
                        f\"visible={last_opts!r} → 瞬间重启Magisk再点Install \"
                        f\"({reopen_used+1}/{max_kill})\",
                    )
                else:
                    need_kill_reopen = False
                    self._log(
                        log,
                        f\"VM={vmindex} round={round_i} 已用尽重启Magisk配额({max_kill})，\"
                        f\"visible={last_opts!r} → 结束 Direct Install 尝试\",
                    )
                    break
"""
new_only = """            only_patch = str(last_opts or \"\").startswith(\"ONLY_PATCH\") or (
                \"select and patch\" in str(last_opts or \"\").lower()
                and \"modify /system\" not in str(last_opts or \"\").lower()
            )
            # 无第3项：先同会话软重试1次；软重试用尽才杀进程重启1次
            if only_patch:
                if soft_retry_used < max_soft:
                    need_kill_reopen = False
                    self._log(
                        log,
                        f\"VM={vmindex} round={round_i} 无第3项 Direct Install \"
                        f\"visible={last_opts!r} → 同会话软重试 \"
                        f\"(soft={soft_retry_used}/{max_soft}，不杀进程)\",
                    )
                elif reopen_used < max_kill:
                    need_kill_reopen = True
                    self._log(
                        log,
                        f\"VM={vmindex} round={round_i} 无第3项 Direct Install \"
                        f\"visible={last_opts!r} → 杀进程重启Magisk再点Install \"
                        f\"({reopen_used+1}/{max_kill})\",
                    )
                else:
                    need_kill_reopen = False
                    self._log(
                        log,
                        f\"VM={vmindex} round={round_i} 已用尽重启Magisk配额({max_kill})，\"
                        f\"visible={last_opts!r} → 结束 Direct Install 尝试\",
                    )
                    break
"""
if old_only not in text:
    raise SystemExit("only_patch block not found")
text = text.replace(old_only, new_only, 1)
old_hide_ok = """            # 点 Hide 后立刻检查首页，成功则马上返回去点 Install
            try:
                xml2 = self.adb.uiautomator_dump(force=True) or \"\"
            except Exception:
                xml2 = \"\"
            low2 = (xml2 or \"\").lower()
            if _home_ready(low2) or (
                \"home_notice_hide\" not in low2
                and \"unofficial version of magisk\" not in low2
            ):
                notes.append(\"hidden\")
                notes.append(\"hide_done_go_install\")
                break
            # 仍在则最多再点一次，不再 monkey 重开
            time.sleep(0.25)
        return \"|\".join(notes)[:280]
"""
new_hide_ok = """            # 点 Hide 后立刻检查首页：必须仍在 Kitsune 且见 Install/Uninstall 才算成功
            try:
                xml2 = self.adb.uiautomator_dump(force=True) or \"\"
            except Exception:
                xml2 = \"\"
            low2 = (xml2 or \"\").lower()
            kitsune_ui = (
                \"io.github.huskydg.magisk:id/\" in low2
                or \"com.topjohnwu.magisk:id/\" in low2
                or \"home_magisk\" in low2
            )
            if kitsune_ui and _home_ready(low2) and not _has_notice(low2):
                notes.append(\"hidden\")
                notes.append(\"hide_done_go_install\")
                break
            if kitsune_ui and (not _has_notice(low2)) and (
                \"install\" in low2 or \"uninstall\" in low2 or \"home_magisk\" in low2
            ):
                notes.append(\"hidden_no_notice\")
                notes.append(\"hide_done_go_install\")
                break
            # 仍有警告卡则再点一次 Hide；绝不因此 force-stop/reopen Kitsune
            notes.append(\"hide_retry_same_session\")
            time.sleep(0.25)
        return \"|\".join(notes)[:280]
"""
if old_hide_ok not in text:
    raise SystemExit("hide ok block not found")
text = text.replace(old_hide_ok, new_hide_ok, 1)
if text == orig:
    raise SystemExit("root_setup no changes applied")
p.write_text(text, encoding="utf-8")
print("root_setup.py patched OK")

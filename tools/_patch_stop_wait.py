# -*- coding: utf-8 -*-
"""Patch only: restore elif setup branch + stop waits for current login before VM shutdown."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"C:\Users\zhang\Desktop\mumuvenmo")
WE = ROOT / "core" / "worker_engine.py"
UI = ROOT / "app_ui.py"
CFG = ROOT / "core" / "config_store.py"


def must_replace(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"FAIL {label}: pattern not found")
    return text.replace(old, new, 1)


# ---------- worker_engine.py ----------
we = WE.read_text(encoding="utf-8")

# 1) header note: mark stop fix; keep history but clarify vpn-gate reverted
old_hdr = (
    "# 2026-07-25 first-setup-vpn-gate-v1: 首次setup代理不通后仍走NekoBox导入/换绑；无tun禁止裸登录\n"
)
new_hdr = (
    "# 2026-07-25 stop-wait-login-v1: 普通停止必须等当前登录完成才关模拟器；未完成不关机；仅强制停止可超时关机\n"
    "# 2026-07-25 first-setup-vpn-gate-v1 REVERTED: 恢复 elif，不改原首次setup/STEP3流程\n"
)
if old_hdr in we:
    we = we.replace(old_hdr, new_hdr, 1)
elif "stop-wait-login-v1" not in we:
    we = we.replace(
        "# 2026-07-25 layout-tight-v1:",
        "# 2026-07-25 stop-wait-login-v1: 普通停止等当前登录完成再关模拟器\n# 2026-07-25 layout-tight-v1:",
        1,
    )

# 2) init: force-stop event
old_init = """        self.running = False
        # 全局串行 create/delete，避免多线程同时删建冲突
        self._vm_ops_lock = threading.Lock()
        # 同步代理池刷新参数
        self._sync_proxy_config()
"""
new_init = """        self.running = False
        # 全局串行 create/delete，避免多线程同时删建冲突
        self._vm_ops_lock = threading.Lock()
        # 强制停止接管优雅停止等待
        self._force_stop_event = threading.Event()
        # 同步代理池刷新参数
        self._sync_proxy_config()
"""
if "self._force_stop_event" not in we:
    we = must_replace(we, old_init, new_init, "init force event")

# 3) replace stop_and_shutdown entirely with safer version
old_stop_fn_start = "    def stop_and_shutdown(\n"
idx = we.find(old_stop_fn_start)
if idx < 0:
    raise SystemExit("FAIL stop_and_shutdown not found")
# find next def at same indent after this
m = re.search(r"\n    def start\(self, vm_indices: list\[int\]\) -> None:", we[idx:])
if not m:
    raise SystemExit("FAIL start() after stop_and_shutdown not found")
end = idx + m.start()
old_fn = we[idx:end]
new_fn = '''    def stop_and_shutdown(
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
            join_timeout = min(float(join_timeout), 12.0)
            self.log(f"强制停止: join_timeout 压缩为 {join_timeout:.0f}s，超时后仍可关模拟器")
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
        if shutdown_vms and vms and (not result["joined"]) and (not force):
            result["shutdown_skipped"] = True
            result["ok"] = False
            self.log(
                "当前登录任务尚未完成：跳过关闭模拟器，保持停止信号"
                "（不再领新号；当前号继续跑完后可再点停止，或点【强制停止】打断）"
            )
            # 保持 running=True / _stopping=True / threads，便于继续等或强制停止
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

'''
we = we[:idx] + new_fn + we[end:]

# 4) revert first-setup-vpn-gate: if -> elif
old_gate = """            except Exception as exc:
                self.log(f"{worker_id} 首次安装异常(继续登录): {exc}")
        # 首次setup无论是否导入NekoBox，勾选代理时都必须再走完整STEP3（主机测通/换绑/导入/Connect）；无tun禁止裸登录。
        # 旧逻辑用 elif，首次setup代理失败后会跳过本段直接登录。 first-setup-vpn-gate-v1
        if use_nekobox and proxy is not None:
"""
new_gate = """            except Exception as exc:
                self.log(f"{worker_id} 首次安装异常(继续登录): {exc}")
        # 原流程：首次 setup 走上面分支；已 setup 的复用机走 elif STEP3。勿改成 if 破坏原流程。
        elif use_nekobox and proxy is not None:
"""
if old_gate in we:
    we = we.replace(old_gate, new_gate, 1)
elif "elif use_nekobox and proxy is not None:" in we and "first-setup-vpn-gate-v1" not in we.split("elif use_nekobox")[0][-200:]:
    print("INFO: elif already present (or gate already reverted)")
else:
    # try looser match
    loose = re.search(
        r"self\.log\(f\"\{worker_id\} 首次安装异常\(继续登录\): \{exc\}\"\)\n"
        r"        # .*?\n(?:        # .*?\n)?"
        r"        if use_nekobox and proxy is not None:\n",
        we,
    )
    if not loose:
        # check current
        if "elif use_nekobox and proxy is not None:" in we:
            print("INFO: elif branch already restored")
        else:
            raise SystemExit("FAIL could not restore elif branch")
    else:
        we = we[: loose.start()] + re.sub(
            r"if use_nekobox and proxy is not None:",
            "elif use_nekobox and proxy is not None:",
            we[loose.start() : loose.end()],
            count=1,
        ) + we[loose.end() :]
        # clean comments above elif if still has gate comment
        we = we.replace(
            "        # 首次setup无论是否导入NekoBox，勾选代理时都必须再走完整STEP3（主机测通/换绑/导入/Connect）；无tun禁止裸登录。\n"
            "        # 旧逻辑用 elif，首次setup代理失败后会跳过本段直接登录。 first-setup-vpn-gate-v1\n",
            "        # 原流程：首次 setup 走上面分支；已 setup 的复用机走 elif STEP3。\n",
        )

WE.write_text(we, encoding="utf-8")
print("patched", WE)

# ---------- app_ui.py ----------
ui = UI.read_text(encoding="utf-8")
old_ui = '''        join_timeout = float(self.cfg.get("stop_join_timeout_seconds", 90) or 90)
        shutdown_vms = bool(self.cfg.get("stop_shutdown_vms", True))
        self._log(
            f"停止中: 等待当前登录完成(最长 {join_timeout:.0f}s), "
            f"之后{'关闭' if shutdown_vms else '不关闭'}模拟器... "
            f"（卡住请再点一次【强制停止】）"
        )
'''
new_ui = '''        # 普通停止：长时间等待当前登录完成；未完成绝不关模拟器
        join_timeout = float(self.cfg.get("stop_join_timeout_seconds", 1800) or 1800)
        if join_timeout < 300:
            join_timeout = 1800.0
        shutdown_vms = bool(self.cfg.get("stop_shutdown_vms", True))
        self._log(
            f"停止中: 等待当前登录任务完成后再关模拟器(最长 {join_timeout:.0f}s)；"
            f"未完成不关机。{'完成后关闭' if shutdown_vms else '完成后不关闭'}模拟器。"
            f"卡住再点【强制停止】才会打断并关机。"
        )
'''
if old_ui in ui:
    ui = ui.replace(old_ui, new_ui, 1)
else:
    # looser
    m = re.search(
        r"join_timeout = float\(self\.cfg\.get\(\"stop_join_timeout_seconds\", \d+\) or \d+\)\n"
        r"        shutdown_vms = bool\(self\.cfg\.get\(\"stop_shutdown_vms\", True\)\)\n"
        r"        self\._log\(\n"
        r"            f\"停止中:.*?\n"
        r"            f\".*?\n"
        r"            f\".*?\n"
        r"        \)\n",
        ui,
        flags=re.S,
    )
    if not m:
        raise SystemExit("FAIL app_ui stop_login join block not found")
    ui = ui[: m.start()] + new_ui + ui[m.end() :]

# _on_stop_done: handle shutdown_skipped / superseded
old_done = '''    def _on_stop_done(self, result: dict | None = None) -> None:
        result = result or {}
        self._stopping_ui = False
        self._set_run_buttons(running=False, stopping=False)
        if result.get("ok"):
            self._log(
                f"停止完成: joined={result.get('joined')} "
                f"shutdown={result.get('shutdown')} vms={result.get('vms')}"
            )
        else:
            self._log(
                f"停止结束(有警告): {result} "
                f"alive_left={result.get('alive_left')} errors={result.get('shutdown_errors')}"
            )
        try:
            self.refresh_vms()
        except Exception as exc:
            self._log(f"停止后刷新列表失败: {exc}")
'''
new_done = '''    def _on_stop_done(self, result: dict | None = None) -> None:
        result = result or {}
        # 被强制停止接管：由 force 路径的 _on_stop_done 收尾
        if result.get("superseded_by_force"):
            self._log("优雅停止已移交强制停止，等待强制停止完成...")
            return
        # 普通停止超时且未关模拟器：保持“停止中”，当前登录继续，可再点强制停止
        if result.get("shutdown_skipped") and not result.get("force"):
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
'''
if old_done in ui:
    ui = ui.replace(old_done, new_done, 1)
elif "shutdown_skipped" in ui and "superseded_by_force" in ui:
    print("INFO: _on_stop_done already patched")
else:
    raise SystemExit("FAIL _on_stop_done block not found exactly")

# tooltip text if present
ui = ui.replace(
    "停止：先等当前账号登录完成再关模拟器。若一直停不下来，再点一次=强制停止（约12秒内打断并关机）",
    "停止：必须等当前账号登录完成后再关模拟器；超时未完成不关机。再点一次=强制停止（约12秒内打断并关机）",
)

UI.write_text(ui, encoding="utf-8")
print("patched", UI)

# ---------- config_store.py ----------
cfg = CFG.read_text(encoding="utf-8")
cfg2 = cfg.replace(
    '"stop_join_timeout_seconds": 300,',
    '"stop_join_timeout_seconds": 1800,',
)
if cfg2 == cfg and '"stop_join_timeout_seconds": 1800,' not in cfg:
    raise SystemExit("FAIL config stop_join_timeout not updated")
CFG.write_text(cfg2, encoding="utf-8")
print("patched", CFG)

# verify markers
we2 = WE.read_text(encoding="utf-8")
ui2 = UI.read_text(encoding="utf-8")
checks = [
    ("elif use_nekobox", "elif use_nekobox and proxy is not None:" in we2),
    ("no if-gate after setup", "first-setup-vpn-gate-v1" not in we2 or "REVERTED" in we2),
    ("shutdown_skipped", "shutdown_skipped" in we2),
    ("force event", "_force_stop_event" in we2),
    ("ui timeout 1800", "stop_join_timeout_seconds\", 1800" in ui2 or "1800.0" in ui2),
    ("ui skip handler", "shutdown_skipped" in ui2),
]
for name, ok in checks:
    print(("OK" if ok else "BAD"), name)
if not all(ok for _, ok in checks):
    raise SystemExit("verification failed")
print("ALL PATCHES OK")

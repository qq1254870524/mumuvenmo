from pathlib import Path

p = Path("core/root_setup.py")
text = p.read_text(encoding="utf-8")

old_h = "# 2026-07-25 pkg-parallel-v1: ensure_packages 并行装勾选 APK；登录 magisk -v 可用即跳过 UI"
new_h = "# 2026-07-25 pkg-serial-all-v2: 同VM串行装齐勾选APK(adb优先)，避免MuMu -201；跨VM仍可并行\n" + old_h
if "pkg-serial-all-v2" not in text:
    text = text.replace(old_h, new_h, 1)

start = text.find("    def ensure_packages(")
end = text.find("\n    def install_ih8_module_ui(", start)
assert start > 0 and end > start, (start, end)

new_fn = r'''
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

'''.lstrip("\n")

text = text[:start] + new_fn + text[end:]

# provision_new_vm: pass install_venmo / install_aurora on ensure_packages calls
# Only within provision_new_vm function to be safe - replace the three known blocks

def patch_call(src: str, marker_before: str) -> str:
    # find ensure_packages blocks that lack install_venmo after provision starts
    return src

# Simple targeted replacements for the three blocks in provision_new_vm that miss venmo
old1 = """        out.update(
            self.ensure_packages(
                vmindex,
                install_nekobox=want_nekobox,
                install_kitsune=want_kitsune,
                install_ih8=want_ih8,
            )
        )

        if want_aurora:"""

new1 = """        out.update(
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

        if want_aurora:"""

if old1 in text:
    text = text.replace(old1, new1, 1)
    print("patched provision first ensure_packages")
else:
    print("WARN first ensure_packages block not found exact")

old2 = """            if rebooted:
                out.update(
                    self.ensure_packages(
                        vmindex,
                        install_nekobox=want_nekobox,
                        install_kitsune=want_kitsune,
                        install_ih8=want_ih8,
                    )
                )
            # 已在一次会话完成则绝不重复 force-stop 再开做 flags/grant"""

new2 = """            if rebooted:
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
            # 已在一次会话完成则绝不重复 force-stop 再开做 flags/grant"""

if old2 in text:
    text = text.replace(old2, new2, 1)
    print("patched rebooted ensure_packages")
else:
    print("WARN rebooted ensure_packages block not found exact")

old3 = """                    out.update(
                        self.ensure_packages(
                            vmindex,
                            install_nekobox=want_nekobox,
                            install_kitsune=want_kitsune,
                            install_ih8=want_ih8,
                        )
                    )
                    if want_aurora:"""

new3 = """                    out.update(
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
                    if want_aurora:"""

if old3 in text:
    text = text.replace(old3, new3, 1)
    print("patched post-ih8 ensure_packages")
else:
    print("WARN post-ih8 ensure_packages block not found exact")

p.write_text(text, encoding="utf-8")
print("root_setup ok", len(text.splitlines()))

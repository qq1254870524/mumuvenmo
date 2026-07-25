from pathlib import Path
p = Path(r"C:\Users\zhang\Desktop\mumuvenmo\core\root_setup.py")
src = p.read_text(encoding="utf-8")
old_fb = (
    "                    try:\n"
    "                        # 兜底也尽量复用会话，避免再 force-stop 重开\n"
    "                        g = self.grant_shell_via_kitsune_superuser(log=log, reuse_session=True)\n"
    "                        result[\"detail\"] += f\" grant_fallback={str(g)[:80]}\"\n"
    "                    except Exception as exc2:\n"
    "                        result[\"detail\"] += f\" grant_err={exc2}\"\n"
)
new_fb = (
    "                    try:\n"
    "                        # GRANT popup first even on fallback path\n"
    "                        popup = self.grant_shell_prefer_popup(log=log)\n"
    "                        if str(popup).startswith(\"popup_grant_ok\") or \"uid=0\" in str(popup):\n"
    "                            g = popup\n"
    "                            self._log(log, f\"VM={vmindex} 已装路径兜底 GRANT弹窗成功\")\n"
    "                        else:\n"
    "                            g = self.grant_shell_via_kitsune_superuser(log=log, reuse_session=True)\n"
    "                            self._log(log, f\"VM={vmindex} 已装路径兜底 Superuser: {str(g)[:120]}\")\n"
    "                        result[\"detail\"] += f\" grant_fallback={str(g)[:80]}\"\n"
    "                    except Exception as exc2:\n"
    "                        result[\"detail\"] += f\" grant_err={exc2}\"\n"
)
if old_fb not in src:
    raise SystemExit("fallback missing")
src = src.replace(old_fb, new_fb, 1)
old_prov = (
    "                try:\n"
    "                    # 仅失败兜底；优先复用会话，不先杀进程\n"
    "                    out[\"shell_su\"] = self.grant_shell_via_kitsune_superuser(\n"
    "                        log=log, reuse_session=True\n"
    "                    )[:200]\n"
    "                except Exception as exc:\n"
    "                    out[\"shell_su\"] = f\"err:{exc}\"\n"
)
new_prov = (
    "                try:\n"
    "                    # GRANT popup first; Superuser only if popup incomplete\n"
    "                    popup = self.grant_shell_prefer_popup(log=log)\n"
    "                    if str(popup).startswith(\"popup_grant_ok\") or \"uid=0\" in str(popup):\n"
    "                        out[\"shell_su\"] = str(popup)[:200]\n"
    "                        self._log(log, f\"VM={vmindex} provision Shell GRANT弹窗成功\")\n"
    "                    else:\n"
    "                        g = self.grant_shell_via_kitsune_superuser(log=log, reuse_session=True)\n"
    "                        out[\"shell_su\"] = f\"{popup}||superuser={g}\"[:200]\n"
    "                        self._log(log, f\"VM={vmindex} provision Shell Superuser兜底\")\n"
    "                except Exception as exc:\n"
    "                    out[\"shell_su\"] = f\"err:{exc}\"\n"
)
if old_prov not in src:
    raise SystemExit("provision missing")
src = src.replace(old_prov, new_prov, 1)
p.write_text(src, encoding="utf-8")
print("fallback+provision patched")
